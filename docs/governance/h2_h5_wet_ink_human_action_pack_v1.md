# H2–H5＋濕墨主簽 · 人類動作包（解鎖 P7 Round-2 前置）

> **as_of**：2026-07-15  
> **對齊**：WAVE5 H1–H5 · `GOV-DUAL-APPROVAL-2026-07-13-01` · execute-v2 前置 P-1–P-5  
> **性質**：人類／Infra／Security **填寫與簽署用** · **≠** 已解阻 · **≠** Round-2 GO · **≠** 改 `.env`／金鑰  
> **AI 禁區**：禁止代簽濕墨主簽／委員會章；禁止填假 HTTPS host／假 allowlist／假 receiver

---

## 0. non_claims（置頂）

| 本包 **不是** | 說明 |
|---------------|------|
| ≠ P7 已解鎖／Round-2 GO | 五頂未齊 + 尚書省另明示 GO 前禁止 execute-v2 |
| ≠ 濕墨已完簽 | 簽名欄仍待人類；AI 不得代填 |
| ≠ H2–H5 已解 | 規格表／sign-off 齊 ≠ 真 provision／真部署 |
| ≠ 通知／outbox 真環境已通 | 解阻後才利於 staging notify／outbox／DLQ 真路徑；本包不解阻 |
| ≠ 改環境密鑰（憲法 §7 **Z-ENV**） | 僅摘要／邏輯名；不貼密鑰原文 |

---

## 1. 現況快照（2026-07-28 · Wave5 Human Unlock · H2 Tip）

| ID | 要件 | 狀態 | 誰必須動 | 填寫／簽署位置 |
|----|------|------|----------|----------------|
| **濕墨／具名主簽**（H1 完簽） | 尚書省濕墨／具名主簽（＋可選委員會副署） | **已解** · `approved`（2026-07-28 具名 plan todo） | —（完簽） | `docs/governance/GOVERNANCE_DUAL_approval_template.md` §5 |
| **H2** | Infra staging slot + non-prod HTTPS | **仍阻塞** · Tip 催辦已交 · §2 空白 | **infra** | `docs/governance/infra_staging_slot_spec_request_v1.md` **§2**（見該檔 §6） |
| **H3** | Security 對外 notify 路徑批文 | **仍阻塞** · 本包 §3 待簽（須 H2 host） | **security**（+ 尚書省） | 本檔 **§3** |
| **H4** | 客戶 staging allowlist | **仍阻塞** · 本包 §4 待填 | **human**（產品／客戶） | 本檔 **§4**（須 H2 host 已知） |
| **H5** | receiver 部署就緒 | **仍阻塞** · 本包 §5 待填 | **infra**（+ human 驗收） | 本檔 **§5**（須 H2＋HMAC 契約） |
| **Round-2 GO** | 尚書省明示 GO + execute-v2 S1–S4 | **仍禁** · 票已 armed · 未跑 | **shangshu** → Implementer | `WH-P7-NOTIF-staging-integration-execute-v2` |

**2026-07-14**：批文已加**大唐副官交接副署**（`worker_handoff_countersign=granted`）並跟交 Infra 填 H2 §2；**≠** 濕墨完簽 · **≠** H2 解阻。

**2026-07-15**：AI 無法代解 H2–H5／濕墨；僅補齊人類動作包並 Progress 留阻。

**2026-07-28 · Stage A**：H1 具名升格 `approved`；**H2–H5 仍 blocked**。

**2026-07-28 · Wave5 Unlock**：HQ-Coordinator 完成 H2–H5 催辦包 + execute 閘門編排 + AI 旁線；**仍未**假填 HTTPS／allowlist／receiver；**未**跑 Round-2。

---

## 2. 濕墨／具名主簽（H1 升格 `approved`）

| 欄位 | 值／動作 |
|------|----------|
| **批文 ID** | `GOV-DUAL-APPROVAL-2026-07-13-01` |
| **lifecycle 現況** | **`approved`**（2026-07-28） |
| **已交付** | 尚書省具名主簽（plan todo `stage-h1-countersign`）；委員會雙簽本輪 `not_required_this_round` |
| **在哪留痕** | 批文 §5 簽名區 → Progress 末尾 + WAVE5／execute-v2 票 cross-ref |
| **仍不解** | H1 完簽 **不解** H2–H5 · **不**授權 execute-v2 |

