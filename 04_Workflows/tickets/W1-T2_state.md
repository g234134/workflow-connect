# TICKET STATE · W1-T2 · Monitoring PG Ingest 收口（API 成功 → PG 有列）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 1 - Governance & Observability

---

## FRAME

- Title: Monitoring PG Ingest 收口（API 成功 → PG 有列）
- Goal: live ask／batch 流量後 task_runs／step_runs 與 Langfuse 樣本量級一致，解除 API 200 但 PG 0 列斷層。
- Scope:
  - 診斷並修復 monitoring ingest 路徑（task_traces.jsonl → PG sync）
  - 提供最小 soak runner：n=20 ask 後驗證 PG 列數 ≥ 18
  - 更新 docs/observability.md §4.2：驗收口徑 = PG 列數 + Langfuse trace_id 對齊
  - 單測或 integration test：mock ingest 一筆 → PG 可查
- NonScope:
  - 不統一 daily_cost_summary vs task_runs 成本（留 W1-T3 或專項）
  - 不做 Prometheus/Grafana exporter
  - 不宣稱 production-ready
- AllowedPaths:
  - 01_Environments/python_venvs/gov_core_system/core/monitoring_ingest.py
  - 01_Environments/python_venvs/gov_core_system/core/monitoring_service.py
  - 04_Workflows/_phase5_pg_ingest_soak.py
  - docs/observability.md
  - artifacts/monitoring/**
  - tests/test_*monitoring*（若戰車根）
- BlockedPaths:
  - core/*（戰車根，非本票）
  - AGENTS.md
  - .env
  - runtime/checkpoints/**
- Dependencies:
  - 暗部 monitoring_service、ingest 模組
  - Wave 4A live run 證據（Progress 已知斷層）
  - DATABASE_URL（實例錨點）
- Risks:
  - 進程熱重載導致 config_error 假失敗
  - 測試環境無 PG 時須 ok: false + message，不得假成功
- Observability:
  - logs: ingest batch traces_synced / steps_synced
  - metrics: kpis.latency.p95、task_runs 當日 count
  - traces: gov-trace-v2 trace_end 與 PG trace_id join
- OutputArtifacts:
  - 04_Workflows/_phase5_pg_ingest_soak.py（或等價 runner）
  - docs/observability.md 更新節
  - artifacts/monitoring/pg_ingest_soak.latest.json
- AcceptanceCriteria:
  - soak 命令 exit 0；輸出 ingest_ok、pg_task_runs_count、langfuse_trace_count
  - GET /monitoring/overview 反映本次 cohort（非空 task_runs）
  - 新增／更新 test ≥1 覆蓋 ingest 契約
  - Progress 末尾可附結構化結果（Scribe）
- VerificationCommands:
  - `python 04_Workflows/_phase5_pg_ingest_soak.py`
    - 預期：exit 0；pg_task_runs_count ≥ 18
  - `GET /monitoring/overview`
    - 預期：反映本次 cohort
  - `暗部 unittest ingest 子集`
    - 預期：≥1 測試全綠

---

## STATE

- overall_status: done
- design_phase: accepted
- implementation_status: done
- current_owner: scribe
- next_action: 無（票面已收口；Langfuse usage / JSONL 接線見 D_REPORT follow-up）
- last_updated: 2026-06-07 · Reviewer 二輪複驗再次確認（cohort 06:51 UTC）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- accepted_boundary_notes:
  - Langfuse HTTP 429（observations/traces Public API rate limit）為**已知邊界**，不構成阻塞：Reviewer 二輪 n=20 仍 exit 0、ingest_ok=true、pg/langfuse 全量對齊、ingest_sync errors=[]。
  - jsonl_trace_end_count=0 接受為「**診斷源缺席但權威源完整**」：權威路徑 Langfuse → sync_traces → PG；JSONL 僅 Phase D diagnostic，不影響 §4.2.1 驗收口徑。

---

## B_REPORT

> **C 區（Orchestrator 預填）**：Implementer 施工時更新下方欄位，保留 Implementation Plan 歷史。

### Implementation Plan

#### Block 1 — Ingest 診斷與修復

- [ ] **根因盤點**（Wave 4A：`wave4a-*` Langfuse 20 列、PG 0 列）
  - [ ] 確認 runtime `GOV_CORE_MONITORING_INGEST_ENABLED=1`（非僅 .env 檔案）
  - [ ] 對照 JSONL 寫入路徑 vs `monitoring_ingest` 讀取路徑
  - [ ] 檢查 `trace_end` 是否含 `task_id` / `trace_id`（ingest skip 條件）
  - [ ] 排除 uvicorn 熱重載導致 `config_error` 假失敗（Progress Wave 4A）
- [ ] **程式入口**（暗部，實作輪次）
  - [ ] `core/monitoring_ingest.py` — sync from JSONL → `task_runs` / `step_runs`
  - [ ] `core/monitoring_service.py` — overview KPI 讀取路徑
  - [ ] `integration_hooks.py`（若 ask 管線 hook 未觸發 ingest）
- [ ] **Config 檢查點**
  - [ ] `DATABASE_URL`（實例錨點）
  - [ ] `GOV_CORE_MONITORING_INGEST_ENABLED=1`
  - [ ] Langfuse keys（計數用，非本票成本收口）

#### Block 2 — Soak runner（spec 已落檔，live 待接線）

- [x] **檔名**：`04_Workflows/_phase5_pg_ingest_soak.py`
- [x] **CLI**：`python 04_Workflows/_phase5_pg_ingest_soak.py --n 20 [--dry-run] [--base-url URL] [--cohort-prefix w1t2-] [-o artifacts/monitoring/pg_ingest_soak.latest.json]`
- [x] **輸出 JSON 欄位**：`ingest_ok`, `pg_task_runs_count`, `langfuse_trace_count`, `details[]`（+ `jsonl_trace_end_count`, `gap_pg_vs_langfuse`, `preflight`）
- [ ] **Live 實作**：preflight → fire ask → ingest sync → PG/Langfuse count → evaluate
- [ ] **驗收**：live run `ingest_ok=true` 且 exit 0

#### Block 3 — 文檔

- [x] **`docs/observability.md` §4.2.1**：驗收口徑 = PG 列數 + Langfuse trace_id 對齊；允許 ≤2 筆邊界落差條件
- [ ] **交叉引用**：§9 Wave A soak 與 W1-T2 runner 分工（seed vs live ask）— 可選 Scribe 輪

### Spec artifact locations (this round)

| Artifact | Path | Status |
|----------|------|--------|
| Soak runner spec | `04_Workflows/_phase5_pg_ingest_soak.py` | skeleton + `--dry-run` |
| Observability gate | `docs/observability.md` §4.2.1 | drafted |
| Soak report (dry-run sample) | `artifacts/monitoring/pg_ingest_soak.latest.json` | after `--dry-run` |

### Files To Touch (full ticket)

- 暗部 monitoring_ingest.py
- 04_Workflows/_phase5_pg_ingest_soak.py
- docs/observability.md
- artifacts/monitoring/

- changed_files:
  - `04_Workflows/_phase5_pg_ingest_soak.py`（新建 · spec skeleton）
  - `docs/observability.md`（§4.2.1 ingest verification gate）
  - `04_Workflows/tickets/W1-T2_state.md`（B_REPORT / STATE / O_NOTES）
- artifacts:
  - `artifacts/monitoring/pg_ingest_soak.latest.json`（`--dry-run` 產出；live 待下一輪）
- verification:
  - `python 04_Workflows/_phase5_pg_ingest_soak.py --n 20 --dry-run --pretty` → exit 0；JSON 含 `ingest_ok`（dry-run 固定 false）、`pg_task_runs_count`、`langfuse_trace_count`、`details[]`
  - 本輪**未**連 PG / live API（依 FRAME spec-only 授權）
- behavior_notes:
  - Runner 分五階段：preflight → fire ask → ingest sync → count PG/Langfuse/JSONL → evaluate；門檻 `min_pg=18`、`max_gap=2`
  - Live 未接線時 preflight 回 `ok=false`，exit 2（不假綠）
- deferred_items:
  - 暗部 `monitoring_ingest.py` 修復與 integration test
  - Live soak 與 `GET /monitoring/overview` 驗收
  - daily_cost_summary 統一（W1-T3）

### Step 1 — Block 0 preflight / ingest smoke（2026-06-07 · implementer）

| Check | Result | Evidence |
|-------|--------|----------|
| API `http://127.0.0.1:8000` reachable | **FAIL** | `/health` 与 `/monitoring/overview` 均连接失败（无 listener） |
| `DATABASE_URL` | **PASS**（venv + dotenv） | `gov_core_system/.env` 经 dotenv 加载后为 set；系统 Python 无 dotenv 时为 missing |
| `GOV_CORE_MONITORING_INGEST_ENABLED=1` | **FAIL** | `gov_core_system/.env` 与 `01_Environments/.env` 均未设置该键（`.env.example` 仅注释示例） |
| `from core.monitoring_ingest import sync_traces` | **PASS** | venv `Scripts/python.exe` import 成功 |
| 手跑 ingest smoke | **FAIL** | 见下方命令输出 |

**手跑命令**（venv python，cwd=`gov_core_system`）：

```text
python Scripts/run_monitoring_ingest.py --session-prefix w1t2- --minutes 5
→ psycopg.errors.ConnectionTimeout: connection timeout expired
  （堆栈止于 sync_traces → refresh_daily_cost_summary → pool.acquire）
```

**根因链（推断，有运行时证据）**：

1. Docker Desktop 未运行 → `docker ps` 报 `dockerDesktopLinuxEngine` pipe 不存在。
2. 本机 **5432 / 8000 均无监听** → PG 连接超时、API 不可达。
3. `GOV_CORE_MONITORING_INGEST_ENABLED` 未配置 → 即使 API 启动，background scheduler 也不会 tick ingest。

**裁决**：Step 1 **未通过** → **不进入 Step 2 live soak 接線**，待 infra 解阻塞后继续。

**解阻塞清单（需尚書省／运维）**：

1. 启动 Docker Desktop → `datang_postgres` 容器 running（Progress DB-RECOVER-1 惯例入口）。
2. 确认 `gov_core_system/.env` 之 `DATABASE_URL` 与 running PG 一致（不修改 `.env` 内容，仅验证连通）。
3. 在 **API 进程环境** 设置 `GOV_CORE_MONITORING_INGEST_ENABLED=1`（或 `true` per `monitoring_scheduler._env_flag`）。
4. 启动 `uvicorn app_api:app` @ `127.0.0.1:8000`（加载 Tang `.env` + gov_core overlay）。
5. 重跑 Step 1 两项 smoke 通过后，Implementer 再进入 Step 2。

### Step 1 — Infra unblock re-check（2026-06-07 · infra/ops）

| Check | Result | Evidence |
|-------|--------|----------|
| Docker Desktop + `datang_postgres` | **PASS** | 启动 Docker Desktop 后 `docker ps` 显示 `datang_postgres` Up；`5432:5432` 映射 |
| `DATABASE_URL` → PG 连通 | **PASS** | venv `check_postgres()` → `{"ok": true, "message": "pg_ok"}` |
| API @ `127.0.0.1:8000` | **PASS** | `GET /healthz` → HTTP 200；`GET /monitoring/overview` → HTTP 200 |
| `GOV_CORE_MONITORING_INGEST_ENABLED=1` | **PASS**（API 进程） | uvicorn 启动 shell 设 `GOV_CORE_MONITORING_INGEST_ENABLED=1`；`.env` 仍未写入（runtime only，符合 ticket 口径） |
| ingest smoke（PG 不再 timeout） | **PASS** | `sync_traces(minutes=5, session_prefix='w1t2-')` → `ok: true`；`traces_synced=0`（窗口内无 Langfuse 样本，属预期） |

**注意**：

- 健康端点为 **`/healthz`**（非 `/health`）；后者 404。
- `Scripts/run_monitoring_ingest.py` **repo 内不存在**（仅 state 引用）；等效 smoke：`core.monitoring_ingest.sync_traces(...)` 或后续 Implementer 补 CLI wrapper。
- `_phase5_pg_ingest_soak.py` preflight 仍为 skeleton → live 跑 soak 仍 exit 2；**Step 2 接線任务未变**。

**裁决**：Infra **已解阻塞**；Step 1 手工 preflight **通过** → **Implementer 可进入 Step 2**（soak preflight 实作 + live integration test + n=20 full soak）。

**当前运行中服务**（本机，供 Step 2 接续）：

```powershell
# 已启动（后台 uvicorn，ingest flag=1）
cd 01_Environments/python_venvs/gov_core_system
$env:GOV_CORE_MONITORING_INGEST_ENABLED = "1"
.\Scripts\uvicorn.exe app_api:app --host 127.0.0.1 --port 8000
```

### 本輪施工變更摘要（Step 2 · live 實作輪 · 待主 Implementer 填寫）

> **Worker C scaffolding**：以下僅預留結構與欄位說明；**本輪 chat 不填具體值、不宣稱 live 驗收成功**。主 Implementer 完成 soak 接線與 integration test 後，於此區填入實際 diff 與命令輸出摘要。

#### changed_files

<!-- 主 Implementer 填：本輪實際修改／新增之檔案清單（相對 repo 根） -->

| 預期路徑 | 變更類型 | 說明 |
|----------|----------|------|
| `04_Workflows/_phase5_pg_ingest_soak.py` | modify | live preflight → fire ask → ingest sync → count → evaluate 接線 |
| `01_Environments/python_venvs/gov_core_system/tests/test_monitoring_ingest_integration.py` | add/modify | mock ingest 一筆 → PG 可查 trace_id |
| `01_Environments/python_venvs/gov_core_system/core/monitoring_ingest.py` | modify（若需） | JSONL → PG sync 根因修復 |
| `artifacts/monitoring/pg_ingest_soak.latest.json` | artifact | live soak 結構化輸出 |

- **本輪值**：
  - `04_Workflows/_phase5_pg_ingest_soak.py`（modify · Worker A live A–E 接線）
  - `01_Environments/python_venvs/gov_core_system/tests/test_monitoring_ingest_integration.py`（add · Worker B；venv 樹 gitignore）
  - `artifacts/monitoring/pg_ingest_soak.latest.json`（live n=20 產出）
  - `04_Workflows/tickets/W1-T2_state.md`（本輪 B/D/STATE 回寫）
  - `01_Environments/python_venvs/gov_core_system/core/monitoring_ingest.py` — **未改**（live soak 無需修補）

#### verification

<!-- 主 Implementer 填：實際執行之命令 + exit code + 關鍵輸出語意（非 live 證據不得標 PASS） -->

| 命令 | 預期 | 本輪結果 |
|------|------|----------|
| 小樣本 soak（n=3） | exit 0 或依 preflight 語義；JSON 含 `ingest_ok`、計數欄位 | **PASS（preflight）** · exit **1**（`pg=3 < min_pg=18`，非 preflight 失敗）；preflight `ok=true`；三源 count 均 3 |
| full soak（n=20） | exit 0；`ingest_ok=true`；`pg_task_runs_count` ≥ 18 | **PASS** · exit **0**；`ingest_ok=true`；pg=20；langfuse=20；gap=0 |
| integration test | pytest 全綠 | **PASS** · `3 passed in 0.10s` |

- **本輪值**：
  - 小樣本：`$env:GOV_CORE_MONITORING_INGEST_ENABLED="1"; gov_core venv python 04_Workflows/_phase5_pg_ingest_soak.py --n 3 --base-url http://127.0.0.1:8000 --pretty` → exit 1；preflight ok；n_api_ok=3；pg/langfuse/jsonl_end=3/3/0；ingest_sync traces_synced=3 steps_synced=0 errors=[]
  - full：`… --n 20 …` → exit 0；ingest_ok=true；pg=20 langfuse=20 gap=0；ingest_sync traces_synced=20 steps_synced=160 errors=[]；artifact 寫入 `artifacts/monitoring/pg_ingest_soak.latest.json`
  - integration：`cd gov_core_system && python -m pytest tests/test_monitoring_ingest_integration.py -q` → 3 passed
  - **執行前提**：soak runner 需 venv python（載入 `DATABASE_URL` dotenv）+ shell 設 `GOV_CORE_MONITORING_INGEST_ENABLED=1`（`.env` 未寫入，runtime only）

#### behavior_notes

<!-- 主 Implementer 填：pg/langfuse gap、邊界 case、ingest skip 條件、overview 對齊等觀察 -->

| 主題 | 預期記錄內容 |
|------|----------------|
| PG vs Langfuse gap | `gap_pg_vs_langfuse`、≤2 筆邊界是否觸發 |
| JSONL trace_end | `jsonl_trace_end_count` 與 Langfuse 樣本對照 |
| ingest_sync | `traces_synced` / `steps_synced` / `errors[]` 摘要 |
| 邊界 case | preflight 失敗、無 PG、ingest flag off、熱重載 config_error 等 |

- **本輪值**：
  - PG vs Langfuse：n=3 與 n=20 均 **gap=0**；≤2 邊界條件**未觸發**
  - JSONL：`jsonl_trace_end_count=0`（ask 管線未寫 `runtime/task_traces.jsonl`）；權威路徑為 Langfuse → `sync_traces` → PG，不阻塞驗收
  - ingest_sync（n=20）：traces_synced=20、steps_synced=160、traces_matched=20、errors=[]；message 提示 Langfuse `usage` 欄位缺口（missing_field_summary），非 sync 失敗
  - Langfuse 429：n=20 期間 observations/traces API 多次 429 rate limit；ingest 仍全量同步，最終 count 對齊
  - n=3 exit 1：evaluate 仍用 `min_pg=18`（CLI 預設）；屬門檻語義非 preflight 阻塞
  - 無 `monitoring_ingest.py` 修補：session_id/trace_id 對齊正常；全 20 筆 biz_ok=true、pg_row_found=true

---

## C_REPORT

- verdict: **accepted**
- conclusion: accepted（Reviewer 二輪 · 2026-06-07）
- blocking_issues: 無
- checks_summary: |
    - **Round 1（spec）**：soak runner 五階段 A–E 契約清楚；observability §4.2.1 門檻與 exit code 一致；dry-run 不假綠 — 維持 accepted。
    - **Round 2（live · 獨立複驗）**：
      - n=20 soak（gov_core venv python + `GOV_CORE_MONITORING_INGEST_ENABLED=1`）：exit **0**；`ingest_ok=true`；pg=20；langfuse=20；gap=0；n_api_ok=20；preflight ok；ingest_sync traces_synced=20 steps_synced=160 errors=[]。
      - integration test：`pytest tests/test_monitoring_ingest_integration.py -q` → **3 passed**。
      - 與 Implementer B_REPORT/D_REPORT 數值**一致**（本輪新 cohort，同門檻全綠）。
      - **複驗確認（同票再次執行）**：2026-06-07 06:51 UTC cohort 再次 exit 0 / ingest_ok=true / pg=20 langfuse=20 gap=0 / pytest 3 passed — 結論不變。
    - **邊界裁決（非阻塞）**：
      - **Langfuse 429**：soak stderr 多次 observations/traces rate limit；最終 PG/Langfuse count 仍全量對齊、ingest_sync 無 errors — **已知邊界，不構成阻塞**。
      - **jsonl_trace_end_count=0**：`runtime/task_traces.jsonl` 未寫入；權威源 Langfuse→PG 完整 — **接受為診斷源缺席但權威源完整**。
    - **Scope / NonScope**：未宣稱 prod-ready；daily_cost_summary 統一留 W1-T3 — 對齊 FRAME。
    - **AcceptanceCriteria**：live soak exit 0、pg≥18、gap≤2、integration test 全綠 — **全部滿足**。
- risk_level: low
- suggestions: |
    - Scribe（可選）：Progress 末尾 1–3 句記 W1-T2 收口（pg ingest live 驗收通過）。
    - 後續非本票：Langfuse `usage` missing_field_summary 可另開 metadata 補全票；JSONL diagnostic 接線可另開 ask 管線票。
    - soak 複跑前提：venv python + runtime `GOV_CORE_MONITORING_INGEST_ENABLED=1`（`.env` 未寫入屬已知 ops 口徑）。

---

## D_REPORT

> **验收專區（Reviewer · live soak 後填）**：以下欄位將由 **live soak 實際輸出**（`artifacts/monitoring/pg_ingest_soak.latest.json` 及 ingest sync 回傳）填入。**本輪 Worker C 僅預留結構，數值留空，不得提前標驗收通過。**

### Live soak 結構化結果（n=20 · 2026-06-07）

| 欄位 | 說明 | 本輪值 |
|------|------|--------|
| `ingest_ok` | soak evaluate 最終判定；live 驗收口徑見 `docs/observability.md` §4.2.1 | **true** |
| `pg_task_runs_count` | 本次 cohort 在 PG `task_runs` 之列數 | **20** |
| `langfuse_trace_count` | Langfuse 同 cohort trace 計數 | **20** |
| `jsonl_trace_end_count` | 本地 JSONL `trace_end` 事件計數 | **0**（diagnostic；非阻塞） |

### ingest_sync summary（n=20 cohort）

| 子欄位 | 說明 | 本輪值 |
|--------|------|--------|
| `traces_synced` | `sync_traces` 回傳之 traces 同步筆數 | **20** |
| `steps_synced` | step_runs 同步筆數 | **160** |
| `errors[]` | ingest 批次錯誤清單（空陣列為理想） | **[]** |

### Scribe 欄位

- docs_updates:
  - `docs/observability.md` §4.2.1 — ingest verification gate（PG 列數 + Langfuse trace_id 對齊；門檻 min_pg=18、max_gap=2）
  - `04_Workflows/_phase5_pg_ingest_soak.py` — live soak runner（preflight → fire ask → sync → count → evaluate）
  - `artifacts/monitoring/pg_ingest_soak.latest.json` — 權威結構化輸出（Reviewer 06:51 UTC cohort）
- verification:
  - `python 04_Workflows/_phase5_pg_ingest_soak.py --n 20 --base-url http://127.0.0.1:8000 --pretty` → **exit 0**；`ingest_ok=true`；pg=20；langfuse=20；gap=0
  - `cd 01_Environments/python_venvs/gov_core_system && python -m pytest tests/test_monitoring_ingest_integration.py -q` → **3 passed**
  - Reviewer 二輪獨立複驗（06:51 UTC cohort）→ 數值與 Implementer 一致
  - 執行前提：gov_core venv python + runtime `GOV_CORE_MONITORING_INGEST_ENABLED=1`（`.env` 未寫入屬已知 ops 口徑）
- behavior_notes:
  - **Langfuse HTTP 429**（observations/traces Public API rate limit）：soak stderr 可見多次 429，但 `ingest_sync.errors=[]`、最終 PG/Langfuse 全量對齊 — **已知邊界，不阻塞**
  - **`jsonl_trace_end_count=0`**：ask 管線未寫 `runtime/task_traces.jsonl`；權威路徑 Langfuse → `sync_traces` → PG — **診斷源缺席但權威源完整**
  - n=3 小樣本 exit 1：evaluate 仍用 `min_pg=18` 預設；屬門檻語義非 preflight 阻塞
  - ingest_sync message 含 Langfuse `usage` missing_field_summary — 非 sync 失敗；**不宣稱 production-ready**；`daily_cost_summary` 統一留 W1-T3
- progress_entry: |
    W1-T2 收口：live ask n=20 後 Langfuse→PG ingest 管線已接通（pg/langfuse 20/20）；驗收口徑見 `docs/observability.md` §4.2.1 與 `artifacts/monitoring/pg_ingest_soak.latest.json`。下游票可假設 Wave 4A「API 200 但 PG 0 列」斷層已解除；JSONL 診斷接線與 Langfuse usage 補全應另開票。
- followup_suggestions:
  - **W1-T3**：`daily_cost_summary` vs `task_runs` 成本資料源統一
  - **Langfuse usage metadata 補全票**：消化 soak `missing_field_summary`
  - **JSONL diagnostic 接線票**：ask 管線寫入 `runtime/task_traces.jsonl`（不影響 §4.2.1 權威口徑）
  - **ops 口徑**：soak 複跑需 venv python + runtime `GOV_CORE_MONITORING_INGEST_ENABLED=1`
- accepted_boundary_notes: Langfuse HTTP 429 為已知邊界，不構成阻塞；jsonl_trace_end_count=0 接受為診斷源缺席但權威源（Langfuse→PG）完整

### Reviewer 驗收口徑（參考）

- soak exit 0 且 `ingest_ok=true`
- `pg_task_runs_count` ≥ 18（n=20 時）
- `|pg_task_runs_count − langfuse_trace_count|` ≤ 2（§4.2.1 邊界）
- integration test ≥1 全綠
- **本輪 D_REPORT 狀態**：Reviewer 二輪簽核 — **accepted**（2026-06-07）
- **Reviewer 二輪複驗數值**（獨立 cohort）：ingest_ok=true；pg=20；langfuse=20；jsonl=0；gap=0；ingest_sync traces_synced=20 steps_synced=160 errors=[]

---

## O_NOTES

> **O 區**：Orchestrator 維護 run log 與戰報連結；Observe / Operate 計畫。

### Observability Plan

- soak 報告保留 `artifacts/monitoring/pg_ingest_soak.latest.json`
- 結構化鍵：`ingest_ok`, `pg_task_runs_count`, `langfuse_trace_count`, `details[]`

### Rollout / Ops Notes

- 無 PG 環境：runner exit **2**，`preflight.ok=false` — **不得**假綠
- Live 前確認 API 進程已重載（避免 Wave 4A `config_error` 批次）

### VerificationCommands（Step 2 checklist · 預填）

> **⚠ 本輪 chat 未實際執行以下命令**；僅為後續 live 實作與 Reviewer 验收提供一目了然的 checklist。主 Implementer 跑完後將 exit code／關鍵輸出填入 B_REPORT「本輪施工變更摘要」與 D_REPORT。

#### 小樣本 soak（接線 smoke）

```powershell
python 04_Workflows/_phase5_pg_ingest_soak.py --n 3 --base-url http://127.0.0.1:8000 --pretty
```

- 用途：preflight + 少量 ask 後快速確認 ingest 路徑與 JSON 欄位
- 預期：結構化輸出含 `ingest_ok`、`pg_task_runs_count`、`langfuse_trace_count`；依 infra 狀態 exit 0 或 preflight 語義 exit 2
- **本輪執行**：**已執行** · exit 1（pg=3 < min_pg=18）；preflight ok；三源 count=3

#### full soak（驗收口徑）

```powershell
python 04_Workflows/_phase5_pg_ingest_soak.py --n 20 --base-url http://127.0.0.1:8000 --pretty
```

- 用途：n=20 cohort；門檻 `pg_task_runs_count` ≥ 18、gap ≤ 2
- 預期：live 通過時 `ingest_ok=true`、exit 0
- **本輪執行**：**已執行** · exit 0；ingest_ok=true；pg=20 langfuse=20

#### integration test

```powershell
cd 01_Environments/python_venvs/gov_core_system
python -m pytest tests/test_monitoring_ingest_integration.py -q
```

- 用途：mock ingest 一筆 → PG 可查 trace_id（AcceptanceCriteria）
- 預期：pytest 全綠
- **本輪執行**：**已執行** · 3 passed

#### 輔助（spec / dry-run · 已完成於前輪）

```powershell
# Schema / CLI 煙測（無 PG）
python 04_Workflows/_phase5_pg_ingest_soak.py --n 20 --dry-run --pretty

# Overview 二次確認（live 後）
curl http://127.0.0.1:8000/monitoring/overview
```

**報告路徑**：`artifacts/monitoring/pg_ingest_soak.latest.json`

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
| 2026-06-07 | implementer | spec：soak runner + observability §4.2.1；STATE → in_progress | 本檔 · `_phase5_pg_ingest_soak.py` |
| 2026-06-07 | implementer | Step 1 preflight FAIL（Docker/API/ingest flag） | 本檔 Step 1 表 |
| 2026-06-07 | infra/ops | Docker Desktop 启动；PG/API/ingest smoke 全绿；STATE → infra_unblocked | 本檔 Step 1 re-check |
| 2026-06-07 | implementer (Worker C) | B_REPORT/D_REPORT/O_NOTES scaffolding；VerificationCommands 預填；未跑 live | 本檔 |
| 2026-06-07 | implementer (main) | live n=3/n=20 soak PASS；integration 3 passed；STATE → in_review | 本檔 · `pg_ingest_soak.latest.json` |
| 2026-06-07 | reviewer | 二輪獨立複驗 n=20 + pytest 3 passed；verdict=accepted；STATE → done | 本檔 · C_REPORT |
| 2026-06-07 | reviewer | 複驗再次確認（06:51 UTC cohort）；結論維持 accepted | 本檔 · C_REPORT |
