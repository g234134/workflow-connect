# Wave 5 · Human／Staging 清單（2026-07-13）

> **票**：`WAVE5-human-staging-checklist-v1`  
> **計劃**：`04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md` §1 Wave 5 · §2.5 P7 · §2.6 P9  
> **五頂母本**：`docs/governance-dual-unblock-checklist-v1.md`  
> **execute 票**：`WH-P7-NOTIF-staging-integration-execute-v2`（仍 **`blocked`**）  
> **機器可解析**：同目錄 `wave5-human-staging-checklist-2026-07-13.yaml`  
> **性質**：文件 only · **≠** 已解阻 · **≠** Round-2 GO · **≠** 改環境密鑰

---

## 0. non_claims（置頂）

| 本清單 **不是** | 說明 |
|-----------------|------|
| ≠ **已解阻** | 列項齊全 ≠ 五頂已交付；狀態以票／Progress 為準 |
| ≠ **P7 Round-2 GO**／execute-v2 已跑 | 仍須尚書省批文 + Infra／Security／allowlist／receiver |
| ≠ **prod GO**／prod flip／prod 金流 | P9 prod provider／ledger、P8.5 prod browser 仍 gap |
| ≠ **改環境密鑰**（憲法 §7 **Z-ENV**） | 禁止貼 `.env`／金鑰原文；驗收只留摘要 |
| ≠ **Dashboard authorize**／Phase% 上調 | 本票 `apply_phase_pct=false` |
| ≠ **Wave 4 UI 已交付** | 視覺已凍結（2026-07-27）；實作走 `W4-UI-A` · **≠** Operator UI 上線 |
| ≠ **DarkOps**／暗部根改寫 | 本輪不碰 |

**狀態快照（2026-07-13 · H1 更新後）**

| 線 | 現況 | 依據 |
|----|------|------|
| Wave 0–3 | 計劃登錄 · 煙霧 **GO** · Phase% 已 W-PROG 寫入 | 全線計劃 · W3-SMOKE · `W-PROG-wave013` |
| Wave 4 UI | **視覺凍結 · 施工開票** | `unified_P1–P5` · 票 `W4-UI-A` · **≠** 已交付 |
| Wave 5 | 清單登錄 · **H1 部分解** · H2–H5 仍 blocked | 本檔 · 批文 |
| **H1** | **`approved`** · ID `GOV-DUAL-APPROVAL-2026-07-13-01`（具名 2026-07-28） | `docs/governance/GOVERNANCE_DUAL_approval_template.md` |
| P7 Round-2 | execute-v2 **`blocked`／armed-not-run**（H2–H5 未齊 · 無 P-GO）· QUEUE H4 **DEFER** | 票 · QUEUE |
| P8.5 | Scenario2 GA **recorded** · **≠ prod browser** | Dashboard ≈20% |
| P9 | sandbox CI **RUN_URL recorded** · **≠ prod／INT** | Dashboard ≈24% |

---

## 1. H1–H5 · P7 Round-2 五前置（對齊計劃 §2.5）

> 任一項未交付 → **禁止**宣稱 Round-2 GO；AI **不得**代填批文／假 endpoint。

| ID | 要件 | owner | 前置 | blocked 原因（現況） | 驗收證據／命令（解阻後） | 解阻後下一工程票 |
|----|------|--------|------|----------------------|--------------------------|------------------|
| **H1** | **governance_dual 真批文** | **human**（尚書省／治理） | Round-1 local slot 已 GO（`run_id=20260623T165252Z` · **simulated** ≠ 本項） | **已解（H1）**：批文 ID `GOV-DUAL-APPROVAL-2026-07-13-01` · lifecycle **`approved`**（2026-07-28 尚書省 plan todo 具名）。**仍不解** H2–H5／Round-2。 | Progress／票引用批文 ID；路徑 `docs/governance/GOVERNANCE_DUAL_approval_template.md` | **W2-T2-infra-staging-slot-spec-request-v1**（H2 規格請求表）→ 仍須解 H2–H5 才談 execute-v2 |
| **H2** | **Infra staging slot + HTTPS endpoint** | **infra** | H1 建議先齊（可並行討論；execute 仍需齊） | 真 staging slot／non-prod HTTPS **未 provision**；local slot ≠ 真 slot | env matrix／票寫入 **slot 名 + HTTPS host**（路徑見 `Master_Map.json` 邏輯名；**不**硬編本機絕對路徑、**不**貼密鑰）；健康探針摘要 2xx | **W2-T2**（Infra staging spec · QUEUE）→ execute-v2 前置 P-2 |
| **H3** | **Security 對外 notify 路徑批文** | **security**（+ 尚書省） | H1＋H2 規格可審 | 外部 POST／客戶通道 **無** Security sign-off | 書面 sign-off 留痕（Progress 末尾一句 + 票 cross-ref）；確認無 prod URL 混入 | planning 占位 → execute-v2 前置 P-3 |
| **H4** | **客戶 staging allowlist** | **human**（產品／客戶對接） | H2 host 已知 | 客戶 staging allowlist **未**部署；local／simulated ≠ 已開 | allowlist 範圍（cohort／tenant／case）+ 生效條件寫入票／Progress；**禁止** prod endpoint | Round-2 前置另票 → execute-v2 前置 P-4 |
| **H5** | **receiver 部署就緒** | **infra**（+ human 驗收） | H2＋HMAC receiver 契約（`WH-P7-NOTIF-HMAC-receiver-*` 已有 impl／fixtures） | staging slot 上 receiver／客戶 receiver **未**就緒 | staging 驗簽探針摘要（2xx／fail 原因）；adapter unittest **≠** 本項 GA | Round-2 前置另票 → execute-v2 前置 P-5 |

