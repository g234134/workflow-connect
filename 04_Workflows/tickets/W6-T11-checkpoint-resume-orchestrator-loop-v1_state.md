# TICKET STATE · W6-T11 · checkpoint-resume-orchestrator-loop-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 6 · Agent Standard Line · HITL Resume Loop  
> **本輪**：Design-only（P1）；**禁止**改 `scripts/`、`hitl/`、`tests/` runtime code。

---

## FRAME

### Goal

讓 Checkpoint A / B 在 human decision 後，orchestrator 可**讀取已批准 checkpoint 狀態並續跑**（S7+ 或 delivery/export），而不是重新從 S3 從頭跑或要求操作者手動拼湊第二套命令。

**目標 UX（一句）**：Human 用 `run_hitl_checkpoint_cli --apply-decision` 批完後，用**同一 orchestrator CLI** 加 `--resume-checkpoint <path>` 即可接續實驗線。

### Scope（v1）

- 定義 resume loop UX、最小狀態機、checkpoint JSON 消費契約
- 僅處理 **`status=approved`** 的 resume（Checkpoint A `approve`；Checkpoint B `approve_delivery`）
- 實驗線 `scripts/run_agent_standard_case_experiment.py` 為唯一 resume 入口（P2 實作）
- 對齊既有 W6-T5 / W6-T6 `resume_context` + `resume_plan_from_*` 契約

### NonScope

- 不做多 checkpoint queue / 分散式 scheduler / 通知系統聯動
- 不處理 `revise_plan` / `request_changes` / `hold` 的 resume 子樹（v1 fail-close）
- 不做「原指令零參數自動偵測 latest approved」（留 P3 optional convenience）
- 不改主鏈 E2E、Local UI、production delivery notify
- 本輪（P1）不寫程式碼

### Dependencies

- **W6-T5** · Checkpoint A integration + `resume_plan_from_checkpoint_a`
- **W6-T6** · Checkpoint B integration + `delivery_plan_from_checkpoint_b`
- **W6-T10** · orchestrator S4/S12 已接整合層；run 模式 CP-A `written` 時 `_can_start_run_execution` 為 false → `waiting_for_human`
- **W5-T2B** · `hitl/checkpoints_v1.py` · `record_human_decision` 寫入 `status` + `resume_context`

### AllowedPaths（P1）

- `04_Workflows/tickets/W6-T11-checkpoint-resume-orchestrator-loop-v1_state.md`（本檔）
- `docs/agent-run-standard-case-orchestrator-v1.md`（§9 resume loop design cross-ref only）

### BlockedPaths（P1）

- `scripts/*.py` · `hitl/*.py` · `tests/*.py`

---

## Acceptance Criteria（票級 · P2+P3 合計）

| AC | 描述 | P | 狀態 |
|----|------|---|------|
| AC-1 | 可從 **approved Checkpoint A** resume 到 **S7 run path**（cleaning / gate 執行） | P2 | ✅ P2 |
| AC-2 | 可從 **approved Checkpoint B** resume 到 **delivery / export path**（實驗線 sandbox bundle 或 profile 允許之 export） | P2 | ✅ P2 |
| AC-3 | **rejected / non-approved / stale / mismatched** checkpoint → **fail-close**（`ok=false` + 明確 `message`） | P2 | ✅ P2 |
| AC-4 | Resume 不重新寫入 pending checkpoint A/B；不重跑 S3–S6（A resume）或 S7–S12（B resume） | P2 | ✅ P2 |
| AC-5 | 測試矩陣覆蓋 A/B approve、reject、stale、case_ref mismatch、duplicate resume | P3 | ✅ P3 |
| AC-6 | `docs/agent-run-standard-case-orchestrator-v1.md` + checkpoint integration docs 補 resume 流程 | P3 | ⬜ |

---

## STATE

- **overall_status**: `p3_hardening_done`（Implementer 2026-06-16 · P3 邊界測試矩陣補齊；待 Reviewer 複驗 + docs AC-6）
- **current_owner**: reviewer
- **next_action**: Reviewer 複驗 P3 測試矩陣；Scribe / 後續票補 docs §9 定稿（AC-6）
- **last_updated**: 2026-06-16
- **status_by_role**:
  - orchestrator: pending（待 Reviewer 簽 P3）
  - implementer: done（P3 hardening）
  - reviewer: pending（P3 複驗）
  - scribe: pending

---

