# Cursor Subagents v0.1 — 主 Agent Dispatch 準則

> **版本**：v0.1（最小可用制度）  
> **位置**：`.cursor/agents/`（Cursor 正式 subagent 目錄）  
> **對照**：`AGENTS.md` 接戰、`04_Workflows/TASK_ROUTING.md` HQ 路由、`ENGINEERING_CONTRACT.md` 四流派

---

## 1. 角色一覽

| Subagent | 檔案 | 對齊 HQ 角色 | readonly |
|----------|------|--------------|----------|
| coordinator | `coordinator.md` | HQ-Coordinator | yes |
| repo-researcher | `repo-researcher.md` | （調研；無 HQ 列） | yes |
| governance-guard | `governance-guard.md` | HQ-Governance-Worker | yes |
| implementation-worker | `implementation-worker.md` | DarkOps / 模組 worker | no |
| checker-reviewer | `checker-reviewer.md` | QA-Reviewer | yes |

**主 agent（父對話）** = 總協調者：決定何時派誰、合併 JSON、對尚書省收口。不必為每步都 spawn coordinator；複雜多 phase 票才用 `/coordinator`。

---

## 2. 標準流水線（Happy Path）

```text
尚書省指令
  → [可選] coordinator：分解 phase + 驗收標準
  → repo-researcher：找檔／契約／runner（若位置不明）
  → governance-guard：高風險或跨邊界時必過
  → implementation-worker：單票單路徑施工
  → checker-reviewer：驗收 + 戰報 JSON 草稿
  → 父 agent：合併結果、決定是否 append Progress
```

---

## 3. 何時用 repo-researcher

**必用**：

- 不確定改哪個檔、哪個 `core`、哪個 runner
- 需要對照既有 runbook、Work Report、tests 先例
- 並行搜尋多模組，避免主 context 膨脹

**可跳過**：

- 尚書省指令已列完整 `allowed_paths` 且父 agent 剛讀過源檔
- 純文檔 typo 級單檔修補（仍建議 Read 後再派 implementation-worker）

** invoke 範例**：

```text
/repo-researcher ticket_id=HQ-xxx question="context_entry deny_rules 與測試入口在哪"
```

---

## 4. 何時直接叫 implementation-worker

**可直派**（仍建議父 agent 先 Read 任務卡）：

- 單檔、單測、單模組 bugfix
- 路徑與 acceptance 已在任務卡寫死
- 不觸憲法 §7 禁區、不改他人 `core`、不改 governance 檔

**不可直派**（須先 researcher 或 governance）：

- 跨模組、跨 `core`、動 `AGENTS.md`／`.cursor/rules`／Progress 正文
- 暗部 cabin、`dark.*` task_type、venv、`.env`、checkpoint
- scope 模糊或「順便 refactor」

**硬規則**：一 invocation = 一 `ticket_id` + 一 `primary_target`。

---

## 5. 何時必須先過 governance-guard

**必過**：

| 觸發 | 例 |
|------|-----|
| 憲法 §7 禁區類型 | env、venv 樹、checkpoint、清算腳本 |
| 跨 worker 邊界 | 改他人 `core`、接管他人 workspace 三件套 |
| 治理檔 | `AGENTS.md`、憲法、合約、`.cursor/rules`、master_status／handoff |
| 路由 blocked | `_route_task.py` → `assignable: false` |
| scope 擴張 | 新增未在任務卡的檔案／模組 |
| coordinator 標 `blocked` 或 researcher 設 `suggest_governance_review: true` |

**verdict 對照**：

- `allow` → 可派 implementation-worker（帶 `guard_verdict_id`）
- `conditional` → 滿足 `conditions` 後再派
- `deny` / `stop_work` → 不得派 implementation；回報尚書省

---

## 6. 何時最後一定要 checker-reviewer

**必用**：

- implementation-worker 回報 `ok: true` 且將關票／封存
- 任何宣稱「可交付」前（合約 GATE-3.5.1）
- 需要 `_ops_cycle.py validate-report` 的戰報 JSON

**可豁免**（父 agent 明示且尚書省同意）：

- 純 repo-researcher 調研票（無 diff）
- coordinator 純計畫票

**禁止**：implementation-worker 自標驗收通過。

---

## 7. 並行策略

可並行：

- 多個 **repo-researcher**（不同 `question`／`allowed_paths`）
- researcher 與 **governance-guard**（guard 審 plan，researcher 查證據）

不可並行：

- 兩個 **implementation-worker** 改同一 `primary_target`
- checker 與 implementation 同時寫同一批檔案

---

## 8. 與內建 subagent 分工

| Cursor 內建 | 本 repo v0.1 |
|-------------|----------------|
| explore | 優先用 **repo-researcher**（含制度／runbook 約束） |
| bash | 父 agent 或 **checker-reviewer** 跑驗證命令 |
| browser | 不取代；Playwright 票仍走 `chariot.scout` 制度 |

---

## 9. 最短驗收

1. **檔案存在**：`ls .cursor/agents/*.md` 含 5 角色 + 本檔。
2. **顯式 invoke**：在新對話執行  
   `/governance-guard` + 測試提案（例如「改 `.env` 加 key」）→ 預期 `verdict: deny`。
3. **流水線乾跑**：  
   coordinator（只讀計畫）→ researcher（只讀）→ guard（allow）→ implementation（拒絕 `governance.cleared: false`）→ checker（rejected 無 evidence）。
4. **對齊 hook**：`python .cursor/hooks/smoke_test_hooks.py`（若 repo 已配置 hooks）。

---

## 10. 與現有制度對齊（摘要）

| 現有 | Subagents v0.1 |
|------|------------------|
| `AGENTS.md` §初始化校準 | 父 agent 接戰；subagent prompt 內嵌 P0 規則摘要 |
| `.cursor/rules/engineering-contract.mdc` | 各 subagent 內建行為規則；guard／checker 顯式引用 |
| `TASK_ROUTING.md` | guard 可只讀 `_route_task.py`；coordinator 建議 task_type |
| `ENGINEERING_CONTRACT.md` Work Report | checker 依附錄 A；implementation 產草案 |
| `OPS_CYCLE.md` | checker 產 `battle_report_json_draft` |
| `workflow_upgrade/90_run_queue.md` | `ticket_id` 對齊 run_queue **ID** 或 **HQ-** 票號 |
| runtime `subagents/*`（H 線 monitoring） | **不同系統**；Cursor subagents 不取代 ask 側車 |

---

## 11. 明確不做（v0.1）

- 不新增第 6 個通用「helper」角色
- 不把 governance + 施工 + 驗收合併
- 不自動改 `lifecycle_config.json`（後續票可索引本目錄）
- 不取代尚書省裁決與 Progress 里程碑編號
