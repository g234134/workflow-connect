# P6 綠日 uplift 裁決包 · 83% → 91%（待尚書省簽署）

> **as_of**：2026-07-28  
> **票**：`WF-P6-INT-NIGHTLY-MONITOR` · QUEUE `P6-nightly-continue` / human_ops `H6`  
> **SSOT 證據**：`docs/p6-int-nightly-monitor-v1.md`  
> **Dashboard 現況**：P6 = **91%**（`docs/WAVE_PROGRESS_DASHBOARD.md` · authorize applied 2026-07-28）  
> **性質**：治理裁決一頁包 · **已 APPROVE** · **已 authorize apply** · ≠ Round-2 GO  
> **plan todo**：`track-b-p6`

---

## 0. non_claims

| 本包 **不是** | 說明 |
|---------------|------|
| ≠ P6 已升至 91% | 須尚書省簽署後另開 W-PROG + `_phase_pct_apply.py --authorize` |
| ≠ 自動 uplift | B2／H6：`RESIGN_AT_TIME` · 滿窗 ≠ 已簽 |
| ≠ Round-2／H2–H5 解阻 | 旁線；不捆 P7 |
| ≠ required CI／PR mandatory | nightly Track B + PR optional 已落地；mandatory 另票 |
| ≠ 改密鑰／DarkOps | 憲法 §7 |

---

## 1. 現況摘要（供簽署人一眼）

| 項 | 值 |
|----|-----|
| **Dashboard P6** | **91%**（was 83 · +8 applied） |
| **建議目標** | **91%**（+8）· **已達** |
| **綠日鐘核心窗** | **≥7/7 已滿** |
| **DAY7 run_id** | `29568619424`（2026-07-17 · schedule · success） |
| **超額綠日** | 續收至 2026-07-27 · latest=`30258570894` success |
| **簽署狀態** | **已 APPROVE** · authorize applied · W-PROG=`W-PROG-p6-uplift-83-to-91-2026-07-28` |

---

## 2. Nightly 證據（核心窗 DAY1–DAY7）

| Day | UTC | run_id | Verdict |
|-----|-----|--------|---------|
| DAY1 | 2026-07-11 | `29159219832` | GREEN |
| DAY2 | 2026-07-12 | `29186698130` | GREEN |
| DAY3 | 2026-07-13 | `29242215006` | GREEN |
| DAY4 | 2026-07-14 | `29320080998` | GREEN |
| DAY5 | 2026-07-15 | `29403223522` | GREEN |
| DAY6 | 2026-07-16 | `29486053016` | GREEN |
| DAY7 | 2026-07-17 | `29568619424` | GREEN · **滿窗** |

> DAY0 RED `29157182114`（missing `core`）**不計**綠日。細節見 monitor 文。

**超額綠（節選）**：`29637960949` … `30258570894`（07-18→07-27 · 皆 schedule success）。

**可重跑核對**：

```powershell
gh run list --workflow=p6-int-gate-nightly.yml --limit 15
```

---

## 3. 建議簽署條件（83 → 91）

尚書省勾選後授權方可 apply：

- [x] 承認核心窗 **≥7/7** 綠（DAY7=`29568619424`）證據充分
- [x] 同意 Dashboard **P6 83 → 91**（proposed_delta=+8）
- [x] 明示 **W-PROG** 票 ID（建議：`W-PROG-p6-uplift-83-to-91-YYYY-MM-DD`）
- [x] 授權執行：`python 04_Workflows/_phase_pct_apply.py apply --ticket-id <W-PROG> --authorize`（僅 P6）
- [x] 確認 **不**捆 Round-2／H2–H5／required CI

**簽署欄（人類）**

| 欄位 | 填寫 |
|------|------|
| **decision** | `[x]` APPROVE 83→91 · `[ ]` DEFER · `[ ]` REJECT |
| **signer** | 尚書省（口令 `DEFER + P6_SIGN` · Cursor plan Implement） |
| **signed_at** | 2026-07-28 |
| **W-PROG ticket** | `W-PROG-p6-uplift-83-to-91-2026-07-28` |
| **notes** | P6_SIGN＝明示 authorize · 僅 P6 · ≠ Round-2／H2–H5／required CI／DarkOps |

