# W11-T4 · agent-and-non-tabular-lines-readme-v2-wave10-aligned

> **Ticket**: W11-T4 · agent-and-non-tabular-lines-readme-v2-wave10-aligned  
> **Type**: Documentation (Architect + Scribe)  
> **Date**: 2026-06-10  
> **Status**: implementer done

---

## 任務摘要

在 v1 README 基礎上，更新整體說明到 Wave 10 對齊狀態：

- 納入：W10-T1 CI suite、W10-T2 metrics、W10-T3 audit、W10-T4 README 自身演進
- 為 Wave 11+ 留出清楚的 future work 區

---

## 已讀文件（Context - Source Driven）

### 必讀（P0）
- [x] `engineering-contract.mdc` — 工程執行合約條款
- [x] `AGENTS.md` — 大唐副官接戰守則
- [x] `docs/agent-and-non-tabular-lines-readme-v1.md` — v1 基礎文件
- [x] `docs/agent-lines-ci-suite-v1.md` — W10-T1 CI Suite
- [x] `docs/agent-lines-metrics-and-monitoring-v1.md` — W10-T2 Metrics
- [x] `docs/agent-lines-audit-quickview-v1.md` — W10-T3 Audit
- [x] `docs/agent-standard-line-governance-view-v2.md` — 治理觀點 v2
- [x] `docs/non-tabular-shadow-flow-blueprint-v1.md` — Non-Tabular 藍圖 v1
- [x] `docs/non-tabular-orchestrator-preview-v1.md` — NT Preview v1
- [x] `docs/ninety-five-percent-automation-blueprint-v2.md` — 95% 藍圖 v2
- [x] `04_Workflows/WORKFLOW_INDEX.md` — 工作流索引
- [x] `docs/WAVE_PROGRESS_DASHBOARD.md` — Wave 進度儀表板

---

## 輸出檔案

### 主要交付
- [x] `docs/agent-and-non-tabular-lines-readme-v2.md` — 更新版 README（保留 v1）

### 索引更新
- [x] `04_Workflows/WORKFLOW_INDEX.md` — 新增 W11-T4 條目（§1.17 → §1.18）
- [x] `docs/WAVE_PROGRESS_DASHBOARD.md` — 新增 Wave 11 段與 W11-T4 行

---

## 內容更新要點檢核

### §1 Overview 更新
- [x] Tabular v2 狀態明確寫出：multi-fixture / run / HITL / metrics / audit / CI helper
- [x] Non-Tabular v1 狀態明確寫出：routing / decision / tool selector / preview
- [x] Wave 10 欄位新增至對照表

### §4 CI / Metrics / Audit 章節
- [x] W10-T1 CI Suite 能力具體列出（CLI、產出、邊界）
- [x] W10-T2 Metrics 能力具體列出（指標清單、輸出檔案、邊界）
- [x] W10-T3 Audit 能力具體列出（CLI、材料來源、邊界）
- [x] 「典型開發者流程」小節新增（PR → CI → metrics → audit quickview）

### §6 Roadmap 章節
- [x] 引用 blueprint v2 / non-tabular blueprint v1
- [x] Wave 11/12 方向對齊（不必拆票，僅方向性規劃）
- [x] 藍圖參考索引新增

### 其他更新
- [x] 「系統現狀一句話摘要」段落新增（文件頂部）
- [x] 核心文件索引更新（加入 W10-T2/T3/T4 文件）
- [x] 核心命令速查更新（加入 W10-T1/T2/T3 CLI）

---

## v2 相對 v1 主要差異

| 差異項 | v1 | v2 |
|--------|-----|-----|
| **版本標記** | v1.0 | v2.0 Wave 10 對齊 |
| **票號** | W10-T4 | W11-T4 |
| **系統現狀摘要** | 無 | 新增「一句話摘要」段落 |
| **Wave 10 內容** | 僅標註 W10-T1/T2/T3「待實作」 | 完整納入 W10-T1/T2/T3 能力 |
| **CI 章節** | §4.1 框架 | W10-T1 完整 CLI、產出、邊界 |
| **Metrics 章節** | §4.2「規劃中」 | W10-T2 完整指標、schema、輸出 |
| **Audit 章節** | §4.3「規劃中」 | W10-T3 完整 CLI、JSON shape、範例 |
| **典型開發者流程** | 無 | 新增 §4.4 完整流程圖 |
| **Wave 11+ Roadmap** | 粗略方向 | 結構化表格 + 藍圖引用 |
| **文件索引** | v1 列表 | 更新加入 W10-T2/T3/T4 |
| **命令速查** | v1 命令 | 加入 W10-T1/T2/T3 CLI |

