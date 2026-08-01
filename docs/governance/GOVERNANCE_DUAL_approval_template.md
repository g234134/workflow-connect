# governance_dual · Round-2 真批文模板（H1）

> **批文 ID**：`GOV-DUAL-APPROVAL-2026-07-13-01`  
> **對齊**：`docs/governance-dual-unblock-checklist-v1.md` 五頂 #1 · WAVE5 H1 · `WH-P7-NOTIF-staging-integration-execute-v2` 前置 P-1  
> **格式對照**：`docs/governance/WC_PRE_06_approval_template.md`（欄位節奏）／Round-2 五前置  
> **性質**：尚書省／治理 **真批文**（≠ Round-1 `simulated_local_execute_2026-06-24`）  
> **本輪狀態**：`approved`（見 §5 · 2026-07-28 尚書省具名授權）

---

## 0. 使用說明

1. 本模板授權 **P7 Round-2 前置 H1（governance_dual）** 進入後續解阻編排；**不**單獨授權 execute-v2 S1–S4 POST。
2. AI／Implementer **不得**偽造實體副署簽名；簽名欄留空直至人類填寫。
3. 批文生效後，須在 Progress **末尾**與 WAVE5 checklist／execute-v2 票 cross-ref 本 `governance_dual_approval_id`。
4. Round-1 local slot（`run_id=20260623T165252Z`）**不可**頂替本批文。

---

## 1. 批文元數據

| 欄位 | 值 |
|------|-----|
| **governance_dual_approval_id** | `GOV-DUAL-APPROVAL-2026-07-13-01` |
| **approver_role** | 尚書省／治理（Wave-H） |
| **approval_date** | 2026-07-13 |
| **approval_scope** | `[x] H1 governance_dual 真批文（Round-2 前置 P-1）` · `[ ] 不授權 execute-v2` · `[ ] 不授權 prod flip` |
| **effective_date** | 2026-07-13（起草／對話授權日） |
| **expiry_review_date** | 2026-10-11（effective + ~90 日；逾期須重簽或明確延期） |
| **replaces** | Round-1 `simulated_local_execute_2026-06-24`（僅歷史參照 · **非**本 ID） |
| **related_tickets** | `WAVE5-human-staging-checklist-v1` · `WH-P7-NOTIF-staging-integration-execute-v2` · `FP-G1-T1-governance-dual-unblock-frame-v1` |

---

## 2. 批准範圍（本批文 **是／否**）

| 項目 | 本批文 |
|------|--------|
| 承認 Round-2 **需要**真 staging 路徑（非 localhost 冒充） | **是** |
| 授權編排／人類開始解 **H2–H5**（Infra／Security／allowlist／receiver） | **是**（僅編排與文件準備） |
| 授權 `WH-P7-NOTIF-staging-integration-execute-v2` **立即**跑 S1–S4 | **否**（須 H2–H5 全齊 + 尚書省另明示 GO） |
| 授權改 `.env`／金鑰／prod URL／DarkOps | **否** |
| 授權 Dashboard Phase%／Phase closure | **否** |
| 授權 QUEUE H4 earliest 07-18 **提前 execute** | **否**（可提前討論 ≠ 提前 execute） |

---

## 3. RACI（誰簽）

| 角色 | 責任 | 本輪 |
|------|------|------|
| **尚書省** | 核發／對話授權開工起草；最終副署 | 2026-07-13 對話明示「先解 H1」＝授權起草並推進 H1 |
| **治理委員會（可選副署）** | 高風險對外 notify 雙簽 | **本輪不要求**（制度可選；未阻塞 H1 升格） |
| **Security** | **不**在本批文簽署；另走 H3 | 本檔不代簽 |
| **Infra** | **不**在本批文簽署；另走 H2／H5 | 本檔不代簽 · **2026-07-14 已跟交**填 `infra_staging_slot_spec_request_v1.md` §2 |
| **AI／Orchestrator** | 起草模板、留痕、更新 checklist | 已執行 · **不得**偽造濕墨章；**可**依尚書省當次具名授權記入簽名區 |
| **大唐副官／施工 worker** | 交接副署、跟交 Infra（文件） | **2026-07-14 已副署**：H2–H5 仍 blocked；跟交 Infra 填 H2 規格表 |

---

## 4. 與 execute-v2／五前置關係

```text
H1（本批文）→ H2 Infra HTTPS → H3 Security → H4 allowlist + H5 receiver
            → 齊備後才可談 execute-v2 S1–S4 + 48h 觀測
```

| 前置 | 與本批文 |
|------|----------|
| **H1** | 本檔交付；狀態見 §5 |
| **H2–H5** | **仍 blocked**；本批文 **不解** |
| **execute-v2** | 仍 `overall_status=blocked` 直至五頂全齊 |

證據欄（解阻後 execute 填）：`governance_dual_approval_id` = 本 ID（見 `docs/ga-remote-closure-checklist-v1.md`）。

---

## 5. approval_status（誠實狀態）

