"""
lead_scout.py - 戰車公司「市場偵察機」

功能：
- 基礎網頁爬取（BeautifulSoup）
- 將頁面文字送入 SmartRouter（Llama 3.1）做「髒度/產值」評估
- 輸出 JSON 報告：案源難度、預估收益比

注意：
- SmartRouter 預設在 http://127.0.0.1:8000/v1/chat/completions
- 若路由服務未啟動或無法連線，會自動 fallback 成啟發式評估（仍可讓腳本順利運行）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_SF = Path(__file__).resolve()
_REPO = _SF.parent.parent if _SF.parent.name in ("core", "factory") else _SF.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
import runtime_guard  # noqa: E402

runtime_guard.enforce(source_file=_SF)
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore


SMART_ROUTER_URL_DEFAULT = "http://127.0.0.1:8000/v1/chat/completions"
DEFAULT_TIMEOUT_S = 30.0


@dataclass
class ScoutReport:
    url: str
    fetched_at: str
    text_chars: int
    data_dirtiness: Dict[str, Any]
    industry_value: Dict[str, Any]
    lead_difficulty: int
    expected_roi_ratio: float
    router: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "fetched_at": self.fetched_at,
            "text_chars": self.text_chars,
            "ai_assessment": {
                "data_dirtiness": self.data_dirtiness,
                "industry_value": self.industry_value,
                "lead_difficulty": self.lead_difficulty,
                "expected_roi_ratio": self.expected_roi_ratio,
            },
            "router": self.router,
        }


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_html(url: str, timeout_s: float = DEFAULT_TIMEOUT_S, user_agent: str = "tank-lead-scout/0.1") -> str:
    headers = {"User-Agent": user_agent}
    with httpx.Client(follow_redirects=True, timeout=timeout_s, headers=headers) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


def html_to_text(html: str) -> str:
    if BeautifulSoup is None:
        # 超輕量 fallback：把 script/style 拿掉後用 regex 擷取文字（避免直接硬依賴 bs4）
        html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
        text = re.sub(r"(?is)<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compact_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def heuristic_assess(text: str) -> Dict[str, Any]:
    lower = text.lower()

    # 以「雜亂訊號」粗估髒度：符號、非結構化描述、隨機碎詞、比例等
    punct = sum(1 for c in text if c in ",;:|/\\[]{}()<>\"'`~!@#$%^&*-_=+")
    digits = sum(1 for c in text if c.isdigit())
    non_ascii = sum(1 for c in text if ord(c) > 127)
    total = max(len(text), 1)

    noise_score = (punct / total) * 80 + (digits / total) * 60 + (non_ascii / total) * 20
    keyword_noise = 0
    for k in ["csv", "xlsx", "json", "api", "catalog", "sku", "spec", "download", "價格", "規格", "型號", "報價"]:
        if k in lower:
            keyword_noise += 6

    dirtiness = int(min(10, max(1, round((noise_score / 20) + (keyword_noise / 10) + 1))))

    # 產值粗估：出現 B2B、批發、供應鏈、規格等詞，偏高；個人部落格偏低
    value_score = 1
    for k in ["wholesale", "supplier", "manufactur", "b2b", "procurement", "quotation", "rfq", "bulk", "trade", "import", "export", "經銷", "批發", "供應", "工廠", "貿易", "採購", "標案"]:
        if k in lower:
            value_score += 1
    value_band = "low"
    if value_score >= 6:
        value_band = "high"
    elif value_score >= 3:
        value_band = "mid"

    # ROI 粗估：越髒、越高價值，越值得；用 0.5~3.0 的比例表示
    roi = round(min(3.0, max(0.5, 0.6 + (value_score * 0.25) - (dirtiness * 0.12))), 2)

    return {
        "data_dirtiness": {"score_1_to_10": dirtiness, "reason": "heuristic"},
        "industry_value": {"band": value_band, "reason": "heuristic"},
        "lead_difficulty": dirtiness,
        "expected_roi_ratio": roi,
    }


def call_smart_router(router_url: str, page_text: str, timeout_s: float = DEFAULT_TIMEOUT_S) -> Dict[str, Any]:
    prompt = (
        "你是「戰車數據清洗有限公司」的案件精算與偵察模型。"
        "請根據以下網頁文字樣本，輸出一個 JSON（只能輸出 JSON，不要多餘文字）：\n"
        "{\n"
        '  "data_dirtiness": {"score_1_to_10": 1-10, "reason": "..."},\n'
        '  "industry_value": {"band": "low|mid|high", "reason": "..."},\n'
        '  "lead_difficulty": 1-10,\n'
        '  "expected_roi_ratio": number\n'
        "}\n"
        "其中：expected_roi_ratio 越大代表越值得接案（例如 2.0 表示回報約為成本 2 倍）。\n\n"
        "網頁文字樣本：\n"
        f"{page_text}\n"
    )

    payload = {
        "messages": [
            {"role": "system", "content": "Return ONLY valid JSON. No markdown. No commentary."},
            {"role": "user", "content": prompt},
        ]
    }

    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(router_url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # smart_router.py 走的是 OpenAI chat.completions 形狀：choices[0].message.content
    content = ""
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        # 若回傳形狀不同，直接把整包當 content 嘗試解析
        content = json.dumps(data, ensure_ascii=False)

    # 盡量擷取 JSON 主體（容錯：模型偶爾包一層文字）
    m = re.search(r"\{[\s\S]*\}", content)
    json_text = m.group(0) if m else content.strip()
    result = json.loads(json_text)

    # 簡單正規化
    lead_difficulty = int(result.get("lead_difficulty") or result.get("data_dirtiness", {}).get("score_1_to_10", 5))
    lead_difficulty = min(10, max(1, lead_difficulty))
    expected_roi_ratio = float(result.get("expected_roi_ratio", 1.0))

    return {
        "data_dirtiness": result.get("data_dirtiness", {"score_1_to_10": lead_difficulty, "reason": "ai"}),
        "industry_value": result.get("industry_value", {"band": "mid", "reason": "ai"}),
        "lead_difficulty": lead_difficulty,
        "expected_roi_ratio": expected_roi_ratio,
        "raw": {"router_response": data, "model_content": content},
    }


def build_report(url: str, router_url: str, max_text_chars: int, timeout_s: float) -> ScoutReport:
    html = fetch_html(url, timeout_s=timeout_s)
    text = html_to_text(html)
    sample = compact_text(text, max_text_chars)

    router_meta: Dict[str, Any] = {"url": router_url, "used": False, "error": None}

    assessment: Optional[Dict[str, Any]] = None
    try:
        ai = call_smart_router(router_url=router_url, page_text=sample, timeout_s=timeout_s)
        assessment = {
            "data_dirtiness": ai["data_dirtiness"],
            "industry_value": ai["industry_value"],
            "lead_difficulty": ai["lead_difficulty"],
            "expected_roi_ratio": ai["expected_roi_ratio"],
        }
        router_meta["used"] = True
    except Exception as e:
        router_meta["error"] = f"{type(e).__name__}: {e}"
        assessment = heuristic_assess(sample)

    return ScoutReport(
        url=url,
        fetched_at=_now_iso_utc(),
        text_chars=len(text),
        data_dirtiness=assessment["data_dirtiness"],
        industry_value=assessment["industry_value"],
        lead_difficulty=int(assessment["lead_difficulty"]),
        expected_roi_ratio=float(assessment["expected_roi_ratio"]),
        router=router_meta,
    )


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Tank lead scout: crawl page and estimate dirtiness/value.")
    p.add_argument("--url", required=False, default="https://example.com", help="Target website URL.")
    p.add_argument(
        "--router-url",
        required=False,
        default=SMART_ROUTER_URL_DEFAULT,
        help="SmartRouter endpoint (OpenAI-compatible chat.completions).",
    )
    p.add_argument("--max-text-chars", type=int, default=6000, help="Max characters of page text fed into AI.")
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S, help="HTTP timeout seconds.")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    report = build_report(
        url=args.url,
        router_url=args.router_url,
        max_text_chars=args.max_text_chars,
        timeout_s=args.timeout,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

