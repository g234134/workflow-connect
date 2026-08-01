# Routing Policy Guide — v1 (B-F3)

> **Ticket**: B-F3 · Routing Policy 文檔＋可調參 v1  
> **Config**: `config/routing_policy.yaml`  
> **Loader**: `python -m core.routing_policy_loader validate|resolve-route`  
> **Catalog authority**: B-F1 Gov Tool Registry (`skills/gov_cards/*.json`)

---

## 1. 緣起

Wave B 已交付 eval export/report、trace query、eval–trace correlate、wf status summary、KB index bootstrap/rag smoke 等 CLI 工具，並在 **B-F1 Skill Catalog** 中以 `tool_id` 登記。

B-F3 在此之上新增 **Routing Policy 配置層**：用一份 YAML 描述「哪些 catalog 工具以何順序組成 Wave B 路由」，使 Wave C 商業流程可 **只改 config** 調整 routing，而不必改 Python 執行邏輯。

**本票刻意不做**：不接 ask/selector 主線、不改既有 observability/KB CLI 預設行為、不接入 prod selector gate。實際執行仍由 catalog 中各工具的既有 CLI/module 負責；policy 層只負責 **載入、驗證、查詢**。

### 1.1 架構邊界（config 層 vs 執行層）

- **Config 層**（`config/routing_policy.yaml`）：**描述** routes——哪些 catalog `tool_id`、以何順序編排、`enabled` / `review_required` 等 metadata。
- **執行層**：各 catalog 工具對應的既有 CLI（eval export、trace query、kb bootstrap 等）；**本票不改 CLI 行為或預設參數**。
- **Policy 載入層**（`core/routing_policy_loader.py`）：載入 config、驗證與 catalog 對齊、解析 route → `tool_ids` 列表。

**Routing Policy v1 尚未接入 prod selector 或 prod gate**；目前僅用於 **描述／驗證／解析** Wave B 的工具編排。未來 Wave C 若要把 policy 接到 prod selector（含 `core/ask_rag_selector.py`），须**另開票**更新 `config/routing_policy.yaml`、`core/routing_policy_loader.py` 及 `kb.index.selector_gate` 卡面接線。

---

## 2. 檔案與命令

| 路徑 | 用途 |
|------|------|
| `config/routing_policy.yaml` | Routing Policy v1 主配置 |
| `core/routing_policy_loader.py` | 載入 / 驗證 / 查詢 API + CLI |
| `docs/ROUTING_POLICY_GUIDE.md` | 本指南 |
| `docs/SKILL_CATALOG_OVERVIEW.md` | Catalog 索引 + Routing Policy 引用說明 |

```bash
# 驗證 policy（exit 0 = ok）
python -m core.routing_policy_loader validate

# 查詢某 route 的 tool 步驟（示範下游如何讀 config）
python -m core.routing_policy_loader resolve-route --route-id wave_b.eval_report
```

---

## 3. Config 結構

### 3.1 頂層欄位

| 欄位 | 必填 | 說明 |
|------|------|------|
| `schema_version` | 是 | 固定 `"routing_policy_v1"` |
| `default_env` | 是 | 預設環境標籤（如 `"dev"`）；route 可覆寫 |
| `tools` | 是 | 本 policy 允許引用的 catalog 工具子集 + metadata |
| `routes` | 是 | 具名路由：有序 tool 步驟 |

### 3.2 `tools` 區塊

每筆工具 **必須** 使用 B-F1 Catalog 中已存在的 `tool_id`（見 `docs/SKILL_CATALOG_OVERVIEW.md`）。

| 欄位 | 說明 |
|------|------|
| `tool_id` | Gov catalog ID，格式 `<domain>.<action>.<target>` |
| `enabled` | `true` 才允許出現在 `routes` 步驟中 |
| `review_required` | 營運提示：變更該工具 routing 前是否建議人工 review |

**範例**（skeleton 工具僅作 metadata 登記，預設禁用）：

```yaml
- tool_id: "kb.index.selector_gate"
  enabled: false
  review_required: true
```

`kb.index.selector_gate` 在 catalog 中標記為 **skeleton/reference**（`decide_kb_index_tool_gate` 純函式參考卡）。Wave C 以前不得把它放進 route steps；本 config 僅保留 `enabled: false` 供日後 Wave C 接 prod gate 時參考。

### 3.3 `routes` 區塊

