# Tabular 主線進度更新 — 2026-06-27

> **Role**: Tabular Mainline Progress Reporter · 可反覆更新的主線狀態快照  
> **Status**: v1 · doc-only · **非** prod gate · **非** closure 宣稱  
> **Authority**: `docs/TABULAR_MVP_SSOT.md` · `docs/tabular-cleaning-automation-manifest-v1.md` · `docs/tabular-mainline-e2e-verification-report-v1.md`  
> **Template for future updates**: `docs/tabular-mainline-progress-template.md`

---

## 摘要（一句話）

Tabular 清洗主線已接 **雙案 smoke + generic-low-risk 錨點 + lifecycle/DLQ/ZIP 工具鏈**；自動化覆蓋約 **90–95%**（operator 保留 type gate、start、CP-A/B approve、repo 外寄檔／收款）。

---

## 主線狀態總覽

| 維度 | 狀態 | 依據 |
|------|------|------|
| **E2E 就緒** | `true_with_known_limits` | `docs/tabular-mainline-e2e-verification-report-v1.md` |
| **Regression 錨點** | 雙案 smoke + generic-low-risk | `run_tabular_mainline_regression_smoke.py` · `run_mvp_mainline_regression.py -v` |
| **Allowlist 標準案** | `demo_phase` · `sampleco/2026-0001` · `internal/generic-low-risk` | `cases/index.json` · profiles 見 `cleaning_profiles_v1.py` |
| **Prod / closure** | **未宣稱** | Batch 1 `hard_no` · `GOV-PHASE-CLOSURE-FULL: NO` |
| **Governance / CI** | **未改動** | 本輪僅 Tabular 主線文檔 |

**最新 case 快照**（`cases/index.json` · `updated_at: 2026-06-27`）：

| Case | `automation_status` | Cleaning | `delivery_ready` | 備註 |
|------|---------------------|----------|------------------|------|
| `demo_phase` | `completed` | 7 → 5 · guard `ok` | **true** | regression 錨點 · CP-B auto-skip |
| `sampleco/2026-0001` | `completed` | 115 → 8 · guard `warning` | **false**（by design） | CP-B HITL 必經 · 低 accepted ratio |

---

## 已完成項目

### 1. Control plane v1

- **產物**：`cases/<case>/automation_state.json` · `scripts/manage_tabular_automation_state.py` · `scripts/tabular_automation_state_lib.py`
- **能力**：人類 `start` / `pause` / `resume` / `stop`；狀態落盤含 CP-A/B · retry · DLQ · delivery 鏡像
- **文檔**：`docs/tabular-cleaning-control-plane-v1.md` · manifest §6.1

### 2. Unified driver v1

- **產物**：`scripts/run_tabular_automation.py` · `scripts/tabular_automation_driver_lib.py`
- **能力**：讀 control state · 鏈式執行 `intake → gate → checkpoint_a → clean → report → bundle → e2e → checkpoint_b` · 寫 `reports/automation_run_log.json`
- **邊界**：allowlist only · 需 `automation_status=running`（`--dry-run` 除外）

### 3. CP-A / CP-B resume v1

- **產物**：`scripts/run_hitl_checkpoint_cli.py` · `scripts/tabular_hitl_resume_lib.py`
- **能力**：`approve-a|approve-b` + `resume-after-checkpoint` 接回 unified driver 主鏈
- **文檔**：`docs/tabular-hitl-resume-flow-v1.md`
- **E2E 期間修復**：driver CP-B 改 `write_state=True` + 統一 nested `case_ref`（`sampleco/2026-0001`）

### 4. Delivery approve v1

- **產物**：`scripts/approve_tabular_delivery.py` · `scripts/tabular_delivery_approval_lib.py` · `cases/<case>/delivery_approval.json`
- **能力**：CP-B 後結構化 `--approve` / `--reject` · 更新 signoff · `cases/index.json` · `automation_state.json` → `delivery`
- **規則**：`delivery_ready=true` 僅當 CP-B approved **且** e2e pass **且** `output_guard.status=ok`

### 5. 雙案 E2E 驗證

- **Checklist**：`docs/tabular-mainline-e2e-verification-v1.md`
- **報告**：`docs/tabular-mainline-e2e-verification-report-v1.md`
- **結果**：
  - `demo_phase`：全鏈 PASS · `delivery_ready=true` · regression smoke exit 0
  - `sampleco/2026-0001`：全鏈 PASS（profile 對齊）· CP-B HITL · `delivery_ready=false` 符合預期
- **Verdict**：`tabular_mainline_e2e_ready: true_with_known_limits`

### 6. 輔助能力（同批落地）

- **Retry / DLQ v1**：transient 3× retry · `cases/<case>/dlq/`（僅收集，不自動重跑）
- **Internal notify hook（占位）**：`scripts/tabular_internal_notify_lib.py` → `internal_notify_log.json`
- **Warning guard 策略 v1**：`scripts/tabular_warning_guard_lib.py` · manifest §1.12 · profile 驅動 `delivery_ready`
- **Tool-executor hook（占位）**：`scripts/tabular_tool_executor_hook_lib.py` · `--use-tool-executor` stub
- **運營只讀**：`scripts/tabular_ops_summary.py` · `--case-id` / `--all` / `--json`

---

## Warning guard 策略示例（sampleco · by design）

`sampleco/2026-0001` 為 **warning guard case** 標準示例：

| 信號 | 值 | 策略解讀 |
|------|-----|----------|
| `warning_guard_profile` | `sampleco` | 邊際品質 regression fixture |
| `output_guard.status` | `warning` | 115→8 · ratio 0.0696 < 0.5 閾值 |
| `checkpoint_b_status` | `approved`（人工） | CP-B HITL 必經 · 不可 auto-skip |
| `delivery_ready` | **false** | 策略 fail-closed · 即使 `--approve` 亦 false |
| `partial_ready` | **true** | 全鏈可 PASS · 產物僅 internal use |
| `internal_use_allowed` | **true** | 不可作對外 delivery 範例 |

