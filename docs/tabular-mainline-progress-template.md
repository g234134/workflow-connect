# Tabular 主線進度更新 — 模板

> **用途**：複製本檔或另存為 `docs/tabular-mainline-progress-update-YYYY-MM-DD.md`，填入各節內容。  
> **更新時機**：僅在 Tabular 主線有**實質變更**時更新（見文末「更新頻率」）— **無需**每日。  
> **Authority**：`docs/TABULAR_MVP_SSOT.md` · `docs/tabular-mainline-e2e-verification-v1.md`

---

## 如何使用

1. 複製下方「骨架」到新檔 `docs/tabular-mainline-progress-update-<date>.md`
2. 從以下来源抽取內容：
   - `docs/tabular-cleaning-automation-manifest-v1.md`（缺口 / B 類 backlog）
   - `docs/tabular-mainline-e2e-verification-report-v1.md`（最新 E2E verdict）
   - `cases/index.json` · `cases/<case>/automation_state.json` · `reports/automation_run_log.json`
   - `04_Workflows/00_Agent_Work_Progress.md` 末尾 Tabular 相關戰報
3. 在 `docs/TABULAR_MVP_SSOT.md` §9、`docs/C2-P2_RUNBOOK.md` §3.4 更新「最新進度」連結（或保留指向本模板 + 最新 dated 檔）
4. 在 `04_Workflows/00_Agent_Work_Progress.md` **末尾 append** 一條戰報（含 `ts` · `author` · `summary` · `link`）

---

## 骨架（複製起點）

```markdown
# Tabular 主線進度更新 — YYYY-MM-DD

> **Role**: Tabular Mainline Progress Reporter
> **Template**: docs/tabular-mainline-progress-template.md

---

## 摘要（一句話）

<!-- 一句話：主線目前可不可用、E2E verdict、是否 closure -->

---

## 主線狀態總覽

| 維度 | 狀態 | 依據 |
|------|------|------|
| **E2E 就緒** | <!-- true / true_with_known_limits / blocked --> | |
| **Regression 錨點** | | |
| **Allowlist 標準案** | | |
| **Prod / closure** | **未宣稱** | Batch 1 hard_no |

**最新 case 快照**（`cases/index.json` · `updated_at:`）：

| Case | `automation_status` | Cleaning | `delivery_ready` | 備註 |
|------|---------------------|----------|------------------|------|
| `demo_phase` | | | | |
| `sampleco/2026-0001` | | | | |

---

## 已完成項目

### Control plane v<!-- -->1
<!-- 狀態 · 關鍵 CLI · 文檔 -->

### Unified driver v<!-- -->1
<!-- 狀態 · driver 步驟 · run log -->

### CP-A / CP-B resume v<!-- -->1
<!-- HITL CLI · resume 語意 -->

### Delivery approve v<!-- -->1
<!-- approve CLI · delivery_ready 規則 -->

### 雙案 E2E 驗證
<!-- checklist / report · verdict -->

---

## 已知限制 / 待辦

<!-- manifest §3–5 · E2E report · known_limits -->

---

## 下一步建議（3–5 項）

<!-- 優先對齊 manifest B4/B6/B7 等 -->

| # | 項目 | 類別 | 預期效果 |
|---|------|------|----------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

**回歸基準**：

\`\`\`bash
python scripts/run_demo_phase_regression_smoke.py --json
\`\`\`

---

## 修訂

| 版本 | 日期 | 說明 |
|------|------|------|
| vN | YYYY-MM-DD | |
```

---

## Progress 戰報條目模板

在 `04_Workflows/00_Agent_Work_Progress.md` **末尾 append**：

```yaml
ts: YYYY-MM-DD
author: Tabular Mainline Progress Reporter
summary: <!-- 1–2 句：本輪主線變更或狀態快照 -->
link: docs/tabular-mainline-progress-update-YYYY-MM-DD.md
```

---

## 更新頻率建議

| 情境 | 是否更新 |
|------|----------|
| control plane / driver / HITL / approve 程式或 schema 變更 | **是** — 跑 E2E 後更新 |
| 新增 allowlist case 或 cleaning profile | **是** |
| 雙案 E2E 重新執行且 verdict 變化 | **是** |
| 僅 supporting rails（GA / CI / governance）變更 | **否** — 除非影響 Tabular 主鏈 |
| 無主線 code/doc 變更 | **否** — 無需每日 |

**最小驗證**（有實質變更時）：

```bash
python scripts/run_demo_phase_regression_smoke.py --json
# 深度：docs/tabular-mainline-e2e-verification-v1.md
```

---

*Tabular mainline progress template · doc-only · NOT PROD GATE*
