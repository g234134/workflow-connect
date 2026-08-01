# W9-T1 State: non-tabular-routing-catalog-v1

> **Ticket**: W9-T1  
> **Title**: non-tabular-routing-catalog-v1  
> **Type**: Architect + Scribe / Design & Structure  
> **Status**: implementer done · pending Reviewer  
> **Created**: 2026-06-10  
> **Upstream**: W8-T4 (non-tabular-shadow-flow-blueprint-v1)

---

## §1 驗收條件 (AC)

### AC-1: 規格文件
- [x] `docs/non-tabular-routing-catalog-v1.md` 存在且可讀
- [x] 包含 NT-A (Document Processing) 案型描述
- [x] 包含 NT-B (Log Analysis) 案型描述
- [x] 定義 routing 欄位：`family`, `task_type`, `case_profile`, `intake_schema`, `target_tools`
- [x] 與 Tabular routing catalog 的差異對照表

### AC-2: Catalog 草稿
- [x] `routing/non_tabular_routing_catalog_v1.yaml` 存在且語法正確
- [x] 包含至少 1 個 NT-A 示例 (`non-tabular.document.clean_and_annotate`)
- [x] 包含至少 1 個 NT-B 示例 (`non-tabular.log.parse_and_summarize`)
- [x] 每條目包含：`task_type`, `description`, `intake_pattern`, `risk_tier`, `default_tools`, `notes`

### AC-3: State 檔
- [x] `04_Workflows/tickets/W9-T1-non-tabular-routing-catalog-v1_state.md` 存在（本檔）

### AC-4: 索引更新
- [x] `04_Workflows/WORKFLOW_INDEX.md` 新增 W9-T1 條目
- [x] `docs/WAVE_PROGRESS_DASHBOARD.md` 新增 Wave 9 區塊與 W9-T1 行

---

## §2 完成摘要

### 新建檔案

| 路徑 | 類型 | 說明 |
|------|------|------|
| `docs/non-tabular-routing-catalog-v1.md` | Spec | NT-A/NT-B 案型規格、routing 欄位定義、差異對照 |
| `routing/non_tabular_routing_catalog_v1.yaml` | Catalog | 3 個 task_type entries (NT-A, NT-B, generic) |
| `04_Workflows/tickets/W9-T1-non-tabular-routing-catalog-v1_state.md` | State | 本檔 |

### 修改檔案

| 路徑 | 變更 |
|------|------|
| `04_Workflows/WORKFLOW_INDEX.md` | 新增 §1.12 Wave 9 — Non-Tabular Routing Catalog |
| `docs/WAVE_PROGRESS_DASHBOARD.md` | 新增 ## Wave 9 區塊 |

### 兩個 Exemplar Task Type

| 案型 | Task Type | 描述 |
|------|-----------|------|
| NT-A | `non-tabular.document.clean_and_annotate` | 混合文件文字提取與結構化 |
| NT-B | `non-tabular.log.parse_and_summarize` | 日誌解析與異常偵測 |

---

## §3 Skeleton / Placeholder

### 本票明確標為 skeleton（無實際 glue）

| 項目 | 狀態 | 備註 |
|------|------|------|
| `target_tools` | Symbolic names only | 實際工具實作在 W9-T3 |
| `routing/intake_to_non_tabular_glue.py` | 未建立 | 規劃於 W9-T4 |
| `cases/docu-corp/` | 未建立 | 規劃於 W9-T5 |
| `cases/log-analytics-co/` | 未建立 | 規劃於 W9-T6 |
| Decision rules 擴展 | 未實作 | 規劃於 W9-T2 |

---

## §4 驗證證據

### 語法驗證

```bash
# YAML 語法檢查
python -c "import yaml; yaml.safe_load(open('routing/non_tabular_routing_catalog_v1.yaml'))"
# 結果: ok (無例外)
```

### 文件可讀性

```bash
# 檔案存在確認
ls -la docs/non-tabular-routing-catalog-v1.md
ls -la routing/non_tabular_routing_catalog_v1.yaml
ls -la 04_Workflows/tickets/W9-T1-non-tabular-routing-catalog-v1_state.md
# 結果: 三檔皆存在
```

---

## §5 阻塞與風險

| 項目 | 狀態 | 說明 |
|------|------|------|
| 與 Tabular catalog 欄位對齊 | 已記錄 | 見 spec §4 差異對照表 |
| Risk tier 閾值 | placeholder | 實際閾值需 W9-T2 decision rules 確認 |
| Tool 實作路徑 | 未定 | W9-T3 將定義實際模組路徑 |

---

## §6 下一步

| 票號 | 描述 | 依賴 |
|------|------|------|
| W9-T2 | Decision rules v2 擴展 non-tabular logic | 本檔 catalog |
| W9-T3 | Tool catalog skeleton | 本檔 `default_tools` |
| W9-T4 | Glue layer route planner | 本檔 routing 欄位 |
| W9-T5 | Fixture docu-corp | 本檔 NT-A spec |
| W9-T6 | Fixture logs-co | 本檔 NT-B spec |

---

## §7 Work Report 參照

- 任務: W9-T1 non-tabular-routing-catalog-v1
- 角色: Architect + Scribe
- 日期: 2026-06-10
- 變更檔案: 3 新建 + 2 修改
- Skeleton: `target_tools` 為 symbolic names
- Placeholder: fixtures、glue、decision rules 擴展
- 驗證: YAML 語法通過、檔案存在確認
- 阻塞: 無
- 下一步: W9-T2~T6 依序實作

---

*W9-T1 State · 2026-06-10*