### 解阻最短路徑（human／Infra · 依序）

```text
H1 批文 → H2 Infra HTTPS → H3 Security → H4 allowlist + H5 receiver → 分配 run_id 跑 execute-v2 S1–S4
```

### 誰必須人類／Infra · 誰 AI 可立刻做

| 類型 | 項目 | 說明 |
|------|------|------|
| **必須 human／Infra** | H1–H5 本體 | 批文、slot、Security、allowlist、receiver 部署／sign-off |
| **必須 human** | Wave 4 UI 照片／欄位凍結 | **已解（2026-07-27）**；後續實作 AI／工程票；不在 H1–H5 內 |
| **AI 可立刻做（本輪）** | 本清單／YAML／索引／票 | **已交付**（文件 only） |
| **AI 解阻後立刻可做** | `WH-P7-NOTIF-staging-integration-execute-v2` S1–S4 + 48h 觀測開窗 + Progress 戰報 | **僅當** H1–H5 全齊且尚書省明示 GO（QUEUE H4 earliest 07-18；可提前討論 ≠ 提前 execute） |
| **AI 可並行（不假裝解阻）** | Round-1 重跑 local smoke（advisory）；P7／P8.5／P9 **advisory** CI 解讀；Wave 3 煙霧重跑 | **≠** Round-2／prod |
| **禁止 AI 代做** | 改 `.env`／金鑰、假批文、假 endpoint、prod flip、Dashboard % authorize | 憲法 §7 **Z-ENV** 等 |

---

## 2. 相鄰 Human／Staging Gap（Wave 5 視野 · 非 H1–H5）

| ID | 主題 | owner | 現況 | blocked／gap | 解阻後下一工程票（建議） |
|----|------|--------|------|--------------|--------------------------|
| **A1** | **P8.5 prod browser** | human／Infra（另授權） | Scenario2 GA-remote **recorded**（advisory）· bridge **in-memory stub** | **≠ prod browser** · **≠** Playwright／required CI | 真 browser／Computer Use 授權票（另開；**非**本清單自動開） |
| **A2** | **P9 prod gap** | human／金流／Infra | sandbox + advisory CI **RUN_URL recorded** | prod provider／prod ledger／INT／required CI **仍 gap** | P9 prod provider／ledger 授權票（另開） |
| **A3** | **Wave 4 UI** | human（用戶） | **released** | 視覺凍結 `unified_P1–P5`；頁序 P1→P5…；A accepted_with_gaps · B P5 殼落地 | `Wave4-C`（P4）另開 · **≠** Operator UI 全量 |
| **A4** | **WC-PRE／required CI** | human／Governance | defer · 本階段不開 required | ≠ Round-2 替代門檻 | FP-G1-T2／WC-PRE 批文線（另裁） |

---

## 3. 建議用戶下一步（H1 已部分解後）

1. **填 H1 實體副署**（`docs/governance/GOVERNANCE_DUAL_approval_template.md` 簽名區）→ 升格 `approved`（若制度要求雙簽）。  
2. **交 Infra 填 H2 規格表** → `docs/governance/infra_staging_slot_spec_request_v1.md`（票 `W2-T2-infra-staging-slot-spec-request-v1`）。  
3. Wave 4 UI：視覺已凍結 → 開工 **`W4-UI-A`**（與 Round-2 可並行編排）。  
4. **禁止**：在 H2–H5 未齊時跑 execute-v2 或宣稱 Round-2 GO。

