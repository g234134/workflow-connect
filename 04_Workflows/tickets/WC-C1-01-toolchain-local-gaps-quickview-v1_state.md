# TICKET STATE · WC-C1-01 · toolchain-local-gaps-quickview-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

<!-- Orchestrator 填：票的邊界與驗收標準；開票時寫，施工前凍結 -->

- **Goal**:
  - 起 Wave C **C1 核心票**：交付 **developer-facing、僅本地執行** 的 toolchain **gaps quickview** CLI，把 WC-PRE-02～05 已驗收能力與 WB-T4 既有 health dashboard **只讀聚合** 成一份 JSON 報告 + 人類可讀 summary。
  - 工程師在開新票、查 toolchain 狀態或盤點 impl gap 時，一條命令即可看到：selector `plan_only` 語義、executor subprocess timeout 契約、audit investigation gaps（可選 case）、smoke matrix dry-run 摘要、以及 WB-T4 agent-lines / catalog 區塊引用。
  - **不**升格任何 PROD gate、**不**改 CI required、**不**實作 WC-PRE-06/07 治理或 mandatory smoke。

- **Scope**:
  - 新增 `scripts/run_toolchain_local_gaps_quickview.py`：
    - 預設 `--dry-run`（只讀探測／子進程僅呼叫既有 read-only CLI，**不**執行 smoke matrix execute、**不**觸發 agent CI suite）。
    - `--format json` 輸出 `schema_version: toolchain_local_gaps_v1`；`--format text` 輸出人類可讀 summary（本票 C1 重點補齊 WC-PRE-04 text formatter gap 的 **gaps-report 層**，非改 audit quickview 本體）。
    - 區塊（sections）至少包含：
      - `selector_plan_only`：對 tabular / non-tabular selector 做 **in-process plan 探測**，斷言回傳 dict 含顯式 `plan_only: True`（WC-PRE-02）。
      - `executor_timeout_contract`：驗證 executor 非 dry_run subprocess 路徑 **timeout=600** 與 `subprocess_timeout` 訊息語義（WC-PRE-03；以 unittest 同級 in-process / mocked 探測，**禁止**本 CLI 預設跑 600s 真 subprocess）。
      - `audit_investigation`：可選 `--case-ref`；有值時呼叫既有 audit quickview investigation 投影或等價 import，摘要 `gaps` 計數與 top gaps；無值時標 `status: skipped` + message。
      - `smoke_matrix_dry_run`：呼叫 `scripts/run_toolchain_smoke_matrix.py --list --dry-run --format json`（或等價 import），摘要 `entries_requested` / tier / `dry_run=true`（WC-PRE-05）。
      - `toolchain_health_embed`：可選 `--include-health-dashboard`；預設 off；on 時只讀聚合 WB-T4 `run_toolchain_health_dashboard.py --dry-run --format json` 的 top-level `ok` / `sections_populated` / `gate_class`（不複製 WB-T4 全文）。
    - 頂層固定：`gate_class: optional`、`blocks_mainline: false`；**不得**輸出 SLA 承諾或 PR required 語義。
    - 可選 `--write` 寫入 `artifacts/toolchain/toolchain_local_gaps.latest.json` + `.md`（與 WB-T4 artifact 目錄對齊，檔名不同）。
  - 新增 `docs/toolchain-local-gaps-quickview-v1.md`：CLI 用法、schema、`toolchain_local_gaps_v1` 區塊表、與 WB-T4 / WC-PRE 交叉引用。
  - 新增 `tests/test_toolchain_local_gaps_quickview_v1.py`（≥10 tests）：schema、各 section shape、dry-run 預設、mocked subprocess、無 case-ref skip、health embed optional、頂層 gate 欄位。
  - 允許在 `docs/toolchain-health-dashboard-v1.md` **末尾追加一行** cross-ref 指向 gaps quickview（不改正文語義）。
  - 本檔 `04_Workflows/tickets/WC-C1-01-toolchain-local-gaps-quickview-v1_state.md`（FRAME 由 Orchestrator 維護）。

