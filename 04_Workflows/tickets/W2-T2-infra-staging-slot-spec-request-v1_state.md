# TICKET STATE · W2-T2-infra-staging-slot-spec-request-v1 · H2 Infra staging 規格請求（文件 only）

> Wave 5 續 · Round-2 前置 H2 準備 · **doc-only** · 2026-07-13  
> QUEUE 對齊：`W2-T2`（Infra staging slot + HTTPS endpoint）  
> **依賴**：H1 `GOV-DUAL-APPROVAL-2026-07-13-01`（lifecycle **`approved`** · 2026-07-28）  
> **≠** 真 provision · **≠** 改環境密鑰 · **≠** staging POST

---

## FRAME

- Goal: 為 Infra 準備可填寫的 **staging slot + non-prod HTTPS endpoint** 規格請求表，解鎖 H2 討論／交付路徑（文件 only）。
- Scope:
  - MUST：規格請求表（slot 名邏輯欄、HTTPS host 佔位、健康探針摘要欄、禁寫密鑰）
  - MUST：cross-ref H1 批文 ID · execute-v2 P-2 · WAVE5 H2
- NonScope:
  - ≠ 實際 provision／DNS／TLS 憑證安裝  
  - ≠ 改 `.env`／貼金鑰  
  - ≠ execute-v2 S1–S4  
  - ≠ Dashboard Phase%  
  - ≠ DarkOps
- AllowedPaths:
  - `docs/governance/infra_staging_slot_spec_request_v1.md`
  - `04_Workflows/tickets/W2-T2-infra-staging-slot-spec-request-v1_state.md`
  - `04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.md`（H2 下一票引用 · 可末尾一句）
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
- BlockedPaths:
  - `.env` · 憲法 §7 · 暗部根 · `core/**`（本票不改）
- phase_targets: [P7]
- baseline_pct: "07-13 Dashboard · P7=30%"
- proposed_delta_pct: "P7 +0"
- evidence_gate: L-local
- apply_phase_pct: false
- non_claims:
  - ≠ H2 已解阻 · ≠ Round-2 GO · ≠ 真 endpoint · ≠ 改密鑰

### AcceptanceCriteria

- AC-1：規格請求表含 slot／HTTPS／探針／禁密鑰欄
- AC-2：明示須 Infra 填寫；AI 不填假 host
- AC-3：`apply_phase_pct=false`

---

## STATE

- overall_status: done_with_gaps
- current_owner: infra
- next_action: Infra 填寫 `docs/governance/infra_staging_slot_spec_request_v1.md` §2 → 解 H2；H2 解前 execute-v2 仍 blocked
- last_updated: 2026-07-13 · 規格請求表已落地
- status_by_role:
  - orchestrator: done — FRAME／開票
  - implementer: done — 規格請求表文件
  - reviewer: pending — Infra 填寫後再驗
  - scribe: pending — Progress 一句
- notes:
  - 請求表已齊 · **≠ H2 解阻**（須 Infra 真填 slot／HTTPS）
  - gap：真實 provision／探針仍待 Infra

---

## Append · 2026-07-14 · 批文交接副署 → Infra 填 §2

- **批文**：`GOV-DUAL-APPROVAL-2026-07-13-01` · `docs/governance/GOVERNANCE_DUAL_approval_template.md` §5 簽名區已加 **大唐副官／施工 worker 交接副署**
- **結論**：H2–H5 **仍 blocked** · lifecycle 仍 `approved_pending_countersign`（濕墨主簽／委員會章仍 pending）
- **跟交**：Infra 填寫 `docs/governance/infra_staging_slot_spec_request_v1.md` **§2**（見該檔 §5 交接副署）
- **current_owner**：infra（不變）
- **next_action**：Infra 填 §2 → §3 驗收 → 解 H2；**≠** execute-v2 · **≠** Round-2 GO
- **non_claims**：≠ H2 已解 · ≠ 改密鑰 · ≠ DarkOps 施工（boot `assignable=false`；本輪僅文件交接）

---

## Append · 2026-07-15 · 解人卡嘗試（H2 仍 blocked）

- 尚書省要求解 H2–H5＋濕墨；**H2 仍 blocked**（§2 空白欄未由 Infra 填寫；AI **未**填假 host）
- 人類動作包（含 H3–H5）：`docs/governance/h2_h5_wet_ink_human_action_pack_v1.md`
- **current_owner**：infra（不變）

## Append · 2026-07-28 · Wave5 Tip H2 催辦（仍 blocked · ≠ Round-2 GO）

- **H1**：已 `approved`（2026-07-28 具名）· 本票依賴敘事對齊
- **交接**：`infra_staging_slot_spec_request_v1.md` **§6** Tip 催辦已交 · §2 **仍空白**
- **current_owner**：infra（不變）
- **next_action**：Infra 真填 §2 → §3 驗收 → 解 H2 → 串 H3；**禁止** AI 假 host／execute-v2
- **non_claims**：≠ H2 已解 · ≠ Round-2 GO · ≠ 改密鑰 · ≠ DarkOps

## Append · 2026-07-28 · Track A H2 催辦／驗收稽核（仍 blocked）

- **稽核**：規格表 **§7** · §2 九欄 **全空白** · §3 **未勾** · H2 **仍 blocked**
- **AI**：僅催辦／完整性核對 · **未**寫假 host／假 slot
- **current_owner**：infra（不變）
- **next_action**：Infra 真填 §2 → §3 四勾選 → 解 H2 → 串 H3–H5
- **apply_phase_pct**：false
- **non_claims**：≠ H2 已解 · ≠ Round-2 GO · ≠ execute-v2 · ≠ 改密鑰
