# Wave5 H2 · Unlock-or-Defer 限時裁決一頁（供尚書省勾選）

> **as_of**：2026-07-28  
> **decision_id**：`WAVE5-H2-UNLOCK-OR-DEFER-2026-07-28-01`  
> **性質**：限時雙裁決 · **一次勾選** · 避免 H2 無限催辦  
> **plan todos**：`unblock-decision-memo`／`human-h2-fill`／`human-h3-h5-sign`／`human-round2-go-exec`／`human-p6-uplift-sign`／`defer-pivot-queue`  
> **≠** Unlock（未勾）· **已** Defer（§4）· **已** P6_SIGN／authorize · **≠** 假 host · **≠** 自動 execute · **≠** Round-2 GO

---

## 0. non_claims（勾選 ≠ 下列任一）

| 勾選本頁 **不是** | 說明 |
|-------------------|------|
| ≠ 假 `https_host`／localhost 冒充真 staging | Round-1 local slot **不可**頂替 Round-2 |
| ≠ 自動跑 execute-v2 S1–S4 | 須五頂齊 + **另**明示 P-GO |
| ≠ 自動 P6 83→91 | 須簽裁決包 + W-PROG + `--authorize` |
| ≠ Monitoring L1／K-2 canary／P9 prod | 本輪解卡範圍外 |
| ≠ 改 `.env`／貼金鑰（憲法 §7 **Z-ENV**） | 僅摘要／邏輯名 |

---

## 1. 卡點一句（供簽署人）

| 表象 | 根因 |
|------|------|
| QUEUE 曾以 H2 tip 無限催辦 · §2 仍空白 | Infra **未** provision 真 staging slot |
| H3–H5 blocked | 依賴 H2 `https_host` |
| execute-v2 `armed-not-run` | P-2–P-5 + **P-GO** 未齊 |

**狀態依據**：Progress Track A/B · `infra_staging_slot_spec_request_v1.md` §7 · execute-v2 STATE · 動作包 `h2_h5_wet_ink_human_action_pack_v1.md`。

---

## 2. 限時 SLA（預設 · 可改）

| 欄 | 預設值 | 尚書省可改 |
|----|--------|------------|
| **裁決日起算截止** | **5 個工作日** | 改寫下方截止日 |
| **預設截止日** | `2026-08-04`（自 2026-07-28 起 5 工作日） | ______________ |
| **逾期後果** | Unlock 未填齊 §2 → **自動落入 §4 Defer**（不靜默繼續催） | 不可取消逾期 Defer，除非另開票 |

---

## 3. 裁決欄 A · Unlock（限時 provision）

> 勾選本欄＝授權 Infra 在截止日前填規格表 §2；**不**等於 H2 已解 · **不**等於 Round-2 GO。

- [ ] **UNLOCK** · 限期內可／願 provision 真 non-prod staging

| 欄 | 填寫（Unlock 必填） |
|----|---------------------|
| **Infra owner**（具名） | ______________ |
| **截止日** | ______________（預設見 §2；逾期→Defer） |
| **§2 必填九欄**（引用規格表 §7.2） | `slot_name` · `https_host` · `tls_class` · `allowlist_ready_for_h4` · `receiver_deploy_target` · `health_probe_summary` · `env_matrix_ref` · `provisioned_at` · `infra_signoff` |
| **驗收** | 九欄非空 + 規格表 §3 四勾 + 探針 2xx／誠實 fail · **禁止** localhost／自簽冒充 |
| **解後鏈** | H3 Security §3 → H4 allowlist §4 → H5 receiver §5 → 五頂齊 → **另**明示 P-GO → execute-v2 S1–S4 + 48h |

**Unlock 執行索引**

| 步 | 檔／票 | AI 邊界 |
|----|--------|---------|
| H2 填表 | `docs/governance/infra_staging_slot_spec_request_v1.md` §2–§3（見該檔 Unlock SLA append） | AI **禁止**代填假 host |
| H3–H5 | `docs/governance/h2_h5_wet_ink_human_action_pack_v1.md` §3–§5 | AI **禁止**代簽 |
| P-GO + execute | `WH-P7-NOTIF-staging-integration-execute-v2` | **無** P-GO 不跑 S1–S4 |

---

## 4. 裁決欄 B · Defer（正式維持 Round-2 DEFER）

> 勾選本欄＝正式 Defer Round-2 真 execute；QUEUE tip **不再**以無限 H2 催辦佔首位。

- [x] **DEFER** · 無法／不願於截止日前 provision · 或 Unlock 逾期自動落入

| 欄 | 值／動作 |
|----|----------|
| **Round-2** | 維持 `blocked`／`armed-not-run` · **禁止**假 endpoint／未授權 prod |
| **QUEUE tip #1** | **`P6-nightly-continue`**（簽署裁決包）或尚書省指定產品旁線（Tabular 回歸／新 case · **≠** Phase% 假閉環） |
| **敘事首阻** | `P7-Round-2-defer` 升敘事 · 不再無限 H2 tip |
| **複審日** | 建議 `2026-08-11`（+14d；可改：______________） |
| **留痕** | Progress + execute-v2 STATE 末尾 append「H2 provision deferred · reason · review_by」 |