## B_REPORT · P1 Design（2026-06-16）

### changed_files

- `04_Workflows/tickets/W6-T11-checkpoint-resume-orchestrator-loop-v1_state.md`（新建 · 本檔）
- `docs/agent-run-standard-case-orchestrator-v1.md`（§9 Resume loop · planned）

### verification

- 無 runtime 變更；P1 以設計對照既有 orchestrator / integration / checkpoints_v1 為準

---

## B_REPORT · P2 Implementation（2026-06-16）

### changed_files

- `scripts/run_agent_standard_case_experiment.py` — `--resume-checkpoint` CLI、`load_checkpoint_for_resume()`、`validate_resume_eligibility()`、CP-A→S7 / CP-B→S13 分支、duplicate delivery marker
- `tests/test_agent_standard_case_experiment.py` — CP-A resume、CP-B resume、case_ref mismatch blocked 測試
- `04_Workflows/tickets/W6-T11-checkpoint-resume-orchestrator-loop-v1_state.md`（本檔 · P2 狀態更新）

### skeleton / placeholder

- 無新增 skeleton；duplicate delivery guard 以 outbox marker 保守實作（非 event log 幂等）

### verification

```bash
python -m unittest tests.test_agent_standard_case_experiment -v
# Ran 36 tests in ~6s — OK
```

新增測試：

- `test_approved_checkpoint_a_resume_runs_s7_path`
- `test_approved_checkpoint_b_resume_runs_s13_delivery`
- `test_resume_checkpoint_case_ref_mismatch_blocked`

### blocked / next

- P3：reject / stale / duplicate resume 擴充矩陣、docs §9 定稿、`--resume-latest-approved` optional

---

## B_REPORT · P3 Hardening（2026-06-16）

### changed_files

- `tests/test_agent_standard_case_experiment.py` — P3 fail-close 邊界測試 7 條；P2 測試 docstring / section comment 對齊 reviewer 用語
- `04_Workflows/tickets/W6-T11-checkpoint-resume-orchestrator-loop-v1_state.md`（本檔 · P3 狀態 + 測試矩陣）

### skeleton / placeholder

- 無

### bug_fix

- **無**。P3 僅補測試；未改 `scripts/run_agent_standard_case_experiment.py` 核心流程。

### P3 測試矩陣（reviewer recommended_tests 對照）

| ID | 測試名稱 | 情境 | `final_status` / 行為 |
|----|----------|------|------------------------|
| R1 | `test_resume_checkpoint_awaiting_human_blocked` | 未 `--apply-decision` 前 resume | `blocked` · message 含 awaiting human decision |
| R2 | `test_resume_checkpoint_preview_mode_blocked` | `--mode preview` + resume | `blocked` · resume requires --mode run |
| R3 | `test_resume_checkpoint_duplicate_delivery_blocked` | 同一 B checkpoint resume 兩次 | 第一次 `ok`；第二次 `duplicate_delivery` |
| R4 | `test_resume_checkpoint_b_stale_artifacts_blocked` | 篡改 artifact 路徑 + 暫移 cleaned/ | `blocked` · stale checkpoint artifacts missing |
| S1 | `test_resume_checkpoint_task_type_mismatch_blocked` | CLI task_type ≠ checkpoint | `checkpoint_mismatch` |
| S2 | `test_resume_checkpoint_rejected_status_blocked` | status=rejected | `blocked` · v1 approved only |
| S3 | `test_resume_checkpoint_wrong_human_action_blocked` | CP-B approved 但 action≠approve_delivery | `blocked` |

**P2 保留（happy path + mismatch）**：`test_approved_checkpoint_a_resume_runs_s7_path` · `test_approved_checkpoint_b_resume_runs_s13_delivery` · `test_resume_checkpoint_case_ref_mismatch_blocked`

### verified_behaviors（P3 新增 fail-close 證明）

- awaiting_human checkpoint 不可 resume（須先 human decision）
- preview mode 與 resume 互斥（fail-close）
- B delivery resume 幂等：outbox marker 阻擋 duplicate
- B resume 前置 artifact 缺失 fail-close（eligibility + cleaned 皆缺）
- task_type / rejected / wrong human action 皆 fail-close，不改 happy path

### verification

```bash
python -m unittest tests.test_agent_standard_case_experiment -v
# Ran 43 tests in ~6s — OK（P2: 36 → P3: +7）
```

### blocked / next

