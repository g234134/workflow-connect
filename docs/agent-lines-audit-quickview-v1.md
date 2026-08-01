# Agent-Lines Audit Quickview v1

> **票號**: W10-T3 · agent-lines-audit-quickview-cli-v1  
> **實作**: `scripts/run_agent_audit_quickview.py`  
> **性質**: **只讀** — 不寫入 outbox、不更新 checkpoint state、不連外部系統  
> **Contract SSOT (WB-T5)**: `docs/audit-quickview-and-case-history-spec-v1.md` — 本檔降級為實作附錄／範例
---

## 1. 目的

為 **Tabular Agent 標準線** 與 **Non-tabular preview** 提供一條審計快查命令，讓 Reviewer / 審計者在單一視圖中查看某 `case_ref` 最近一次 Agent-run 的：

- 決策（`decision` / `risk_level`）
- 規劃路徑（`planned_route` / `planned_tools`）
- Checkpoint A / B 狀態（是否觸發、磁碟記錄、人類決策）
- Delivery approval（如有 CP-B 人類決策）

---

## 2. CLI 用法

```bash
# 文字摘要（預設）
python scripts/run_agent_audit_quickview.py --case-ref demo_phase

# JSON（供腳本 / dashboard 消費）
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --format json

# 巢狀 case_ref
python scripts/run_agent_audit_quickview.py --case-ref sampleco/2026-0001

# 自訂 repo root（unittest / 離線 scratch）
python scripts/run_agent_audit_quickview.py --case-ref demo_phase --repo-root /path/to/repo
```

| 參數 | 必填 | 說明 |
|------|------|------|
| `--case-ref` | ✅ | 案型參考（如 `demo_phase`、`sampleco/2026-0001`、`nt_docu_stub`） |
| `--format` | | `text`（預設）或 `json` |
| `--repo-root` | | 覆寫戰車根；預設為 `scripts/` 上層 |

**退出碼**：找到至少一筆 run artifact 或 checkpoint 記錄 → `0`；否則 → `1`。

---

## 3. 資料來源（只讀）

| 來源目錄 | 用途 | 匹配規則 |
|----------|------|----------|
| `outbox/agent_experiment_regression/` | Tabular 實驗線 regression JSON | `{timestamp}_{case_slug}.json` 或 payload 內 `case_ref` |
| `outbox/agent_ci/` | Agent CI 產物（預留） | 同上 |
| `outbox/non_tabular_experiment/` | Non-tabular preview 產物 | 同上 |
| `outbox/<case_ref>/checkpoint_A-intake-confirmation_*.json` | CP-A 人類決策 | 目錄名 = `case_ref` |
| `outbox/<case_ref>/checkpoint_B-delivery-confirmation_*.json` | CP-B / delivery approval | 同上 |

**最新一筆**：依檔名時間戳字串排序（`YYYYMMDDTHHMMSSZ` 或 ISO-8601）取最大者。

---

## 4. JSON 輸出形狀

```json
{
  "ok": true,
  "read_only": true,
  "schema_version": "agent_audit_quickview_v1",
  "case_ref": "demo_phase",
  "latest_run": {
    "found": true,
    "source_kind": "agent_experiment_regression",
    "artifact_path": "outbox/agent_experiment_regression/20260609T232936Z_demo_phase.json",
    "mode": "run",
    "final_status": "waiting_for_human"
  },
  "decision": { "decision": "needs_review", "risk_level": "medium" },
  "planned_route": {
    "selector_task_type": "e2e",
    "planned_tools": ["validate.eligibility", "clean.phase_demo", "export.delivery_bundle"]
  },
  "checkpoint_a": {
    "would_trigger": true,
    "status": "auto_approved",
    "on_disk": false,
    "human_decision": null
  },
  "checkpoint_b": {
    "would_trigger": true,
    "status": "approved",
    "on_disk": true,
    "checkpoint_path": "outbox/demo_phase/checkpoint_B-delivery-confirmation_....json",
    "human_decision": { "action": "approve_delivery", "operator_id": "operator_cli" }
  },
  "delivery_approval": {
    "source": "checkpoint_B_on_disk",
    "action": "approve_delivery",
    "status": "approved"
  },
  "sources_read": ["..."]
}
```

---

## 5. Text 模式範例（demo_phase）

執行：

```bash
python scripts/run_agent_audit_quickview.py --case-ref demo_phase
```

預期輸出摘要（依本機 outbox 最新 artifact 略有差異）：

```
Agent-Lines Audit Quickview (W10-T3 · read-only)
case_ref: demo_phase
ok: True

── Latest Agent Run ──
found: True
source: agent_experiment_regression
artifact: outbox/agent_experiment_regression/20260609T232936Z_demo_phase.json
timestamp: 20260609T232936Z
mode: run
final_status: waiting_for_human
task_type: tabular.cleaning.mvp
experiment_id: aef7ac87-3bc6-4e1b-b690-7f7226ce117a

── Decision ──
decision: needs_review
risk_level: medium

── Planned Route ──
selector_task_type: e2e
planned_tools: validate.eligibility, clean.phase_demo, export.delivery_bundle

── Checkpoint A (Intake) ──
would_trigger: True
status: auto_approved
on_disk: False

── Checkpoint B (Delivery) ──
would_trigger: True
status: approved
on_disk: True
path: outbox/demo_phase/checkpoint_B-delivery-confirmation_2026-06-09T23-29-33Z.json
human_decision: action=approve_delivery by=operator_cli

── Delivery Approval ──
source: checkpoint_B_on_disk
action: approve_delivery
status: approved
operator_id: operator_cli
comment: LGTM demo W8-T3
timestamp: 2026-06-09T23:29:36Z
```

---

## 6. 驗證

```bash
python -m unittest tests.test_agent_audit_quickview_v1 -v
```

---

## 7. 限制（NonScope）

- ❌ 不寫入任何檔案
- ❌ 不更新 checkpoint / outbox state
- ❌ 不呼叫 executor、notify gateway 或外部 API
- ❌ 不取代完整 regression runner 或 delivery approval CLI

---

## 8. 相關文件

- `docs/agent-standard-line-governance-view-v2.md` — 審計材料清單
- `docs/agent-standard-line-v1-summary.md` — 標準線案型與 checkpoint 語意
- `docs/hitl-checkpoints-v1.md` — CP-A / CP-B 檔案命名
- `scripts/run_agent_standard_case_regression.py` — regression artifact 產生者
- `scripts/run_non_tabular_experiment_preview.py` — non-tabular preview 產生者