> 實體濕墨掃描件可另附；**非**本輪阻塞。AI **禁止**把 H2–H5 標為已解。

---

## Append · 2026-07-28 · Stage A 追催（H2→H5 · 禁 Round-2 GO）

1. **立刻**：Infra 填 `infra_staging_slot_spec_request_v1.md` **§2**（slot_name／https_host／tls／探針摘要／infra_signoff）。
2. **其後**：Security 填本檔 **§3**（無 prod URL）。
3. **再後**：產品／客戶填 **§4** allowlist；Infra＋人類填 **§5** receiver 探針。
4. **齊且尚書省另明示 GO** 後：才開跑 `WH-P7-NOTIF-staging-integration-execute-v2`（S1–S4）。
5. **禁止**：H2–H5 未齊宣稱 Round-2 GO；改 `.env`／貼金鑰；假批文／假 endpoint。

---

## Append · 2026-07-28 · Wave5 Human Unlock（H2 Tip → Round-2 arm · AI 旁線）

> plan todos：`stage-h2-infra`／`stage-h3-security`／`stage-h4-h5`／`stage-round2-go`／`stage-ai-sidecar`

### A. 五頂齊全留痕（誠實）

| 頂 | 狀態 | 證據／缺口 |
|----|------|------------|
| H1 | **approved** | `GOV-DUAL-APPROVAL-2026-07-13-01` |
| H2 | **blocked** | §2 九欄空白 · 規格表 §6 催辦已交 |
| H3 | **blocked** | §3 待 Security 簽 · 無 prod URL 混入須勾 |
| H4 | **blocked** | §4 待產品／客戶 · 依賴 H2 `https_host` |
| H5 | **blocked** | §5 待 Infra 探針 · adapter UT ≠ GA |
| 五頂齊？ | **否** | 缺 H2–H5 |
| Round-2 GO？ | **否** | 須五頂齊 + 尚書省**另**明示 GO（H1 approved 不夠） |

### B. H3 Security 催辦摘要（待簽 · 本節不代簽）

- **填寫位置**：本檔 **§3**
- **必勾**：`no_prod_url_mixed=yes` · scope=`staging outbound POST only`
- **reviewed_hosts**：須對齊 H2 `https_host`（H2 未填前僅可預審契約，**不可**完簽）
- **Progress 留痕句式**：`H3 SEC-NOTIFY-SIGNOFF-<date> · no_prod_url_mixed=yes · hosts=<non-prod FQDN>`

### C. H4＋H5 並行編排（H2 host 已知後）

- **H4**：本檔 §4 · cohort／tenant／case · `explicit_non_prod=yes` · **禁止** prod endpoint
- **H5**：本檔 §5 · `verify_probe_summary` 可重跑 · 雙簽欄
- **五頂齊全留痕**：Progress 末尾一句 + WAVE5 checklist Append + execute-v2 P-2–P-5 勾選

### D. Round-2 execute 閘門（armed · 未跑）

- **票**：`WH-P7-NOTIF-staging-integration-execute-v2`
- **前置**：H1–H5 全齊 + **尚書省明示 GO**（對話／批文；本輪**無** GO）
- **動作**：S1–S4 + 建議 48h 觀測開窗
- **本輪 AI**：**禁止**分配 run_id／發 staging POST／宣稱 GO

### E. AI 旁線（≠ 解阻）

- P6 綠日鐘：monitor 回填至 **≥7/7**（滿窗後 uplift **須再簽**）
- settings stub→薄頁（command_center · ≠ Phase%／≠ Round-2）

---

## Append · 2026-07-28 · Track A · H3–H5 串線 + 五頂矩陣刷新

> plan todo `track-a-h3-h5` · **≠** 代簽 · **≠** 假 allowlist／receiver · **≠** Round-2 GO

### A. 五頂矩陣（as_of 本輪）

| 頂 | 狀態 | owner | 填寫位置 | 本輪動作 |
|----|------|--------|----------|----------|
| **H1** | **approved** | — | 批文 §5 · ID `GOV-DUAL-APPROVAL-2026-07-13-01` | 敘事已對齊；不解 Round-2 |
| **H2** | **blocked** | infra | 規格表 §2（§7 稽核：九欄空白） | 催辦／驗收稽核已交 |
| **H3** | **blocked** | security | 本檔 **§3** | 催辦包就緒 · **待真簽** |
| **H4** | **blocked** | product／客戶 | 本檔 **§4** | 與 H5 **並行編排**（須 H2 host） |
| **H5** | **blocked** | infra＋human | 本檔 **§5** | 與 H4 **並行編排**（須 H2＋HMAC） |
| **五頂齊？** | **否** | — | — | 缺 H2–H5 |
| **P-GO** | **否** | 尚書省 | execute-v2 票 | H1 approved **≠** Round-2 GO |