**Defer 樞紐 playbook**：`docs/governance/wave5_h2_defer_pivot_playbook_v1.md`

---

## 5. 裁決欄 C · P6 並行（無論 Unlock／Defer）

> 綠日 ≥7/7 與裁決包**已齊**；卡的是**簽署**，不是證據。**不**捆 Round-2。

- [x] **本週簽署** `docs/governance/p6_uplift_decision_pack_83_to_91_v1.md`（83→91）
- [ ] **本週不簽** · 維持 Dashboard 83% · 續收超額綠日

簽署後路徑（人類勾選裁決包後）：

1. 確認草稿票 `W-PROG-p6-uplift-83-to-91-2026-07-28`（見 tickets STATE）  
2. 尚書省明示授權 → `python 04_Workflows/_phase_pct_apply.py apply --ticket-id W-PROG-p6-uplift-83-to-91-2026-07-28 --authorize`  
3. **未簽不改** Dashboard %

---

## 6. 簽署欄（尚書省）

| 欄位 | 填寫 |
|------|------|
| **主裁決** | `[ ]` Unlock · `[x]` Defer · `[ ]` Unlock 逾期後自動 Defer（預設） |
| **P6 並行** | `[x]` 本週簽 · `[ ]` 本週不簽 |
| **signer** | 尚書省（口令 `DEFER + P6_SIGN` · Cursor plan Implement） |
| **signed_at** | 2026-07-28 |
| **notes** | `P6_SIGN` · W-PROG=`W-PROG-p6-uplift-83-to-91-2026-07-28` · `review_by=2026-08-11` · §3 UNLOCK 未勾 · ≠ Round-2 GO · ≠ 假 host · ≠ execute |

**勾選規則**：Unlock 與 Defer **互斥**（擇一）；逾期未填 §2 視為 Defer，無需再勾。

---

## 7. AI／Scribe 本輪已交付 vs 仍待人類

| AI／Scribe（本輪） | 人類／Infra／尚書省 |
|--------------------|---------------------|
| 本裁決一頁 | 勾選 Unlock 或 Defer + 具名 |
| Unlock 支 H2／H3–H5／execute 脚手架 append | 真 provision · 真簽 · 真 P-GO |
| P6 W-PROG **草稿**票 | 簽 P6 裁決包 → 授權 authorize |
| Defer 樞紐 playbook + QUEUE tip 改指向本裁決 | Defer 勾選後依 playbook 落 tip＝P6 |
| Progress 留痕 | Infra owner 截止日內填表 |

---

## 8. 交叉引用

| 文件 | 角色 |
|------|------|
| `docs/governance/infra_staging_slot_spec_request_v1.md` | H2 §2 九欄 |
| `docs/governance/h2_h5_wet_ink_human_action_pack_v1.md` | H3–H5 真簽 |
| `04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md` | Round-2 execute |
| `docs/governance/p6_uplift_decision_pack_83_to_91_v1.md` | P6 83→91 |
| `04_Workflows/tickets/W-PROG-p6-uplift-83-to-91-2026-07-28_state.md` | uplift 草稿票 |
| `docs/governance/wave5_h2_defer_pivot_playbook_v1.md` | Defer QUEUE 樞紐 |
| `04_Workflows/command_queue/QUEUE.yaml` | `priority_next` |

---

## 9. 驗收（對齊 plan）

```powershell
python -m unittest tests.test_wave5_human_staging_checklist_v1 -v
# Unlock：§2 九欄非空 + §3 勾選後才改 H2 狀態（人類填後 AI 覆核）
# Defer：QUEUE tip 再不無限 H2；Progress 有 defer 原因＋複審日
# P6：簽署後 authorize apply（未簽不改 Dashboard %）
```

---

## 10. Append · 2026-07-28 · Plan Implement 閘門覆核（shangshu-check-decision）

> plan todo `shangshu-check-decision` · Cursor plan「下一階段計畫：尚書省勾選 Unlock-or-Defer」**Implement** 接戰  
> **AI 禁區**：禁止代勾 §3 Unlock／§4 Defer／§5 P6 · 禁止假 host · 禁止自動 execute／authorize

### 10.1 勾選狀態稽核（本輪）

| 欄 | 現況 | 驗收 |
|----|------|------|
| §3 **UNLOCK** | `[ ]` **未勾** | ❌ 未生效 |
| §4 **DEFER** | `[ ]` **未勾** | ❌ 未生效 |
| §5 P6 本週簽／不簽 | `[ ]`／`[ ]` **未勾** | ❌ 未生效 |
| §6 signer／signed_at | **空白** | ❌ |
| 截止日 | 預設 `2026-08-04` · **未逾期**（as_of 2026-07-28） | ⏳ 未觸發逾期自動 Defer |
| `decision_status` | **`awaiting_explicit_unlock_or_defer`** | 主裁決 unset |

