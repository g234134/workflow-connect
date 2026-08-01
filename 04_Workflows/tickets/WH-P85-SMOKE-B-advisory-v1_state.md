# WH-P85-SMOKE-B-advisory-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Phase：Wave-H · P8.5 HTTP path · Smoke B CI advisory (non-blocking)

---

## FRAME

- **summary**: 在 `.github/workflows/bridge-smoke.yml` 新增 **non-blocking** job **`p85-bridge-smoke-b`**，deps 足夠時跑 `tests.test_app_api_orchestration_bridge`（**7/7**）；deps 不足時優雅 skip。更新 runbook §0.3 與 Progress。**不改任何程式碼或測試。**

- **goal**:
  - 保留既有 **`p85-bridge-smoke-a`** job 原樣（steps / env 不變）。
  - 新增 **`p85-bridge-smoke-b`**：`continue-on-error: true` · Python 3.12 · `GOV_CORE_ORCHESTRATION_BRIDGE_OUTBOX_PG_ENABLED=false` · pip install（`|| true`）· skip 判斷（目錄 / `fastapi` / test module import）· unittest **7/7** · 失敗 `::warning` 但不阻 merge。
  - PR `paths` 增加 `test_app_api_orchestration_bridge.py` 與 `app_api.py`。
  - runbook §0.3：雙 job 表（`p85-bridge-smoke-a` · **P85 Bridge Smoke A (advisory · 14/14)** · **14/14**；`p85-bridge-smoke-b` · **P85 Bridge Smoke B (advisory · HTTP API)** · **7/7**）；Smoke C 仍 manual；Scenario 1/2 交叉引用見 **`WH-P85-CI-LAND-v1`** B_REPORT §5。
  - Progress **末尾 append** Wave-H 條目。

- **non_goals**:
  - 不修改 Smoke A job 任何 step 或 env。
  - 不把 Smoke B 設為 branch protection required check。
  - 不改 `gov_core_system/tests/**`、`core/**`、`app_api.py` 或任何 `.py`。
  - 不改 `p7-notification-smoke.yml` / `p9-wc-m2-fixture-execute.yml`。
  - Smoke C（live curl）仍 manual。

