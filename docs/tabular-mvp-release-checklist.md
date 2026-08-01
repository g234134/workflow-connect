# Tabular MVP Release Checklist

> **Ticket**: W4-T4 · Routing CI Hooks（release checklist · 策略 3）  
> **Date**: 2026-06-10  
> **Audience**: 發版前人工執行；**非** PR CI 唯一守門

---

## §1 目的

本 checklist 列出 **Tabular MVP**（Wave 1–4：主鏈、Intake/Routing、Tabular 工具層、Routing↔Tool glue）在對外 demo 或 tag 發版**之前**應跑通的命令。

- PR CI **已自動**覆蓋 routing eval dry-run（見 §4）；其餘多數項需**本地或 release 管線人工**執行。
- 本清單 **不**取代 Observability V2、Gov Core smoke 或暗部 `gov_core_system` 既有 gate。

---

## §2 必跑命令清單

依序或並行執行；全部 exit 0 方可標記 release ready。

### 2.1 Wave 1 — 主鏈回歸（6/6）

```bash
python scripts/run_mvp_mainline_regression.py -v
```

預期：`6/6` tests OK，`overall_ok: true`。涵蓋 `cases/demo_phase` 與 `cases/sampleco/2026-0001`。

### 2.2 Wave 2 — Intake catalog + eval cases 一致性

```bash
python -m unittest tests.test_intake_routing_catalog tests.test_routing_eval_cases -v
```

預期：catalog 10/10 + eval cases 8/8（合計 18 tests OK）。

### 2.3 Wave 3-TL — 工具層四件套

```bash
python -m unittest \
  tests.test_tabular_tool_catalog \
  tests.test_tabular_tool_selector \
  tests.test_tabular_tool_executor \
  tests.test_tabular_outbox_consumer \
  -v
```

預期：四模組 unittest 全綠（Catalog / Selector / Executor / Consumer）。

### 2.4 Wave 4 — Routing eval runner

```bash
python -m unittest tests.test_routing_eval_runner -v
python scripts/run_routing_eval.py --dry-run --format json
```

預期：unittest **12/12 OK**；CLI JSON `ok: true`，`message` 含 `4/4 case(s) aligned`。

### 2.5 Wave 4 — 建議加跑（非阻塞，release 前推薦）

```bash
python -m unittest tests.test_routing_tabular_glue tests.test_tabular_intake_tool_path -v
python scripts/run_tabular_intake_tool_path.py --task-type tabular.cleaning.mvp --case-dir cases/demo_phase --json
```

預期：glue / intake path 預演無 crash；intake preview `ok: true`（plan only，不寫 outbox）。

### 2.6 Wave 6/7/8 — INT Tier-A 集成回归（推荐 · 装配变更 mandatory）

```bash
python 04_Workflows/_wave7_regression_gate.py --tier A --pretty
```

預期：stdout JSON `ok: true`，exit `0`；需 `gov_core_system` venv。SSOT → `docs/phase6-int-regression-gate-contract-v1.md` §2。PR CI **不**跑此项；`core-agent-smoke` + `eval-gate` 绿 ≠ INT 绿。

---

## §3 解讀結果

| 命令 | 成功信號 | 常見失敗原因 |
|------|----------|--------------|
| `run_mvp_mainline_regression.py -v` | exit 0；摘要 6/6 | gate / cleaning / bundle 任一步失敗；fixture 路徑或 guard 變更 |
| Wave 2 unittest | 18/18 OK | catalog YAML 與 spec 漂移；eval case 引用未知 `task_type` |
| W3-TL 四件套 | 全模組 OK | catalog JSON 與 selector 規則不一致；outbox schema 變更 |
| `run_routing_eval.py --dry-run` | `ok: true`，4/4 aligned | cases YAML 與 catalog / glue / policy 不對齊 |
| intake tool path preview | JSON `ok: true` | glue flag、case_dir 或 catalog 缺 route |

失敗時：**不要 tag**；修復 SSOT 或 runner 後重跑 §2 全段。

---

## §4 與 CI 的關係

| 檢查項 | PR CI（自動） | Release（人工 / 未來 nightly） |
|--------|---------------|--------------------------------|
| Routing eval unittest + dry-run | **是** — `.github/workflows/eval-gate-ci.yml` → step `Routing eval dry-run (W4-T4)` | 同左（可選重跑） |
| P+ eval gate / observability | **是** — 同 workflow `eval-gate` job | 同左 |
| Core agent smoke (PR tier) | **是** — `.github/workflows/core-agent-smoke.yml` | dispatch 可跑 DARK/ALL |
| 主鏈 6/6 regression | **否** | **必跑** — §2.1 |
| Wave 2 catalog / eval cases unittest | **否** | **必跑** — §2.2 |
| W3-TL 四件套 unittest | **否** | **必跑** — §2.3 |
| Glue / intake path unittest + CLI | **否** | **建議** — §2.5 |
| INT Tier-A integration gate | **否** | **推薦**（装配变更 **必跑**）— §2.6 · `docs/phase6-int-regression-gate-contract-v1.md` |
| `run_routing_eval.py --execute` | **禁止** | 僅 allowlist smoke；**非** release 必跑項 |

**設計原則（W4-T4 NonScope）**：PR CI 只做 **dry-run / plan 對照**，不跑 `--execute`、不拉起 mainline regression，避免 CI 時間與 fixture 副作用膨脹。

---

## 交叉引用

- Runner spec：`docs/routing-eval-runner-v1.md`
- 主鏈回歸：`docs/mvp-mainline-regression.md`
- Wave 完成度：`docs/WAVE_PROGRESS_DASHBOARD.md`
- CI 索引：`04_Workflows/WORKFLOW_INDEX.md` §1.5 · §1.6 · §1.25（WA-T6 INT gate）
- INT gate SSOT：`docs/phase6-int-regression-gate-contract-v1.md`