- **NonScope**（含 **Must-Not-Assume · PROD/CI**）:
  - **不得假設** `OG-TOOLCHAIN-HEALTH` 或本 quickview 已成為 PR **required** check 或 SLA 欄位（WC-PRE-06 僅 design_ready · pending_approval）。
  - **不得假設** WB-T4 toolchain health dashboard 已是 **blocking gate** 或會阻斷 MVP mainline / delivery gate。
  - **不得假設** smoke matrix runner 已是 **mandatory CI gate**（WC-PRE-07 design_draft · blocked_on_approval；**禁止**改 `.github/workflows/*`）。
  - **不得假設** selector / executor 已接上任何 prod INT regression 或 MVP mainline **blocking** gate；quickview 僅報告 plan_only / timeout 契約，不驅動 execute。
  - **不得假設** WC-PRE-06 observability 治理升級已獲尚書省批文——設計稿 `docs/toolchain-observability-governance-upgrade-v1.md` 僅作參考，**不可**當作已決策或已實作。
  - 不改 `routing/toolchain_smoke_matrix_v1.yaml` 內容、WB-T1～T8 contract/spec 正文、`core/wave7_regression_gate.py`、MVP mainline regression 行為。
  - 不建 Web UI、不接 Prometheus/Grafana、不改 outbox writers、不實作 WC-PRE-07 CI workflow step。
  - 不把 audit quickview 本體改為高階 text formatter（WC-PRE-04 deferred；本票只在 gaps-report 層提供 summary）。
  - 不將 quickview 輸出寫入 Progress / master_status（Scribe 票末處理）。

- **AllowedPaths**:
  - `scripts/run_toolchain_local_gaps_quickview.py`（新建）
  - `docs/toolchain-local-gaps-quickview-v1.md`（新建）
  - `tests/test_toolchain_local_gaps_quickview_v1.py`（新建）
  - `docs/toolchain-health-dashboard-v1.md`（僅末尾一行 cross-ref）
  - `04_Workflows/tickets/WC-C1-01-toolchain-local-gaps-quickview-v1_state.md`（FRAME/STATE · Orchestrator；B_REPORT · Implementer）

- **BlockedPaths**:
  - `.github/workflows/**`（含 `eval-gate-ci.yml`、`core-agent-smoke.yml`）
  - `core/wave7_regression_gate.py` · `core/**`（非本票必要且非 Implementer 本人 core）
  - `docs/tool-catalog-and-selector-contract-v1.md` · `docs/tool-executor-and-sandbox-safety-contract-v1.md` · `docs/audit-quickview-and-case-history-spec-v1.md` · `docs/phase6-int-regression-gate-contract-v1.md`（contract/spec **正文**）
  - `routing/toolchain_smoke_matrix_v1.yaml`（內容）
  - `scripts/run_toolchain_smoke_matrix.py` · `scripts/run_agent_audit_quickview.py` · `scripts/run_toolchain_health_dashboard.py`（**核心邏輯**；僅允許 subprocess 呼叫或只讀 import 既有公開函式，不重寫）
  - `tools/tabular_tool_selector.py` · `tools/non_tabular_tool_selector_v1.py` · tabular executor 實作檔（WC-PRE 已收口）
  - `04_Workflows/00_Agent_Work_Progress.md` · `docs/WAVE_PROGRESS_DASHBOARD.md` · `04_Workflows/WORKFLOW_INDEX.md`（Scribe 票）
  - `HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md` · `AGENTS.md`

- **Dependencies**（可依賴 · 已驗收）:
  - **Wave B contracts / runtime（WB-T1～T8）**：
    - WB-T1：tool catalog + selector contract；selector 模組與 catalog JSON。
    - WB-T2：executor / sandbox safety contract；tabular executor timeout 語義。
    - WB-T3：outbox / feedback layer（read-only outbox 路徑慣例）。
    - WB-T4：`scripts/run_toolchain_health_dashboard.py` · `toolchain_health_v1` · optional / `blocks_mainline: false`。
    - WB-T5：audit quickview spec · `scripts/run_agent_audit_quickview.py`。
    - WB-T7：`routing/toolchain_smoke_matrix_v1.yaml` · smoke matrix schema。
    - WB-T6/T8：Wave B readme / execution plan / closure handoff（索引與 hygiene 已 WC-PRE-01 對齊）。
  - **WC-PRE（accepted / accepted_with_gaps）**：
    - WC-PRE-01：Wave B doc hygiene；D_REPORT 非空；Dashboard/索引對齊現況。
    - WC-PRE-02：tabular / non-tabular selector 回傳 dict 顯式 `plan_only: True`（32/32 unittest OK）。
    - WC-PRE-03：tabular executor 非 dry_run subprocess `timeout=600`；timeout → `ok=false`、`exit_code=null`、`message` 含 `subprocess_timeout`（23/23 OK）。
    - WC-PRE-04：`run_agent_audit_quickview.py --view investigation` 產 investigation JSON；`audit_investigation_view_v1`；20/20 OK（text 高階 formatter 仍 gap）。
    - WC-PRE-05：`scripts/run_toolchain_smoke_matrix.py` 讀 YAML；`--dry-run`/`--list` JSON summary；19/19 OK；**本地 optional runner，非 CI gate**。
  - **參考（非依賴 · 未批文）**：
    - WC-PRE-06：design only · `docs/toolchain-observability-governance-upgrade-v1.md`。
    - WC-PRE-07：design_draft · blocked_on_approval；不得依賴其 CI 行為。