```bash
python scripts/approve_tabular_delivery.py --case-id 2026-0001 --evaluate-only --json
# readiness.delivery_ready=false · readiness_gaps 含 output_guard.warning
```

---

## Ops summary CLI 示例輸出

### demo_phase（delivery_ready=true · report 缺 output_guard 時 guard=unknown）

```bash
python scripts/tabular_ops_summary.py --case-id demo_phase
```

```
Tabular Ops Summary (read-only)
query: {'case_id': 'demo_phase', 'client_ref': None, 'all': False}
count: 1

case_id          client_ref       auto       step           done  cp_a         cp_b         guard    deliv      ready dlq
--------------------------------------------------------------------------------------------------------------------------
demo_phase       internal-demo    completed  checkpoint_b   0/8   approved     not_required unknown  approved   yes   yes
  ↳ profile=demo_phase internal_use=no partial_ready=no
  ↳ dlq queued=1 total=1

message: summarized 1 case(s)
```

> 若 `report.json` 含 `output_guard.status=ok`，guard 欄位顯示 `ok` · `partial_ready=no`（策略表 demo_phase+ok）。

### sampleco/2026-0001（guard warning · delivery_ready=false · by design）

```bash
python scripts/tabular_ops_summary.py --case-id 2026-0001
```

```
Tabular Ops Summary (read-only)
query: {'case_id': '2026-0001', 'client_ref': None, 'all': False}
count: 1

case_id          client_ref       auto       step           done  cp_a         cp_b         guard    deliv      ready dlq
--------------------------------------------------------------------------------------------------------------------------
2026-0001        sampleco         completed  approved_for_delivery 4/8   approved     approved     warning  approved   no    no
  ↳ profile=sampleco internal_use=yes partial_ready=yes

message: summarized 1 case(s)
```

---

## 已知限制 / 待辦

> 來源：manifest §3–§5 · E2E report §5–§7 · `cases/index.json` · `known_limits`

### 產品 / 清洗通用性

| 限制 | 說明 |
|------|------|
| **Phase-schema tight cleaner** | 主鏈 runner 仍為 `clean_phase_demo.py`；非任意 schema 通用清洗 |
| **sampleco 邊際品質** | 115 → 8 · `accepted_ratio=0.0696` · `output_guard.warning` · 不適合作 `delivery_ready=true` 範例 |
| **Excel 多 sheet** | 僅個案支援；非預設自動路徑 |
| **Allowlist 外 case** | 需 `--force`（internal demo）或 CP-A approve |

### 編排 / 狀態一致性（P2 follow-up）

| 項目 | 說明 |
|------|------|
| Run-log vs state 不同步 | `approve-b` 後 run log 仍可能顯示 `checkpoint_b.awaiting_hitl` |
| Readiness 評估 | `evaluate_delivery_readiness` 尚未完全 honor `automation_state.checkpoint_b_status=approved` |
| sampleco smoke | 僅 `demo_phase` 有一鍵 regression；sampleco 仍依 checklist §4 逐步 CLI |

### 明確非目標（仍有效）

- Prod-ready · GA · SLA · 7×24 託管
- Full-line Phase closure · Phase% 上調 · required CI merge gate
- 客戶自助上傳 pipeline · prod Telegram/SMTP 通知
- 改 `.github/workflows/*` · governance Batch 1 YAML

---

## 下一步建議（3–5 項）

優先序對齊 manifest §4 B 類 backlog：

| # | 項目 | 類別 | 預期效果 |
|---|------|------|----------|
| **1** | **Cleaning profile 抽象（B7）** | 工程 | `intake.json` → `cleaning_profile` 驅動規則集；allowlist 外低風險 case 可 auto |
| **2** | **Glue → E2E 接線（B6）** | 工程 | driver 可選 `--via-tool-executor`；tool path 接主鏈而非 dry-run only |
| **3** | **sampleco 一鍵 regression smoke** | 工程 | 泛化 `run_demo_phase_regression_smoke.py` 或新增雙案 runner（E2E report §7.2） |
| **4** | **CP-B / readiness 狀態同步** | 工程 | 修 run-log step status 或 readiness 讀 `checkpoint_b_status`（E2E report §7.1） |
| **5** | ~~**產品決策：warning guard + human approve**~~ | 產品 | ✅ v1 策略 manifest §1.12 · `tabular_warning_guard_lib.py` · fail-closed on warning |

**回歸基準（任何主鏈變更必跑）**：

```bash
python scripts/run_demo_phase_regression_smoke.py --json
# 雙案深度驗證：docs/tabular-mainline-e2e-verification-v1.md
```

---

## 相關文檔索引

| 主題 | 文件 |
|------|------|
| SSOT / landing | `docs/TABULAR_MVP_SSOT.md` |
| 自動化邊界 | `docs/tabular-cleaning-automation-manifest-v1.md` |
| 對內 Runbook | `docs/C2-P2_RUNBOOK.md` §3.4 |
| E2E checklist / report | `docs/tabular-mainline-e2e-verification-v1.md` · `-report-v1.md` |
| 進度更新模板 | `docs/tabular-mainline-progress-template.md` |
| Case 索引 | `cases/index.json` |

---

## 修訂

| 版本 | 日期 | 說明 |
|------|------|------|
| v1 | 2026-06-27 | 初版 · Tabular Mainline Progress Reporter · 雙案 E2E 後首份進度快照 |

---

*Tabular mainline progress update · doc-only · NOT PROD GATE · NOT CLOSURE*