| 欄位 | 說明 |
|------|------|
| `route_id` | 穩定路由名（如 `wave_b.eval_report`） |
| `description` | 人類可讀說明 |
| `env` | 環境標籤（與 `default_env` 對齊或覆寫） |
| `steps` | 有序步驟列表 |

每個 step：

| 欄位 | 說明 |
|------|------|
| `kind` | v1 僅支援 `"tool"` |
| `tool_id` | 必須同時存在於 **catalog** 與本檔 **`tools`** 區塊，且 `enabled: true` |

---

## 4. v1 內建路由

| route_id | 用途 | steps（tool_id 順序） |
|----------|------|------------------------|
| `wave_b.eval_report` | eval 匯出 → 報表 → wf 總覽 | `obs.eval.export` → `obs.eval.report` → `obs.wf.status_summary` |
| `wave_b.kb_index_bootstrap` | KB index bootstrap → RAG smoke | `kb.index.bootstrap` → `kb.index.rag_smoke` |

---

## 5. 如何新增或調整路由

1. **選 tool_id**：僅從 `python -m skills.gov_tool_registry list` 或 `docs/SKILL_CATALOG_OVERVIEW.md` 選取；禁止自創 ID。
2. **加入 `tools`**：新工具先在 `tools` 區塊宣告 `enabled` / `review_required`。
3. **編排 `routes`**：在 `steps` 中按執行順序列出 `kind: tool` + `tool_id`。
4. **跑驗證**：`python -m core.routing_policy_loader validate` 必須 `ok=True`。
5. **下游讀取**（Wave C）：呼叫 `resolve_route_tool_ids(policy, route_id)` 或 CLI `resolve-route`，再依回傳 `tool_ids` 調度 catalog CLI。

### 5.1 避免誤用 skeleton / composite

| 類型 | catalog 範例 | routing policy 規則 |
|------|--------------|---------------------|
| **skeleton** | `kb.index.selector_gate` | 可出現在 `tools`（通常 `enabled: false`）；**禁止**出現在 `routes.steps` |
| **composite** | `obs.eval.triage` | **禁止**直接放入 route；改列底層工具 `obs.eval.correlate` + `obs.trace.query` |

`obs.eval.triage` 是 composite 卡，無獨立 module；triage 工作流應展開為 correlate（`--format triage-md`）與 trace query（`--format triage`），而非在 policy 中引用 composite ID。

---

## 6. Loader API

```python
from core.routing_policy_loader import (
    load_routing_policy,
    validate_routing_policy,
    get_route,
    resolve_route_tool_ids,
    get_default_wave_b_eval_route_tool_ids,
)

policy = load_routing_policy()
result = validate_routing_policy(policy)  # ok, total_tools, total_routes, errors
route = get_route(policy, "wave_b.eval_report")
steps = resolve_route_tool_ids(policy, "wave_b.eval_report")  # tool_ids list
default_eval = get_default_wave_b_eval_route_tool_ids()  # 載入預設 config 的 eval route
```

`validate_routing_policy` 可選 `registry=` 傳入 catalog cards 或 `build_registry_context()` 結果，以檢查 skeleton/composite/disabled 工具是否誤入 routes。

回傳形狀：`{ok, message, total_tools, total_routes, errors}`；`errors` 為 `{code, message, ...}` 列表。

---

## 7. 與 B-F1 / Wave B Execution Plan 的關係

- **B-F1** 定義「有哪些工具、如何驗證」→ `skills/gov_cards/*.json` + `gov_tool_registry validate`。
- **B-F3** 定義「Wave B 場景下工具如何編排」→ `config/routing_policy.yaml` + `routing_policy_loader validate`。
- **Wave B Execution Plan**（`docs/WAVE_B_EXECUTION_PLAN.md`）描述各票交付的 CLI；policy 不取代該計畫，只提供可調參編排層。

實際 CLI 入口、verify_command 仍以 catalog 卡為準；修改 routing **不會** 自動改變 observability 或 KB pipeline 的 argparse 預設值（留給 Wave C 接線票）。

---

## 8. 驗證清單（Implementer / Reviewer）

```bash
python -m core.routing_policy_loader validate
python -m unittest tests.test_routing_policy_loader -v
python -m skills.gov_tool_registry validate
python -m unittest tests.test_gov_tool_registry -v
```

---

## 9. Wave C / 後續小票留項

- ask / RAG selector 主線讀取 policy（如 `core/ask_rag_selector.py`）
- prod `kb.index.selector_gate` 與 env 開關接線
- CI workflow 加入 `routing_policy_loader validate`
- 多 env（staging/prod）route 分叉與 composite step kind