- **Assumptions**（Implementer 可安全假設）:
  - 上述 WB-T1～T8 contract/spec 層與 WC-PRE-01～05 runtime 能力 **已存在且 unittest 綠**；無 blocking_issues。
  - Selector 成功/錯誤路徑均可讀 `plan_only: True`；下游須自行消費，quickview **不**宣稱已接 execute gate。
  - Smoke matrix runner 在本地可 `--list --dry-run`；`blocks_mainline` 在 YAML/報告中僅語義，runner **不**自動升格 release gate。
  - WB-T4 dashboard 預設 dry-run 只讀 outbox；`gate_class=optional` 恆定。
  - Repo 根可透過既有 `scripts/*.py` 慣例 bootstrap `sys.path`；測試走 `python -m unittest`。

- **AcceptanceCriteria**:
  - **AC-1**：`python scripts/run_toolchain_local_gaps_quickview.py --format json` → exit 0；頂層 `schema_version=toolchain_local_gaps_v1`、`gate_class=optional`、`blocks_mainline=false`、`dry_run=true`（預設）。
  - **AC-2**：JSON `sections` 含 `selector_plan_only`、`executor_timeout_contract`、`audit_investigation`、`smoke_matrix_dry_run`；每 section 含 `status`（`ok|degraded|missing|skipped`）、`ok`、`message`。
  - **AC-3**：`selector_plan_only` 斷言 tabular + non-tabular 探測結果均報告 `plan_only=True`（或明確 `degraded` + 原因）；**不**執行真 tool execute。
  - **AC-4**：`executor_timeout_contract` 驗證 timeout 契約（in-process / mock）；**不**在 CLI 預設路徑觸發 600s 真 subprocess；若 timeout 語義不符則 section `ok=false`。
  - **AC-5**：`--case-ref demo_phase --format json` 時 `audit_investigation` 含 gaps 摘要（計數或 top-N）；無 `--case-ref` 時 `status=skipped` 且 CLI 仍 exit 0。
  - **AC-6**：`smoke_matrix_dry_run` 摘要與 `run_toolchain_smoke_matrix.py --list --dry-run --format json` 一致（至少 `entries_requested`、`dry_run=true`）；**不**執行 smoke execute。
  - **AC-7**：`python -m unittest tests.test_toolchain_local_gaps_quickview_v1 -v` → **≥10 tests 全綠**；含 mocked subprocess / 無 case-ref skip。
  - **AC-8**：`docs/toolchain-local-gaps-quickview-v1.md` 記載 CLI、schema、與 WB-T4/WC-PRE cross-ref；**Must-Not-Assume** PROD/CI 段落與本 FRAME NonScope 對齊。
  - **AC-9（不變更證）**：diff **未**修改 `.github/workflows/*`、`routing/toolchain_smoke_matrix_v1.yaml` 內容、`core/wave7_regression_gate.py`；WB-T contract 正文無改。
  - **AC-10（可選）**：`--include-health-dashboard` 時嵌入 WB-T4 dry-run 摘要欄位；預設 off；嵌入內容 **不得** 改寫 WB-T4 `gate_class` 語義。

---

## STATE

- overall_status: accepted_with_gaps
- current_owner: orchestrator
- next_action: Scribe 依 C_REPORT 收尾 docs cross-ref / Progress 末尾摘要 · Orchestrator 決定下一張 Wave C 票
- last_updated: 2026-06-11 · reviewer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: pending

---

## B_REPORT

<!-- Implementer 填：施工結果；只寫本區塊，不改 FRAME / STATE -->