- AC-6 docs §9 定稿（本輪 AllowedPaths 外；留 Scribe / 後續票）
- Optional：`--resume-latest-approved` convenience flag

---

## REVIEW · P2（2026-06-16）

### verdict

**`accept_with_followups`**

P2 核心 resume 路徑（CP-A→S7、CP-B→S13）與設計對齊；fail-close 驗證邏輯已落地於 `validate_resume_eligibility()` / B artifact guard / duplicate marker，但邊界測試仍偏薄（票面 AC-5 本屬 P3）。建議帶 follow-ups 進 P3，不阻塞 P2 合流。

### verification（Reviewer 重跑）

```bash
python -m unittest tests.test_agent_standard_case_experiment -v
# Ran 36 tests in ~6s — OK
```

### design_alignment（逐條）

| 設計項 | 結果 | 證據 |
|--------|------|------|
| `--resume-checkpoint <path>` | ✅ | CLI `--resume-checkpoint` → `_run_experiment_resume_from_checkpoint()` |
| resume 僅 `--mode run` | ✅ | `validate_resume_eligibility` L1038–1039 |
| `schema_version == hitl_checkpoint_v1` | ✅ | 對照 `CHECKPOINT_SCHEMA_VERSION` |
| `status == approved` | ✅ | 非 approved → blocked；含 awaiting_human / rejected / revise / on_hold |
| `case_ref` / `task_type` match | ✅ | `checkpoint_mismatch`；task_type 可 fallback `agent_output.task_type` |
| human action + `resume_context` | ✅ | A:`approve`+`resume_from=selector`；B:`approve_delivery`；整合層 plan 二次驗證 |
| CP-A 跳 S3–S6，從 S7 | ✅ | `skipped_steps` + 無 S3–S6 in `steps_run`；直接 `_execute_run_path_tools` |
| CP-B 跳 S3–S12，S13 export | ✅ | `resume_from_step=S13`；僅 `export.delivery_bundle` profile |
| 不重寫 resumed CP-A/B pending | ✅ | A/B resume 皆 `resumed_*` status，不呼叫 `maybe_create_checkpoint_a`；B 不跑 S12 integration write |
| fail-close（code） | ✅ 實作 / ⚠️ 測試 | mismatch / non-approved / stale artifact / duplicate 均有 code path；僅 mismatch 有單測 |

### risks / gaps

1. **測試缺口**：3 測試僅覆 happy path（A/B）+ case_ref mismatch；reject、awaiting_human、preview+resume、task_type mismatch、duplicate delivery、stale artifact 均未測（AC-5 → P3）。
2. **Stale 定義偏窄**：`expires_at` 僅在 `status=awaiting_human` 時檢查；approved checkpoint 無 resolved_at / artifact mtime guard（設計 v1 可接受）。
3. **B artifact 解析**：`_artifact_path_exists` 僅 repo-root 相對路徑；`cleaned_csv` 路徑常與 fixture 不符時靠 `case_path/cleaned/*.csv` fallback 通過——實際環境若兩者皆缺才 fail-close。
4. **Duplicate guard**：outbox marker 檔（非 event log）；成功才寫 marker、失敗可重試——合理但無單測；刪 marker 可重送 delivery。
5. **Profile drift（R5）**：CP-A resume 仍用當前 `get_run_path_profile()`，planned_tools 來 checkpoint——與 P1 設計「v1 信任 checkpoint」一致，非 bug。
6. **CP-A resume 後若觸發 CP-B**：`_finalize_after_run_execution` 可寫**新** pending CP-B——屬正常前進，非重寫 resumed CP-A。

### recommended_tests（P3 優先序）

1. `test_resume_checkpoint_awaiting_human_blocked` — 未 `--apply-decision` 前 resume
2. `test_resume_checkpoint_preview_mode_blocked` — `--mode preview` + resume
3. `test_resume_checkpoint_duplicate_delivery_blocked` — 同一 B checkpoint resume 兩次
4. `test_resume_checkpoint_b_stale_artifacts_blocked` — 刪除 eligibility / cleaned 後 fail-close

（次優：`task_type` mismatch、`status=rejected`、wrong human action）

### follow_ups（→ W6-T11-P3）

- 補上表 4 測試 + AC-5 矩陣其餘項
- `docs/agent-run-standard-case-orchestrator-v1.md` §9 定稿
- 評估 artifact 路徑解析是否需對齊 case_dir / outbox（非 P2 blocker）

