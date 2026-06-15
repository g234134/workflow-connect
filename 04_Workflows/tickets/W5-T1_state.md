# TICKET STATE · W5-T1 · Skill Card 審批 → 可重用 Registry 管道

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 5 - Browser + Skill Distillation

---

## FRAME

- Title: Skill Card 審批 → 可重用 Registry 管道
- Goal: Wave8 draft skill card 經 review queue 批准後進入 approved registry，供 selector 只讀消費。
- Scope:
  - 收口 _wave8_skill_card_review_queue.py 批准路徑
  - 產出 skills/approved_registry.json（與 gov_cards 分離）
  - CLI：skill-registry list-approved / promote-from-queue
  - 對齊 WAVE8_SKILL_CARD_REVIEW_QUEUE_RUNBOOK_v0.1.md
- NonScope:
  - 自動改 prod selector
  - 與 Gov Tool Catalog 合 schema
  - 客戶門戶上架
- AllowedPaths:
  - 04_Workflows/_wave8_skill_card_review_queue.py
  - skills/approved_registry.json
  - tests/test_skill_registry.py
- BlockedPaths:
  - skills/gov_cards/*
  - core/ask_rag_selector.py
  - AGENTS.md
- Dependencies:
  - Wave 8 review queue 既有腳本
  - W3-T1 catalog 權威邊界文檔
- Risks:
  - 重複 promote → 冪等跳過
  - approved card 缺 applicable_scenarios → incomplete 不進 selector
- Observability:
  - logs: promote、reject、reviewer
  - metrics: skill_cards_approved_total
  - traces: N/A
- OutputArtifacts:
  - skills/approved_registry.json
  - promote CLI + tests
  - 更新 runbook
- AcceptanceCriteria:
  - draft → approved 後 registry 含 skill_id、version、approved_at
  - 未審批 draft 不得出現在 approved registry
  - unittest 覆蓋 promote/reject/duplicate
  - Review queue 與 registry 雙向可追溯
- VerificationCommands:
  - `python -m unittest tests.test_skill_registry -v`
    - 預期：全綠

---

## STATE

- overall_status: accepted_with_gaps
- implementation_status: review_passed
- current_owner: orchestrator
- next_action: closed — 後續追蹤：selector 消費 approved_registry、runbook 同步、skills/cards↔registry 雙向 sync（見 D_REPORT / C_REPORT gaps；**非** W5-T1-intake-decision-rules-v1）
- last_updated: 2026-06-15 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

> **Orchestrator 預填（2026-06-15）**：Implementer 依「Orchestrator 施工說明」施工；完成後更新 deliverable 欄位。**保留本節歷史，不刪除。**

### Orchestrator 施工說明（Implementer 依此執行）

**Goal（1 句）**：Wave8 draft skill card 經 review queue 批准後寫入 **`skills/approved_registry.json`**（與 `gov_cards` / `skills/cards/` 分離），供 selector **只讀**消費；CLI 支援 `list-approved` / `promote-from-queue`。

**Files to touch**

- `04_Workflows/_wave8_skill_card_review_queue.py`（**擴充** · 保留既有 list/approve/reject；新增 `promote-from-queue` 寫 registry、`list-approved` 讀 registry；**不破壞**既有 approve→`skills/cards/` 移動行為，或文檔化雙軌）
- `skills/approved_registry.json`（**新建** · 結構含 `schema_version`、`registry_revision`、`approved[]`；每項含 `skill_id`、`version`、`approved_at`、來源 draft 路徑或 queue id）
- `tests/test_skill_registry.py`（**新建** · promote/reject/duplicate 冪等；未審 draft 不得進 registry）
- `04_Workflows/WAVE8_SKILL_CARD_REVIEW_QUEUE_RUNBOOK_v0.1.md`（**可選輕修** · 若 FRAME 未列 AllowedPaths 則 **deferred**；優先只改 AllowedPaths 內檔）

**Non-Scope（Implementer 不得做）**

- 自動改 prod selector、`core/ask_rag_selector.py`
- 與 Gov Tool Catalog 合 schema
- 客戶門戶上架、改 `skills/gov_cards/*`
- 改 `AGENTS.md`

**Steps**

1. 對照既有 `tests/test_wave8_skill_card_review_queue.py` 與 runbook §3 CLI，設計 `approved_registry.json` schema（與 `skills/cards/` 檔案內容**分離** — registry 為索引/元資料 SSOT）。
2. 實作 `promote-from-queue`：從 `skills/drafts/` 經既有 approve 校驗 → append/update registry（duplicate `skill_id` **冪等跳過**或回傳 `ok: true, skipped: true`）。
3. 實作 `list-approved`：stdout JSON `{ok, count, approved[]}`。
4. 校驗：`applicable_scenarios` 缺失或 `review_status != approved` 的 card 標 `incomplete`，**不**寫入 registry（或寫入但 `selector_eligible: false` — 在 B_REPORT 明示選項）。
5. 新增 `tests/test_skill_registry.py`：draft→approved 後 registry 含必填欄位；reject 不進 registry；duplicate promote 冪等。
6. B_REPORT 附 CLI demo 命令與 structured 輸出語意。

**Tests / Verification**

- `python -m unittest tests.test_skill_registry -v` → 全綠
- 手動 CLI demo（temp `--skills-root` 或 fixture）：
  - `python 04_Workflows/_wave8_skill_card_review_queue.py list-approved --pretty`
  - `python 04_Workflows/_wave8_skill_card_review_queue.py promote-from-queue --draft skills/drafts/<fixture>.json --pretty`
- 回歸：`python -m unittest tests.test_wave8_skill_card_review_queue -v` → 既有測試仍綠（若改同一腳本）

**Deferred / out-of-scope**

- selector 實際消費 `approved_registry.json`（另票）
- runbook 全文更新（若未在 AllowedPaths — Scribe 或 follow-up）
- `skills/cards/` 與 registry 自動雙向同步（本票僅 queue→registry 單向可追溯）

### Implementation Plan (initial)

- [x] 收口 review queue promote 路徑
- [x] 產出 approved_registry.json
- [x] CLI list-approved / promote-from-queue
- [x] tests promote/reject/duplicate

### Files To Touch

- 04_Workflows/_wave8_skill_card_review_queue.py
- skills/approved_registry.json
- tests/test_skill_registry.py

- changed_files:
  - `04_Workflows/_wave8_skill_card_review_queue.py`（新增 `list-approved`、`promote-from-queue`；保留 list/approve/reject）
  - `skills/approved_registry.json`（新建 · `schema_version` + `registry_revision` + `approved[]`）
  - `tests/test_skill_registry.py`（新建 · promote/reject/duplicate/未審/incomplete）
- artifacts:
  - Approved registry SSOT at `skills/approved_registry.json`
  - CLI subcommands `list-approved`, `promote-from-queue`
- verification:
  - `python -m unittest tests.test_skill_registry -v` → **6 tests OK**
  - `python -m unittest tests.test_wave8_skill_card_review_queue -v` → **6 tests OK**（既有回歸仍綠）
  - CLI demo（temp `--skills-root`）：`list-approved --pretty` → `{ok: true, count: N}`；`promote-from-queue --draft <cards/...>` → `{ok: true, skill_id, approved_at, source_card_path}`
- behavior_notes: `promote-from-queue` 要求 `review_status=approved` + 非空 `applicable_scenarios`；缺 scenarios 標 incomplete 不寫 registry（`selector_eligible: false` 語意）；duplicate `skill_id` 回傳 `ok: true, skipped: true`；reject/未審 draft 不進 registry；**未**改 `approve→cards/` 移動行為
- deferred_items: selector 實際消費 `approved_registry.json`（另票）；runbook 全文更新（Scribe/follow-up）；`skills/cards/` 與 registry 自動雙向同步

---

## C_REPORT

<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

> **Orchestrator 預填草稿（2026-06-15）**：Reviewer 依 AC 勾選後填 `conclusion`。

### Reviewer Checklist（對照 FRAME AcceptanceCriteria）

| AC | 檢查項 | 通過條件 |
|----|--------|----------|
| **AC-1** | draft → approved 進 registry | registry 含 `skill_id`、`version`、`approved_at`；B_REPORT 附 verification 輸出 |
| **AC-2** | 未審 draft 隔離 | reject 或未 approve 的 draft **不在** `approved_registry.json` |
| **AC-3** | unittest 覆蓋 | promote / reject / duplicate 三路徑；Reviewer 重跑 `tests.test_skill_registry` |
| **AC-4** | 雙向可追溯 | B_REPORT 或 registry 項含來源 draft 路徑／queue 參照 |
| **AC-5** | 冪等 duplicate | 重複 promote 不 corrupt registry（skip 或 no-op 有測試） |
| **AC-6** | BlockedPaths | 未改 `gov_cards/*`、`ask_rag_selector`、未自動改 prod selector |

### 結論門檻

- **`accepted`**：AC-1～AC-6 全 ✅；unittest 全綠；既有 review queue 測試仍綠。
- **`accepted_with_gaps`**：AC-1/2/3/5/6 ✅；AC-4 追溯欄位簡略或 runbook 未同步（deferred）；incomplete card 策略已在 B_REPORT 明示。
- **`needs_changes`**：AC-1/2/3 任一 ❌（未審進 registry、測試紅、duplicate 非冪等）。
- **`rejected`**：改 selector 生產路徑、merge gov_cards schema、觸 BlockedPaths。

- conclusion: accepted_with_gaps
- blocking_issues: 無
- checks_summary: |
    - **AC-1** ✅ 達成 — `promote-from-queue` 寫入 registry；項含 `skill_id`、`version`、`approved_at`；B_REPORT verification 附 CLI 輸出語意。
    - **AC-2** ✅ 達成 — `test_reject_does_not_enter_registry`、`test_unapproved_draft_promote_fails` 驗證 reject/未審 draft 不進 registry。
    - **AC-3** ✅ 達成 — Reviewer 重跑 `tests.test_skill_registry` 6/6 OK；回歸 `tests.test_wave8_skill_card_review_queue` 6/6 OK。
    - **AC-4** ✅ 達成 — registry 項含 `source_card_path`；queue→registry 單向可追溯（B_REPORT behavior_notes）。
    - **AC-5** ✅ 達成 — `test_duplicate_promote_is_idempotent` 驗證 `ok: true, skipped: true` 冪等。
    - **AC-6** ✅ 達成 — 未改 `skills/gov_cards/*`、`core/ask_rag_selector.py`；未自動改 prod selector。
- risk_level: low
- gaps: |
    - selector 實際消費 `approved_registry.json`（另票）。
    - `WAVE8_SKILL_CARD_REVIEW_QUEUE_RUNBOOK_v0.1.md` 全文同步（不在本票 AllowedPaths）。
    - `skills/cards/` 與 registry 自動雙向同步。
- suggestions: |
    1. 另票讓 selector 只讀消費 `approved_registry.json`。
    2. Scribe 或 follow-up 票更新 runbook §promote/list-approved CLI。
    3. **票號語境**：本票 W5-T1 = Skill Registry 管道；Dashboard `W5-T1-intake-decision-rules-v1` 為不同票。

---

## D_REPORT

> **Scribe skeleton（2026-06-15）** — 基於 Reviewer `accepted_with_gaps`；Orchestrator 關票前為草稿。

- **Summary**: Wave8 Skill Card 審批→Registry 管道落地：`skills/approved_registry.json` SSOT、`_wave8_skill_card_review_queue.py` 新增 `list-approved`/`promote-from-queue`（保留既有 approve/reject）、`tests/test_skill_registry.py`（6 tests OK；review queue 回歸 6/6 OK）。
- **Scope**: queue→registry 單向 promote 與 CLI；與 `gov_cards` 分離；不負責 prod selector 改動、Gov catalog 合 schema、客戶門戶上架。
- **Deferred**: selector 消費 registry；runbook 全文更新；`skills/cards/` 與 registry 雙向自動同步。

- docs_updates: 建議更新 `docs/WAVE_PROGRESS_DASHBOARD.md` Wave 5 註解（**Skill Registry** `W5-T1_state.md` `accepted_with_gaps`，與 intake decision rules 分軌）；Progress 末尾追加條目。
- progress_entry: W5-T1 Skill Registry 管道 Reviewer `accepted_with_gaps` — registry + CLI + tests 6+6 OK；selector/runbook/sync deferred（**非** `W5-T1-intake-decision-rules-v1`）。
- followup_suggestions: selector 只讀消費 registry 另票；runbook §CLI 由 Scribe/follow-up 補；雙向 sync 另票。

---

## O_NOTES

> **O 區**：Orchestrator 維護 run log 與戰報連結；Observe / Operate 計畫。

### Observability Plan

- approved 與 gov_cards 分離維護

### Rollout / Ops Notes

- approved 與 gov_cards 分離維護

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
| 2026-06-15 | orchestrator | B_REPORT 施工說明 + C_REPORT Reviewer checklist 預填；STATE → implementer in_progress | 本檔 |
| 2026-06-15 | reviewer | C_REPORT `needs_changes` — approved registry 管道未交付；交棒 implementer | 本檔 |
| 2026-06-15 | implementer | B_REPORT deliverables 回填 — registry + CLI + tests | 本檔 |
| 2026-06-15 | reviewer | C_REPORT `accepted_with_gaps` — AC-1～AC-6 達成；selector/runbook/sync deferred；交棒 scribe | 本檔 |
| 2026-06-15 | scribe | D_REPORT filled based on reviewer acceptance (with gaps) | 本檔 |