- changed_files:
  - `scripts/run_toolchain_local_gaps_quickview.py`（新建 · WC-C1-01 CLI）
  - `docs/toolchain-local-gaps-quickview-v1.md`（新建 · schema / CLI / Must-Not-Assume）
  - `tests/test_toolchain_local_gaps_quickview_v1.py`（新建 · 17 tests）
  - `docs/toolchain-health-dashboard-v1.md`（末尾一行 cross-ref 追加）
  - `04_Workflows/tickets/WC-C1-01-toolchain-local-gaps-quickview-v1_state.md`（本 B_REPORT 區塊）

- artifacts:
  - JSON schema：`toolchain_local_gaps_v1`（頂層 `gate_class=optional` · `blocks_mainline=false` · `dry_run=true` 預設）
  - Sections：`selector_plan_only` · `executor_timeout_contract` · `audit_investigation` · `smoke_matrix_dry_run` · 可選 `toolchain_health_embed`
  - CLI demo：
    - `python scripts/run_toolchain_local_gaps_quickview.py --format json` → exit 0 · `ok=true` · 四 section 全 ok
    - `python scripts/run_toolchain_local_gaps_quickview.py --case-ref demo_phase --format json` → audit `status=ok` · `gaps_count=1`
    - `python scripts/run_toolchain_local_gaps_quickview.py --write` → 可寫 `artifacts/toolchain/toolchain_local_gaps.latest.{json,md}`

- verification:
  - `python -m unittest tests.test_toolchain_local_gaps_quickview_v1 -v` → **17/17 OK**（≥10 要求已滿足）
  - `python scripts/run_toolchain_local_gaps_quickview.py --format json` → exit 0；預期 `schema_version=toolchain_local_gaps_v1` · `gate_class=optional` · `blocks_mainline=false` · `dry_run=true`；實際一致 · `ok=true`
  - `python scripts/run_toolchain_local_gaps_quickview.py --case-ref demo_phase --format json` → exit 0；預期 audit section 非 skipped 且含 gaps 計數；實際 `status=ok` · `gaps_count=1`
  - AC-9 不變更證：未改 `.github/workflows/*` · `routing/toolchain_smoke_matrix_v1.yaml` · `core/*` · contract/spec 正文 · 既有 quickview/smoke/health CLI 邏輯

- behavior_notes:
  - 預設 `--dry-run=true`：selector 為 in-process plan 探測；executor timeout 以 mock `subprocess.run` 驗證契約（**不**跑 600s 真 subprocess）；smoke matrix 僅 `--list --dry-run` import 摘要
  - 未新增或修改任何 CI workflow；JSON/text 為本地 optional quickview report，`gate_class=optional` · `blocks_mainline=false` 恆定，**非** gating signal
  - audit investigation 透過 import `run_agent_audit_quickview` + `project_audit_investigation_view`，不改 WC-PRE-04 本體
  - `--include-health-dashboard` 透過 import `build_toolchain_health`，嵌入摘要欄位，不改 WB-T4 contract 語義

- deferred_items:
  - 更豐富的 text formatter（例如 color / table layout）— 本票以 JSON 投影為準
  - Web UI / Prometheus 整合 — FRAME NonScope
  - WC-PRE-06/07 治理升格（PR required · mandatory smoke CI）— 僅 doc 參考，未實作
  - audit quickview 本體高階 text formatter（WC-PRE-04 deferred）— 本票僅 gaps-report 層 summary

---

## C_REPORT

