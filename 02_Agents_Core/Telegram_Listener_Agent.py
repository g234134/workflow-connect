# Telegram_Listener_Agent.py — 門下省·上行通信員
# Long-polling getUpdates → 白名單檢核 → 指令分派 → sendMessage。
# 嚴守選項 A：未識別指令僅回 help，不寫 Failed；異常事件以 telegram_listener_warning 入 C3。

from __future__ import annotations

import json
import os
import ssl
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from Base_Agent import AgentStatus, Base_Agent  # type: ignore
from gov_paths import (  # type: ignore
    get_artifact_path,
    get_secret,
    get_tang_gov_root,
    resolve_agent_output_path,
)
from GroqHybridRecovery_Agent import DEFAULT_UA, GROQ_MODEL_DEFAULT, GROQ_URL_DEFAULT  # type: ignore


def _ssl_ctx() -> ssl.SSLContext:
    try:
        return ssl.create_default_context()
    except Exception:  # noqa: BLE001
        return ssl._create_unverified_context()  # type: ignore[attr-defined]


def _http_json(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None,
    timeout: int = 35,
) -> Tuple[int, Any]:
    last_err: Optional[BaseException] = None
    for ctx in (_ssl_ctx(), ssl._create_unverified_context()):  # type: ignore[attr-defined]
        try:
            req = urllib.request.Request(url, data=body, method=method)
            for k, v in (headers or {}).items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return resp.getcode(), json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            try:
                parsed = json.loads(err_body) if err_body.strip() else {}
            except json.JSONDecodeError:
                parsed = {"raw": err_body[:2000]}
            return e.code, parsed
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = e
            continue
    return 0, {"error": repr(last_err)}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Telegram_Listener_Agent:
    AGENT_NAME = "Telegram_Listener_Agent"
    DEPARTMENT = "門下省"

    def __init__(self, *, dest_root: Optional[str] = None) -> None:
        self.dest_root = os.path.abspath(dest_root or get_tang_gov_root())
        self.agent = Base_Agent(
            dest_root=self.dest_root,
            department=self.DEPARTMENT,
            agent_name=self.AGENT_NAME,
        )
        self.token = (get_secret("TELEGRAM_BOT_TOKEN", "") or "").strip()
        if not self.token or "PLACEHOLDER" in self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN missing or placeholder")
        # 白名單：多個 chat_id 以逗號分隔；空白則允許所有 private 私訊（不建議）
        raw_ids = (get_secret("TELEGRAM_ALLOWED_CHAT_IDS", "") or "").strip()
        if not raw_ids:
            raw_ids = (get_secret("TELEGRAM_CHAT_ID", "") or "").strip()
        self.allowed_ids = {s.strip() for s in raw_ids.split(",") if s.strip()}
        self.poll_timeout = int(get_secret("TELEGRAM_LISTENER_POLL_TIMEOUT", "") or "25")

        # 狀態檔（offset 持久化、避免重複處理）
        workflows_dir = os.path.dirname(get_artifact_path("status_json"))
        self.state_path = os.path.join(workflows_dir, ".telegram_listener_state.json")
        self.lock_path = os.path.join(workflows_dir, ".telegram_listener.lock")

        # 產出目錄（與歷史腳本相容；本 Agent 多走 C3 / sendMessage）
        self.reports_dir = resolve_agent_output_path(self.dest_root, "06_Exports_Output", "reports")
        # 一般文字 → Groq 副官：背景執行緒回覆，不阻塞指令與長輪詢主迴圈

    def _truncate_reply(self, text: str, max_len: int = 150) -> str:
        s = (text or "").strip().replace("\n", " ")
        if len(s) <= max_len:
            return s
        return s[: max_len - 1] + "…"

    def _snapshot_status_for_llm(self) -> str:
        d = self._read_status()
        slim: Dict[str, Any] = {
            "updated_at": d.get("updated_at"),
            "pipeline_status": d.get("pipeline_status"),
            "asset_value_evaluator": d.get("asset_value_evaluator"),
            "code_cleaner_throttle": d.get("code_cleaner_throttle"),
            "warning_repair": d.get("warning_repair"),
            "runs_tail": (d.get("runs") or [])[-5:],
        }
        raw = json.dumps(slim, ensure_ascii=False)
        return raw[:3500] + ("…" if len(raw) > 3500 else "")

    def _snapshot_c3_for_llm(self) -> str:
        try:
            c3_root = resolve_agent_output_path(self.dest_root, "03_RAG_Database", "c3_logs")
        except Exception:  # noqa: BLE001
            return "C3_Logs: （無法解析路徑）"
        n_jsonl = 0
        last_mtime = 0.0
        sample_tail = ""
        if os.path.isdir(c3_root):
            for dp, _, fns in os.walk(c3_root):
                for fn in fns:
                    if not fn.endswith(".jsonl"):
                        continue
                    fp = os.path.join(dp, fn)
                    n_jsonl += 1
                    try:
                        m = os.path.getmtime(fp)
                        if m > last_mtime:
                            last_mtime = m
                            with open(fp, "rb") as f:
                                f.seek(0, os.SEEK_END)
                                sz = f.tell()
                                f.seek(max(0, sz - 400))
                                tail = f.read().decode("utf-8", errors="replace")
                            lines = [ln for ln in tail.splitlines() if ln.strip()][-2:]
                            sample_tail = " | ".join(lines)[:300]
                    except OSError:
                        continue
        return (
            f"根目錄: {c3_root}\n"
            f".jsonl 事件檔約 {n_jsonl} 個；最近活動尾端（節流）: {sample_tail or '（無）'}"
        )

    def _groq_api_err_hint(self, code: int, data: Any) -> str:
        hint = ""
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict):
                hint = str(err.get("message") or err.get("type") or "")[:90]
            elif isinstance(err, str):
                hint = err[:90]
        base = f"HTTP {code}"
        return f"{base} {hint}".strip() if hint else base

    def _groq_chat_reply(self, user_text: str) -> str:
        key = (get_secret("GROQ_API_KEY", "") or "").strip()
        if not key or "PLACEHOLDER" in key:
            return "報告尚書省：雲端副官密鑰未就緒，請先輸入 /status 查看本地戰況。"

        status_blob = self._snapshot_status_for_llm()
        c3_blob = self._snapshot_c3_for_llm()
        system = (
            "妳是大唐三省六部的 AI 副官。請根據當前的 Status.json 與 C3_Logs 狀態，"
            "用親切且簡潔的方式回覆尚書省（使用者）。"
        )
        user_block = (
            "下列為最新戰況摘要（請據此作答，勿臆測未提供的数据）：\n\n"
            "── Status.json ──\n"
            f"{status_blob}\n\n"
            "── C3_Logs ──\n"
            f"{c3_blob}\n\n"
            "── 使用者訊息 ──\n"
            f"{user_text[:1200]}\n\n"
            "請只輸出給使用者的正文一句話為佳；總長度務必不超過 150 個字元（含標點），不要用 markdown。"
        )
        primary = (get_secret("GROQ_MODEL", "") or GROQ_MODEL_DEFAULT).strip()
        fb_raw = (get_secret("GROQ_FALLBACK_MODEL", "") or "llama-3.1-8b-instant").strip()
        fallback = fb_raw if fb_raw != primary else ""

        url = (get_secret("GROQ_API_URL", "") or GROQ_URL_DEFAULT).strip()
        payload_base: Dict[str, Any] = {
            "temperature": 0.3,
            "max_tokens": 120,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_block},
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": DEFAULT_UA,
            "Accept": "application/json",
        }

        models_try = [primary]
        if fallback:
            models_try.append(fallback)

        last_code = 0
        last_data: Any = {}
        for idx, mdl in enumerate(models_try):
            payload = dict(payload_base)
            payload["model"] = mdl
            body = json.dumps(payload).encode("utf-8")
            code, data = _http_json(url, method="POST", headers=headers, body=body, timeout=45)
            last_code, last_data = code, data
            if code == 200:
                try:
                    choices = data.get("choices") or []
                    content = str((choices[0].get("message") or {}).get("content") or "")
                except Exception:  # noqa: BLE001
                    return "報告尚書省：副官解析回應失敗，請輸入 /status。"
                return self._truncate_reply(content, 150)
            if idx == 0 and fallback and code in (401, 403):
                self.agent.log_event(
                    event="telegram_groq_model_fallback",
                    http=code,
                    primary_model=primary,
                    fallback_model=fallback,
                    hint=self._groq_api_err_hint(code, data),
                )
                continue
            break

        detail = self._groq_api_err_hint(last_code, last_data)
        msg = (
            f"報告尚書省：雲端無回應（{detail}）。403 常見為金鑰失效、帳號未開該模型權限，或來源地區被限制；"
            "請至 console.groq.com 確認；亦可設 GROQ_FALLBACK_MODEL。可先輸入 /status。"
        )
        return self._truncate_reply(msg, 150)

    def _schedule_groq_chat(
        self,
        chat_id: Any,
        user_text: str,
        update_id: Any,
        *,
        message_thread_id: Optional[int] = None,
    ) -> None:
        agent = self.agent

        def _worker() -> None:
            try:
                reply = self._groq_chat_reply(user_text)
                code, body = self.send(chat_id, reply, message_thread_id=message_thread_id)
                ok = bool(isinstance(body, dict) and body.get("ok"))
                agent.log_event(
                    event="telegram_groq_chat_done",
                    chat_id=chat_id,
                    update_id=update_id,
                    send_http=code,
                    send_ok=ok,
                    reply_len=len(reply),
                )
            except Exception as e:  # noqa: BLE001
                agent.log_event(
                    event="telegram_listener_warning",
                    reason="groq_chat_worker_failed",
                    chat_id=chat_id,
                    update_id=update_id,
                    error=repr(e),
                )
                try:
                    self.send(
                        chat_id,
                        "報告尚書省：副官處理時遇到異常，請輸入 /status。",
                        message_thread_id=message_thread_id,
                    )
                except Exception:  # noqa: BLE001
                    pass

        threading.Thread(target=_worker, name="tg-groq-chat", daemon=True).start()
        self.agent.log_event(
            event="telegram_groq_chat_scheduled",
            chat_id=chat_id,
            update_id=update_id,
            preview=user_text[:80],
        )

    def _load_state(self) -> Dict[str, Any]:
        if not os.path.isfile(self.state_path):
            return {"last_update_id": 0, "processed": 0, "started_at": _utc_iso()}
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return {"last_update_id": 0, "processed": 0, "started_at": _utc_iso()}

    def _save_state(self, state: Dict[str, Any]) -> None:
        state["updated_at"] = _utc_iso()
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _acquire_lock(self) -> bool:
        if os.path.exists(self.lock_path):
            try:
                with open(self.lock_path, "r", encoding="utf-8") as f:
                    info = json.load(f)
                pid = int(info.get("pid", 0))
            except Exception:  # noqa: BLE001
                pid = 0
            # 簡易：lock 存在即視為被佔用（避免兩進程搶 getUpdates）
            self.agent.log_event(
                event="telegram_listener_warning",
                reason="lock_exists",
                pid=pid,
                lock_path=self.lock_path,
            )
            return False
        with open(self.lock_path, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "since": _utc_iso()}, f, ensure_ascii=False)
        return True

    def _release_lock(self) -> None:
        try:
            os.remove(self.lock_path)
        except OSError:
            pass

    # ── Telegram I/O ──
    def _api(self, method: str, **params: Any) -> Tuple[int, Any]:
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        body = json.dumps(params, ensure_ascii=False).encode("utf-8")
        return _http_json(
            url,
            method="POST",
            headers={"Content-Type": "application/json"},
            body=body,
            timeout=self.poll_timeout + 10,
        )

    def send(
        self,
        chat_id: Any,
        text: str,
        *,
        message_thread_id: Optional[int] = None,
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, Any]:
        params: Dict[str, Any] = {"chat_id": chat_id, "text": text[:3900]}
        if message_thread_id is not None:
            params["message_thread_id"] = message_thread_id
        if reply_markup is not None:
            params["reply_markup"] = reply_markup
        return self._api("sendMessage", **params)

    def answer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str = "",
        show_alert: bool = False,
    ) -> Tuple[int, Any]:
        return self._api(
            "answerCallbackQuery",
            callback_query_id=callback_query_id,
            text=text[:200] if text else "",
            show_alert=bool(show_alert),
        )

    def get_updates(self, offset: int) -> Tuple[int, Any]:
        return self._api(
            "getUpdates",
            offset=offset,
            timeout=self.poll_timeout,
            allowed_updates=["message", "edited_message", "callback_query"],
        )

    # ── 指令分派 ──
    def _allowed(self, chat_id: Any) -> bool:
        if not self.allowed_ids:
            return True  # 空白表示不限（自有風險）
        return str(chat_id) in self.allowed_ids

    def _read_status(self) -> Dict[str, Any]:
        try:
            with open(get_artifact_path("status_json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return {}

    def _cmd_help(self) -> str:
        return (
            "📜 大唐戰車 · Telegram 指令集\n"
            "/ping — 心跳\n"
            "/help — 顯示本表\n"
            "/whoami — 顯示您的 chat_id\n"
            "/status — 摘要 pipeline_status / runs / 最近波次\n"
            "/lastrun — 最後一次 run 細節\n"
            "/stats — 倉廩計數（quarantine / Archive / C2）\n"
            "/runs [N] — 最近 N 筆 runs（預設 5）\n"
            "/health — 系統自檢（地圖 + 部門碑）\n"
            "（一般文字）私訊本 Bot 即可閒聊；在「群組」若打了字沒反應，多半是 Telegram 預設只把 /指令與 @機器人 轉給 Bot——請在群組裡 @本機器人 再打字，或到 @BotFather → Bot Settings → Group Privacy → Disable。\n"
            "副官會依 Status/C3 摘要作答（150字內）。\n"
            "偵察戰報 Inline 按鈕：callback_data 以 scout: 開頭（尚書省後續可接事件總線）。"
        )

    def _cmd_ping(self) -> str:
        return f"pong · {_utc_iso()}"

    def _cmd_whoami(self, msg: Dict[str, Any]) -> str:
        chat = msg.get("chat") or {}
        frm = msg.get("from") or {}
        return (
            "👤 身分卡\n"
            f"chat_id: {chat.get('id')}\n"
            f"chat_type: {chat.get('type')}\n"
            f"username: @{frm.get('username')}\n"
            f"first_name: {frm.get('first_name')}\n"
            f"在白名單: {'是' if self._allowed(chat.get('id')) else '否'}"
        )

    def _cmd_status(self) -> str:
        d = self._read_status()
        runs = d.get("runs", []) or []
        last = runs[-1] if runs else {}
        waves = []
        for k in (
            "migration_last_wave",
            "liquidation_last_wave",
            "indexing_last_wave",
            "log_backup_last_wave",
            "cleanup_last_wave",
            "recovery_last_wave",
            "hybrid_cloud_last_wave",
            "hybrid_cloud_campaign",
        ):
            v = d.get(k)
            if isinstance(v, dict) and v.get("status"):
                waves.append(f"  · {k}: {v.get('status')}")
        return (
            "🛡️ 系統狀態\n"
            f"pipeline_status: {d.get('pipeline_status', '?')}\n"
            f"updated_at: {d.get('updated_at', '?')}\n"
            f"runs 累計: {len(runs)}\n"
            f"最後 run: {last.get('department')} / {last.get('agent_name')} = {last.get('status')}\n"
            "近期波次:\n" + ("\n".join(waves) if waves else "  · (無)")
        )

    def _cmd_lastrun(self) -> str:
        d = self._read_status()
        runs = d.get("runs", []) or []
        if not runs:
            return "（無 runs 紀錄）"
        last = runs[-1]
        return (
            "🕘 最後一次 run\n"
            f"run_id: {last.get('run_id')}\n"
            f"department: {last.get('department')}\n"
            f"agent: {last.get('agent_name')}\n"
            f"status: {last.get('status')}\n"
            f"created_at: {last.get('created_at')}\n"
            f"updated_at: {last.get('updated_at')}"
        )

    def _cmd_runs(self, n: int) -> str:
        d = self._read_status()
        runs = (d.get("runs", []) or [])[-max(1, min(n, 20)):]
        if not runs:
            return "（無 runs 紀錄）"
        lines = ["📋 最近 runs："]
        for r in runs:
            lines.append(
                f"  · [{r.get('status')}] {r.get('department')} / {r.get('agent_name')} "
                f"@ {r.get('updated_at') or r.get('created_at')}"
            )
        return "\n".join(lines)

    def _cmd_stats(self) -> str:
        from gov_paths import get_department_under  # type: ignore

        def _cnt(p: str) -> Tuple[int, float]:
            if not os.path.isdir(p):
                return 0, 0.0
            n = 0
            sz = 0
            for dp, _, fns in os.walk(p):
                for fn in fns:
                    n += 1
                    try:
                        sz += os.path.getsize(os.path.join(dp, fn))
                    except OSError:
                        pass
            return n, round(sz / 1024 / 1024, 2)

        root = self.dest_root
        targets = {
            "quarantine": os.path.join(get_department_under(root, "05_Temp_Cache"), "quarantine"),
            "raw_inbound": os.path.join(get_department_under(root, "05_Temp_Cache"), "raw_inbound"),
            "Archive": os.path.join(get_department_under(root, "06_Exports_Output"), "Archive"),
            "C2_核心知識庫": os.path.join(get_department_under(root, "03_RAG_Database"), "C2_核心知識庫"),
            "C3_Logs": os.path.join(get_department_under(root, "03_RAG_Database"), "C3_Logs"),
        }
        lines = ["📦 倉廩點檢"]
        for k, p in targets.items():
            n, mb = _cnt(p)
            lines.append(f"  · {k}: {n} 件 / {mb} MB")
        return "\n".join(lines)

    def _cmd_health(self) -> str:
        from gov_paths import get_department_under, load_master_map  # type: ignore

        try:
            m = load_master_map()
            mp_ver = m.get("version", "?")
        except Exception as e:  # noqa: BLE001
            return f"❌ 地圖讀取失敗: {e}"
        depts = ["01_Environments", "02_Agents_Core", "03_RAG_Database", "04_Workflows", "05_Temp_Cache", "06_Exports_Output"]
        lines = [f"🩺 系統自檢 · Master_Map v{mp_ver}"]
        ok = True
        for d in depts:
            p = get_department_under(self.dest_root, d)
            exist = os.path.isdir(p)
            ok = ok and exist
            lines.append(f"  · {d}: {'✓' if exist else '✗'}")
        lines.append(f"整體: {'🟢 健康' if ok else '🔴 異常'}")
        return "\n".join(lines)

    def _gov_main_python(self) -> str:
        return os.path.normpath(
            os.path.join(self.dest_root, "01_Environments", "python_venvs", "gov_main", "Scripts", "python.exe")
        )

    def _run_closeout_report_telegram(self) -> Tuple[int, str]:
        """呼叫 v2.56 _report_generator.py --telegram-send（結案草案）。"""
        wf = os.path.dirname(get_artifact_path("status_json"))
        script = os.path.join(wf, "_report_generator.py")
        py = self._gov_main_python()
        if not os.path.isfile(py) or not os.path.isfile(script):
            return 2, "report_generator_or_python_missing"
        env = os.environ.copy()
        env.setdefault("PYTHONUTF8", "1")
        env["TANG_GOV_ROOT"] = self.dest_root
        env["PYTHONPATH"] = os.pathsep.join(
            [self.dest_root, os.path.join(self.dest_root, "02_Agents_Core"), wf]
        )
        r = subprocess.run(
            [py, script, "--telegram-send"],
            cwd=wf,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        tail = (r.stderr or "")[-1500:] + (r.stdout or "")[-1500:]
        return int(r.returncode), tail

    def _handle_scout_callback(self, cq: Dict[str, Any], update_id: Any) -> None:
        """偵察兵 Inline：scout:f / scout:i / scout:confirm → 結案報告器。"""
        cq_id = str(cq.get("id") or "")
        data = str(cq.get("data") or "")
        msg = cq.get("message") or {}
        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        frm = cq.get("from") or {}
        if not cq_id or chat_id is None:
            return
        if not self._allowed(chat_id):
            self.agent.log_event(
                event="telegram_listener_warning",
                reason="scout_callback_unauthorized",
                chat_id=chat_id,
                update_id=update_id,
            )
            return
        if not data.startswith("scout:"):
            self.answer_callback_query(cq_id, text="未支援的回調")
            return

        if data.startswith("scout:f:"):
            self.answer_callback_query(cq_id, text="跟進已記錄")
            self.agent.log_event(
                event="scout_callback_follow",
                data=data[:120],
                update_id=update_id,
                user_id=frm.get("id"),
            )
            return
        if data.startswith("scout:i:"):
            self.answer_callback_query(cq_id, text="略過已記錄")
            self.agent.log_event(
                event="scout_callback_ignore",
                data=data[:120],
                update_id=update_id,
                user_id=frm.get("id"),
            )
            return
        if data == "scout:confirm" or data.startswith("scout:confirm:"):
            self.answer_callback_query(cq_id, text="正在生成結案草案並回傳…")
            rc, tail = self._run_closeout_report_telegram()
            self.agent.log_event(
                event="scout_callback_confirm",
                data=data[:120],
                update_id=update_id,
                user_id=frm.get("id"),
                report_exit_code=rc,
            )
            if rc != 0:
                self.send(
                    chat_id,
                    "結案報告器執行失敗（請確認已跑偵察 --match 且存在 scout_last_pipeline.json）。\n"
                    f"exit={rc}\n{tail[-800:]}",
                )
            return

        self.answer_callback_query(cq_id, text="已記錄")
        self.agent.log_event(
            event="scout_callback_received",
            callback_query_id=cq_id,
            data=data[:180],
            update_id=update_id,
            user_id=frm.get("id"),
        )

    def dispatch(self, msg: Dict[str, Any]) -> Optional[str]:
        text = (msg.get("text") or "").strip()
        if not text:
            cap = (msg.get("caption") or "").strip()
            if cap:
                text = cap
        if not text:
            return None
        # 命令首段
        head = text.split()[0].lower()
        # 去掉 @bot_name 後綴（群組常見）
        if "@" in head:
            head = head.split("@", 1)[0]
        if head in ("/start", "/help"):
            return self._cmd_help()
        if head == "/ping":
            return self._cmd_ping()
        if head == "/whoami":
            return self._cmd_whoami(msg)
        if head == "/status":
            return self._cmd_status()
        if head == "/lastrun":
            return self._cmd_lastrun()
        if head == "/stats":
            return self._cmd_stats()
        if head == "/health":
            return self._cmd_health()
        if head == "/runs":
            parts = text.split()
            n = 5
            if len(parts) >= 2:
                try:
                    n = int(parts[1])
                except ValueError:
                    n = 5
            return self._cmd_runs(n)
        # 非指令訊息：不再沈默；交由 Groq 背景回覆（不阻塞本輪其它更新）
        if text.startswith("/"):
            return "未識別指令。輸入 /help 查看可用清單。"
        return "__GROQ_CHAT__"

    def process_updates(self, updates: List[Dict[str, Any]]) -> Dict[str, int]:
        handled = 0
        skipped_unauth = 0
        skipped_other = 0
        groq_scheduled = 0

        def _incoming_plain(u: Dict[str, Any]) -> str:
            if u.get("callback_query"):
                return "/callback"
            m = u.get("message") or u.get("edited_message") or {}
            return str((m.get("text") or m.get("caption") or "")).strip()

        # 優先處理指令類訊息（以 / 開頭），再處理一般閒聊，降低長推理對指令的体感延遲
        ordered = sorted(updates, key=lambda u: 0 if _incoming_plain(u).startswith("/") else 1)
        for u in ordered:
            cq = u.get("callback_query")
            if cq:
                self._handle_scout_callback(cq, u.get("update_id"))
                handled += 1
                continue
            msg = u.get("message") or u.get("edited_message") or {}
            chat = msg.get("chat") or {}
            chat_id = chat.get("id")
            if chat_id is None:
                skipped_other += 1
                continue
            if not self._allowed(chat_id):
                skipped_unauth += 1
                self.agent.log_event(
                    event="telegram_listener_warning",
                    reason="unauthorized_chat",
                    chat_id=chat_id,
                    update_id=u.get("update_id"),
                )
                # 不回應陌生人，避免成為 spam 反射器
                continue
            reply = self.dispatch(msg)
            thread_id = msg.get("message_thread_id")
            thread_kw: Dict[str, Any] = {}
            if thread_id is not None:
                thread_kw["message_thread_id"] = int(thread_id)

            if reply == "__GROQ_CHAT__":
                txt = (msg.get("text") or "").strip()
                if not txt:
                    txt = (msg.get("caption") or "").strip()
                if txt:
                    self._schedule_groq_chat(
                        chat_id,
                        txt,
                        u.get("update_id"),
                        message_thread_id=thread_kw.get("message_thread_id"),
                    )
                    handled += 1
                    groq_scheduled += 1
                else:
                    skipped_other += 1
                continue
            if reply is None:
                skipped_other += 1
                continue
            code, body = self.send(chat_id, reply, **thread_kw)
            ok = bool(isinstance(body, dict) and body.get("ok"))
            self.agent.log_event(
                event="telegram_command_handled",
                chat_id=chat_id,
                update_id=u.get("update_id"),
                command=(msg.get("text") or "")[:40],
                send_http=code,
                send_ok=ok,
            )
            handled += 1
        return {
            "handled": handled,
            "skipped_unauth": skipped_unauth,
            "skipped_other": skipped_other,
            "groq_scheduled": groq_scheduled,
        }

    def poll_once(self) -> Dict[str, Any]:
        """單發輪詢：取一次 getUpdates 並處理；適合排程觸發或測試。"""
        self.agent.set_status(AgentStatus.Running.value, reason="telegram_poll_once")
        state = self._load_state()
        offset = int(state.get("last_update_id", 0)) + 1 if state.get("last_update_id") else 0

        code, data = self.get_updates(offset)
        if code != 200 or not isinstance(data, dict) or not data.get("ok"):
            self.agent.log_event(event="telegram_listener_warning", reason="getUpdates_failed", http=code, body=data)
            self.agent.set_status(AgentStatus.Manual.value, reason="getUpdates_failed")
            return {"ok": False, "http": code, "data": data}

        updates = data.get("result", []) or []
        stats = self.process_updates(updates)
        if updates:
            state["last_update_id"] = max(int(u.get("update_id", 0)) for u in updates)
            state["processed"] = int(state.get("processed", 0)) + stats["handled"]
            self._save_state(state)

        self.agent.log_event(event="telegram_poll_once_done", received=len(updates), **stats)
        self.agent.set_status(AgentStatus.Success.value, reason="telegram_poll_once_done")
        return {"ok": True, "received": len(updates), **stats, "last_update_id": state.get("last_update_id", 0)}

    def run_forever(self) -> None:
        """長輪詢主迴圈：以 lockfile 確保單實例。"""
        if not self._acquire_lock():
            self.agent.set_status(AgentStatus.Manual.value, reason="lock_held_by_other")
            print("[Telegram_Listener] 另一進程持有鎖，退出。")
            return
        self.agent.set_status(AgentStatus.Running.value, reason="telegram_loop_start")
        self.agent.log_event(event="telegram_loop_start", allowed_ids=sorted(self.allowed_ids))
        state = self._load_state()
        offset = int(state.get("last_update_id", 0)) + 1 if state.get("last_update_id") else 0
        try:
            while True:
                code, data = self.get_updates(offset)
                if code != 200 or not isinstance(data, dict) or not data.get("ok"):
                    self.agent.log_event(event="telegram_listener_warning", reason="getUpdates_failed", http=code)
                    time.sleep(3)
                    continue
                updates = data.get("result", []) or []
                if updates:
                    stats = self.process_updates(updates)
                    new_max = max(int(u.get("update_id", 0)) for u in updates)
                    state["last_update_id"] = new_max
                    state["processed"] = int(state.get("processed", 0)) + stats["handled"]
                    self._save_state(state)
                    offset = new_max + 1
                # else: long-poll 已等到 timeout，循環即可
        except KeyboardInterrupt:
            self.agent.log_event(event="telegram_loop_stop", reason="KeyboardInterrupt")
            self.agent.set_status(AgentStatus.Success.value, reason="telegram_loop_stopped")
        finally:
            self._release_lock()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Telegram_Listener_Agent CLI")
    parser.add_argument("--mode", choices=("once", "loop"), default="once", help="once: 單次輪詢；loop: 常駐長輪詢")
    args = parser.parse_args()

    a = Telegram_Listener_Agent()
    if args.mode == "once":
        out = a.poll_once()
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        a.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