---

## 1. Resume UX 方案

### 方案 A（**推薦 · v1 採用**）：顯式 `--resume-checkpoint <path>`

```bash
# Step 1 — 初次 run，停在 Checkpoint A
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --format json
# → final_status=waiting_for_human, checkpoint_a_status.checkpoint_path=...

# Step 2 — Human 決策（既有 CLI，不 resume 主鏈）
python scripts/run_hitl_checkpoint_cli.py \
  --apply-decision approve \
  --checkpoint-id A-intake-confirmation \
  --notes "LGTM"

# Step 3 — Orchestrator resume（**本票 P2 新增**）
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --resume-checkpoint outbox/demo_phase/checkpoint_A-intake-confirmation_<ts>.json \
  --format json
# → 從 S7 續跑；若觸發 CP-B 則再次 waiting_for_human
```

**選擇理由**：

1. **Fail-close**：路徑明確，避免「同一 case 多份 checkpoint」歧義
2. **可審計**：resume 命令與 checkpoint 檔案一一對應
3. **對齊 roadmap**：`docs/agent-and-non-tabular-lines-readme-v1.md` §6 已預留 `--resume-from-checkpoint`
4. **測試友好**：fixture 可直接指向 golden checkpoint JSON

**Companion flags（P2 最小集）**：

| Flag | Required | 說明 |
|------|----------|------|
| `--resume-checkpoint` | resume 時 yes | checkpoint JSON 路徑（repo-relative / outbox-relative / absolute，沿用 W6-T5 三層解析） |
| `--task-type` | yes | 須與 checkpoint `task_type` 一致 |
| `--case-dir` | yes | 須與 checkpoint `case_ref` 一致 |
| `--mode` | yes | resume **必須** `run`（preview + resume → fail-close） |
| `--outbox-root` | no | 與初次 run 相同時才通過 artifact 路徑解析 |

### 方案 B（備選 · v1 不採 · P3 optional）：`--resume-latest-approved`

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --resume-latest-approved \
  --checkpoint-id A-intake-confirmation
```

掃描 `outbox/<case_ref>/` 下 **最新** `status=approved` 且 `checkpoint_id` 匹配的檔案。

**不採為 v1 預設原因**：多 checkpoint、跨 run_id、測試 outbox override 時易選錯；僅適合作 operator 便利層（P3）。

### 方案 C（拒絕）：原指令零 flag 自動偵測

同一 `--case-dir` 再跑 `--mode run` 時自動找 approved checkpoint 續跑。

**拒絕原因**：與「初次 run 寫新 checkpoint」語意衝突；無法區分「新 run」vs「resume」；fail-close 困難。

---

## 2. 最小狀態機

### 2.1 現況（W6-T10 已落地）

```
[S3 decision] → [S5 route] → [S6 preview] → [S4 CP-A write?]
                                              │
                    status=written ───────────┼──→ final_status=waiting_for_human
                    (_can_start_run_execution=false, S7+ 不跑)
                                              │
                    status=auto_approved ───────┴──→ S7–S12 繼續
