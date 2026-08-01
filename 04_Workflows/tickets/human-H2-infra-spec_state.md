# TICKET STATE · human-H2-infra-spec · Staging 規格討論

> **QUEUE tip**：`human-H2-infra-spec` · mode=human  
> **授權**：尚書省「全開」→ 准許 **討論稿** 落地 · **仍禁假 host** · **≠** UNLOCK／Round-2 execute  
> **日期**：Round-2 review_by=**2026-08-11**

---

## FRAME

- Goal: 產出 staging 規格**討論稿**，釐清可討論項與硬禁，指向既有 §2 填表權威。
- Scope:
  - `docs/governance/human_h2_infra_spec_discussion_v1.md`
  - 本 STATE
- NonScope:
  - 代填 `https_host`／假 slot
  - UNLOCK／execute-v2／改 `.env`
  - DarkOps／Round-2 GO
- AcceptanceCriteria:
  - AC-1：討論稿存在 · non_claims 置頂
  - AC-2：明示仍禁假 host · ≠ UNLOCK
  - AC-3：§2 權威仍指向 `infra_staging_slot_spec_request_v1.md`

---

## STATE

- **overall_status**: `done_with_gaps` · **WAITING_HUMAN**（§2）
- **overall_status_rationale**: 討論稿 DONE；§2 九欄仍空白（human／Infra）· H2 未解阻
- **current_owner**: human／Infra
- **next_action**: Infra 真人填 `infra_staging_slot_spec_request_v1.md` §2 · 08-11 前可討論 · **禁** AI 假 host · **禁** execute
- **last_updated**: 2026-07-29T00:50+08:00 · 全授權 B2（標待填 · 未代填）
- **gaps**:
  - §2 九欄空白（見下方待填欄）
  - H2 未解阻
  - Round-2 日期未到

### B2 · 待填欄稽核（2026-07-29 · AI 禁止假 host）

| 欄位（§2） | 狀態 |
|------------|------|
| slot_name | **空白 · 等 Infra 真人** |
| https_host | **空白 · 等 Infra 真人** |
| tls_class | **空白 · 等 Infra 真人** |
| allowlist_ready_for_h4 | **空白 · 等 Infra 真人** |
| receiver_deploy_target | **空白 · 等 Infra 真人** |
| health_probe_summary | **空白 · 等 Infra 真人** |
| env_matrix_ref | **空白 · 等 Infra 真人** |
| provisioned_at | **空白 · 等 Infra 真人** |
| infra_signoff | **空白 · 等 Infra 真人** |

**本輪 AI 動作**：只讀討論稿／標待填 · **未**寫入任何 host／IP／連線字串。

---

## B_REPORT

- changed_files:
  - `docs/governance/human_h2_infra_spec_discussion_v1.md`
  - `04_Workflows/tickets/human-H2-infra-spec_state.md`
- verification: 文件存在 · 全文無假 FQDN／localhost 頂替
- non_claims: ≠ UNLOCK · ≠ Round-2 GO · ≠ 假 host · ≠ execute-v2
