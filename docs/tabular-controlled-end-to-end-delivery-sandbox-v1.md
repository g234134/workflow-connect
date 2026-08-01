# Tabular Controlled End-to-End Delivery Sandbox v1 (W12-T1)

> **版本**: v1.0  
> **票號**: W12-T1 · tabular-controlled-end-to-end-delivery-sandbox-v1  
> **適用**: Tabular Agent Standard Line v2（`controlled_experimental` fixture）  
> **日期**: 2026-06-10

---

## 1. 目的

在既有 Tabular Agent Standard Line v2 之上，為**單一 sandbox fixture** 提供受控「真實跑到 bundle」的 end-to-end 交付線：

- 真實執行 gate → cleaning → bundle
- 交付產物僅落地 `outbox/sandbox_delivery/`（sandbox manifest + 複本 artifacts）
- **不**觸發 production notify
- **不**進 production delivery contract
- **不**改 `demo_phase` / `sampleco` 錨點行為

---

## 2. Allowlist

| case_ref | sandbox e2e | 預設 run_path（無 flag） |
|----------|-------------|-------------------------|
| `additional_demo` | ✅ `--sandbox-end-to-end` | `checkpoint_b`（W11-T1） |
| `demo_phase` | ❌ blocked | `bundle`（stable） |
| `sampleco/2026-0001` | ❌ blocked | `checkpoint_b`（stable） |
| `sandbox_client` | ❌ blocked | `cleaning_preview` |

**權威常數**：`delivery/sandbox_delivery_bundle_v1.py` → `SANDBOX_E2E_ALLOWLIST`

---

## 3. 與 Production Delivery 的差異

| 維度 | Production / demo_phase bundle | W12-T1 Sandbox E2E |
|------|-------------------------------|-------------------|
| 觸發 | 標準 `_RUN_PATH_PROFILES` | 僅 `--sandbox-end-to-end` + allowlist |
| Bundle 落地 | `cases/<ref>/reports/` + signoff | **複本** → `outbox/sandbox_delivery/<case_ref>/` |
| Notify | W7-T3 simulated（demo/sampleco only） | **永不觸發** |
| Contract | MVP case bundle | `production_contract: false` |
| CP-A | HITL 或 `--auto-approve-intake` | 同左 |
| CP-B | live guard + human | guard OK 或 `--auto-approve-delivery` 後才 bundle |

---

## 4. Run Profile：`end_to_end_sandbox`

啟用 `--sandbox-end-to-end` 時，orchestrator 使用 `stop_at: sandbox_bundle`：

```
S1 Intake          — Human（既有 case fixture）
S2 Index           — 不跑（實驗線）
S3 Decision        — ✅ evaluate_intake_decision
S4 Checkpoint A    — ✅ HITL / --auto-approve-intake
S5 Route Planning  — ✅ plan_tabular_route
S6 Tool Selection  — ✅ tool path preview
S7 Gate            — ✅ validate.eligibility（真跑）
S8 Cleaning        — ✅ clean.phase_demo（真跑）
S9 Outbox          — ✅ executor outbox record
S10 Bundle         — ✅ export.delivery_bundle（CP-B 通過後）
S11 Output Guard   — ✅ live cleaning_stats
S12 Checkpoint B   — ✅ W6-T6 `maybe_create_checkpoint_b`（W12-T2）→ 再以
                     `_can_proceed_sandbox_bundle_after_checkpoint_b` 決定是否進 bundle
                     （**不再**直接呼叫 `can_proceed_sandbox_bundle` 內嵌閘門）
S10b Sandbox Copy  — ✅ write_sandbox_delivery_bundle → manifest.json
S13–S15            — ❌ 不跑 delivery approval / notify
```

> **W12-T2 語意**：CP-B 狀態檔寫入 `{outbox_root}/{case_ref}/checkpoint_B-*.json`（與一般 run path 共用 integration layer）；sandbox **manifest** 仍獨立於 `{outbox_root}/sandbox_delivery/{case_ref}/...`。詳見 `docs/checkpoint-b-integration-v1.md` § sandbox consumer · 票 `W12-T2-sandbox-e2e-checkpoint-b-full-integration-v1`。

---

## 5. 可觀察指標

| 指標 | 來源 | 說明 |
|------|------|------|
| `removal_ratio` | `output_guard.removal_ratio` | live `cleaning_stats.json` |
| `guard.status` | `output_guard.status` | ok / warning |
| `guard.checks` | `output_guard.checks` | ratio_check · schema_check |
| `checkpoint_trace` | sandbox `manifest.json` | CP-A / CP-B status |
| `sandbox_delivery.bundle_dir` | orchestrator result | 人工檢閱目錄 |
| `notify_triggered` | manifest | 恆為 `false` |

**Audit**：`python scripts/run_agent_audit_quickview.py --case-ref additional_demo --format json`  
→ `sandbox_delivery` 區塊（`sandbox: true`）

---

## 6. CLI 用法

```bash
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/additional_demo \
  --mode run \
  --auto-approve-intake \
  --sandbox-end-to-end \
  --format json
```

可選：`--auto-approve-delivery` 在 guard warning 時仍允許進入 sandbox bundle（實驗室 only）。

非 allowlist 嘗試：

```bash
# → final_status=blocked, message=sandbox_end_to_end_not_allowed
python scripts/run_agent_standard_case_experiment.py \
  --task-type tabular.cleaning.mvp \
  --case-dir cases/demo_phase \
  --mode run --sandbox-end-to-end --format json
```

---

## 7. 落地路徑

```
outbox/sandbox_delivery/<case_ref>/<YYYYMMDDTHHMMSSZ>_<experiment_id_prefix>/
  manifest.json
  report.json
  cleaning_stats.json
  eligibility_result.json
  delivery_signoff.md
  cleaned/*.csv
```

---

## 8. 驗證

```bash
python -m unittest tests.test_sandbox_delivery_bundle_v1 tests.test_agent_standard_case_experiment -v
python scripts/run_agent_audit_quickview.py --case-ref additional_demo --format json
```

---

## 9. 非範圍（NonScope）

- 不改 `scripts/build_case_delivery_bundle.py` / production notify
- 不改 `demo_phase` / `sampleco` `_RUN_PATH_PROFILES`
- 不將 `additional_demo` 標為 production fixture
