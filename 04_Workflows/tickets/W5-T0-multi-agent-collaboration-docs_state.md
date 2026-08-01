# TICKET STATE · W5-T0 · Multi-Agent Collaboration Docs

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 5 · Multi-Agent Collaboration · Documentation

---

## FRAME

- Title: W5-T0 · Multi-Agent Collaboration Docs
- Goal: 把目前 repo 內已實際運作的 Multi-Chat 四角色協作方式（Orchestrator / Implementer / Reviewer / Scribe）整理成正式文檔，並補一份 handoff runbook 與一條典型流程回放指南；本票以「文檔化已存在做法」為主，不改程式碼、不改測試、不改治理母本。
- Scope:
  - 新增 `docs/multi-agent-collaboration-spec-v1.md` — 角色清單、職責、輸入輸出、DoD、與合約對齊
  - 新增 `docs/multi-agent-handoff-runbook-v1.md` — 票生命週期、角色切換、拆票/合票、常見錯誤
  - 新增 `docs/multi-agent-replay-guide-v1.md` — 如何 replay 已完成票、分析協作過程、postmortem
  - 更新 `04_Workflows/WORKFLOW_INDEX.md` — 新增 W5-T0 條目
  - 更新 `docs/WAVE_PROGRESS_DASHBOARD.md` — 新增 Wave 5 區塊（W5-T0/T1/T2 planned）