```

Human 批完後 checkpoint 檔案：`status=approved`，`resume_context` 已填充（W5-T2B `record_human_decision`）。

### 2.2 Resume 狀態轉移（v1 · approved only）

#### Checkpoint A · `approve` → resume at **S7**

| 前置 | 驗證 | 續跑入口 | 跳過步驟 | 終態 |
|------|------|----------|----------|------|
| `checkpoint_id=A-intake-confirmation` | `status==approved` | **S7** `_execute_run_path_tools` | S3–S6、S4 寫檔 | `run_complete` 或 CP-B `waiting_for_human` |
| `resume_context.resume_from==selector` | `case_ref` / `task_type` match CLI | 使用 `resume_context.planned_tools` + profile | 不重跑 decision | |
| | `schema_version` 支援 | | | |

**S7 語意**：gate validation + cleaning execution（依 `run_path_profile.tools_to_run`）；非從 S5 重算 route（v1 信任 approved checkpoint 內 `planned_tools`；P3 可加 optional re-validate）。

#### Checkpoint B · `approve_delivery` → resume at **S13 delivery/export**

| 前置 | 驗證 | 續跑入口 | 跳過步驟 | 終態 |
|------|------|----------|----------|------|
| `checkpoint_id=B-delivery-confirmation` | `status==approved` | **S13** sandbox delivery / export | S3–S12 | `sandbox_e2e_complete` 或 `run_complete` |
| `resume_context.resume_from==delivery` | 前置 artifacts 存在（bundle path） | `write_sandbox_delivery_bundle` 或 export tool | 不重跑 cleaning | |
| | CP-A 曾 approved（或同 run 語意） | | | |

**前置假設**：Checkpoint B resume 時 S7–S11 已在**同一 experiment run** 完成並寫入 checkpoint B payload；resume 僅執行 delivery/export 步驟。

#### Fail-close 表（v1）

| 條件 | `ok` | `final_status` | `message` 語意 |
|------|------|----------------|----------------|
| `status=awaiting_human` | false | `blocked` | 尚未 human decision；請先 `run_hitl_checkpoint_cli --apply-decision` |
| `status=rejected` | false | `blocked` | Checkpoint A reject；不可 resume |
| `status=revised` / `on_hold` | false | `blocked` | v1 不支援 revise/hold resume |
| human action 非 approve / approve_delivery | false | `blocked` | v1 僅支援 approved resume |
| `expires_at` 已過且仍 pending | false | `stale_checkpoint` | checkpoint 過期 |
| `case_ref` ≠ CLI `--case-dir` 推導 | false | `checkpoint_mismatch` | case 不一致 |
| `task_type` ≠ CLI `--task-type` | false | `checkpoint_mismatch` | task 不一致 |
| `schema_version` 未知 | false | `blocked` | schema 不支援 |
| `resume_context` 缺失 | false | `blocked` | 未經 `record_human_decision` |
| B resume 但 artifacts 缺失 / bundle 不存在 | false | `blocked` | stale artifact |
| B resume 但 delivery 已寫（duplicate） | false | `duplicate_delivery` | idempotency guard（P2/P3） |
| `--mode preview` + `--resume-checkpoint` | false | `blocked` | resume 需 run mode |

**Stale artifact（approved checkpoint）**：v1 最小規則 — checkpoint B 內 `agent_output.artifacts.delivery_bundle` 指向的檔案不存在 → fail-close；可選 P3 加 `resolved_at` vs bundle mtime 檢查。

---

## 3. 資料來源與契約

### 3.1 Orchestrator 必讀欄位（checkpoint JSON）

| 欄位 | 用途 | 必填 |
|------|------|------|
| `schema_version` | 版本 gate | yes |
| `checkpoint_id` | 分支 A vs B | yes |
| `case_ref` | 與 `--case-dir` 交叉驗證 | yes |
| `task_type` | 與 `--task-type` 交叉驗證 | yes |
| `status` | 必須 `approved`（v1） | yes |
| `human_decision.action` | 必須 `approve` 或 `approve_delivery` | yes |
| `resume_context` | 續跑計畫 SSOT | yes |
| `resume_context.resume_from` | `selector`（A）或 `delivery`（B） | yes |
| `resume_context.planned_tools` | A resume 工具列表 | A only |
| `resume_context.selector_task_type` | A resume selector | A optional |
| `resume_context.artifacts` | B resume 交付物路徑 | B only |
| `created_at` / `resolved_at` | 審計、stale 檢查 | optional |
| `expires_at` | pending stale | optional |
| `run_id` / `experiment_id` | 幂等、duplicate 檢測 | optional（P3 強化） |

### 3.2 不採用或次要的欄位

| 欄位 | 說明 |
|------|------|
| `decision.status` | **不存在**於 checkpoint schema；用 top-level `status` |
| `next_step` | **不存在**；用 `resume_context.resume_from` + integration `resume_plan_from_*` |
| `resume_plan` | 在 integration **回傳**中，非 checkpoint 檔必存欄；resume 時由 `resume_plan_from_checkpoint_a(b)(resume_context)` **衍生** |

### 3.3 解析與衍生流程（P2 實作契約）

```
load_checkpoint(path) → validate_resume_eligibility() → branch:
  A: resume_plan_from_checkpoint_a(resume_context)
  B: delivery_plan_from_checkpoint_b(resume_context)
→ orchestrator_enter_at(S7 | S13)
```

`checkpoint_path` 解析沿用 W6-T5 §7 三層 fallback（repo-relative → outbox-relative → absolute）。

---

## 4. Proposed CLI（P2 目標）

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run \
  --resume-checkpoint outbox/demo_phase/checkpoint_A-intake-confirmation_2026-06-16T12-00-00Z.json \
  [--outbox-root <same-as-initial-run>] \
  --format json
```

