# P8.6–8.8 Runtime Inspect · Catalog → Selector → Executor (dry_run) v1

> **Ticket**: `P868-W2-runtime-inspect-catalog-selector-executor-v1` · Wave 2 #4 · 2026-07-13  
> **Goal**：在既有 WB-T1／WB-T2 contract 與 W3-TL／W9-T3 實作之上，交付**只讀** runtime 配線 inspect：catalog 碰撞檢查 → selector `plan_only` → executor `dry_run`。

---

## Non-claims

| 聲明 | 狀態 |
|------|------|
| = prod browser / Playwright | **否** |
| = Wave 4 Web UI | **否** |
| = Phase closure / Dashboard % authorize | **否** · `apply_phase_pct=false` |
| = DarkOps / 暗部 `core/tool_executor` | **否** · 僅戰車根 Tabular／NT |
| = `execute` subprocess／寫 outbox | **否** · 僅 `dry_run` |
| = 重寫 catalog／selector／executor 本體 | **否** · 只配線既有 API |

---

## 配線步驟

| Step | Phase | 行為 |
|------|-------|------|
| 1 Catalog | P8.6 | 讀 `tabular_tool_catalog_v1.json` + `non_tabular_tool_catalog_v1.json`；`tool_id` 交集必須為空 |
| 2 Selector | P8.7 | `select_tabular_tools(case_dir, task_type)`；強制 `plan_only=true`；可選 NT stub |
| 3 Executor | P8.8 | 對首個 candidate `execute_tabular_tool(..., dry_run=True)`；不 spawn、不寫盤 |
| 4 Allowlist | P8.8 | 附上 WB-T2 case × `execution_mode` 矩陣摘要（只讀常數） |

---

## API / CLI

```text
delivery.p868_runtime_inspect_v1.inspect_p868_runtime(case_ref, task_type=..., ...) → dict
python scripts/inspect_p868_runtime_v1.py --case-ref demo_phase --format json
python -m unittest tests.test_p868_runtime_inspect_v1 -v
```

頂層穩定鍵：`ok` · `schema_version=p868_runtime_inspect_v1` · `read_only` · `case_ref` · `catalog` · `selector` · `executor` · `allowlist` · `non_claims`。

---

## Related

- Contract：`docs/tool-catalog-and-selector-contract-v1.md` · `docs/tool-executor-and-sandbox-safety-contract-v1.md`
- Tabular：`tools/tabular_tool_selector.py` · `tools/tabular_tool_executor.py`
- NT stub：`tools/non_tabular_tool_selector_v1.py`
