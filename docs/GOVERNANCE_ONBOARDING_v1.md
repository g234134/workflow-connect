# Governance Onboarding v1 — 三層接戰指南

> 對齊 `AGENTS.md` §初始化校準（三層精簡版）。  
> **接戰第一動作**：跑 CLI，讀 JSON 的 `read_plan`——不要全文順讀九份制度檔。

---

## 一條命令接戰（Tier 1）

```powershell
python 04_Workflows/_boot_context.py --text "<尚書省指令摘要>" --pretty
```

等價：

```powershell
python 04_Workflows/_ops_cycle.py bootstrap --text "<尚書省指令摘要>" --pretty
```

僅「接戰待命」、尚書省尚未下具體票：

```powershell
python 04_Workflows/_boot_context.py --text "接戰待命" --pretty
```

### 輸出怎麼用

| 鍵 | Agent 動作 |
|----|------------|
| `read_plan[]` | 依序讀取；遵守每項 `scope` |
| `skip[]` | **不要讀** |
| `progress_tail.text` | 視為已讀 Progress 末段；**勿開全文** |
| `route.assignable` | `false` → 停工回報 |
| `workflow_index_hint` | 只 grep `WORKFLOW_INDEX.md` 所列 §1.x |

---

## 三層模型

| 層 | 內容 | 何時 |
|----|------|------|
| **Tier 0** | `AGENTS.md` + `.cursor/rules/engineering-contract.mdc` | Cursor 自動載入 |
| **Tier 1** | `_boot_context.py` / `_ops_cycle.py bootstrap` | **每次接戰必跑** |
| **Tier 2** | 憲法 §7、Progress 末段、master_status 最近段 | boot 預設併入 `read_plan` |
| **Tier 3** | 任務 runbook、WORKFLOW_INDEX §1.x、Tabular SSOT 等 | boot 依 `--text` 追加 |
| **Tier 4** | 憲法／合約／地圖／錨點全文 | `hq.governance` 等治理票 |

---

## 快速入口

| 鏈 | 文件 |
|----|------|
| 接戰守則 | [`AGENTS.md`](../AGENTS.md) |
| 本指南 | 本檔 |
| 工作流索引 | [`04_Workflows/WORKFLOW_INDEX.md`](../04_Workflows/WORKFLOW_INDEX.md)（**僅 §1.x 節**） |
| 路徑地圖 | [`04_Workflows/Master_Map.json`](../04_Workflows/Master_Map.json) |
| W0 分流 | [`04_Workflows/_PORTABLE_CORE_INDEX.md`](../04_Workflows/_PORTABLE_CORE_INDEX.md) |

---

## 常見 `--text` 範例

| 指令摘要 | 預期追加讀檔（Tier 3） |
|----------|------------------------|
| `tabular delivery MVP` | `docs/TABULAR_MVP_SSOT.md` · WORKFLOW_INDEX §1.7 |
| `RAG smoke test` | `runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md` · §1.2 |
| `Gov Core smoke` | `runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md` · Conditions smoke 條目 |
| `P85 bridge smoke` | `docs/phase8_5-bridge-smoke-runbook-v1.md` · §1.4 |
| `Multi-Chat Implementer` | `.cursor/rules/multi_chat_roles.mdc` §Implementer |
| `hq.governance W0 定稿` | Tier 4 全文制度檔 |

---

## 不必讀（boot `skip` 預設）

- `ENGINEERING_CONTRACT.md` 全文（`.mdc` 已 alwaysApply）
- `WORKFLOW_INDEX.md` 全文（~72KB）
- `TASK_ROUTING.md`（路由已由 CLI 輸出）
- `OPS_CYCLE.md`（**封存時**再對照 checklist）

---

## 可選：完整就緒自檢（Wave 1）

非每次接戰必跑；尚書省明示或封存前：

```powershell
python 04_Workflows/_ops_cycle.py checklist --mode full --pretty
```

| step_id | 命令 | 預期 |
|---------|------|------|
| `smoke_keys` | `_smoke_test_keys.py` | exit 0；僅 `[OK]`/`[FAILED]` |
| `routing_policy_validate` | `python -m core.routing_policy_loader validate --format json` | `"ok": true` |
| `eval_gate_ci_subset` | fixture 子集 eval CI | `"ok": true` |
| `darkops_route_gate` | `_route_task.py --type dark.infra` | `assignable: false`（預期 blocked） |

保存 JSON：`python 04_Workflows/_ops_cycle.py checklist --mode full --save-json --pretty`

---

## 封存（收兵）

```powershell
python 04_Workflows/_ops_cycle.py checklist --mode minimal --pretty
python 04_Workflows/_ops_cycle.py validate-report --json <戰報.json>
python 04_Workflows/_ops_cycle.py append-report --json <戰報.json>
```

詳細欄位契約：`04_Workflows/OPS_CYCLE.md` · `04_Workflows/ops_cycle_schema.json`

---

## Progress 讀法（戰史）

- **禁止**接戰時通讀 `00_Agent_Work_Progress.md`（>250KB）。
- 以 boot 輸出 `progress_tail` 為準；需更多上下文時 `--progress-tail 120`。
- 人類查歷史：grep 日期標題（`## YYYY-MM-DD`）或 ticket 號。

---

## checklist JSON schema（Wave 1）

見前版 Step 10；頂層鍵：`ok`、`mode`、`archive_checklist`、`wave1_readiness`（僅 `--mode full`）。