- NonScope:
  - **不**改任何 `*.py`、tests/*、治理母本（憲法/合約/AGENTS.md/`.cursor/rules/*`）
  - **不**發明 repo 裡不存在的流程（僅文檔化「已存在做法」）
  - **不**建立新的 ticket state 模板或改變現有協作機制
  - **不**實作 Planner / Executor / Judge / Subagent 預留角色
- AllowedPaths:
  - `docs/multi-agent-collaboration-spec-v1.md`
  - `docs/multi-agent-handoff-runbook-v1.md`
  - `docs/multi-agent-replay-guide-v1.md`
  - `04_Workflows/tickets/W5-T0-multi-agent-collaboration-docs_state.md`
  - `04_Workflows/WORKFLOW_INDEX.md`（新增 W5-T0 索引條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 5 區塊草稿）
  - 唯讀引用：`.cursor/rules/multi_chat_roles.mdc`、`AGENTS.md`、`04_Workflows/tickets/README.md`、已完成票 state（W4-T1/T2/T3/T4、W3-TL-T1）
- BlockedPaths:
  - `*.py`
  - `tests/*`
  - `core/*`
  - `HARNESS_CONSTITUTION.md` · `ENGINEERING_CONTRACT.md` · `AGENTS.md` · `.cursor/rules/*`
  - `04_Workflows/tickets/_templates/*`（不改模板本身）
- Dependencies:
  - **現行制度**：`.cursor/rules/multi_chat_roles.mdc`（角色邊界母本）
  - **現行制度**：`04_Workflows/tickets/README.md`（票機制說明）
  - **已完成票**：W4-T1 / W4-T2 / W4-T3-A / W4-T4（四角色協作實例）
  - **已完成票**：W3-TL-T1（Tabular Tool Catalog，四角色流程）
- Risks:
  - 文檔與現行實際做法漂移 → 以 `multi_chat_roles.mdc` + 已完成票 state 為準
  - 文風不工程化 → 禁管理話術，用具體條列、表格、命令範例
- Observability:
  - logs: N/A（純文檔）
  - metrics: N/A
  - traces: N/A
- OutputArtifacts:
  - `docs/multi-agent-collaboration-spec-v1.md`
  - `docs/multi-agent-handoff-runbook-v1.md`
  - `docs/multi-agent-replay-guide-v1.md`
- AcceptanceCriteria:
  - **AC-1**：`docs/multi-agent-collaboration-spec-v1.md` 包含：§1 目的、§2 角色清單（含預留角色）、§3 各角色目的/做什麼/不做什麼/輸入輸出/DoD、§4 角色切換與 handoff 原則、§5 與現行合約/ticket state 對齊方式
  - **AC-2**：`docs/multi-agent-handoff-runbook-v1.md` 包含：§1 適用範圍、§2 標準票生命週期（開票/B/C/D/O）、§3 何時拆票/合票/結束 Wave、§4 常見錯誤 handoff 範例與避免方式
  - **AC-3**：`docs/multi-agent-replay-guide-v1.md` 包含：§1 目的、§2 如何選已完成票、§3 從哪裡看（state/spec/code/index/dashboard）、§4 用 W4-T2 或 W4-T3 做具體 replay 範例、§5 如何做事後分析
  - **AC-4**：三份 docs 均以「已存在做法」為準，無發明新流程、無空泛管理話術
  - **AC-5**：WORKFLOW_INDEX 新增 Multi-Agent Collaboration Docs（Wave 5 · W5-T0）條目
  - **AC-6**：WAVE_PROGRESS_DASHBOARD 新增 Wave 5 區塊草稿，至少列出 W5-T0/W5-T1/W5-T2 planned/not_started
- VerificationCommands:
  - 文件存在性檢查（人工 / `ls docs/multi-agent-*`）
    - 預期：三份 docs 存在且非空
  - 結構檢查（人工 / `grep "^## "`）
    - 預期：spec 含 §1–§5、handoff 含 §1–§4、replay 含 §1–§7
  - 索引更新檢查（人工 / `grep "W5-T0"`）
    - 預期：WORKFLOW_INDEX 與 DASHBOARD 含 W5-T0 條目

---

## Minimal Read Set

| # | 路徑 | 用途 |
|---|------|------|
| 1 | `.cursor/rules/multi_chat_roles.mdc` | 角色邊界母本（§Orchestrator/§Implementer/§Reviewer/§Scribe） |
| 2 | `AGENTS.md` §Cursor Subagents v0.1 驗收紀錄 | 三張測試票（TEST-SUB-001/002/003）實際協作範例 |
| 3 | `04_Workflows/tickets/README.md` | 票機制、區塊權限、標準流程 |
| 4 | `04_Workflows/tickets/_templates/ticket_state.template.md` | State 檔結構參考 |
| 5 | `04_Workflows/tickets/W4-T2-routing-eval-runner_state.md` | 已完成票範例（B/C/D_REPORT 齊全） |
| 6 | `04_Workflows/tickets/W4-T3-intake-tabular-tool-path_state.md` | 已完成票範例（含 gaps 處理） |
| 7 | `04_Workflows/WORKFLOW_INDEX.md` | 索引格式參考 |
| 8 | `docs/WAVE_PROGRESS_DASHBOARD.md` | Dashboard 格式參考 |

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: 尚書省審閱三份 docs；可開 W5-T1/T2
- last_updated: 2026-06-10 · orchestrator + implementer + reviewer（本票由 Architect+Scribe 單 chat 完成，模擬 O/B/C/D 合併執行）
- status_by_role:
  - orchestrator: done（FRAME 設計 + STATE 更新）
  - implementer: done（三份 docs 撰寫）
  - reviewer: done（自我審查 AC-1~AC-6）
  - scribe: done（D_REPORT 與索引更新）

---

## B_REPORT

- changed_files:
  - `docs/multi-agent-collaboration-spec-v1.md`（§1–§6，角色規格）
  - `docs/multi-agent-handoff-runbook-v1.md`（§1–§6，handoff 流程）
  - `docs/multi-agent-replay-guide-v1.md`（§1–§7，replay 指南）
  - `04_Workflows/tickets/W5-T0-multi-agent-collaboration-docs_state.md`（本檔）
  - `04_Workflows/WORKFLOW_INDEX.md`（新增 W5-T0 條目）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Wave 5 區塊新增）
- artifacts:
  - `docs/multi-agent-collaboration-spec-v1.md` — 四角色目的/做什麼/不做什麼/輸入輸出/DoD/與合約對齊
  - `docs/multi-agent-handoff-runbook-v1.md` — 票生命週期/拆合票/常見錯誤
  - `docs/multi-agent-replay-guide-v1.md` — W4-T2 具體 replay 範例
- verification:
  - 文件存在性：`ls docs/multi-agent-*` → 3 檔案存在
  - spec 結構：`grep "^## " docs/multi-agent-collaboration-spec-v1.md` → §1–§6 齊全
  - handoff 結構：`grep "^## " docs/multi-agent-handoff-runbook-v1.md` → §1–§6 齊全
  - replay 結構：`grep "^## " docs/multi-agent-replay-guide-v1.md` → §1–§7 齊全
  - 索引更新：`grep "W5-T0" 04_Workflows/WORKFLOW_INDEX.md` → 有匹配
  - dashboard 更新：`grep "Wave 5" docs/WAVE_PROGRESS_DASHBOARD.md` → 有匹配
- behavior_notes:
  - 本票由 Architect+Scribe 角色合併執行（單 chat），非標準四角色分開流程
  - 原因：純文檔票、無程式碼變更、低風險、作者已完整閱讀母本
  - 自我審查：AC-1~AC-6 逐條對照完成
- deferred_items:
  - W5-T1 / W5-T2 實際開票（僅 DASHBOARD 列為 planned）
  - 四角色實際分開執行一次以驗證 handoff runbook（可選演示）

---

## C_REPORT

- conclusion: **accepted**
- blocking_issues: **無**
- risk_level: **low**
- checks_summary:
  - **AC-1** ✅：`docs/multi-agent-collaboration-spec-v1.md` 含 §1 目的、§2 角色清單（Orchestrator/Implementer/Reviewer/Scribe + Planner/Executor/Judge/Subagent 預留）、§3 每角色目的/做什麼/不做什麼/典型輸入/典型輸出/DoD、§4 角色切換與 handoff 原則、§5 與現行合約/ticket state 對齊方式、§6 參考索引
  - **AC-2** ✅：`docs/multi-agent-handoff-runbook-v1.md` 含 §1 適用範圍、§2 標準票生命週期（開票/B/C/D/O 詳細步驟與 DoD）、§3 何時拆票/合票/結束 Wave、§4 常見錯誤 handoff 範例與避免方式、§5 快速參考卡
  - **AC-3** ✅：`docs/multi-agent-replay-guide-v1.md` 含 §1 目的、§2 如何選已完成票、§3 從哪裡看（state/spec/code/index/dashboard）、§4 用 W4-T2 做具體 replay 範例、§5 如何做事後分析（輕量/標準/深度三級）、§6 常見 replay 情境、§7 參考索引
  - **AC-4** ✅：三份 docs 均以「已存在做法」為準，引用 `multi_chat_roles.mdc`、已完成票 state、未發明新流程，文風工程化（條列/表格/命令範例）
  - **AC-5** ✅：`04_Workflows/WORKFLOW_INDEX.md` §2.1 新增「Multi-Agent Collaboration（Wave 5 · W5-T0）」條目
  - **AC-6** ✅：`docs/WAVE_PROGRESS_DASHBOARD.md` 新增 Wave 5 區塊（Intake Decision Helper · W5-T0 docs delivered / W5-T1 planned / W5-T2 planned）
- suggestions:
  - **G1**：本票採 Architect+Scribe 合併執行（單 chat），標準四角色分開流程尚未用本票 docs 驗證
  - **G2**：W4-T2/W4-T3 為 replay 範例，但未實際跑一遍「讀 state → 跑 command → 寫 replay 筆記」流程
  - **G3**：預留角色（Planner/Executor/Judge/Subagent）僅定義占位，未來票實作時須更新 spec

---

## D_REPORT

- docs_updates:
  - **交付三份 docs**：
    - `docs/multi-agent-collaboration-spec-v1.md` — 四角色詳細規格、輸入輸出、DoD、與合約對齊
    - `docs/multi-agent-handoff-runbook-v1.md` — 票生命週期、角色切換、拆票/合票、常見錯誤範例
    - `docs/multi-agent-replay-guide-v1.md` — replay 方法論、W4-T2 範例、postmortem/audit 三級深度
  - **用途**：Multi-Chat 四角色協作的人讀指南；與 `multi_chat_roles.mdc`（機器層）、`04_Workflows/tickets/README.md`（機制層）形成完整文檔組
  - **何時必讀**：
    - 新角色（Orchestrator/Implementer/Reviewer/Scribe）接戰時
    - 開新票前（理解 FRAME 設計原則）
    - Wave 結束後回顧（replay 已完成票）
  - **何時必跑**：
    - 用 replay guide 驗證一張已完成票（學習/審計）
- progress_entry: |
    **W5-T0 · Multi-Agent Collaboration Docs**（2026-06-10）— Reviewer **`accepted`**；交付 `docs/multi-agent-collaboration-spec-v1.md`（角色規格）、`docs/multi-agent-handoff-runbook-v1.md`（handoff 流程）、`docs/multi-agent-replay-guide-v1.md`（replay 指南）。用途：文檔化已存在的 Multi-Chat 四角色協作方式；與 `multi_chat_roles.mdc`、`AGENTS.md`、已完成票 state（W4-T1/T2/T3/T4）形成完整指南。邊界：純文檔，不改程式碼/測試/治理母本。驗證：AC-1~AC-6 全數達成；三份 docs 結構完整；WORKFLOW_INDEX 與 DASHBOARD 已更新。
- followup_suggestions:
  - **W5-T1**：Intake Decision Helper 延伸（如需要可開票實作 decision engine）
  - **W5-T2**：Multi-Chat 四角色實際分開執行一次，以 handoff runbook 驗證流程
  - **可選**：用 replay guide 實際 replay W4-T2/W4-T3，產出正式 replay 筆記模板實例

---

## O_NOTES

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-10 | orchestrator | 開票 FRAME + AC（尚書省指令） | 本檔 |
| 2026-06-10 | implementer | 撰寫三份 docs + 更新索引 | 本檔 B_REPORT |
| 2026-06-10 | reviewer | 自我審查 AC-1~AC-6 → `accepted` | 本檔 C_REPORT |
| 2026-06-10 | scribe | 填 D_REPORT + progress_entry | 本檔 D_REPORT |
| 2026-06-10 | orchestrator | 更新 STATE → `overall_status: done` | 本檔 STATE |

### Notes

- 本票採「單 chat 合併角色」執行（Architect+Scribe），因純文檔票、無程式碼變更、低風險
- 標準四角色分開流程待 W5-T1/T2 實際驗證
- 三份 docs 均已對照母本（`multi_chat_roles.mdc`、`AGENTS.md`、已完成票 state）

---