**輸出新增欄位（建議）**：

```json
{
  "resume": {
    "ok": true,
    "checkpoint_path": "outbox/demo_phase/checkpoint_A-....json",
    "checkpoint_id": "A-intake-confirmation",
    "resume_from_step": "S7",
    "skipped_steps": ["S3_decision_evaluate", "S4_checkpoint_a", "S5_route_planning", "S6_tool_path_preview"]
  },
  "final_status": "waiting_for_human"
}
```

---

## 5. Risks

| ID | 風險 | 緩解（P2/P3） |
|----|------|---------------|
| R1 | **Stale artifact** — 批完後 case 檔案已變 | B resume 前檢查 artifacts 存在；optional mtime guard |
| R2 | **case_ref mismatch** — CLI 指錯 case | 硬性 cross-check `case_ref` ↔ `case_dir` |
| R3 | **Duplicate delivery** — 同一 B checkpoint resume 兩次 | idempotency：檢查 `outbox/sandbox_delivery/` manifest 或 event log |
| R4 | **planned_tools drift** — A approve 後 route 規則變更 | v1 信任 checkpoint；P3 optional `--revalidate-route` |
| R5 | **Partial run profile** — resume 與初次 profile 不一致 | resume 時從 checkpoint 還原 `run_path_profile` 或 fail-close |
| R6 | **External outbox** — path 解析失敗 | 沿用 W6-T5 三層 fallback + 相同 `--outbox-root` |

---

## 6. 子票拆分

### W6-T11-P2 · Minimal CLI / orchestrator resume（Implementer）

**Goal**：實作 `--resume-checkpoint` + orchestrator branch + fail-close validators。

**Scope**：

- `scripts/run_agent_standard_case_experiment.py` — resume entry、S7/S13 branch、skip logic
- `hitl/checkpoint_resume_v1.py`（或 orchestrator 內 `_load_*`）— `load_checkpoint_for_resume()` · `validate_resume_eligibility()`
- `tests/test_agent_standard_case_experiment.py` — AC-1～AC-4 最小測試

**AllowedPaths**：`scripts/run_agent_standard_case_experiment.py` · `hitl/checkpoint_resume_v1.py`（新建）· `tests/test_agent_standard_case_experiment.py`

**DoD**：AC-1～AC-4；unittest 全綠；B_REPORT。

### W6-T11-P3 · Test matrix / docs / guardrails（Implementer + Reviewer）

**Goal**：補齊邊界測試、文件、幂等 guard。

**Scope**：

- 測試矩陣：reject、stale、case mismatch、duplicate B resume、external outbox path
- `docs/agent-run-standard-case-orchestrator-v1.md` §9 定稿
- `docs/checkpoint-a-integration-v1.md` · `docs/checkpoint-b-integration-v1.md` — resume consumer 小節
- Optional：`--resume-latest-approved` convenience flag
- `docs/agent-and-non-tabular-lines-readme-v1.md` §6 Resume framework 狀態更新

**DoD**：AC-5～AC-6；Reviewer accepted；Scribe cross-ref。

---

## O_NOTES

| 日期 | 角色 | 內容 |
|------|------|------|
| 2026-06-16 | implementer (B-design) | P1 design complete. Recommend explicit `--resume-checkpoint` over auto-detect. v1 approved-only; A→S7, B→S13 delivery. Split P2 (impl) / P3 (matrix+docs). |
| 2026-06-16 | implementer (P2) | 落地 `--resume-checkpoint`：CP-A 跳 S3–S6 進 S7+；CP-B 跳 S3–S12 進 S13 export；fail-close 含 mismatch / non-approved / stale artifact / duplicate marker；36 unittest OK。 |
| 2026-06-16 | reviewer (P2) | **accept_with_followups**。設計對齊 AC-1～AC-4；fail-close code 完整但單測僅 3 條。風險：artifact 路徑 fallback、duplicate marker 未測、stale 檢查偏窄。P3 補 4 測試 + docs。 |
| 2026-06-16 | implementer (P3) | 補 7 條 fail-close 邊界測試（R1–R4 + S1–S3）；未改核心流程；43 unittest OK；AC-5 ✅。 |

---

*W6-T11 · checkpoint-resume-orchestrator-loop-v1 · P1 design · 2026-06-16*
