# Wave 4 UI · Visual Freeze v1

> **Ticket**：`W4-UI-FREEZE-unified-p1-p5-v1`  
> **施工首票**：`W4-UI-A-static-shell-align-p1-v1`  
> **日期**：2026-07-27  
> **性質**：視覺／頁序凍結紀錄 · **≠** 已交付 Operator UI · **≠** Dashboard Phase% 上調

---

## 1. 凍結裁決

| 項 | 裁決 |
|----|------|
| **視覺 SSOT** | `docs/ui-templates/unified_P1.png` … `unified_P5.png` |
| **凍結？** | **是**（解 Wave 4 UI HOLD） |
| **頁優先序** | **P1 → P5 → P4 → P3 → P2**（維持計劃建議；**未**改優先序） |
| **JPG 07-13** | 歷史參考 only |
| **`page01–05.html`** | 可改造成「對齊 PNG 的靜態殼」；**不是**最終美觀標準 |
| **欄位契約** | 計劃 §2.1–2.4 + `docs/p89-operator-fields-projection-v1.md` 等（圖管 layout，契約管 JSON） |

**確認依據**：尚書省指派完成 plan todos `await-freeze-confirm` + `await-ui-scope`（2026-07-27）；資產路徑見 `docs/ui-templates/`。

---

## 2. 五頁產品地圖（凍結）

| ID | 頁 | 職責 |
|----|----|------|
| **P1** | 全局總覽 | KPI · 主流程管線 · 六部／暗部狀態點 · 活動日誌 |
| **P2** | 技能與資源 | 技能卡 · 模組表 · API／Token · **金鑰庫僅遮罩** |
| **P3** | 暗部執行閉環 | 七模組卡 · 回流圖 · 重試／告警（只讀；≠ 改暗部 core） |
| **P4** | 三省六部指揮台 | 中書／門下／尚書拓撲 · 六部卡 · 任務佇列 |
| **P5** | 多任務協作作業台 | 泳道 · 業務摘要 · 技能／工具／模型／API 健康 |

---

## 3. 實作波次（凍結後）

```text
Wave4-A  殼：共用 sidebar/header/token + P1 靜態對齊 unified_P1（mock JSON）  ← **accepted_with_gaps**
Wave4-B  P5 作業台泳道（ticket / outbox / gate 只讀 mock → 再真 API）  ← **accepted_with_gaps（靜態 mock）**
Wave4-C  P4 三省拓撲（可部分靜態）  ← **accepted_with_gaps（靜態 mock）**
Wave4-D  P3 暗部閉環圖（只讀健康／計數；≠ 改暗部根）  ← **accepted_with_gaps（靜態 mock）**
Wave4-E  P2 技能／資源（金鑰僅遮罩；metrics stub）  ← **accepted_with_gaps（靜態 mock）· 五頁靜態殼 A–E 完成**
```

**宿主**：獨立靜態／輕量殼掛在戰車根（可後接 `app/local_ui`）· **≠** 暗部 `dashboard.html` 大翻修 · **≠** Grafana。

**收口狀態（2026-07-28）**：Wave4 **A–E 靜態殼**均 `accepted_with_gaps`；導覽 P1–P5 可互點；settings 為 stub。  
**Wave4.5（同日）**：`W4-UI-F` live 只讀掛載（P1／P5 · `?source=live` · CLI 投影）→ `accepted` · **≠** Operator 全量 prod · **≠** Phase% authorize。

---

## 4. 紅線（凍結即生效）

- **禁止**畫面展示金鑰原文（憲法 §7 **Z-ENV**／AGENTS 紅線）；P2 僅遮罩 + 額度敘事。
- **禁止** DarkOps Blocked 時改暗部根；產品文案可寫「暗部」。
- KPI／流程節點須映射既有 operator fields／gate／outbox／monitoring；**禁止**硬編假 100% 當驗收。
- `apply_phase_pct=false`（本凍結與 Wave4-A 均 **未**授權 Dashboard %）。

---

## 5. 交叉引用

| 路徑 | 角色 |
|------|------|
| `docs/ui-templates/unified_P*.png` | 視覺 SSOT |
| `docs/ui-templates/page*.html` | 靜態殼起點 |
| `docs/p89-operator-fields-projection-v1.md` | P8.9 UI 五鍵 |
| `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md` §2.1–2.4 | 各 Phase UI 欄位草案 |
| `04_Workflows/tickets/W4-UI-A-static-shell-align-p1-v1_state.md` | Wave4-A 施工票 |
| `04_Workflows/tickets/W4-UI-E-p2-skills-resources-v1_state.md` | Wave4-E 施工票（P2 · 五頁收口） |
| `docs/wave4-ui-e-p2-skills-resources-runbook-v1.md` | P2 開啟／mock／驗證 |
