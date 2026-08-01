# Multi-Agent Handoff Runbook v1

> **§0 上游 contract**：Phase 4 contract SSOT → [`docs/phase4-multi-agent-collaboration-contract-v1.md`](phase4-multi-agent-collaboration-contract-v1.md)（标准工作流 O→B→C→D、handoff 关口）；本 runbook 为操作层生命周期细则。

> **版本**：v1.0  
> **適用**：大唐三省六部 repo 內 Multi-Chat 四角色協作（Orchestrator / Implementer / Reviewer / Scribe）  
> **日期**：2026-06-10  
> **上游文件**：`docs/multi-agent-collaboration-spec-v1.md` · `04_Workflows/tickets/README.md`

---

## §1 適用範圍

本 runbook 定義 Multi-Chat 四角色協作時的標準 handoff 流程，包括：

- 票的完整生命週期（開票 → 實作 → 審查 → 收口 → 關票）
- 每個角色的啟動與退出動作
- 何時拆票、合票、結束 Wave
- 常見錯誤 handoff 範例與避免方式

適用對象：
- Orchestrator：開票、分派、收口
- Implementer/Reviewer/Scribe：執行各階段並回寫 REPORT
- 人類協調者：啟動 chat、監督流程

---

## §2 標準票生命週期

### 2.1 流程總覽

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   開票/FRAME  │ → │ Implementer │ → │   Reviewer   │ → │    Scribe    │ → │ Orchestrator │
│  (Orchestrator)│    │   (Step B)   │    │   (Step C)   │    │   (Step D)   │    │  (關票/Step O) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼                  ▼
   建 state.md        寫 B_REPORT        寫 C_REPORT        寫 D_REPORT       更新 STATE
   填 FRAME           實作+驗證          審查判定            整理+戰報          標 done
   初始化 STATE       直接寫檔           直接寫檔            直接寫檔           結案