### 10.2 Implement 語義（具名對話）

| 項 | 值 |
|----|-----|
| **chat_implement** | `granted`（尚書省對 plan 按下 Implement） |
| **主裁決代勾** | **`forbidden`** · Implement ≠ 已選 Unlock／Defer |
| **解阻下一句** | 尚書省回覆其一：`UNLOCK` · `DEFER`（可加 `P6_SIGN` 或 `P6_HOLD`） |
| **UNLOCK 另需** | Infra owner 具名 + 截止日（可沿用 08-04） |

### 10.3 AI 本輪

| 做了 | **沒做** |
|------|----------|
| 本稽核 append · Progress／execute-v2／QUEUE 留痕 · unittest | 代勾 Unlock／Defer／P6 · 改 §2 假 host · Defer tip 覆寫 · authorize apply · S1–S4 |

---

## 11. Append · 2026-07-28T03:46 · Plan todos await-shangshu／branches（再覆核）

> plan todos `await-shangshu`／`branch-unlock`／`branch-defer`／`branch-p6` · Cursor plan「Wave5 進度盤點與下一階段」Implement（四 todo）  
> **AI 禁區**：禁止代勾 · 禁止假 host · 禁止未授權 `--authorize`／execute

### 11.1 主裁決仍 unset

| 欄 | 現況 |
|----|------|
| §3 UNLOCK／§4 DEFER／§5 P6 | **皆未勾** |
| signer／signed_at | **空白** |
| 截止 `2026-08-04` | **未逾期** → 自動 Defer **未**觸發 |
| `decision_status` | **`awaiting_explicit_unlock_or_defer`** |
| QUEUE tip#1 | 維持 `human-H2-unlock-or-defer` |
| Infra §2 九欄 | **仍全空白** |

### 11.2 四 todo 本輪結果

| Todo | 結果 | 說明 |
|------|------|------|
| `await-shangshu` | **待命已登記** | 口令就緒；Implement ≠ 主裁決 |
| `branch-unlock` | **STOP** | 無 UNLOCK · **未**催假 §2／代簽／P-GO／execute |
| `branch-defer` | **STOP** | 無 DEFER／未逾期 · tip **未**改 P6 · defer 句 **未**寫 |
| `branch-p6` | **STOP** | 無 P6_SIGN · 裁決包未簽 · Dashboard **仍 83%** · **未** authorize |

**解阻下一句（擇一）**：`UNLOCK`｜`DEFER`｜`UNLOCK + P6_SIGN`｜`DEFER + P6_SIGN`｜`P6_HOLD`

---

## 12. Append · 2026-07-28 · DEFER + P6_SIGN 生效（branch-defer／branch-p6）

> plan todos `branch-defer`／`branch-p6`／`progress-close` · 口令 **`DEFER + P6_SIGN`** · Cursor plan Implement  
> **decision_status**：`deferred_with_p6_sign`

| 欄 | 現況 |
|----|------|
| §3 **UNLOCK** | `[ ]` **未勾**（維持） |
| §4 **DEFER** | `[x]` **已勾** |
| §5 P6 本週簽 | `[x]` **已勾** |
| §6 signer／signed_at | 尚書省（`DEFER + P6_SIGN`）／`2026-07-28` |
| `review_by` | `2026-08-11` |
| QUEUE tip#1 | → `P6-nightly-continue`（依 defer playbook §2） |
| Round-2／execute-v2 | 維持 `blocked`／`armed-not-run` · **≠** S1–S4 |
| P6 | 裁決包 APPROVE → authorize apply `W-PROG-p6-uplift-83-to-91-2026-07-28`（83→91） |

**non_claims**：≠ Round-2 GO · ≠ 假 host · ≠ DarkOps · ≠ Monitoring L1／K-2 canary · ≠ UNLOCK／H3–H5 代簽

---

## 13. Append · 2026-07-28 · 下一階段三軌就緒（next-p6-watch／next-r2-review／next-war-bump）

> plan todos `next-p6-watch`／`next-r2-review`／`next-war-bump` · 口令預設 `執行計畫`  
> SSOT：`docs/governance/wave5_next_stage_post_defer_p6_v1.md`

| 軌 | 狀態 |
|----|------|
| **A · P6 盯梢** | tip#1 維持 · 超額綠日 latest=`30258570894`（UTC 07-27 success）· **不再** uplift 除非新裁決包 · Tabular 旁線僅口令 `TABULAR_SIDELINE` |
| **B · R2 複審** | 閘門日 **2026-08-11** · 議程 `wave5_round2_review_agenda_2026-08-11_v1.md` · 仍禁假 host · 提前須 `R2_REVIEW` |
| **C · war_status** | 維持 **v2.63** · 草稿 `war_status_bump_v2.64_draft_v1.md` · **未**套用 · 須 `WAR_BUMP_v2.64` |

**non_claims**：≠ Round-2 GO · ≠ UNLOCK · ≠ execute · ≠ 假 host · ≠ 未授權升檔 · ≠ Phase% 假閉環