<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- conclusion: accepted_with_gaps
- blocking_issues: none
- checks_summary:
  - **AC-1/AC-2**：Reviewer 實跑 `python scripts/run_toolchain_local_gaps_quickview.py --format json` → exit 0；頂層 `schema_version=toolchain_local_gaps_v1`、`gate_class=optional`、`blocks_mainline=false`、`dry_run=true`；四 section 均含 `status`/`ok`/`message`。
  - **AC-3**：`probe_selector_plan_only` in-process 呼叫 tabular/non-tabular selector，斷言 `plan_only=True`；無 execute 路徑；degraded 分支有對應 unittest。
  - **AC-4**：`probe_executor_timeout_contract` 以 `unittest.mock.patch(subprocess.run)` 驗證 `timeout=600` 與 `subprocess_timeout` 訊息；CLI 預設不觸發 600s 真 subprocess。
  - **AC-5**：`--case-ref demo_phase` → audit `status=ok`、`gaps_count=1`、top_gaps 非空；無 case-ref 時 `status=skipped` 且 exit 0（CLI + unittest）。
  - **AC-6**：`probe_smoke_matrix_dry_run` import `run_toolchain_smoke_matrix(tier=all, dry_run=True)`；摘要含 `entries_requested=12`、`dry_run=true`、tier_counts；未執行 smoke execute。
  - **AC-7**：`python -m unittest tests.test_toolchain_local_gaps_quickview_v1 -v` → **17/17 OK**（≥10）；含 mocked executor/audit/smoke、live mock executor、live smoke matrix、CLI subprocess 兩條。
  - **AC-8**：`docs/toolchain-local-gaps-quickview-v1.md` 含 CLI、schema、WB-T4/WC-PRE cross-ref 與 **§5 Must-Not-Assume（PROD/CI）** 與 FRAME NonScope 對齊。
  - **AC-9**：變更集僅 AllowedPaths 五項；`.github/workflows/*` 工作區另有未提交修改但與本票新建檔無關；未改 `routing/toolchain_smoke_matrix_v1.yaml`、`core/*`、contract 正文、blocked CLI/selector/executor 邏輯。
  - **AC-10（gap）**：`--include-health-dashboard` 程式路徑 import `build_toolchain_health(dry_run=True)` 並嵌入摘要欄位；unittest 僅 mock embed，**無 live integration test**（非 blocking）。
  - **AllowedPaths/NonScope**：JSON/text 恆定 optional 本地報告；`main()` 固定 exit 0；health dashboard doc 僅末尾一行 cross-ref；未升格 gate/CI。
- risk_level: low
- suggestions:
  - **Wave C 後續依賴**：開票前/impl gap 盤點可一條命令跑 gaps quickview（可選 `--case-ref` + `--include-health-dashboard`）作為 WC-PRE-02～05 能力與 WB-T4 的只讀聚合入口；Scribe/Orchestrator 可在 runbook 或 Wave C readme 索引 `docs/toolchain-local-gaps-quickview-v1.md`，**不**寫入 Progress/master_status 除非 Scribe 票末處理。
  - **仍不得假設**：`OG-TOOLCHAIN-HEALTH` / WC-PRE-06 **非** PR required；WB-T4 health dashboard **非** blocking gate；smoke matrix **非** mandatory CI gate（WC-PRE-07 blocked_on_approval）；selector/executor quickview 探測 **不** 代表 prod INT regression 或 MVP mainline blocking gate 已接通。
  - **非 blocking follow-up（optional）**：補 `--include-health-dashboard` live import 單測與 `--write` artifact 路徑 smoke test；rich text formatter 維持 B_REPORT deferred。

---

## D_REPORT

<!-- Scribe 填：文檔與進度建議；只寫本區塊 -->

- docs_updates:
  - `04_Workflows/tickets/README.md` — 新增 §Wave C C1 票務索引列（WC-C1-01 · accepted_with_gaps · owner orchestrator）
  - `04_Workflows/WORKFLOW_INDEX.md` — 新增 §1.27 Toolchain Local Gaps Quickview（依賴 Wave B + WC-PRE-02～05 · local only / optional / non-gating）
  - `04_Workflows/00_Agent_Work_Progress.md` — 檔尾追加 WC-C1-01 戰報條目（2026-06-11）
  - 既有交付不變：`docs/toolchain-local-gaps-quickview-v1.md` · `docs/toolchain-health-dashboard-v1.md` 末尾 cross-ref（B_REPORT）
- progress_entry:
  - 2026-06-11 · Wave C · WC-C1-01 toolchain local gaps quickview — accepted_with_gaps；本地 optional quickview 已索引於 tickets/README §Wave C C1 與 WORKFLOW_INDEX §1.27；後續 Wave C 票可依賴 WC-PRE-02～05 + 本 CLI 作開票前 gaps 盤點，gate/CI 升格仍走 WC-PRE-06/07。
- followup_suggestions:
  - **Orchestrator**：決定下一張 Wave C 票；可選將 gaps quickview 一條命令列入 Wave C readme／runbook 開票前 checklist（仍標 optional）。
  - **非 blocking（optional）**：補 `--include-health-dashboard` live import 單測與 `--write` artifact smoke test（C_REPORT suggestions）。
  - **gate 升格**：`OG-TOOLCHAIN-HEALTH` PR required · mandatory smoke CI 須 WC-PRE-06/07 批文後另票，**不得**以 WC-C1-01 quickview 輸出當 gate 依據。