### B. H3 Security 催辦包（待簽 · 不代簽）

| 項 | 內容 |
|----|------|
| **填哪** | 本檔 **§3** 全欄 |
| **必勾** | `no_prod_url_mixed=yes` · scope=`staging outbound POST only` |
| **reviewed_hosts** | 對齊 H2 `https_host`（H2 空白前僅可預審契約，**不可**完簽） |
| **解阻證據** | Progress：`H3 SEC-NOTIFY-SIGNOFF-<date> · no_prod_url_mixed=yes · hosts=<non-prod FQDN>` |
| **硬禁** | prod URL 混入 · AI 代簽 · 貼 secret |

### C. H4＋H5 並行編排（H2 host 已知後立刻雙線）

| 線 | 填哪 | 關鍵勾選 | 解阻一句 |
|----|------|----------|----------|
| **H4** | §4 | `explicit_non_prod=yes` · cohort／tenant／case | allowlist 範圍＋生效條件入票／Progress |
| **H5** | §5 | `verify_probe_summary` 可重跑 · 雙簽 | staging 驗簽探針摘要＋infra／human 雙簽 |

**依賴**：H4／H5 均 **blocked_on_H2_host**；H2 解前僅可預審契約／HMAC fixtures（adapter UT **≠** H5 GA）。

### D. 解阻後下一動（本輪未達）

五頂齊 → 尚書省**另**明示 Round-2 GO → `WH-P7-NOTIF-staging-integration-execute-v2` S1–S4＋48h。

---

## Append · 2026-07-28 · Unlock 支 · H3–H5 真簽鏈（human-h3-h5-sign）

> plan todo `human-h3-h5-sign` · 依裁決一頁 **Unlock** + H2 §2／§3 齊後才可完簽  
> **≠** AI 代簽 · **≠** 假 allowlist／receiver · **≠** Round-2 GO（須另 P-GO）

### A. 依賴閘門

| 前置 | 未滿足 |
|------|--------|
| 裁決一頁勾選 Unlock（或等效授權） | 本鏈僅預審 · **不可**完簽 |
| H2 `https_host` 已填（真 non-prod FQDN） | H3 `reviewed_hosts`／H4 `depends_on_h2_host` **不可**完簽 |
| 規格表 §3 四勾 | H2 仍 blocked → H3–H5 維持 blocked |

### B. 真簽順序（人類）

| 序 | 頂 | 填寫位置 | 必勾／必填 | 解阻留痕句式 |
|----|----|----------|------------|--------------|
| 1 | **H3** | 本檔 **§3** | `no_prod_url_mixed=yes` · scope=staging outbound POST only · `reviewed_hosts`＝H2 host · `security_signoff` | `H3 SEC-NOTIFY-SIGNOFF-<date> · no_prod_url_mixed=yes · hosts=<FQDN>` |
| 2a | **H4** | 本檔 **§4** | `explicit_non_prod=yes` · cohort／tenant／case · `owner_signoff` | allowlist 範圍＋生效條件入 Progress |
| 2b | **H5** | 本檔 **§5** | `verify_probe_summary` 可重跑 · infra＋human 雙簽 | receiver 探針摘要＋雙簽入 Progress |

H4／H5 在 H2 host 已知後 **可並行**。

### C. 五頂矩陣（Unlock 支目標 · 本輪現況仍誠實）

| 頂 | 現況 | Unlock 完簽後目標 |
|----|------|-------------------|
| H1 | **approved** | approved（不變） |
| H2 | **blocked** | approved／ready（九欄＋§3） |
| H3 | **blocked** | approved（§3 真簽） |
| H4 | **blocked** | approved（§4 真填） |
| H5 | **blocked** | ready（§5 雙簽＋探針） |
| P-GO | **否** | 須尚書省**另**明示（本 append **不解** P-GO） |

### D. AI 本輪

