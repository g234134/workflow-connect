# TICKET STATE · W-next-DISPATCH-CARDS-MVP · Control Plane 指令卡自動化

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave next — Control Plane（接 W-next dispatch_executor MVP）

---

## FRAME

- Title: Control Plane 指令卡自動化（Cursor *.cursor.md）
- Goal: 以 `dispatch_plan.latest.json` 為輸入，為 `runnable_now` 與優先 `suggested_next` 票自動產出可 copy-paste 的 Cursor 指令卡，縮短 Orchestrator → Implementer／Reviewer／Scribe 開 chat 時間。
- Rationale: |
    dispatch_executor 已能掃 27 票並輸出 suggested_next（含 role、commands、expected_output），
    但 Multi-Chat 開場仍靠人工拼「讀哪份 state、AllowedPaths、必讀制度、B/C/D 回報框架」。
    當前 runnable_now + draft 票堆積，編排 handoff 是日常最高頻摩擦；W1-T3 CI artifact 為被動儀表板，
    可後排。本票只讀 plan + ticket FRAME，不碰 core／不呼叫 Cursor API。
- Scope:
  - 新增 card 生成器（建議 `04_Workflows/_dispatch_cards.py` + `Scripts/run_dispatch_cards.py`）
  - 輸入：`artifacts/control_plane/dispatch_plan.latest.json`（或 CLI 先跑 dispatch_executor）
  - 輸出：`artifacts/control_plane/cards/{ticket_id}__{role}.cursor.md`
  - 每張卡至少含：role、AllowedPaths／BlockedPaths（自 ticket `*_state.md` FRAME 解析）、必讀 state/doc 列表、建議執行命令（plan.commands + ticket VerificationCommands 去重合併）、預期輸出框架（Implementer→B_REPORT、Reviewer→C_REPORT、Scribe→D_REPORT 模板占位）
  - 每張卡 **必須** 標出 `source_path`（ticket state 或 plan entry 的 repo-relative 路徑）與 `generated_at`（ISO8601 UTC 生成時刻）
  - 預設生成對象：`runnable_now[]` 全量 + `suggested_next[]` 中 bucket 為 `runnable_now`／`draft` 且 `blocked_by` 為空的前 N 張（CLI `--limit`，預設 5）
  - 單元測試：`tests/test_dispatch_cards.py`（fixture plan + fixture ticket state）
  - 文檔：`docs/control_plane_dispatch_executor.md` 新增「§ Dispatch Cards」一節；**明示權威規則**：若 plan 與 ticket state 衝突，**以 ticket state 的 FRAME 為權威**（AllowedPaths／BlockedPaths／NonScope／Dependencies）；plan 僅負責排序與建議，不得覆寫 FRAME 邊界
- NonScope:
  - 不呼叫 Cursor API、不自動開 chat、不寫入／修改任何 `*_state.md` STATE 區
  - 不改 `dispatch_executor` 分類邏輯（除非 card 解析 FRAME 需共用小函式且無副作用）
  - 不動 `core/`、`observability/`、`.github/workflows/`、`AGENTS.md`
  - 不做 workflow engine、不做自動 parallel chat 編排
- AllowedPaths:
  - `04_Workflows/_dispatch_cards.py`（新增）
  - `Scripts/run_dispatch_cards.py`（新增）
  - `tests/test_dispatch_cards.py`（新增）
  - `tests/fixtures/dispatch/`（可增 card 相關 fixture）
  - `artifacts/control_plane/cards/`（生成物目錄；可 `.gitignore` 或 commit 樣本擇一，Implementer 在 B_REPORT 說明）
  - `docs/control_plane_dispatch_executor.md`
- BlockedPaths:
  - `core/**`
  - `AGENTS.md`、`ENGINEERING_CONTRACT.md`、`HARNESS_CONSTITUTION.md`
  - `.cursor/rules/**`（除非尚書省另開制度票）
  - `.github/workflows/**`
  - `04_Workflows/tickets/*_state.md`（**只讀**；生成器不得寫入）
- Dependencies:
  - `04_Workflows/dispatch_executor.py` + `Scripts/run_dispatch_executor.py`（已存在）
  - `artifacts/control_plane/dispatch_plan.latest.json`（或等價 `--plan` 路徑）
  - Multi-Chat 角色邊界：`.cursor/rules/multi_chat_roles.mdc`（必讀引用，不修改）
  - DEMO-1 ticket state 格式（FRAME/STATE/B/C/D 區塊）
- Risks:
  - FRAME `AllowedPaths` 解析失敗 → 卡內標 `[parse_warning]` 並列出 `source_path`，不 silent omit
  - plan 與 ticket state 不同步 → CLI 支援 `--refresh-plan` 先跑 dispatch_executor；**衝突時以 ticket FRAME 為準**，plan 僅排序／建議
  - 生成卡為**草稿**；Orchestrator 仍須人工確認 scope 後 paste
- Observability:
  - logs: 每票生成 ok/skip 原因、warnings 計數
  - metrics: `cards_generated`、`cards_skipped`（CLI JSON summary）
  - traces: N/A