---

## 4. AI／Scribe 邊界（本輪已遵守）

| 做了 | **沒做** |
|------|----------|
| 組裝本裁決包 · 引用 nightly 證據 · Progress／票留痕 | 改 Dashboard % 數字 · 跑 `_phase_pct_apply` · 宣稱 91% 已生效 |

`apply_phase_pct=false`（本包／本輪）。

---

## 5. 交叉引用

| 文件 | 角色 |
|------|------|
| `docs/p6-int-nightly-monitor-v1.md` | 綠日鐘 SSOT |
| `04_Workflows/tickets/WF-P6-INT-NIGHTLY-MONITOR_state.md` | 監控票 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Phase% SSOT（現 83%） |
| `04_Workflows/command_queue/QUEUE.yaml` | `P6-nightly-continue` · H6 uplift resign |
| `docs/governance/wave5_h2_unlock_or_defer_decision_v1.md` | Unlock-or-Defer 欄 C 並行簽署 |
| `04_Workflows/tickets/W-PROG-p6-uplift-83-to-91-2026-07-28_state.md` | uplift **草稿**票（待簽 · 未 authorize） |

---

## 6. Append · 2026-07-28 · human-p6-uplift-sign 草稿路徑

> plan todo `human-p6-uplift-sign` · **任一支可並行** · **不**捆 Round-2

| 步 | 誰 | 動作 | 本輪狀態 |
|----|----|------|----------|
| 1 | 尚書省 | 簽本包 §3（APPROVE 83→91） | **待簽** |
| 2 | Scribe | 確認 W-PROG 草稿票 ID 寫入簽署欄 | 草稿**已開** |
| 3 | 尚書省 | 明示 authorize | **未** |
| 4 | Ops | `_phase_pct_apply.py apply --ticket-id W-PROG-p6-uplift-83-to-91-2026-07-28 --authorize` | **未跑** |

**AI 本輪**：僅開草稿票 + 本 append；Dashboard **仍 83%**；`apply_phase_pct=false`。

---

## 7. Append · 2026-07-28 · Plan Implement · branch-p6-authorize STOP

> plan todo `branch-p6-authorize` · Implement 接戰 · **未**代簽 §3 · **未** authorize

| 項 | 現況 |
|----|------|
| §3 APPROVE／DEFER／REJECT | **未勾** |
| signer／signed_at | **空白** |
| Dashboard P6 | **仍 83%** |
| `_phase_pct_apply --authorize` | **未跑** |
| W-PROG 草稿 | `W-PROG-p6-uplift-83-to-91-2026-07-28` **仍草稿** |

**解阻**：尚書省簽 §3 APPROVE + 明示 authorize（或裁決一頁回覆 `P6_SIGN`）→ 新對話才可 apply。

---

## 8. Append · 2026-07-28T03:46 · plan todo `branch-p6` STOP（再覆核）

> **P6_SIGN 未明示** · §3 APPROVE **未勾** · signer 空白 · Dashboard **仍 83%** · **未**跑 `_phase_pct_apply.py --authorize`

**解阻後才做**：簽本包 → 明示 authorize → apply `W-PROG-p6-uplift-83-to-91-2026-07-28`。

---

## 9. Append · 2026-07-28T03:55 · APPROVE + authorize（branch-p6）

> 口令 **`DEFER + P6_SIGN`** · §3 APPROVE **已勾** · W-PROG=`W-PROG-p6-uplift-83-to-91-2026-07-28`

| 項 | 現況 |
|----|------|
| §3 APPROVE 83→91 | **已勾** |
| signer／signed_at | 尚書省（`DEFER + P6_SIGN`）／`2026-07-28` |
| authorize | **明示**（口令 `P6_SIGN`） |
| CLI | `_phase_pct_apply.py apply --ticket-id W-PROG-p6-uplift-83-to-91-2026-07-28 --authorize` |

**non_claims**：≠ Round-2 GO · ≠ H2–H5 解阻 · ≠ required CI · ≠ DarkOps · ≠ 自動 war_status（無另授權）
