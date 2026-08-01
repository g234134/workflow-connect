# WC-PRE-07 · Mandatory Smoke CI · Human Approval Workflow Template

> **票號**：WC-PRE-07 · W5-WC-PRE-07-approval-workflow-v1  
> **性質**：尚書省／治理委員會 **批文流程 SSOT**（doc-only）  
> **狀態**：**未批准** · `blocked_on_approval`  
> **設計 SSOT**：`docs/toolchain-smoke-mandatory-ci-runner-v1.md` · `docs/governance/wc_pre_07_approval_workflow_policy_v1.json`

---

## 1. 誰可以批准

| 級別 | 批准方 | 可否單獨授權改 workflow |
|------|--------|-------------------------|
| **L1 · optional_ci advisory** | **尚書省** | 否 — 須另開 `WC-IMPL-SMOKE-CI-L1` 且本模板 L1 簽核 |
| **L2 · mandatory 白名單** | **尚書省 + 治理委員會** | 否 — 須 `WC-IMPL-SMOKE-CI-L2` + branch protection 變更票 |
| **Rollback L2→L1** | 工程 on-call 可先執行 | 24h 內尚書省備案 |
| **Rollback 至 L0** | 尚書省或治理委員會 | 須書面/口頭批文 |

---

## 2. 批文產物

| 產物 | 格式 | 必填欄位 |
|------|------|----------|
| **Approval record** | 本模板 §5 表格 | `wc_pre_approval_id` · `approver` · `approval_date` · `approval_scope` |
| **Design doc sync** | `docs/toolchain-smoke-mandatory-ci-runner-v1.md` §6 | `approval_status.*` |
| **Policy JSON sync** | `wc_pre_07_approval_workflow_policy_v1.json` | `approval_status.*` · `mandatory_ci_scope` |
| **Progress 末尾** | YAML 條目（append-only） | 見 §3 |
| **Email / 會議紀要** | 自由文字 | 可選 · **不可** 以 run URL 代替批文 |
| **Implementation 授權** | 票 FRAME Dependencies | `WC-IMPL-SMOKE-CI-L1` / `L2` ticket id |

---

## 3. Trace 欄位（`wc_pre_approval_id` 構想）

### 3.1 ID 格式

```text
wc_pre_approval_id: WC-PRE-07-APPROVAL-YYYYMMDD-NNN
```

- **YYYYMMDD**：批文日期  
- **NNN**：當日序號（001 起）  
- 同一 ID 須出現在：Progress 末尾 · policy JSON · implementation 票 FRAME ·（可選）email subject

### 3.2 Progress 末尾最小 YAML

```yaml
wc_pre_approval_id: WC-PRE-07-APPROVAL-________
ticket: WC-PRE-07
wave5_ticket: W5-WC-PRE-07-approval-workflow-v1
scope: L1|L2|rollback
approver: ___
approval_date: YYYY-MM-DD
approval_status.L1: pending|approved|rolled_back
approval_status.L2: pending|approved|rolled_back
mandatory_ci_scope: TS-TOOLCHAIN-DASHBOARD-UNIT,TS-W3TL-UNIT  # L2 only
implementation_ticket: WC-IMPL-SMOKE-CI-L1|L2|none
non_claim: mandatory smoke CI 批文 ≠ P10 prod-ready ≠ prod selector 啟用
```

### 3.3 State 票欄位（future · observer 只讀）

| 欄位 | 用途 |
|------|------|
| `wc_pre_approval_id` | 人類批文唯一鍵 |
| `approval_status.L1` | smoke advisory CI 授權狀態 |
| `approval_status.L2` | mandatory 白名單授權狀態 |
| `mandatory_ci_scope` | L2 批准的 smoke_id 列表 |
| `design_ready` | doc bundle 完成（**≠ approved**） |

---

## 4. L1 批文 checklist（尚書省）

- [ ] `docs/toolchain-smoke-mandatory-ci-runner-v1.md` 已 Reviewer `design_ready`
- [ ] Rollout D3/D5 白名單敘事已讀（L2 不含 `TS-ROUTING-EVAL-*`）
- [ ] `WC-IMPL-SMOKE-CI-L1` FRAME 已凍結
- [ ] 確認 L1 step 為 `continue-on-error: true` · **不** 改 branch protection
- [ ] `wc_pre_approval_id` 已分配
- [ ] **簽核**：`approval_status.L1_optional_ci_advisory` = `approved`

---

## 5. L2 批文 checklist（尚書省 + 治理委員會）

- [ ] L1 advisory 連續 **21 日** · flake **< 5%**
- [ ] 白名單僅：`TS-TOOLCHAIN-DASHBOARD-UNIT` · `TS-W3TL-UNIT`
- [ ] Rollback 演練 1 次已留痕 Progress
- [ ] `WC-IMPL-SMOKE-CI-L2` FRAME 已凍結
- [ ] P3.5 修訂票（CH-43）已排程（若升格 mandatory class）
- [ ] 新 `wc_pre_approval_id`（與 L1 不同）
- [ ] **雙簽**：`approval_status.L2_mandatory_whitelist` = `approved`

---

## 6. approval_status 填寫區（預設 pending）

| 欄位 | 值 | 填寫人 | 日期 |
|------|-----|--------|------|
| proposal_review | **pending** | | |
| L1_optional_ci_advisory | **pending** | | |
| L2_mandatory_whitelist | **pending** | | |
| mandatory_ci_scope | `TS-TOOLCHAIN-DASHBOARD-UNIT,TS-W3TL-UNIT`（設計預設 · 非批准） | | |
| wc_pre_approval_id | — | | |

---

## 7. Rollback 流程（摘要）

1. Workflow smoke step → `continue-on-error: true` 或移除（implementation 票 revert）
2. 若 branch protection 已增 required check → 取消（Platform + 尚書省留痕）
3. 更新 `approval_status.L2` 或 `L1` = `rolled_back`
4. Progress 末尾 append：`wc_pre_approval_id` · 原因 · 影響 · 是否一次性
5. 通知 Dashboard Lane B 消費方：smoke CI **非** merge blocker

詳見 `docs/toolchain-smoke-mandatory-ci-runner-v1.md` §5 · rollout plan §4.3。

---

## 8. Non-Claims

- 本模板填寫 **不等於** mandatory smoke CI 已上線
- **不等於** WC-PRE-06 governance 已啟用
- **不等於** prod selector 已啟用
- **不等於** P10 S15 notify / intake API 已交付
- **不得** 由 AI 預填 `approved` 或偽造 `wc_pre_approval_id`

---

## 9. 簽核欄（空白）

```text
尚書省裁決（L1）：
- 核准：optional_ci advisory CI step（WC-IMPL-SMOKE-CI-L1）
- wc_pre_approval_id：WC-PRE-07-APPROVAL-________
- 條件：[ 無 / 見備註 ]
簽核：__________  日期：__________

治理委員會 + 尚書省裁決（L2）：
- 核准 mandatory 白名單：[ TS-TOOLCHAIN-DASHBOARD-UNIT · TS-W3TL-UNIT ]
- wc_pre_approval_id：WC-PRE-07-APPROVAL-________
- branch protection 變更授權：[ 是 / 否 / 延後 ]
簽核（尚書省）：__________  日期：__________
簽核（治理委員會）：__________  日期：__________
```

---

*WC-PRE-07 Approval Workflow Template · design_only · blocked_on_approval · 2026-06-26*
