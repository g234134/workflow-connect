# WC-PRE-06 · Toolchain Health Gate · Human Approval Template

> **票號**：WC-PRE-06 · W5-WC-PRE-06-governance-spec-v1  
> **性質**：尚書省／治理委員會 **批文空白模板**（doc-only）  
> **狀態**：**未批准** — 填寫前不得開 `WC-IMPL-L1` / `WC-IMPL-L2` 施工  
> **設計 SSOT**：`docs/toolchain-observability-governance-upgrade-v1.md` · `docs/governance/wc_pre_06_governance_policy_v1.json`

---

## 0. 使用說明

1. 本模板由 **尚書省／治理委員會** 填寫；AI／Implementer **不得**預填 `approved`。
2. 批文完成後，將 `wc_pre_approval_id` 寫入 Progress **末尾** 與對應 implementation 票 FRAME。
3. 本批文 **僅** 授權 toolchain health gate 升格路徑；**不** 授權 smoke mandatory CI（見 WC-PRE-07 獨立模板）。

---

## 1. 批文元數據

| 欄位 | 值（human 填寫） |
|------|------------------|
| **wc_pre_approval_id** | `WC-PRE-06-APPROVAL-________`（建議：日期 + 序號） |
| **approver** | 尚書省／治理委員會 簽核人 |
| **approval_date** | YYYY-MM-DD |
| **approval_scope** | `[ ] L0 baseline ack only` · `[ ] L0→L1` · `[ ] L0→L1→L2` |
| **effective_date** | 不得早於 implementation 票 merge 日 |
| **expiry_review_date** | 建議 effective_date + **90 日** |

---

## 2. 批准方（RACI）

| 級別 | 可批准方 | 最低證據 |
|------|----------|----------|
| **L0 baseline ack** | 尚書省 | 確認 WB-T4 optional 現況為合意基線 |
| **L1 PR optional advisory** | **尚書省** | §2.2 G1–G5 全滿 + 本模板 §4 L1 checklist |
| **L2 PR required** | **尚書省 + 治理委員會** | L1 連續 21 日 + §2.2 G1–G6 + rollback 演練留痕 |

---

## 3. 批文產物格式

| 產物 | 路徑／形式 | 必填 |
|------|------------|------|
| **Signed approval_status** | `docs/toolchain-observability-governance-upgrade-v1.md` §8 表格 | 是 |
| **Policy JSON 同步** | `docs/governance/wc_pre_06_governance_policy_v1.json` → `approval_status.*` | 是（implementation 前） |
| **Progress 末尾條目** | `04_Workflows/00_Agent_Work_Progress.md` append-only | 是 |
| **Meeting / email ref** | 自由文字（**非** run URL） | 可選 |
| **Ticket cross-ref** | `WC-IMPL-L1` / `WC-IMPL-L2` FRAME Dependencies | 是（開工前） |

**Progress 條目最小欄位**

```yaml
wc_pre_approval_id: WC-PRE-06-APPROVAL-________
ticket: WC-PRE-06
scope: L0|L1|L2
approver: ___
approval_date: YYYY-MM-DD
approval_status.L1: pending|approved|rolled_back
approval_status.L2: pending|approved|rolled_back
non_claim: 批文僅授權 CI 設計路徑；不等於 prod selector 已啟用
```

---

## 4. 升格條件確認（human checklist）

### 4.1 L0 → L1（須全部勾選 + 尚書省簽核）

- [ ] G1：WB-T4 unittest + `TS-TOOLCHAIN-DASHBOARD-*` 連續 **14 日** 全綠（CI log 或 ops 週報）
- [ ] G2：`artifacts/toolchain/toolchain_health.latest.json` 在 **≥80%** 活躍週可產出且 `sections_populated ≥ 3`
- [ ] G3：`HOOK-CATALOG-COUNT` + `HOOK-SMOKE-SUMMARY` 契約測試就緒
- [ ] G4：`WC-IMPL-L1` FRAME 已凍結且 NonScope 不含改 dashboard 評分邏輯
- [ ] G5：flake 率未超過 rollout plan 觀察期閾值（L1 advisory fail **不** 阻 merge）
- [ ] **Human signoff**：`approval_status.L1_pr_optional` = `approved`

### 4.2 L1 → L2（須全部勾選 + 雙簽）

- [ ] G1：L1 連續 **21 日**；PR optional step 失敗率 **< 5%**（排除 outbox 空檔 degraded）
- [ ] G2：main 分支 outbox 7 日滾動存在率 **≥ 95%**
- [ ] G3：§5 hooks 全量接入且 investigation spec 投影穩定
- [ ] G4：rollback playbook（design doc §7）演練 **1 次** 並留痕 Progress
- [ ] G5：`aggregated_health_score` **不** 作 hard assert（rollout D2 = NO）
- [ ] G6：`WC-IMPL-L2` FRAME 已凍結
- [ ] **Human signoff**：`approval_status.L2_pr_required` = `approved` + 治理委員會簽核

---

## 5. approval_status 填寫區（預設 pending · 禁止 AI 填 approved）

| 欄位 | 值 | 填寫人 | 日期 |
|------|-----|--------|------|
| proposal_review | **pending** | | |
| L0_baseline_ack | **pending** | | |
| L1_pr_optional | **pending** | | |
| L2_pr_required | **pending** | | |
| OG-TOOLCHAIN-HEALTH_row | **pending** | | |
| score_threshold_L2 | **不採用**（rollout D2） | | |
| rollback_drill_required | yes | | |
| wc_pre_approval_id | — | | |

---

## 6. Rollback 引用

| 場景 | 動作 SSOT |
|------|-----------|
| L2 → L1 | `docs/toolchain-observability-governance-upgrade-v1.md` §7.2 |
| L2/L1 → L0 | 同上 §7.3 |
| 恢復 L2 | §7.5 + 新 `wc_pre_approval_id` |

---

## 7. Non-Claims（本批文不等於）

- **不等於** governance 已在 prod 啟用或 branch protection 已變更
- **不等於** prod selector / Monitoring Graph L1/L2 已啟用
- **不等於** P10（48%）runtime 閉環（S15 notify · intake API）已交付
- **不等於** WC-PRE-07 smoke mandatory CI 已批准（獨立模板）

---

## 8. 簽核欄（空白）

```text
尚書省／治理委員會裁決：
- 核准級別：[ L0 only / L0→L1 / L0→L1→L2 ]
- OG-TOOLCHAIN-HEALTH 寫入 P3.5：[ 是 / 否 / 延後 ]
- L2 score 下限：[ 不採用 / ≥60 / 其他___ ]
- wc_pre_approval_id：WC-PRE-06-APPROVAL-________
- 條件：[ 無 / 見備註 ]

簽核：__________  日期：__________
治理委員會（L2 必填）：__________  日期：__________
```

---

*WC-PRE-06 Approval Template · design_only · pending_approval · 2026-06-26*