---

## Append · 2026-07-13 · H1 批文落地

- **批文**：`docs/governance/GOVERNANCE_DUAL_approval_template.md` · ID `GOV-DUAL-APPROVAL-2026-07-13-01`
- **H1 狀態**：`approved_pending_countersign`（對話授權 + 模板齊；實體副署 pending）
- **H2 準備票**：`W2-T2-infra-staging-slot-spec-request-v1` + `docs/governance/infra_staging_slot_spec_request_v1.md`
- **non_claims**：≠ Round-2 GO · ≠ execute-v2 · ≠ H2–H5 解阻 · ≠ 改密鑰


## 4. 驗證（本清單可重跑）

```powershell
python -m unittest tests.test_wave5_human_staging_checklist_v1 -v
# 期望：2+ tests OK · YAML 可解析 · H1–H5 鍵齊

rg "non_claims|H1|Round-2|prod browser|Z-ENV" 04_Workflows/plans/wave5-human-staging-checklist-2026-07-13.md
```

**不**跑：真 staging POST、prod flip、Dashboard `apply --authorize`、DarkOps。

---

## 5. 交叉引用

| 文件 | 角色 |
|------|------|
| `docs/governance-dual-unblock-checklist-v1.md` | 五頂 FRAME 母本 |
| `04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md` | Round-2 execute（blocked） |
| `04_Workflows/command_queue/QUEUE.yaml` | H4 `P7-Round-2-five-gates` · `global_blocked.P7-Round-2` |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | Phase% SSOT（只讀） |
| `docs/wave4-p85-p9-evidence-ssot-v1.md` | P8.5／P9 advisory 證據（≠ prod） |

---

## Append · 2026-07-14 · 交接副署

- 批文簽名區已加**大唐副官交接副署**（H2–H5 仍 blocked；跟交 Infra 填 H2 規格表 §2）。
- 規格表交接節：`docs/governance/infra_staging_slot_spec_request_v1.md` §5 · 票 `W2-T2-infra-staging-slot-spec-request-v1`。
- **≠** 濕墨升格 `approved` · **≠** H2 解阻 · **≠** Round-2 GO。

## Append · 2026-07-15 · 解人卡嘗試（仍 blocked）

- **指令**：解人卡 H2–H5＋濕墨主簽（解鎖 P7／利於通知 outbox 真環境）
- **結論**：**未解鎖** — 濕墨／H2–H5 均需人類／Infra；AI 未代簽、未假 provision
- **人類動作包**：`docs/governance/h2_h5_wet_ink_human_action_pack_v1.md`
- **票**：`WAVE5-h2-h5-wet-ink-unlock-attempt-v1`
- **P7／execute-v2**：仍 `blocked` · **≠** Round-2 GO · **≠** 通知／outbox 真環境已通

---

## Append · 2026-07-27 · Wave 4 UI 視覺凍結（A3 released）

- **凍結**：`docs/wave4-ui-visual-freeze-v1.md` · 票 `W4-UI-FREEZE-unified-p1-p5-v1`
- **答案**：視覺 SSOT=`unified_P1–P5.png` → **是**；頁優先序 **未改**（P1→P5→P4→P3→P2）
- **A3**：`hold` → **`released`**；下一工程票 **`W4-UI-A-static-shell-align-p1-v1`**（frame_ready）
- **non_claims**：≠ Operator UI 已交付 · ≠ Round-2 GO · ≠ 改密鑰 · ≠ DarkOps · ≠ Dashboard % authorize
- **依據**：尚書省指派完成 plan todos `await-freeze-confirm`／`await-ui-scope`

## Append · 2026-07-27 · A3 對齊 W4-UI-A／B

- **A3**：仍 `released`；工程進度：`W4-UI-A` accepted_with_gaps · `W4-UI-B` P5 靜態殼落地（≠ Operator UI 全量交付）
- **下一工程票建議**：`Wave4-C`（P4 三省拓撲）另開
- **non_claims**：≠ Round-2 GO · ≠ live API · ≠ Dashboard % authorize


## Append · 2026-07-28 · 並行催辦（W4-UI-F 可並行 · Round-2 仍禁）

