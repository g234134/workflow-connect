# W10-T4 · agent-and-non-tabular-lines-readme-v1

> **角色**: Architect + Scribe  
> **類型**: 文檔工單（Document Ticket）  
> **狀態**: implementer done · Reviewer pending  
> **日期**: 2026-06-10

---

## 1. 目的

為未來合作者與新加入 Agent 提供一份 **README 級別的總覽文件**：

- 概述 **Tabular Agent Standard Line v2** 的核心流程（S1-S15）
- 概述 **Non-Tabular Shadow Flow v1** 的定位、現有能力與未來方向
- 解釋兩條線如何與 **CI / Metrics / Audit / HITL** 配合
- 提供快速索引（文件、命令、Wave Dashboard）

---

## 2. Acceptance Criteria

- [x] README 包含 §1–§6 完整結構
- [x] Tabular v2 的 S1-S15 流程與 Wave 7 狀態準確對齊 `docs/agent-standard-line-v1-summary.md`
- [x] Non-Tabular v1 的 Shadow 定位準確對齊 `docs/non-tabular-shadow-flow-blueprint-v1.md`
- [x] CI 整合參照 `docs/agent-lines-ci-suite-v1.md`（W10-T1）
- [x] Metrics（W10-T2）與 Audit（W10-T3）標示為「待實作」並列出規劃方向
- [x] Governance 決策權分佈準確對齊 `docs/agent-standard-line-governance-view-v2.md`
- [x] 安全邊界摘要涵蓋 R1/R3/R4/R6/R8 與 R-NT1~R-NT5
- [x] Roadmap Glimpse 僅列方向、不開新票

---

## 3. 交付物

| 文件 | 路徑 | 說明 |
|------|------|------|
| **README 主檔** | `docs/agent-and-non-tabular-lines-readme-v1.md` | 本工單主交付 |
| **工單 State** | `04_Workflows/tickets/W10-T4-agent-and-non-tabular-lines-readme-v1_state.md` | 本檔 |

---

## 4. 章節結構驗收

| 章節 | 標題 | 驗收 |
|------|------|------|
| §1 | Overview：這兩條線是什麼，解決什麼問題 | ✅ 含定位表、問題陳述、主鏈關係圖 |
| §2 | Tabular Agent Standard Line v2 | ✅ S1-S15 流程總覽、Wave 7 狀態表、Run/Preview/HITL/Notify 合作說明 |
| §3 | Non-tabular Shadow Flow v1 | ✅ 現有能力、Shadow 理由、未來演進方向 |
| §4 | CI / Metrics / Audit | ✅ CI 整合（W10-T1 done）、Metrics（W10-T2 TBD）、Audit（W10-T3 TBD） |
| §5 | Governance & HITL | ✅ 15 步決策權矩陣、五大禁止事項、NT 特有風險、安全邊界速查表 |
| §6 | Roadmap Glimpse | ✅ Wave 11/12+ 方向、未開票聲明 |
| 附錄 | 快速索引 | ✅ 核心文件表、命令速查、Wave Dashboard 引用 |

---

## 5. 上游依據清單

以下文件在撰寫時已被閱讀並對齊：

- `docs/agent-standard-line-v1-summary.md` — Tabular v1 收口總結
- `docs/agent-standard-line-governance-view-v2.md` — Wave 7 治理觀點
- `docs/agent-run-experiment-eval-guide-v1.md` — 實驗線驗收指南
- `docs/ninety-five-percent-automation-blueprint-v2.md` — Wave 7 自動化藍圖
- `docs/non-tabular-shadow-flow-blueprint-v1.md` — W8-T4 Shadow 設計
- `docs/non-tabular-routing-catalog-v1.md` — W9-T1 Routing 規格
- `docs/non-tabular-orchestrator-preview-v1.md` — W9-T4 Preview CLI
- `docs/agent-lines-ci-suite-v1.md` — W10-T1 CI 整合
- `04_Workflows/WORKFLOW_INDEX.md` — 工作流索引
- `docs/WAVE_PROGRESS_DASHBOARD.md` — Wave 完成度總覽

---

## 6. 設計決策與注意事項

### 6.1 為何不包含 Metrics / Audit 詳細規格？

W10-T2（Metrics）與 W10-T3（Audit）為獨立工單，本 README 僅：
- 列出規劃中的觀測點與命令框架
- 標示「待實作」避免讀者誤以為已上線

### 6.2 為何 Roadmap 不開新票？

Wave 11+ 方向需尚書省/架構師評估後才會成為正式工單，本 README 僅作「方向性規劃」供讀者理解長期走向。

### 6.3 Non-Tabular 的 Shadow 定位強調

多次強調「shadow = 設計層 only」以避免：
- 誤以為 Wave 9 已可執行真實 OCR/parser
- 誤以為 Non-Tabular 已影響 Tabular 主鏈

---

## 7. 驗證

### 7.1 文件存在檢查

```bash
ls -la docs/agent-and-non-tabular-lines-readme-v1.md
ls -la 04_Workflows/tickets/W10-T4-agent-and-non-tabular-lines-readme-v1_state.md
```

### 7.2 章節完整性檢查

```bash
grep "^## §" docs/agent-and-non-tabular-lines-readme-v1.md | wc -l
# 預期輸出: 6
```

### 7.3 關鍵錨點檢查

```bash
grep -E "(W7-T2|W8-T4|W9-T4|W10-T1)" docs/agent-and-non-tabular-lines-readme-v1.md
# 應包含這些 Wave 票的引用
```

---

## 8. Reviewer 檢查清單

- [ ] 文件路徑正確（`docs/` + `04_Workflows/tickets/`）
- [ ] 無本機絕對路徑（符合 engineering-contract META-0.4）
- [ ] 所有上游文件引用正確（無 404 連結）
- [ ] Tabular v2 狀態與 `WAVE_PROGRESS_DASHBOARD.md` §Wave 7 一致
- [ ] Non-Tabular v1 定位與 `non-tabular-shadow-flow-blueprint-v1.md` §1.2 一致
- [ ] 安全邊界涵蓋所有 R1/R3/R4/R6/R8 與 R-NT1~R-NT5
- [ ] 命令速查表中所有 CLI 與 `WORKFLOW_INDEX.md` 所列一致

---

## 9. 狀態更新

| 日期 | 狀態 | 說明 |
|------|------|------|
| 2026-06-10 | implementer done | README 與 state 檔撰寫完成 |
| 2026-06-10 | Reviewer pending | 待 Reviewer 驗收 |

---

## 10. 交叉引用

- **上游**: W7-T4（95% blueprint v2）、W8-T4（NT Shadow）、W9-T1~T4（NT implementation）、W10-T1（CI Suite）
- **同波**: W10-T2（Metrics）、W10-T3（Audit）— 本 README 提及但不依賴
- **下游**: 未來 Wave 11/12+ 實作票可能引用本 README 作為 onboarding 入口

---

*W10-T4 State · agent-and-non-tabular-lines-readme-v1 · 2026-06-10*
