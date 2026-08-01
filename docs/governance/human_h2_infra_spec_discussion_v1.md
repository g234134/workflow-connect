# Human H2 Infra Spec · Staging 規格討論稿 v1

> **票／QUEUE tip**：`human-H2-infra-spec`  
> **性質**：**討論稿** · **≠** UNLOCK · **≠** Round-2 GO · **≠** execute-v2  
> **日期閘**：Round-2 仍鎖至 **2026-08-11**（見 `wave5_round2_review_agenda_2026-08-11_v1.md`）  
> **授權**：尚書省「全開」准許本討論稿落地；**仍禁假 host**

---

## 0. non_claims（置頂）

| 本稿 **不是** | 說明 |
|---------------|------|
| ≠ H2 已解阻 | §2 九欄仍空白直至 Infra 真人填寫 |
| ≠ UNLOCK／Round-2 GO | 複審日未到 · 無尚書省 GO 不得 execute |
| ≠ 假 host／localhost 頂替 | **禁止** AI 代填 `https_host`／`slot_name` |
| ≠ 改 `.env`／金鑰原文 | 僅引用 `Master_Map.json` 邏輯名 |
| ≠ DarkOps 解禁 | 真 provision 另開票 |

---

## 1. 討論範圍（可談）

1. **staging 槽位邏輯名**慣例（例：`p7-notif-staging-slot-A` 語意 · 非磁碟路徑）  
2. **TLS 類別**選項：managed cert／org CA／other（摘要）  
3. **H4 allowlist**／**H5 receiver** 銜接欄位語意  
4. 健康探針摘要格式：`status=` · `http=`（2xx／fail 原因 · 無 token）  
5. 與五頂 checklist、`GOV-DUAL-APPROVAL-2026-07-13-01` 的依賴順序

---

## 2. 不可談成「已完工」的事項

- 填寫真實／虛構 FQDN  
- 宣稱 slot 已 provision  
- 提前 Round-2 execute／wet-ink 代簽  
- 把 Round-1 local slot 寫進正式 §2 當 staging

---

## 3. 填表權威（人類／Infra）

完整九欄請求表：

**`docs/governance/infra_staging_slot_spec_request_v1.md` §2**

本討論稿 **不**複製空白欄位值；討論結論若有，以 Progress／票 notes **append** 引用，**不**覆寫 §2。

---

## 4. 建議討論議程（08-11 前可開，仍 ≠ GO）

| # | 題目 | 產出 |
|---|------|------|
| D1 | slot 命名與 env_matrix 邏輯名 | 命名公約一段 |
| D2 | TLS／allowlist 責任方 | RACI 一句 |
| D3 | 探針失敗時的誠實 fail 格式 | 範例句（無 secret） |
| D4 | 與 Round-2 議程對接 | 列入 `wave5_round2_review_agenda` 附件 |

---

## 5. 解阻後下一動（提醒 · 非本票）

Infra 填齊 §2 → §3 驗收 → H3 Security → H4/H5 → **另需**尚書省 Round-2 GO 才可 execute-v2。

---

## 6. Cross-ref

- `docs/governance/infra_staging_slot_spec_request_v1.md`
- `docs/governance/wave5_h2_unlock_or_defer_decision_v1.md`
- `docs/governance/wave5_round2_review_agenda_2026-08-11_v1.md`
- `04_Workflows/tickets/human-H2-infra-spec_state.md`

---

## 7. 全授權 B2 稽核（2026-07-29 · append）

> AI **僅**標待填 · **未**代填 §2 · **WAITING_HUMAN**

| 項 | 內容 |
|----|------|
| 討論稿 | 仍有效 · non_claims 置頂 |
| §2 九欄 | **全空白**（slot_name／https_host／tls_class／allowlist_ready_for_h4／receiver_deploy_target／health_probe_summary／env_matrix_ref／provisioned_at／infra_signoff） |
| 誰填 | Infra 真人（另見 `infra_staging_slot_spec_request_v1.md` §2／§4 AI 禁止） |
| 禁 | 假 FQDN／localhost 頂替／UNLOCK／Round-2 execute |