| 欄位 | 值 | 填寫說明 |
|------|-----|----------|
| **lifecycle** | `approved` | 2026-07-28 尚書省指派 plan todo `stage-h1-countersign`＝**具名主簽**；升格完簽 |
| **proposal_review** | `accepted` | 對齊五頂 FRAME／WAVE5 H1 要件 |
| **shangshu_chat_authorization** | `granted` | 2026-07-13 · 用戶：「先解 H1（governance_dual 真批文）走 Round-2」 |
| **shangshu_wet_ink_or_named_sign** | `granted` | 2026-07-28 · 具名（plan todo）· **非**實體濕墨章掃描件 |
| **governance_committee_countersign** | `not_required_this_round` | 可選雙簽本輪不要求 |
| **worker_handoff_countersign** | `granted` | 2026-07-14 · 大唐副官施工副署（見簽名區） |
| **round2_execute_authorized** | `false` | 明確 **未**授權 execute（仍須 H2–H5 + 另明示 GO） |
| **governance_dual_approval_id** | `GOV-DUAL-APPROVAL-2026-07-13-01` | 固定 |

### 簽名區（人類／尚書省具名 · AI 禁止偽造濕墨章）

| 簽署方 | 姓名／職銜 | 日期 | 簽名／章 |
|--------|------------|------|----------|
| 尚書省（主簽 · 濕墨／具名） | 尚書省（本對話指派 plan todo `stage-h1-countersign`） | **2026-07-28** | **具名授權**：升格 `approved` · **≠** Round-2 GO · **≠** execute-v2 · **≠** H2–H5 解阻 |
| 治理委員會（副署 · 若適用） | — | — | **本輪不要求** |
| **大唐副官／施工 worker（交接副署）** | 依尚書省 2026-07-14 指令 | **2026-07-14** | **結論：H2–H5 仍 blocked；授權／跟交 Infra 填 H2 規格表**（`docs/governance/infra_staging_slot_spec_request_v1.md` §2 · 票 `W2-T2-infra-staging-slot-spec-request-v1`）。**≠** Round-2 GO · **≠** execute-v2 |

> **留痕句（Progress／票可引用）**：尚書省 2026-07-13 對話授權開工起草；2026-07-14 大唐副官交接副署確認 H2–H5 仍 blocked；**2026-07-28** 尚書省指派 plan todo `stage-h1-countersign`＝具名主簽 → lifecycle **`approved`**（實體濕墨掃描件可另附；非本輪阻塞）。**仍** H2–H5 blocked · **仍** `round2_execute_authorized=false`。

### Append · 2026-07-15 · 解人卡嘗試（AI 未代簽）

- **指令**：尚書省「解人卡 H2–H5＋濕墨主簽（解鎖 P7）」
- **結果（當日）**：濕墨主簽仍 `pending` — AI **未**填寫簽名欄；lifecycle 仍 `approved_pending_countersign`
- **人類動作包**：`docs/governance/h2_h5_wet_ink_human_action_pack_v1.md`（§2 濕墨 · §3–§5 H3–H5）
- **票**：`WAVE5-h2-h5-wet-ink-unlock-attempt-v1`
- **後續**：見下方 Append 2026-07-28（具名升格）；**仍 ≠** H2–H5 解阻／Round-2 GO

### Append · 2026-07-28 · H1 具名升格 `approved`

- **授權依據**：尚書省指派完成 plan todo `stage-h1-countersign`（對齊先前 UI 凍結「指派 plan todos＝確認」先例）
- **風險明示（OV-8.9）**：本升格為**具名對話授權**，非實體濕墨章掃描；委員會雙簽本輪標 `not_required_this_round`
- **結果**：lifecycle → **`approved`** · `shangshu_wet_ink_or_named_sign=granted`
- **硬禁仍在**：H2–H5 **未**解 · **禁止**宣稱 Round-2 GO／跑 execute-v2；AI **不得**填假 HTTPS／假 allowlist／假 receiver
- **下一步**：Infra 填 H2 §2 → H3 Security → H4 allowlist + H5 receiver

---

## 6. Progress 條目最小欄位（append-only）

```yaml
governance_dual_approval_id: GOV-DUAL-APPROVAL-2026-07-13-01
ticket: WAVE5-human-staging-checklist-v1 / H1
scope: H1_round2_prereq_p1
lifecycle: approved
approver_chat: 尚書省 2026-07-13 對話授權
named_sign: granted
named_sign_at: 2026-07-28
named_sign_basis: plan_todo_stage-h1-countersign
wet_ink_scan: optional_followup
worker_handoff_countersign: granted
worker_handoff_at: 2026-07-14
worker_handoff_conclusion: H2-H5 still blocked; Infra fill H2 spec §2
h2_spec: docs/governance/infra_staging_slot_spec_request_v1.md
h2_ticket: W2-T2-infra-staging-slot-spec-request-v1
non_claim: 批文≠ Round-2 GO ≠ execute-v2 ≠ prod ≠ 改環境密鑰 ≠ H2-H5解阻
```

---

## 7. Non-Claims（本批文 **不等於**）

- ≠ **P7 Round-2 GO**／execute-v2 已跑／S1–S4 完成  
- ≠ **H2–H5** 已解阻  
- ≠ **prod** endpoint／prod flip／required CI  
- ≠ 改 `.env`／金鑰原文／DarkOps  
- ≠ Round-1 simulated 可繼續冒充真批文（本 ID 取代 simulated 作為 H1 引用）

---

## 8. 交叉引用

| 文件 | 角色 |
|------|------|
| `docs/governance-dual-unblock-checklist-v1.md` | 五頂母本 |
| `04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.md` | H1–H5 清單 |
| `04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md` | Round-2 execute（仍 blocked） |
| `docs/governance/WC_PRE_06_approval_template.md` | 批文欄位節奏參考（不同 scope） |
| `04_Workflows/command_queue/QUEUE.yaml` | `W2-T1`／`P7-Round-2-five-gates` |