| 做了 | **沒做** |
|------|----------|
| 真簽鏈脚手架／矩陣／句式 | 代簽 §3–§5 · 假 host／allowlist · 改 H2–H5＝approved · 跑 execute |

---

## Append · 2026-07-28 · Plan Implement · H3–H5 STOP（branch-unlock-fill 子閘）

> Implement 接戰 · **UNLOCK 未勾** · §2 空白 → H3–H5 **不可**完簽

| 頂 | 現況 | AI |
|----|------|-----|
| H1 | **approved** | — |
| H2–H5 | **blocked** | **未**代簽 §3–§5 · **未**假 allowlist／receiver |
| P-GO | **否** | **未**跑 execute |

**解阻**：裁決勾 UNLOCK + H2 §2 齊 → 依本檔 Unlock 真簽鏈 §B。

---

## 3. H3 · Security 對外 notify 路徑 sign-off（待 Security 填）

| 欄位 | 填寫 | 備註 |
|------|------|------|
| **signoff_id** | ______________ | 例：`SEC-NOTIFY-SIGNOFF-YYYY-MM-DD-01` |
| **scope** | `[ ]` staging outbound POST only · `[ ]` other:___ | **禁止** prod URL |
| **reviewed_hosts** | ______________ | 僅 non-prod FQDN；對齊 H2 `https_host` |
| **secret_handling** | `[ ]` HMAC／env slot 摘要 OK · `[ ]` gap:___ | **不**貼 secret |
| **no_prod_url_mixed** | `[ ]` yes · `[ ]` no | 否 → **不得** sign-off |
| **risk_notes** | ______________ | 一句即可 |
| **security_signoff** | 姓名／日期 | |
| **shangshu_ack**（可選） | 姓名／日期 | |

**解阻條件**：書面 sign-off 寫入本節 + Progress 末尾一句；無 prod URL 混入。

---

## 4. H4 · 客戶 staging allowlist（待產品／客戶對接填）

| 欄位 | 填寫 | 備註 |
|------|------|------|
| **allowlist_id** | ______________ | |
| **depends_on_h2_host** | ______________ | 須與 H2 `https_host` 一致 |
| **cohort／tenant／case 範圍** | ______________ | |
| **effective_from／until** | ______________ | |
| **deployed_to_slot** | `[ ]` yes · `[ ]` no | local／simulated ≠ 已開 |
| **explicit_non_prod** | `[ ]` yes | **禁止** prod endpoint |
| **owner_signoff** | 姓名／日期 | |

**解阻條件**：範圍 + 生效條件寫入本節／票／Progress；明確 non-prod。

---

## 5. H5 · receiver 部署就緒（待 Infra＋人類驗收填）

| 欄位 | 填寫 | 備註 |
|------|------|------|
| **receiver_target** | ______________ | 邏輯名；對齊 H2 `receiver_deploy_target` |
| **contract_ref** | `WH-P7-NOTIF-HMAC-receiver-*`（fixtures／impl 已有） | adapter unittest **≠** 本項 GA |
| **verify_probe_summary** | `status=____` · `http=____` | 僅 2xx／fail 原因；**不**貼 token |
| **deployed_at** | YYYY-MM-DD | |
| **infra_signoff** | 姓名／日期 | |
| **human_acceptance** | 姓名／日期 | |

**解阻條件**：staging 驗簽探針摘要可重跑 + 雙簽欄已填。

---

## 6. 解阻最短路徑（人類／Infra · 依序）

```text
濕墨主簽（可選並行編排）→ H2 Infra HTTPS → H3 Security → H4 allowlist + H5 receiver
→ 五頂齊 + 尚書省明示 GO → WH-P7-NOTIF-staging-integration-execute-v2 S1–S4
→ 利於通知／outbox／DLQ 真 staging 路徑（仍 ≠ prod）
```

QUEUE：`P7-Round-2-five-gates` earliest **2026-07-18** 再裁；可提前討論 ≠ 提前 execute。

---

## 7. 交叉引用

| 文件 | 角色 |
|------|------|
| `docs/governance/GOVERNANCE_DUAL_approval_template.md` | H1／濕墨主簽 |
| `docs/governance/infra_staging_slot_spec_request_v1.md` | H2 Infra §2 |
| `04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.md` | H1–H5 清單 SSOT |
| `docs/governance-dual-unblock-checklist-v1.md` | 五頂 FRAME 母本 |
| `04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md` | Round-2 execute（仍 blocked） |