```

### 2.2 開票 / FRAME（Orchestrator）

**人工動作**：
1. 開新 chat，貼 `_templates/orchestrator_instruction.template.md`
2. 指定 `ticket_id`（如 `W5-T1-intake-decision-rules`）

**Agent 動作**：
1. 複製 `ticket_state.template.md` → `04_Workflows/tickets/<ticket_id>_state.md`
2. 填寫 **FRAME** 區塊：
   - Title：簡潔標題
   - Goal：一句話目標
   - Scope：要做什麼（條列）
   - NonScope：明確不做什麼
   - AllowedPaths：可修改路徑（檔案層級）
   - BlockedPaths：禁止碰的路徑
   - Dependencies：前置票/阻塞項
   - AcceptanceCriteria：驗收條件（AC-1, AC-2...）
   - VerificationCommands：驗證命令與預期結果
3. 初始化 **STATE**：
   - `overall_status: draft`
   - `current_owner: orchestrator`
   - `next_action: Assign to Implementer`
   - `status_by_role`：全設 `pending`

**凍結原則**：FRAME 開票後即凍結，若需變更須 Orchestrator 更新並通知當前 owner。

**DoD**：
- [ ] state 檔存在
- [ ] FRAME 七要素齊全
- [ ] STATE 初始化完成

### 2.3 Implementer 實作（Step B）

**人工動作**：
1. 開新 chat，貼 `_templates/implementer_instruction.template.md`
2. 給定 state 路徑：`04_Workflows/tickets/<ticket_id>_state.md`

**Agent 動作**：
1. 讀取 FRAME（AllowedPaths 為硬邊界）與 STATE
2. 依 Scope 實作，遵守：
   - ENGINEERING_CONTRACT 四流派與 12-rule
   - Rule 3（最小觸及）：不改 BlockedPaths
   - Rule 6（路徑權威）：不硬編磁碟路徑
   - Rule 8（邊界尊重）：不改非本人 core
3. 執行 VerificationCommands，保留輸出
4. 填寫 **B_REPORT**（直接寫入 state 檔）：
   - `changed_files`：實際變更的檔案路徑（條列）
   - `artifacts`：新建模板、報告、截圖等產物
   - `verification`：跑過的命令與關鍵結果（`ok` / `count` / `exit 0`）
   - `behavior_notes`：行為變更或設計取捨（簡短）
   - `deferred_items`：刻意留到下一張票的項目

**DoD**：
- [ ] B_REPORT 五欄位填寫
- [ ] verification 含可重跑命令
- [ ] 無 BlockedPaths 誤觸

**常見錯誤**：
- ❌ 只在 chat 輸出 B_REPORT，不寫入 state 檔
- ❌ 改動超出 AllowedPaths（Reviewer 應攔截）
- ❌ 無 verification 即宣稱完成

### 2.4 Reviewer 驗收（Step C）

**人工動作**：
1. 開新 chat，貼 `_templates/reviewer_instruction.template.md`
2. 給定 state 路徑

**Agent 動作**：
1. 讀取 FRAME（AC 為驗收標準）、STATE、B_REPORT
2. 讀取變更檔案 diff（spot-check）
3. 對照 FRAME.AC 逐條檢查
4. 檢查四流派覆蓋、12-rule 遵守
5. 填寫 **C_REPORT**（直接寫入 state 檔）：
   - `conclusion`：四選一 — `accepted` / `accepted_with_gaps` / `needs_changes` / `rejected`
   - `blocking_issues`：必須修的問題（若 conclusion 為 needs_changes/rejected）
   - `checks_summary`：對照 AC 的檢查摘要（✅ / ⚠️ / ❌）
   - `risk_level`：`low` / `medium` / `high`
   - `suggestions`：非阻塞建議（`G1`, `G2`...）

**結論定義**：
| 結論 | 含義 | 下一步 |
|------|------|--------|
| `accepted` | 完全符合 AC，無保留 | 進 Step D |
| `accepted_with_gaps` | 符合核心 AC，有非阻塞遺漏 | 進 Step D，gaps 列於 suggestions |
| `needs_changes` | 不符部分 AC，需修改 | **回到 Step B** |
| `rejected` | 嚴重問題（如觸及 BlockedPaths）| Orchestrator 介入 |

**DoD**：
- [ ] C_REPORT 五欄位填寫
- [ ] conclusion 明確
- [ ] checks_summary 對照 AC

**常見錯誤**：
- ❌ 幫 Implementer 修 code 以「幫忙過關」
- ❌ 無 checks_summary 僅寫「看起來 OK」
- ❌ 發現 BlockedPaths 誤觸但未標 `rejected`

### 2.5 Scribe 收口（Step D）

**人工動作**：
1. 開新 chat，貼 `_templates/scribe_instruction.template.md`
2. 給定 state 路徑

**Agent 動作**：
1. 讀取 FRAME、STATE、B_REPORT、C_REPORT
2. 確認 Reviewer conclusion ∈ {`accepted`, `accepted_with_gaps`}
3. 填寫 **D_REPORT**（直接寫入 state 檔）：
   - `docs_updates`：建議新增/更新的文檔路徑與要點
   - `progress_entry`：建議寫入 Progress 末尾的摘要（1–3 句）
   - `followup_suggestions`：後續票或尚書省待裁決事項
4. 執行 docs_updates（若為本票 scope）

**DoD**：
- [ ] D_REPORT 三欄位填寫
- [ ] progress_entry 符合 OPS_CYCLE.md 格式
- [ ] 未重排 Progress 既有段落

**常見錯誤**：
- ❌ 發現實作問題但自行修補（應回報 Orchestrator）
- ❌ 未經確認即宣稱票項封存完成

### 2.6 Orchestrator 關票（Step O）

**人工動作**：
1. 開 Orchestrator chat（或續原 chat）
2. 指示「讀取 state，更新 STATE，標 done」

**Agent 動作**：
1. 讀取 B/C/D_REPORT
2. 更新 **STATE**：
   - `overall_status: done`
   - `current_owner: orchestrator`
   - `next_action: 無 / 開下一張票`
   - `status_by_role`：B/C/D 標 `done`
   - `last_updated`：日期 + 角色
3. 對尚書省輸出結構化回報：
   - 變更摘要
   - 風險與 gaps
   - 後續票建議

**DoD**：
- [ ] STATE 更新完成
- [ ] overall_status: done
- [ ] 關票回報輸出

---

## §3 何時拆票 / 合票 / 結束 Wave

### 3.1 拆票（開新票）時機

| 情境 | 拆票方式 | 範例 |
|------|----------|------|
| Scope 跨多領域 | 按領域拆 | W3-TL-T1 (Catalog) / W3-TL-T2 (Selector) / W3-TL-T3 (Executor) |
| 有獨立驗收標準 | 按驗收點拆 | W4-T1 (glue) / W4-T2 (runner) / W4-T3 (CLI path) / W4-T4 (CI hooks) |
| 涉及不同角色時間 | 按時間序拆 | W1-T1 (OPS 自检) / W1-T1B (治理收斂) |
| 有明確依賴關係 | 先後拆 | W4-T1 (glue) → W4-T2 (runner consumes glue) |

**拆票原則**：
- 每票有獨立 FRAME、獨立 AC、可獨立驗收
- 依賴關係寫入 Dependencies，不循環依賴

### 3.2 合票時機

| 情境 | 合票方式 | 注意 |
|------|----------|------|
| 多票發現為同一 root cause | 合為一張，更新 FRAME | 保留原票號於 O_NOTES |
| 票 A 發現無法獨立交付（須 B 才能完成）| A 併入 B，或開新票 AB | 更新 Dependencies |

**禁止合票**：
- 已進入 Step C/D 的票不建議合併（已產生 B/C/D_REPORT）
- 跨 Wave 的票不建議合併（Wave 為主題批次）

### 3.3 結束 Wave

**Wave 定義**：主題批次（如 Wave 1 治理+可觀測、Wave 2 Intake/Routing/Eval）+ Execution Plan + 票隊列。

**結束 Wave 條件**：
1. Wave 內全部票 `overall_status: done`
2. Execution Plan 定義的驗收標準達成
3. Orchestrator 於 Progress 末尾追加 Wave 結束條目
4. 更新 `docs/WAVE_PROGRESS_DASHBOARD.md`

**Wave 結束後**：
- 可開新 Wave（須尚書省裁決主題與範圍）
- 可進入「維護模式」（僅修復 bugs，不新增 feature）

---

## §4 常見錯誤 Handoff 範例與避免方式

### 4.1 錯誤：Implementer 不寫 B_REPORT 或僅在 chat 輸出

**錯誤場景**：
- Implementer 完成實作，只在 chat 說「我做完了」，未回寫 state
- 人工需手動複製 chat 內容貼回 state

**避免方式**：
- Implementer instruction 模板明確要求「直接讀寫 state 檔，只寫 B_REPORT 區塊」
- Orchestrator 開票時強調「不回寫 state = 未完工」

### 4.2 錯誤：Reviewer 幫忙修 code

**錯誤場景**：
- Reviewer 發現小錯，心想「我順手修了更快」，直接 commit fix
- 混淆 Reviewer（審查者）與 Implementer（實作者）角色

**避免方式**：
- Reviewer 權限：唯讀不寫任何 code/docs
- 發現問題 → C_REPORT `needs_changes` + 具體修改項 → 回到 B

### 4.3 錯誤：Scribe 發現問題自行修補

**錯誤場景**：
- Scribe 整理 docs 時發現 code 有 bug，心想「我順手修了省事」
- 結果未經 Reviewer 審查，可能引入新問題

**避免方式**：
- Scribe 職責：整理、術語統一、戰報；**不**修 code
- 發現問題 → 回報 Orchestrator → Orchestrator 決定是否退回 B

### 4.4 錯誤：跨區塊寫入

**錯誤場景**：
- Implementer 發現 FRAME 有誤，順手修了 FRAME.Scope
- Reviewer 想加速流程，直接更新 STATE.current_owner

**避免方式**：
- 嚴格遵守「區塊讀寫權限表」（見 §4.4）
- FRAME/STATE 僅 Orchestrator 可寫
- 發現 FRAME 問題 → chat 回報 → Orchestrator 評估是否更新

### 4.5 錯誤：無結論或模糊結論

**錯誤場景**：
- C_REPORT conclusion: 「大致 OK，有些小問題」
- 無法判斷該進 D 還是回 B

**避免方式**：
- 強制四選一：`accepted` / `accepted_with_gaps` / `needs_changes` / `rejected`
- `accepted_with_gaps` 須列 gaps 於 suggestions（G1, G2...）
- `needs_changes` 須列具體修改項

### 4.6 錯誤：進度條目遺漏或錯置

**錯誤場景**：
- Scribe 忘記寫 progress_entry
- 人工把 progress_entry 插入 Progress 中段（破壞 append-only）

**避免方式**：
- D_REPORT 必填 progress_entry
- Scribe 權限：僅可 **末尾追加**，不可重排既有段落
- Orchestrator 關票前檢查 Progress 末尾是否新增條目

---

## §5 快速參考卡

### 5.1 角色啟動指令

| 角色 | 人工貼給 Agent |
|------|----------------|
| Orchestrator | `Ticket: <ticket_id>` + orchestrator_instruction.template.md |
| Implementer | `State: 04_Workflows/tickets/<ticket_id>_state.md` + implementer_instruction.template.md |
| Reviewer | `State: 04_Workflows/tickets/<ticket_id>_state.md` + reviewer_instruction.template.md |
| Scribe | `State: 04_Workflows/tickets/<ticket_id>_state.md` + scribe_instruction.template.md |

### 5.2 區塊權限速查

| 區塊 | 誰能寫 | 誰能讀 |
|------|--------|--------|
| FRAME | Orchestrator | 全角色 |
| STATE | Orchestrator | 全角色 |
| B_REPORT | Implementer | 全角色 |
| C_REPORT | Reviewer | 全角色 |
| D_REPORT | Scribe | 全角色 |

### 5.3 Conclusion 決策樹

```
審查完成？
  ├── 完全符合 AC ──→ accepted ──→ 進 D
  ├── 核心符合，有小遺漏 ──→ accepted_with_gaps ──→ 進 D（記 gaps）
  ├── 不符部分 AC ──→ needs_changes ──→ 回 B（列修改項）
  └── 嚴重問題（BlockedPaths/架構錯誤）─→ rejected ──→ Orchestrator 介入
```

---

## §6 參考索引

| 文件 | 用途 |
|------|------|
| `docs/multi-agent-collaboration-spec-v1.md` | 角色詳細規格 |
| `04_Workflows/tickets/README.md` | 票機制總覽 |
| `.cursor/rules/multi_chat_roles.mdc` | 角色邊界完整版 |
| `04_Workflows/tickets/_templates/*.template.md` | 各角色 instruction 模板 |
| `AGENTS.md` | 接戰／封存口令 |
| `ENGINEERING_CONTRACT.md` | 工程合約四流派/12-rule |

---

*本檔為 W5-T0 · Multi-Agent Collaboration Docs 交付物 · 2026-06-10*
