# SPEC — Repo Tool Catalog v1 (戰線 A · Week 2 · A-W2-1)

> **定位**：repo pipeline 工具（index / graph / embed / retrieve）的**單一真相**；供 A-W2-2 Selector / Executor 讀取。  
> **不取代**：Phase 8.8 `tool_catalog_v1`（orchestration 有限工具池 · `core/tool_catalog.py`）。

---

## 1. 儲存與載入

| 項 | 路徑／模組 |
|----|------------|
| Wire + seed | `shared/schemas/repo_tool_catalog_v1.json` |
| Pydantic | `core/schemas/repo_tool_catalog.py` |
| 讀取 API | `core/repo_tool_catalog.py` |
| DB（可選、未接線） | `Departments/05_Data_Vault/db/012_repo_tool_catalog_schema.sql` |

v0.1 loader **僅**讀 JSON；`repo_tool_catalog` 表供日後 seed／熱更新。

---

## 2. Catalog 根欄位

| 欄位 | 型別 | 說明 |
|------|------|------|
| `schema_version` | `literal` | 固定 `repo_tool_catalog_v1` |
| `catalog_revision` | `string` | 目錄修訂號（如 `a-w2-1.0.0`） |
| `tier` | `literal` | 固定 `week2_a_v0.1` |
| `tools` | `RepoToolSpec[]` | 3–32 條，tool_id 唯一 |

---

## 3. RepoToolSpec 欄位

| 欄位 | 型別 | 說明 |
|------|------|------|
| `tool_id` | `string` | 唯一 id，`^[a-z][a-z0-9_]{2,48}$` |
| `human_name` | `string` | 顯示名 |
| `description` | `string` | 人讀說明 |
| `intent_tags` | `string[]` | 任務／意圖標籤（Selector 篩選） |
| `input_schema` | `JsonSchemaShape` | `required` + `properties` + `examples` |
| `output_schema` | `JsonSchemaShape` | 同上 |
| `preconditions` | `ToolPrecondition[]` | 前置（env / artifact / db / qdrant / job_status） |
| `cost_class` | enum | `trivial` \| `low` \| `medium` \| `high` |
| `latency_class` | enum | `interactive` \| `batch_seconds` \| `batch_minutes` |
| `failure_modes` | `string[]` | 常見失敗語意 |
| `structured_error_refs` | `StructuredErrorRef[]` | `code` + `message_hint` + `retryable` |
| `side_effects` | `ToolSideEffects` | DB／artifact／外部 API |
| `observability_fields` | `string[]` | trace 建議欄位 |
| `example_calls` | `object[]` | 簡短調用示例 |
| `usage_notes` | `string` | 備註 |
| `enabled` | `bool` | 是否可被 Selector 選中 |
| `implementation_ref` | `string` | Executor 模組提示（catalog **不**執行） |

### ToolPrecondition

| 欄位 | 型別 |
|------|------|
| `kind` | `env` \| `artifact` \| `db_table` \| `db_row` \| `qdrant_collection` \| `job_status` |
| `key` | `string` |
| `description` | `string` |
| `required` | `bool` |

---

## 4. 讀取 API

```python
from core.repo_tool_catalog import list_tools, get_tool_spec, load_repo_tool_catalog

# 全表
out = list_tools()  # {ok, tools, count, catalog_revision, ...}

# 依 intent 篩選
out = list_tools(intent_tag="smoke")

# 單條
out = get_tool_spec("repo_index_v1_job")  # {ok, tool, message}
```

回傳皆為 **`dict`**（`ok` / `message`）；`tool`／`tools` 與 Pydantic dump 對齊。

---

## 5. 已登錄工具（v0.1 seed）

| tool_id | 用途 |
|---------|------|
| `repo_index_v1_job` | manifest + DB job |
| `code_graph_builder_v0_1` | graph.v0.json |
| `repo_chunks_embed_v1` | Qdrant repo_chunks |
| `repo_code_retrieve_smoke` | 語意檢索 smoke |
| `repo_graph_manifest_read` | 只讀 artifact |

---

## 6. 驗收

```text
python -m unittest tests.test_repo_tool_catalog -v
python -m unittest tests.test_tool_layer_schemas -v
```

Week 1 smoke 路徑**未**修改 index／graph／retrieve 實作。

---

## 7. A-W2-2+ 使用建議（未實作）

1. **Selector**：`list_tools(intent_tag=...)` → 依 `preconditions` 與 runtime 狀態（job 完成、Qdrant 可達）過濾 eligible。  
2. **Executor**：`get_tool_spec(tool_id)` → 讀 `implementation_ref` 派發；寫 trace 用 `observability_fields`。  
3. **錯誤對照**：執行失敗時映射 `structured_error_refs[].code`。  
4. **與 Phase 8.8 並存**：orchestration 任務仍用 `tool_catalog_v1`；repo 任務用 `repo_tool_catalog_v1`。