---

## 驗證檢查

### 文件存在性
```bash
# 檢查 v2 README 存在
ls -la docs/agent-and-non-tabular-lines-readme-v2.md

# 檢查章節完整性（預期 6 個 § 章節 + 附錄）
grep "^## §" docs/agent-and-non-tabular-lines-readme-v2.md | wc -l
# 預期輸出: 6

# 檢查 Wave 10 關鍵字
grep -c "W10-T1\|W10-T2\|W10-T3\|Wave 10" docs/agent-and-non-tabular-lines-readme-v2.md
# 預期輸出: >10

# 檢查「典型開發者流程」存在
grep -c "典型開發者流程\|Typical Developer Flow" docs/agent-and-non-tabular-lines-readme-v2.md
# 預期輸出: >=1
```

### 索引更新驗證
```bash
# WORKFLOW_INDEX 檢查
grep -c "W11-T4\|readme-v2" 04_Workflows/WORKFLOW_INDEX.md

# WAVE_PROGRESS_DASHBOARD 檢查
grep -c "W11-T4\|Wave 11" docs/WAVE_PROGRESS_DASHBOARD.md
```

---

## 阻塞與風險

| 風險 | 狀態 | 說明 |
|------|------|------|
| W10-T2 Metrics 實作變更 | 低 | v2 文件已預留彈性描述，若 schema 變更需追蹤更新 |
| W10-T3 Audit 欄位變更 | 低 | JSON shape 以 W10-T3 文件為準，v2 已引用 |
| Non-Tabular W11+ 方向 | 中 | 依賴 `non-tabular-shadow-flow-blueprint-v1.md`，若藍圖修訂需同步 |

**無阻塞** — 本票純文檔，無程式碼變更，無依賴阻塞。

---

## 工時與成本

| 項目 | 估算 |
|------|------|
| 閱讀 11 份上游文件 | ~30 min |
| 撰寫 v2 README | ~45 min |
| 索引更新（2 檔） | ~10 min |
| Ticket state 文件 | ~10 min |
| **總計** | ~95 min |

---

## Work Report（本輪結構）

### §1 變更檔案
1. `docs/agent-and-non-tabular-lines-readme-v2.md` — 新建（v2 主文件）
2. `04_Workflows/WORKFLOW_INDEX.md` — 修改（新增 W11-T4 條目）
3. `docs/WAVE_PROGRESS_DASHBOARD.md` — 修改（新增 Wave 11 段）
4. `04_Workflows/tickets/W11-T4-agent-and-non-tabular-lines-readme-v2_state.md` — 新建（本檔）

### §2 Skeleton
無 — 本文檔票無程式碼 skeleton。

### §3 Placeholder
無 — 本文檔票無未實作 placeholder。

### §4 驗證證據
- 文件存在性：`ls -la` 命令驗證（見「驗證檢查」節）
- 章節完整性：`grep "^## §"` 預期 6 章節
- 內容覆蓋：`grep` Wave 10 關鍵字預期命中

### §5 阻塞
無。

### §6 下一步
1. Reviewer 審閱 v2 README 內容準確性
2. 若 W10-T1/T2/T3 實作細節變更，追蹤更新 v2 文件
3. Wave 11 實作啟動時，依 v2 Roadmap 開票

### §7 Override 與留痕
無 — 無權威衝突或邊界覆寫。

---

## 相關 Ticket

| 上游 | 關係 |
|------|------|
| W10-T4-agent-and-non-tabular-lines-readme-v1 | v2 基礎文件 |
| W10-T1-integrate-agent-lines-into-ci-v1 | v2 §4.1 CI 內容來源 |
| W10-T2-agent-lines-metrics-and-monitoring-v1 | v2 §4.2 Metrics 內容來源 |
| W10-T3-agent-lines-audit-quickview-cli-v1 | v2 §4.3 Audit 內容來源 |
| W8-T4-non-tabular-shadow-flow-blueprint-v1 | v2 §3/§6 Non-Tabular 內容來源 |
| W7-T4-update-ninety-five-percent-blueprint-and-skills-wave7-v1 | v2 §6 Roadmap 參考 |

---

*W11-T4 State · implementer done · 2026-06-10 · Architect + Scribe*