- **allowed_paths**:
  - `.github/workflows/bridge-smoke.yml`（僅新增 job B + path filters + 註解）
  - `docs/phase8_5-bridge-smoke-runbook-v1.md`（§0.3 + Smoke B 敘述）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/tickets/WH-P85-SMOKE-B-advisory-v1_state.md`

- **blocked_paths**:
  - `01_Environments/python_venvs/gov_core_system/tests/**`
  - `gov_core_system/core/**`、`app_api.py`、任何 `*.py`
  - `.github/workflows/p7-notification-smoke.yml`
  - `.github/workflows/p9-wc-m2-fixture-execute.yml`
  - `p85-bridge-smoke-a` 既有 steps

- **acceptance_criteria**:
  - **AC-1**：`bridge-smoke.yml` 含 job **`p85-bridge-smoke-b`**，display name 含「HTTP API」· `continue-on-error: true`。
  - **AC-2**：Smoke A job **`p85-bridge-smoke-a`** steps / env **零 diff**（本票僅在其後 append job B）。
  - **AC-3**：Smoke B 在 deps 不足時輸出 `::notice title=Bridge Smoke B skipped::reason=…` 並 **exit 0**。
  - **AC-4**：deps OK 時於 `gov_core_system` cwd 執行 `python -m unittest tests.test_app_api_orchestration_bridge -v`（預期 **7/7**）。
  - **AC-5**：unittest 失敗時輸出 `::warning`；job 仍 `continue-on-error`（non-blocking）。
  - **AC-6**：PR `paths` 含 `test_app_api_orchestration_bridge.py` 與 `app_api.py`。
  - **AC-7**：runbook §0.3 索引 Smoke A + B advisory；Smoke C 仍 manual。
  - **AC-8**：Progress 末尾 append Wave-H 條目；**零** tests/core 程式 diff。

---

## STATE

- **overall_status**: done
- **current_owner**: scribe
- **next_action**: 無（P8.5 advisory CI 線 Reviewer/Scribe 收口完成）
- **last_updated**: 2026-06-22 · reviewer + scribe
- **notes**: Wave-H 新票；Smoke B 接 Wave-G Smoke A advisory 同一 workflow · CI-LAND 設計收口後 C/D 收口（本機 smoke · 遠端 GA pending push）
- **review_done**: true
- **scribe_done**: true
- **status_by_role**:
  - **Orchestrator (A)**: done — 2026-06-22 開票（FRAME 由 Implementer 依任務卡重建）
  - **Implementer (B)**: done — 2026-06-22 workflow + runbook + Progress
  - **Reviewer (C)**: done — 2026-06-22 AC 對照 · Scenario 1 本機 smoke validated · C_REPORT
  - **Scribe (D)**: done — 2026-06-22 D_REPORT · Progress 設計收口條目

---

## B_REPORT (Implementer)

- **changed_files**:
  - `.github/workflows/bridge-smoke.yml` — header 註解 · PR paths（+2）· 新增 job **`p85-bridge-smoke-b`**（Smoke A job 未改）
  - `docs/phase8_5-bridge-smoke-runbook-v1.md` — §0.3 雙 job 表 · Smoke B advisory · Smoke C manual
  - `04_Workflows/00_Agent_Work_Progress.md` — Wave-H append
  - `04_Workflows/tickets/WH-P85-SMOKE-B-advisory-v1_state.md` — 本檔（FRAME + B_REPORT）

- **not_changed**: 所有 `*.py`（含 tests / core / `app_api.py`）· Smoke A steps · 其它 workflow 檔

- **verification**:
  - **本地 deps 存在**（`gov_core_system` venv `Scripts\python.exe`）:
    - `python -m unittest tests.test_app_api_orchestration_bridge -v` → **7/7 OK**
    - `python -m unittest tests.test_minimal_orchestration_bridge -v` → **14/14 OK**（Smoke A 回歸）
  - **本地 deps 缺失**：系統 Python（無 fastapi）import test module → `ModuleNotFoundError: fastapi`；對應 CI skip 路徑（`import fastapi` 檢查）— **未在 CI runner 實跑 skip 分支**，邏輯與 Smoke A 同型。
  - **YAML**：`python -c "import yaml; yaml.safe_load(open('bridge-smoke.yml'))"` → parse OK
  - **Smoke A diff 審查**：`p85-bridge-smoke-a` steps / env 與 Wave-G 交付一致（本票僅在其後 append job B）

- **AC checklist**:
  - **AC-1 ✅**: job `p85-bridge-smoke-b` · name `P85 Bridge Smoke B (advisory · HTTP API)` · `continue-on-error: true`
  - **AC-2 ✅**: Smoke A job 本票 diff 中 steps / env 無變更
  - **AC-3 ✅**: skip 分支三項檢查 + `::notice title=Bridge Smoke B skipped::reason=…` + exit 0
  - **AC-4 ✅**: 本地 venv **7/7 OK**；CI wiring 指向同命令
  - **AC-5 ✅**: 失敗路徑 `::warning title=Bridge Smoke B failed (advisory)::…` + exit test code；job-level `continue-on-error`
  - **AC-6 ✅**: PR paths 已加 `test_app_api_orchestration_bridge.py`、`app_api.py`
  - **AC-7 ✅**: runbook §0.3 雙 job 表；Smoke C = manual only
  - **AC-8 ✅**: Progress append；零 `.py` diff

- **gaps / honesty**:
  - CI runner 上「deps 缺失 skip」與「deps OK 7/7 pass」僅驗證後者（本地 venv）；skip 分支依 Smoke A 同型腳本審查，**待首次 CI 執行確認**。
  - Smoke B 非 branch protection required check（依 FRAME；未改 repo settings）。

---

## C_REPORT (Reviewer)

- **verdict**: **accepted** — P8.5 advisory CI（Smoke A + B）與 runbook §0.3 一致；Scenario 1 **本機 smoke validated**（A **14/14** · B **7/7**）；**遠端 GA 未執行**；仍 **non-blocking / 非 required check**。

- **workflow_design_and_local_smoke**:
  - 現況（2026-06-24 敘事修正）：`.github/workflows/bridge-smoke.yml` **本機版控** · **未 landing 至 `origin/main`** · Actions 無 **P85 Bridge Smoke CI (advisory)** workflow · **無 run_id / run URL**。
  - 對照：workflow `name:` · 雙 job id · `continue-on-error: true` · PR path filters（含 `test_app_api_orchestration_bridge.py` · `app_api.py`）與 B_REPORT / runbook §0.3 **一致**（設計層）。
  - 本機 smoke（暗部 venv cwd）：`test_minimal_orchestration_bridge` **14/14 OK** · `test_app_api_orchestration_bridge` **7/7 OK** — **非遠端 GA log**。

- **smoke_a_job (`p85-bridge-smoke-a`)**:
  | 項 | 預期 | 審查 |
  |----|------|------|
  | 測試模組 | `tests.test_minimal_orchestration_bridge` | workflow step 同命令 · runbook §0.3 表第一列 |
  | 預期 | **14/14** | 本機 smoke **14/14 OK**（暗部 venv）· 遠端 GA log **未收錄** · 未 skip |
  | runbook §0.3 | Smoke A = CI advisory · cwd `gov_core_system` · skip 三項 gate | 與 workflow skip 分支（目錄 / pip / fastapi / core import）語意一致 |
  | 性質 | `continue-on-error: true` | **advisory** · 非 branch protection required |

- **smoke_b_job (`p85-bridge-smoke-b`)**:
  | 項 | 預期 | 審查 |
  |----|------|------|
  | 測試模組 | `tests.test_app_api_orchestration_bridge` | workflow step 同命令 · runbook §0.3 表第二列 |
  | 預期 | **7/7** | 本機 smoke **7/7 OK**（暗部 venv）· 遠端 GA log **未收錄** · 未 skip |
  | skip 條件（workflow） | ① `gov_core_system` 目錄缺失 → `Bridge Smoke B skipped::reason=gov_core_system directory missing` · ② `import fastapi` 失敗 → `reason=fastapi not available` · ③ `import tests.test_app_api_orchestration_bridge` 失敗 → `reason=test module import failed` · 皆 **exit 0** | 本機 happy path **未觸發** skip 分支（deps OK）；腳本邏輯與 AC-3 / runbook §0.3 Skip 列 **一致**（靜態審查 + 本機 happy path）· **GA runner 未實測** |
  | 失敗路徑 | `::warning title=Bridge Smoke B failed (advisory)::…` + job `continue-on-error` | 本機 / GA 均未刻意觸發 · wiring 與 AC-5 一致 |
  | 性質 | 同 Smoke A | **advisory / non-blocking** |

- **AC_recheck（Reviewer）**:
  - **AC-1–AC-8**: 維持 Implementer ✅；本機 smoke 補強 AC-4（**7/7**）· AC-2（Smoke A **14/14** 未 regress）— **均為本機 venv · 非遠端 GA**。
  - **AC-3 gap（誠實）**: Scenario 2（deps 缺失 skip）**仍未在 GA runner 實測**；本機 happy path 已驗 · **遠端 GA pending CI-LAND push**。

- **conclusion**:
  - 兩 job 皆 **advisory · non-blocking · 非 required check**；workflow 失敗不阻 merge（`continue-on-error` + 無 branch protection 升格）。
  - Smoke C（live curl）仍 **manual only**（runbook §0.3 · workflow 無 Smoke C job）。
  - **Bridge 仍 in-memory stub** — 本票驗證 **unittest / CI smoke 路徑**，不等同 production browser 或持久化 bridge。

---

## D_REPORT (Scribe)

- **status**: done
- **evolution（Wave-G → Wave-H）**:
  - **Wave-G**：`.github/workflows/bridge-smoke.yml` 僅 **Smoke A** job `p85-bridge-smoke-a`（`test_minimal_orchestration_bridge` **14/14**）· advisory · deps skip · `continue-on-error`。
  - **Wave-H（本票）**：同一 workflow **append** **Smoke B** job `p85-bridge-smoke-b`（`test_app_api_orchestration_bridge` **7/7** · HTTP API / `TestClient`）· 同型 skip / advisory 語意 · PR paths 擴至 `app_api.py` 與 API test 模組；**Smoke A steps 零 diff**。
  - **Wave-H+1（CI-LAND）**：五檔本機版控 · 首跑 checklist · **遠端 Actions 首跑 pending**（`bridge-smoke.yml` 未 on `origin/main`）· 本 C/D 收口。

- **scenario1_local_smoke_summary**（**無 run id / run URL** · 本機 smoke · 非遠端 GA）:
  1. **Workflow 狀態**：`.github/workflows/bridge-smoke.yml` **本機版控** · **未 landing 至 `origin/main`** · Actions 無 **P85 Bridge Smoke CI (advisory)** workflow。
  2. **Scenario 1（happy path · 本機）**：暗部 venv cwd · `test_minimal_orchestration_bridge` **14/14 OK** · `test_app_api_orchestration_bridge` **7/7 OK** · 兩模組均未 skip — **非遠端 GA log**。
  3. **Advisory 語意**：設計上兩 job `continue-on-error: true` · **非** branch protection required · 與 runbook §0.3 索引一致 · bridge 仍 **in-memory stub**。

- **scenario_2_skip**:
  - **未實測**（本機 + GA）。本機 happy path deps 充足，**未**出現 `::notice title=Bridge Smoke B skipped::reason=…`。
  - **後續**：**CI-LAND push** 後 ops-run **`scenario=scenario2`** GA dispatch；或低優先 doc-only 票刻意觸發 skip 分支複驗 AC-3。

- **progress_pointer**: `04_Workflows/00_Agent_Work_Progress.md` 末尾 **2026-06-22 · Wave-H+1 · P8.5 bridge CI 設計收口** 條目。