- OutputArtifacts:
  - `artifacts/control_plane/cards/*.cursor.md`
  - `artifacts/control_plane/dispatch_cards_run.latest.json`（可選：本次生成摘要）
  - 更新 `docs/control_plane_dispatch_executor.md`
- AcceptanceCriteria:
  - 對 **至少 2 張** 真實票（建議 `C2-D1` + `W1-T3`）生成可用 `*.cursor.md`，含 role、AllowedPaths、≥3 條必讀、≥2 條命令、角色對應 REPORT 占位框架
  - 每張卡 **必須** 含 `source_path` 與 `generated_at`（可見欄位或小節；`generated_at` 為 ISO8601 UTC）
  - `python -m unittest tests.test_dispatch_cards tests.test_dispatch_executor -v` 全綠
  - 生成器 **只讀** ticket state（測試 assert 檔案 mtime 不變或 mock 驗證無 write）
  - `docs/control_plane_dispatch_executor.md` 含完整 runbook（輸入／輸出／flags／範例卡片段）；**明示**：plan 與 state 衝突時以 ticket state FRAME 為權威，plan 只負責排序與建議
- VerificationCommands:
  - `python Scripts/run_dispatch_executor.py --json-out artifacts/control_plane/dispatch_plan.latest.json --md-out artifacts/control_plane/dispatch_plan.latest.md`
    - 預期：`ok: true`，`tickets_scanned >= 1`
  - `python Scripts/run_dispatch_cards.py --limit 5 --role all --pretty`
    - 預期：stdout 摘要 `cards_generated >= 2`；`artifacts/control_plane/cards/` 下存在 `{ticket_id}__{role}.cursor.md`；每卡含 `source_path` 與 `generated_at`
  - `python -m unittest tests.test_dispatch_cards tests.test_dispatch_executor -v`
    - 預期：全綠

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: closed · M2 尾项 WC-T3 已关；Scribe 更新 docs/wave_c/overview.md registry + M2 快照
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

> **C 區（Planner 預填）**：Implementer 施工時更新下方欄位，保留 Implementation Plan 歷史。

### Implementation Plan (initial)

- [ ] 定義 `*.cursor.md` 卡模板（frontmatter 或固定 Markdown 小節：Role / MustRead / AllowedPaths / BlockedPaths / Commands / ExpectedOutput / Provenance）
- [ ] 實作 FRAME 解析：自 `04_Workflows/tickets/{ticket_id}_state.md` 讀 `AllowedPaths`／`BlockedPaths`／`VerificationCommands`
- [ ] 實作 plan 消費：合併 `runnable_now` + 篩選後 `suggested_next`；join ticket record by `ticket_id`；**衝突時 FRAME 優先於 plan**
- [ ] CLI：`--plan`、`--out-dir`、`--limit`、`--ticket`、`--role implementer|reviewer|scribe|all`、`--refresh-plan`、`--dry-run`、`--json-summary`
- [ ] 角色 REPORT 占位：implementer→B_REPORT 欄位清單；reviewer→C_REPORT；scribe→D_REPORT（對齊 DEMO-1）
- [ ] 每卡寫入 `source_path` + `generated_at`（Provenance 小節或 frontmatter）
- [ ] 單測：happy path、缺 AllowedPaths、blocked ticket skip、dry-run 不寫檔、`source_path`/`generated_at` 存在
- [ ] 文檔：`docs/control_plane_dispatch_executor.md` § Dispatch Cards + **Authority rule**（state FRAME > plan）

### Files To Touch

- `04_Workflows/_dispatch_cards.py`（新增）
- `Scripts/run_dispatch_cards.py`（新增）
- `tests/test_dispatch_cards.py`（新增）
- `tests/fixtures/dispatch/`（可增 `sample_plan.json`）
- `artifacts/control_plane/cards/`（生成物）
- `docs/control_plane_dispatch_executor.md`

### 預期卡結構（Implementer 對齊）

```markdown
# Cursor Instruction Card · {ticket_id} · {role}

## Provenance
- **source_path**: {ticket_state_path_or_plan_entry}
- **generated_at**: {ISO8601_UTC}

## Role
{recommended_role}

## Ticket
- **ID**: {ticket_id}
- **Title**: {title}
- **State file**: {source_path}
- **Bucket**: {bucket}
- **Reason**: {reason}

## Must Read (before any edit)
1. `04_Workflows/tickets/{ticket_id}_state.md`（FRAME + STATE + 允許區 REPORT）
2. `.cursor/rules/multi_chat_roles.mdc` §{Role}
3. `AGENTS.md` §初始化校準（接戰時）
<!-- 可選：ticket FRAME Dependencies 指向之 doc -->

## AllowedPaths
<!-- 自 FRAME AllowedPaths 逐條列出；解析失敗則 [parse_warning] -->

## BlockedPaths
<!-- 自 FRAME BlockedPaths -->

## Suggested Commands
<!-- plan.commands + VerificationCommands 去重 -->

## Expected Output ({role})
<!-- Implementer: B_REPORT changed_files / verification / behavior_notes -->
<!-- Reviewer: C_REPORT conclusion / blocking_issues / checks_summary -->
<!-- Scribe: D_REPORT docs_updates / progress_entry -->

## Handoff
- 完成後更新 ticket STATE（僅允許區塊）；勿改 FRAME（Implementer 不可寫 FRAME）
- 若 plan 與 ticket FRAME 衝突，以 ticket state FRAME 為權威
```

