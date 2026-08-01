# Toolchain Local Gaps Quickview v1 (WC-C1-01)

> **定位**：developer-facing、**僅本地執行** 的 toolchain gaps 只讀聚合 CLI。  
> **非** PR required check · **非** CI gate · **非** SLA metric。

**Schema**：`toolchain_local_gaps_v1`  
**CLI**：`scripts/run_toolchain_local_gaps_quickview.py`  
**交叉引用**：WB-T4 health dashboard · WC-PRE-02～05 runtime gaps

---

## 1. Purpose

工程師在開新票、查 toolchain 狀態或盤點 impl gap 時，一條命令即可看到：

| Section | 來源 | 說明 |
|---------|------|------|
| `selector_plan_only` | WC-PRE-02 | tabular / non-tabular selector in-process plan 探測 |
| `executor_timeout_contract` | WC-PRE-03 | executor subprocess `timeout=600` 與 `subprocess_timeout` 契約（mock 探測） |
| `audit_investigation` | WC-PRE-04 | 可選 `--case-ref` 的 investigation gaps 摘要 |
| `smoke_matrix_dry_run` | WC-PRE-05 | smoke matrix `--list --dry-run` 摘要 |
| `toolchain_health_embed` | WB-T4 | 可選 `--include-health-dashboard` 嵌入 health dashboard 摘要 |

---

## 2. CLI usage

```bash
# 預設 dry-run + text summary
python scripts/run_toolchain_local_gaps_quickview.py

# JSON 報告（AC-1）
python scripts/run_toolchain_local_gaps_quickview.py --format json

# 含 audit investigation gaps（AC-5）
python scripts/run_toolchain_local_gaps_quickview.py --case-ref demo_phase --format json

# 嵌入 WB-T4 health dashboard 摘要（AC-10）
python scripts/run_toolchain_local_gaps_quickview.py --include-health-dashboard --format json

# 寫入 artifacts
python scripts/run_toolchain_local_gaps_quickview.py --write --format json
```

### Flags

| Flag | Default | 說明 |
|------|---------|------|
| `--dry-run` / `--no-dry-run` | `true` | 只讀探測；不執行長時間 subprocess |
| `--format` | `text` | `json` 或 `text`（text 由 JSON 投影，不重寫各工具邏輯） |
| `--case-ref` | *(none)* | 傳遞給 audit investigation；無值時 section `status=skipped` |
| `--include-health-dashboard` | `false` | 嵌入 WB-T4 dry-run 摘要 |
| `--write` | `false` | 寫入 `artifacts/toolchain/toolchain_local_gaps.latest.{json,md}` |
| `--output-dir` | `artifacts/toolchain` | artifact 輸出目錄 |
| `--repo-root` | repo root | 可選 repo 根覆寫 |

---

## 3. JSON schema (`toolchain_local_gaps_v1`)

### 3.1 Top-level

| Field | Type | 說明 |
|-------|------|------|
| `schema_version` | `"toolchain_local_gaps_v1"` | 固定 |
| `ok` | bool | 所有 section `ok=true` 時才 true |
| `gate_class` | `"optional"` | 固定；非 blocking gate |
| `blocks_mainline` | `false` | 固定 |
| `dry_run` | bool | CLI dry-run 模式 |
| `generated_at` | ISO8601 | 生成時間 |
| `case_ref` | string \| null | 可選 audit case |
| `sections` | object | 見 §3.2 |
| `toolchain_health_embed` | object | 僅 `--include-health-dashboard` 時存在 |
| `output_paths` | object | 僅 `--write` 時存在 |
| `message` | string | 人讀摘要 |

### 3.2 Section common fields

每個 section 至少含：

| Field | Type | Values |
|-------|------|--------|
| `status` | string | `ok` · `degraded` · `missing` · `skipped` |
| `ok` | bool | section 是否通過 |
| `message` | string | 人讀說明 |

### 3.3 Section-specific fields

**`selector_plan_only`**

- `tabular.plan_only` · `tabular.ok` · `tabular.selector_rule_id`
- `non_tabular.plan_only` · `non_tabular.ok` · `non_tabular.selector_rule_id`

**`executor_timeout_contract`**

- `timeout_seconds` (expect 600)
- `subprocess_timeout_message_ok`
- `mocked_probe` (true when in-process mock used)

**`audit_investigation`**

- `case_ref` · `gaps_count` · `audit_gaps_count`
- `audit_sections_found` · `top_gaps[]` · `investigation_ok`
- 無 `--case-ref`：`status=skipped` · `gaps_count=null`

**`smoke_matrix_dry_run`**

- `dry_run` · `entries_requested` · `tier_counts`
- `matrix_schema_version` · `matrix_revision`

**`toolchain_health_embed`** (optional)

- `ok` · `gate_class` · `blocks_mainline` · `dry_run`
- `schema_version` · `sections_populated` · `sections_ok`
- `aggregated_health_score` · `message`

---

## 4. Cross-references

| Ticket / Doc | 關係 |
|--------------|------|
| **WB-T4** · `docs/toolchain-health-dashboard-v1.md` | `--include-health-dashboard` 嵌入 `run_toolchain_health_dashboard.py` dry-run 摘要 |
| **WC-PRE-02** | selector `plan_only=True` in-process 探測 |
| **WC-PRE-03** | executor timeout 契約 mock 探測 |
| **WC-PRE-04** | audit investigation projection gaps 摘要 |
| **WC-PRE-05** | smoke matrix dry-run list 摘要 |
| **WC-PRE-06** | observability 治理設計稿（**未批文** · 僅參考） |
| **WC-PRE-07** | smoke matrix CI 設計稿（**blocked_on_approval** · 未實作） |

---

## 5. Must-Not-Assume（PROD/CI）

本 quickview **不得**被解讀或描述為：

1. **PR required check** 或 GitHub Actions blocking gate（含 `OG-TOOLCHAIN-HEALTH` · WC-PRE-06 僅 design_ready）。
2. **WB-T4 toolchain health dashboard** 的 blocking gate 或 MVP mainline / delivery gate 阻斷器。
3. **Smoke matrix runner** 的 mandatory CI gate（WC-PRE-07 design_draft · **禁止**改 `.github/workflows/*`）。
4. Selector / executor 已接 prod INT regression 或 MVP mainline **blocking** gate——quickview 僅報告 plan_only / timeout 契約，不驅動 execute。
5. WC-PRE-06 observability 治理升級已獲尚書省批文——`docs/toolchain-observability-governance-upgrade-v1.md` 僅作參考。
6. SLA 承諾或 production deploy 阻斷信號——`gate_class=optional` · `blocks_mainline=false` 恆定。

---

## 6. Verification

```bash
python -m unittest tests.test_toolchain_local_gaps_quickview_v1 -v
python scripts/run_toolchain_local_gaps_quickview.py --format json
python scripts/run_toolchain_local_gaps_quickview.py --case-ref demo_phase --format json
```

---

*TOOLCHAIN-LOCAL-GAPS-QUICKVIEW-v1 · WC-C1-01 · 2026-06-11*