- **催辦序**：H1 實體副署（`docs/governance/GOVERNANCE_DUAL_approval_template.md` 簽名區）→ H2 Infra 填 `infra_staging_slot_spec_request_v1.md` → H3 Security → H4 allowlist + H5 receiver。
- **現況（當條寫入時）**：H1 仍 `approved_pending_countersign`；H2–H5 仍 **blocked**；`WH-P7-NOTIF-staging-integration-execute-v2` 仍 **blocked**。
- **AI 並行**：`W4-UI-F` live 只讀掛載已驗收（48/48）· **不**代替 H1–H5。
- **硬禁**：H2–H5 未齊時 **禁止**跑 Round-2 execute-v2／宣稱 Round-2 GO；AI **不得**代填批文或假 endpoint。
- **QUEUE**：`priority_next` 首項＝`human-H1-countersign`；`global_blocked.P7-Round-2` 維持。
- **non_claims**：≠ 已解阻 · ≠ Round-2 GO · ≠ prod · ≠ 改密鑰 · ≠ Phase% authorize

## Append · 2026-07-28 · H1 具名升格 + H2–H5 追催（Stage A）

- **H1**：lifecycle → **`approved`**（尚書省指派 plan todo `stage-h1-countersign`＝具名主簽；見批文 §5 Append 07-28）。
- **H2–H5**：**仍 blocked** — AI **未**填假 HTTPS／假 allowlist／假 receiver；人類動作包仍為填寫權威：`docs/governance/h2_h5_wet_ink_human_action_pack_v1.md` §3–§5 + H2 規格表 §2。
- **最短序**：Infra 填 H2 §2 → Security 填 H3 → 產品／客戶填 H4 + Infra 驗 H5 → **齊且尚書省另明示 GO** 才談 `WH-P7-NOTIF-staging-integration-execute-v2`。
- **QUEUE**：`priority_next` 首項改 `human-H2-infra-spec`；Round-2 維持 DEFER／blocked。
- **non_claims**：≠ 五頂全解 · ≠ Round-2 GO · ≠ execute-v2 · ≠ prod · ≠ 改密鑰

## Append · 2026-07-28 · Wave5 Human Unlock（H2 Tip · 五頂留痕 · Round-2 arm · AI 旁線）

- **stage-h2-infra**：規格表 §6 催辦交接已交 · §2 **仍空白** · **≠** H2 解阻 · **≠** AI 假 host
- **stage-h3-security**：動作包 Append 含 H3 催辦摘要／Progress 句式 · §3 **待 Security 簽** · 強調 `no_prod_url_mixed`
- **stage-h4-h5**：H4／H5 並行編排已寫 · 五頂矩陣 **H1 only** · H2–H5 blocked
- **stage-round2-go**：execute-v2 **armed／仍 blocked** · **無**尚書省 GO · **未**跑 S1–S4／48h
- **stage-ai-sidecar**：P6 綠日鐘回填 ≥7/7（uplift 須再簽）· settings stub→薄頁 · **不**捆 Round-2
- **硬禁**：五頂未齊／無 GO → 禁止 execute-v2；禁假 endpoint／代簽／改 `.env`

## Append · 2026-07-28 · Track A Round-2 Next（H2 稽核 · H3–H5 串線 · 五頂矩陣）

### 五頂矩陣（刷新）

| ID | 狀態 | 依據 |
|----|------|------|
| **H1** | **approved** | `GOV-DUAL-APPROVAL-2026-07-13-01` · 具名 2026-07-28 |
| **H2** | **blocked** | 規格表 §7 稽核：§2 九欄空白 · **≠** 假 host |
| **H3** | **blocked** | 動作包 §3 待 Security 真簽 · `no_prod_url_mixed` 必勾 |
| **H4** | **blocked** | 動作包 §4 · 並行編排 · 依賴 H2 host |
| **H5** | **blocked** | 動作包 §5 · 並行編排 · 依賴 H2＋HMAC |
| **五頂齊？** | **否** | 缺 H2–H5 |
| **P-GO／execute-v2** | **armed／未跑** | 無尚書省 Round-2 GO · **未** S1–S4／48h |

### 串線摘要

- **H2**：催辦＋§7 驗收稽核已交（Infra）
- **H3**：Security 催辦包就緒（動作包 Track A Append）
- **H4＋H5**：並行編排就緒；H2 host 前不可完簽／完驗
- **硬禁**：禁假 endpoint／代簽／未齊跑 Round-2 · `apply_phase_pct=false`