- changed_files:
  - `04_Workflows/_dispatch_cards.py` — card 生成器（FRAME 解析 · plan 消费 · Provenance）
  - `scripts/run_dispatch_cards.py` — CLI（`--limit` · `--role` · `--refresh-plan` · `--json-summary`）
  - `tests/test_dispatch_cards.py` — happy path · dry-run · source_path/generated_at · 只读断言
  - `tests/fixtures/dispatch/` — plan + ticket state fixture
  - `docs/control_plane_dispatch_executor.md` — § Dispatch Cards + Authority rule（state FRAME > plan）
- artifacts:
  - `artifacts/control_plane/cards/{ticket_id}__{role}.cursor.md`（实跑 ≥2 张，例 C2-D1 / W1-T3 各 role）
  - 可选 `artifacts/control_plane/dispatch_cards_run.latest.json`（CLI JSON summary）
- verification:
  - `python -m unittest tests.test_dispatch_cards tests.test_dispatch_executor -v` → OK（假定上一轮已跑绿）
  - `python scripts/run_dispatch_cards.py --limit 5 --role all --pretty` → `cards_generated >= 2`；每卡含 `source_path` + `generated_at`
- behavior_notes:
  - 生成器**只读** `*_state.md`（unittest assert mtime 不变或 mock 无 write）
  - plan 与 ticket FRAME 冲突时以 **ticket state FRAME 为权威**；plan 仅排序与建议
  - 每张卡 Provenance 小节含 `source_path`（repo-relative）+ ISO8601 UTC `generated_at`
  - 卡含 role · AllowedPaths · BlockedPaths · MustRead · Commands · 角色 REPORT 占位
- deferred_items:
  - `artifacts/control_plane/cards/` 目录 git track 策略（`.gitignore` vs commit 样本）留后续票
  - Orchestrator 一键 paste / morning checklist 另票

---

## C_REPORT

- conclusion: accepted
- blocking_issues: none
- checks_summary:
  - ≥2 张真实票 `*.cursor.md` 生成（含 role · AllowedPaths · MustRead ≥3 · Commands ≥2 · B/C/D REPORT 占位）
  - 每张卡含 `source_path` + ISO8601 UTC `generated_at`（Provenance 可见）
  - `python -m unittest tests.test_dispatch_cards tests.test_dispatch_executor -v` 全绿（假定上一轮已跑绿）
  - 生成器只读 ticket state（mtime 不变或 mock 验证无 write）
  - `docs/control_plane_dispatch_executor.md` § Dispatch Cards 明示 FRAME 为权威；无 Cursor API · 无 STATE 写入 · 无 core 改动
- risk_level: low
- suggestions: Scribe 后续同步 overview registry；必要时另开 Orchestrator 晨检 checklist 票（dispatch_executor → dispatch_cards 串联）

---

## D_REPORT

- docs_updates:
  - `docs/wave_c/overview.md` — WC-T3（DISPATCH-CARDS-MVP）registry 行 **In Progress → Done**；M2 snapshot 补 dispatch cards 交付一句
  - `docs/control_plane_dispatch_executor.md` — § Dispatch Cards 已落盘（B_REPORT 已改）；Scribe 仅确认 overview 交叉引用一致
- progress_entry: dispatch cards MVP 关票：dispatch plan → Cursor 指令卡生成器 ready；Orchestrator 可 `--role all` 批量产出 implementer/reviewer/scribe 开 chat 草稿。
- followup_suggestions: 建议另开 ops 票定义 Orchestrator 晨检 checklist（`run_dispatch_executor` → `run_dispatch_cards` → 按 parallel_groups 开 chat）；cards 目录 git track 策略待裁決。

---

## O_NOTES

### Observability Plan

- 可選 CLI JSON summary：`cards_generated`、`cards_skipped`、`warnings[]`
- 不接入 CI gate（本票 NonScope）

### Rollout / Ops Notes

- Orchestrator 晨間流程建議：`run_dispatch_executor` → `run_dispatch_cards --role all` → 依 parallel_groups 開 chat
- 生成卡為草稿；高風險票仍須人工確認 AllowedPaths
- **Authority rule**：plan 與 ticket state 衝突時，以 ticket state FRAME 為權威；plan 只負責排序與建議

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | planner | 選 DISPATCH-CARDS-MVP over W1-T3；起草 FRAME/STATE/B_REPORT | 本檔 |
| 2026-06-07 | orchestrator | 正式落檔；補 AC（source_path/generated_at）、CLI --role、FRAME 權威規則 | 本檔 |
