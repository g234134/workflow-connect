# Wave5 H2 · Defer 樞紐 Playbook（QUEUE · Progress · execute-v2）

> **as_of**：2026-07-28  
> **觸發**：裁決一頁 `wave5_h2_unlock_or_defer_decision_v1.md` 勾選 **DEFER**，或 Unlock **逾期**未填齊 §2  
> **plan todo**：`defer-pivot-queue`  
> **性質**：正式維持 Round-2 DEFER 的 QUEUE／留痕步驟 · **≠** 假 endpoint · **≠** 自動 execute · **≠** 自動 P6 uplift

---

## 0. non_claims

| 本 playbook **不是** | 說明 |
|----------------------|------|
| ≠ Unlock 已選 | 須裁決一頁欄 B 或逾期自動落入 |
| ≠ H2 已解／五頂齊 | Defer＝停止無限催辦，不解阻 |
| ≠ Round-2 GO | 維持 `armed-not-run` |
| ≠ P6 已升 91% | tip 改 P6 **簽署**，簽後另 authorize |

---

## 1. 正式 DEFER 語義

| 項 | 動作 |
|----|------|
| Round-2 | 維持 `blocked`／`armed-not-run` |
| H2–H5 | 維持 blocked · **不再**以無限 H2 tip 佔 `priority_next[0]` |
| 敘事首阻 | `P7-Round-2-defer` 升敘事 |
| tip #1 | **`P6-nightly-continue`**（或尚書省指定產品旁線 · ≠ Phase% 假閉環） |
| 複審日 | 預設 **`2026-08-11`**（裁決日 +14d；可改） |

---

## 2. QUEUE `priority_next` 目標形狀（Defer 生效後）

```yaml
priority_next:
- id: P6-nightly-continue
  seq: 1
  mode: human
  reason: Defer 樞紐 · 綠日≥7/7 · 裁決包待簽 83→91 · ≠ 自動 uplift · ≠ Round-2 GO
- id: P7-Round-2-defer
  seq: 2
  mode: human
  reason: 正式 DEFER Round-2 · H2 provision deferred · review_by=2026-08-11 · armed-not-run
- id: human-H2-infra-spec
  seq: 3
  mode: human
  reason: 複審日前可討論 provision · **不**佔 tip#1 無限催辦 · 仍禁假 host
- id: WAVE6-unified-close
  seq: 4
  mode: archived_narrative
  reason: Wave6 已歸檔敘事 · 不佔 active human tip
```

**過渡態（裁決未勾前 · 本輪已落）**：tip #1 = `human-H2-unlock-or-defer`（指向裁決一頁），結束「僅催 H2 §2」死循環；勾 Defer 後依上表覆寫。

---

## 3. Progress／票 append 句式（Defer 勾選或逾期時）

**Progress 末尾（必）**：

```text
H2 provision deferred · reason=<Unlock逾期|尚書省DEFER> · review_by=YYYY-MM-DD
· QUEUE tip#1 → P6-nightly-continue · Round-2 armed-not-run · ≠ 假 host／≠ execute
```

**execute-v2 STATE 末尾（必）**：

```text
### Append · DEFER pivot
overall_status=blocked · armed-not-run · H2 provision deferred · review_by=...
· 禁止 S1–S4／假 endpoint／未授權 prod
```

---

## 4. 產品旁線（可選 · 尚書省指定）

若 tip #1 不走 P6，可改：

| 選項 | 說明 |
|------|------|
| Tabular 回歸／新 case | **≠** Phase% 假閉環 |
| 其他產品旁線 | 須具名寫入裁決一頁 notes |

---

## 5. 交叉引用

| 文件 | 角色 |
|------|------|
| `docs/governance/wave5_h2_unlock_or_defer_decision_v1.md` | 裁決一頁 |
| `04_Workflows/command_queue/QUEUE.yaml` | `priority_next` |
| `04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md` | Round-2 |
| `docs/governance/p6_uplift_decision_pack_83_to_91_v1.md` | P6 簽署 |

---

## 6. Append · 2026-07-28 · Plan Implement · branch-defer-apply STOP

> plan todo `branch-defer-apply` · **DEFER 未勾** · 截止 `2026-08-04` **未逾期** · Implement ≠ 代勾 Defer

| 項 | 現況 |
|----|------|
| 裁決 §4 DEFER | **未勾** |
| 逾期自動 Defer | **未觸發** |
| QUEUE tip#1 | 維持 `human-H2-unlock-or-defer`（**未**升 P6） |
| Progress defer 句 | **未寫**（須勾選／逾期後才寫 `H2 provision deferred · reason=… · review_by=2026-08-11`） |
| execute-v2 | 維持 `blocked`／`armed-not-run` · defer_reason pending |

**解阻**：尚書省勾 DEFER（或回覆 `DEFER`）／Unlock 逾期 → 依本 playbook §2–§3 覆寫 tip + Progress／票 append。

---

## 7. Append · 2026-07-28T03:46 · plan todo `branch-defer` STOP（再覆核）

> **DEFER 仍未勾** · 截止未逾期 · tip#1 仍 `human-H2-unlock-or-defer` · Progress defer 句 **未**寫 · **未**升 tip＝P6

**解阻後才做**：§2 tip 形狀 + §3 Progress／execute-v2 append（`review_by=2026-08-11`）。

---

## 8. Append · 2026-07-28T03:55 · DEFER 生效（branch-defer）

> 口令 **`DEFER + P6_SIGN`** · 裁決一頁 §4 **已勾** · tip 依 §2 覆寫

| 項 | 現況 |
|----|------|
| 裁決 §4 DEFER | **已勾** |
| QUEUE tip#1 | **`P6-nightly-continue`** |
| QUEUE tip#2 | **`P7-Round-2-defer`**（`review_by=2026-08-11`） |
| `human-H2-unlock-or-defer` | **已降級離 tip#1** |
| Progress defer 句 | 已 append |
| execute-v2 | `blocked`／`armed-not-run` · defer_reason=尚書省DEFER · review_by=2026-08-11 |

**non_claims**：≠ Round-2 GO · ≠ 假 host · ≠ execute · ≠ 自動 P6 uplift（P6 另走 authorize）。

---

## 9. Append · 2026-07-28 · 下一階段（post DEFER+P6）

> plan todos `next-p6-watch`／`next-r2-review`／`next-war-bump`

| 項 | 動作 |
|----|------|
| tip 形狀 | **不變**（§2：P6-nightly-continue → P7-Round-2-defer → H2-infra-spec） |
| P6 | 超額綠日續收 · Dashboard 已 91 · **禁**無新包 uplift |
| 複審 | 議程預排 `wave5_round2_review_agenda_2026-08-11_v1.md` · 日＝`2026-08-11` |
| war_status | **不**升 · 草稿待 `WAR_BUMP_v2.64` |
| 總覽 | `docs/governance/wave5_next_stage_post_defer_p6_v1.md` |
