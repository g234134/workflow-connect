# P8 / P8.9 · Evidence Index (v1)

> **Ticket**: `W3-P89-EVD-scenario1-bridge-evidence-index-v1` · **Wave 3** · **doc-only SSOT**  
> **Authority**: P8 · P8.9 · P8.5 bridge cross-ref · Wave-next 敘事的**統一證據分層**；下游 runbook / GA spec **必須引用本檔 tier 名稱**，**不得自創** tier 別名。  
> **Related**: `docs/evidence-tier-contract-v1.md`（ticket/Progress 栏位 · B/C/D/O）· `docs/P7_ADVISORY_CI_INDEX.md`（P7 專線）

---

## Non-claims（必讀）

| 聲明 | 狀態 |
|------|------|
| 本索引就緒 = 任一 **GA-remote** 證據已存在 | **否** — **Scenario1/2 遠端 GA 截至 2026-06-26 仍 pending human**（`WH-P85-SMOKE-B-scenario2-ops-run-v1` **`blocked`** · 无 run URL） |
| **CI-advisory landing**（yml on `origin/main`）= **GA pass** / 遠端 CI 綠 | **否** — landing 僅表 workflow **版控就位**；遠端 completed run 須 **GA-remote** tier + **run URL** |
| **L-local** unittest / MP-SMOKE 綠 = prod-ready / INT Tier-A | **否** |
| **CI-advisory** 綠 = branch protection required check / merge gate | **否** — 均 `continue-on-error` · 非 required（除非尚書省另開 G8 類升格票） |
| 本索引 = Dashboard **Phase% 上調** | **否** — 本 Wave **不改 Phase%**；§5 僅定義**未來**上調時應看的證據門檻 |
| bridge smoke = P8/P8.9 發版 gate | **否** — bridge 為 **optional advisory 側線** · in-memory stub · cross-ref `W3-P8-BRG-*` |

**P7 / P9 專線**：P7 advisory 索引見 `docs/P7_ADVISORY_CI_INDEX.md`；P9 payment sandbox CI 首跑語意見 §4.3 · Wave 4 `W4-P9-CI-*` — **本檔主責 P8 / P8.9 / P8.5 bridge 交叉引用**。

---

## 1. 三層定義（SSOT · 固定命名）

| Tier ID | 中文 | 定義 | 典型證據形狀 | 禁止表述 |
|---------|------|------|--------------|----------|
| **`L-local`** | 本機 / sandbox smoke | 開發者或 agent 在**本機**（或 sandbox venv cwd）執行的 **unittest · CLI orchestrator · 單次命令紀錄**；**无** GitHub Actions run URL | exit code · `N/N OK` · JSON artifact 路徑 · Progress 命令摘要 | 「遠端 validated」「GA pass」「CI 綠（GitHub）」 |
| **`CI-advisory`** | Advisory CI · 非 gating | **已 landing** 的 GitHub Actions workflow · job **`continue-on-error: true`** · **非** branch protection required · 示範性 / 回歸觀測 | workflow 檔名 · job id · `ci_class: advisory` · landing commit · **可无** completed run | 「merge gate」「required check」「landing = GA pass」 |
| **`GA-remote`** | 遠端具名 GA run | **至少一次** completed 的 GitHub Actions run（或等價遠端環境一次具名執行），含 **`run_url`** + **`run_id`** · 通常 **`workflow_dispatch`** 或 PR/cron 觸發的**真實 runner log** | run URL · run id · job 摘要 · artifact 名 · Progress append 模板 | 无 URL 时使用「validated」「首跑 pass」「遠端 CI 綠」 |

**trace 鍵（票 STATE / B_REPORT 建議）**：

```yaml
evidence_tier: L-local | CI-advisory | GA-remote
evidence_kind: local_unittest | local_cli_smoke | ci_advisory_landing | ci_advisory_run | ga_remote_dispatch
```

**Reviewer 硬門**（引用 SSOT · 不重复定义）：`wave-next-code-inspector-v1.md` §3.2–3.3 · `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1` D_REPORT「不可說」表。

---

## 2. Tier 表 · P8 / P8.9 / P8.5 bridge

### 2.1 · `L-local`

| ID | 命令 / 入口 | 用途 | 預期信號 | 權威引用 |
|----|-------------|------|----------|----------|
| **EVD-LL-P89-MP** | `python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json` | P7.5 → P8 → P8.9 七步 orchestration smoke | 七步 `ok=true` · `failed_steps` 空 · artifact `outbox/verification/<case_slug>/multi_phase_smoke_run.json` | `MP-SMOKE-std-case-multi-phase-smoke-v1` · Dashboard §Multi-phase smoke |
| **EVD-LL-P89-BND** | `python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --format json` | P8.9 consumer / feedback / dispatch 回歸 bundle | bundle `ok` · `events_summary.count>0`（demo_phase 基線）· `p8.9_verification_run.json` · executed report: `docs/p8_9-verification-report-v1.md` · `functional_gaps: true_with_known_limits` | `P8.9-REGRESSION-standard-case-verification-bundle-v1` · `WF-P89-OUTBOX` |
| **EVD-LL-P89-CI** | `python scripts/run_ci_smoke_check_v1.py --format text` | **Repo local release sanity**（串 MP-SMOKE + metrics 規則）· **无** GitHub workflow 綁定 | exit 0/1 依本地規則 · **≠** GitHub required workflow | `CI-SMOKE-multi-phase-smoke-and-metrics-hook-v1` · W3-P8-ADV 敘事 |
| **EVD-LL-P89-MC** | `python scripts/run_multi_case_smoke_v1.py …` | 多 case fleet smoke | per-case summary JSON | `MC-SMOKE-multi-case-smoke-runner-v1` |
| **EVD-LL-P85-A** | `python -m unittest tests.test_minimal_orchestration_bridge -v`（cwd：暗部 `gov_core_system`） | P8.5 bridge Smoke A · Scenario1 本機 | **14/14 OK** | `docs/phase8_5-bridge-smoke-runbook-v1.md` · `WH-P85-SMOKE-B-advisory-v1` |
| **EVD-LL-P85-B** | `python -m unittest tests.test_app_api_orchestration_bridge -v`（同上 cwd） | P8.5 bridge Smoke B · HTTP API · Scenario1 本機 | **7/7 OK** | 同上 |
| **EVD-LL-P89-UT** | 各 P8/P8.9 子模組 unittest（例：`tests.test_multi_phase_smoke_v1` · `tests.test_p8_9_verification_bundle_v1`） | 單元 / 契約回歸 | `N/N OK` | 各子票 B_REPORT |

**Scenario1 本機組合（Wave-next 現況 · 2026-06-25 敘事）**：**EVD-LL-P85-A** + **EVD-LL-P85-B** = **14/14 · 7/7 validated**（**L-local only** · 非 GA-remote）。

---

### 2.2 · `CI-advisory`

| ID | Workflow 檔 | Actions 顯示名 | Job id(s) | 觸發 | blocking | 與 GA-remote 關係 |
|----|-------------|----------------|-----------|------|----------|-------------------|
| **EVD-CA-P85-BRG** | `.github/workflows/bridge-smoke.yml` | **P85 Bridge Smoke CI (advisory)** | `p85-bridge-smoke-a` · `p85-bridge-smoke-b` | `pull_request` · cron · `workflow_dispatch`（`scenario` input） | **non-gate** · `continue-on-error: true` | **Landing ✅**（`origin/main` · 2026-06-24）· **completed GA run 仍 pending**（Scenario2：`WH-P85-SMOKE-B-scenario2-ops-run-v1` **`blocked`**） |
| **EVD-CA-P89-REF** | （P8/P8.9 主链 **无** 独立 advisory yml） | — | — | — | — | P8/P8.9 主链 release sanity 走 **EVD-LL-P89-CI**（local script）· 非 GitHub job |

**bridge-smoke 子情境**（input `scenario` · 均 **CI-advisory** 直到有 **GA-remote** run URL）：

| 情境 | Job 集合 | 設計意圖 | 現況 tier |
|------|----------|----------|-----------|
| **Scenario1**（default） | A + B 跑 unittest | happy path 14/14 + 7/7 | 本機 **L-local validated** · yml **CI-advisory landing** · **GA-remote：pending** |
| **Scenario2** | `p85-bridge-smoke-a-scenario2` · `p85-bridge-smoke-b-scenario2` | deps-gate skip 探针 · exit 0 | **GA-remote：blocked** · 本機 bash 探针 **≠ GA 證據** |

**Cross-ref（同 Wave 家族 · 非 P8/P8.9 主票 AC，仅索引）**：

| Workflow | Phase | 備註 |
|----------|-------|------|
| `p7-notification-smoke.yml` | P7 | 見 `docs/P7_ADVISORY_CI_INDEX.md` |
| `p9-payment-sandbox-smoke.yml` | P9 | Wave 4 · **GA-remote PASS** run_id=`29159159265` · ≠ prod provider |
| `p9-wc-m2-fixture-execute.yml` | P9 | advisory · non-blocking |

---

### 2.3 · `GA-remote`

| ID | 描述 | 前置 | 必填欄位 | 現況（2026-06-26） |
|----|------|------|----------|-------------------|
| **EVD-GR-P85-S1** | Scenario1 遠端 GA（default input · A+B jobs completed） | `bridge-smoke.yml` landing · human 或 PR/cron 觸發 | `run_url` · `run_id` · job log 摘要 · artifact 名（若有） | **pending** — Dashboard 明示 **Scenario1/2 遠端 GA 未實跑** |
| **EVD-GR-P85-S2** | Scenario2 遠端 GA（`scenario=scenario2` dispatch） | 同上 + ops-run 票 FRAME | 同上 + design-skip / deps-gate notice 摘要 · Progress append | **`recorded`** · run_id=`29157178993` · 2026-07-11 · Scenario2 A/B **success** · S1 skipped · ≠ prod browser |

**GA-remote 紀錄模板**（Wave 4 runbook **必須引用本節 · 不得自創欄位名**）：

```yaml
ga_run:
  evidence_tier: GA-remote
  evidence_kind: ga_remote_dispatch
  workflow_file: .github/workflows/bridge-smoke.yml
  workflow_display_name: "P85 Bridge Smoke CI (advisory)"
  scenario: default | scenario2
  run_url: "<https://github.com/<org>/<repo>/actions/runs/<run_id>>"
  run_id: "<numeric>"
  branch: main
  jobs:
    - job_id: p85-bridge-smoke-a
      conclusion: success | skipped | failure
      log_excerpt: "<one-line notice or pass summary>"
  non_claims:
    - advisory ≠ merge gate
    - GA pass ≠ prod browser / bridge prod-ready
```

**禁止**：预填假 URL · 本機 bash 探针填入 `ga_run` · 无 URL 写「GA pass / validated / 遠端 CI 綠」。

**下游票（引用本 Index · 不重复 tier 定义）**：

- `W4-P85-S2-GA-RUNBOOK-v1` · `WH-P85-SMOKE-B-scenario2-ops-run-v1`
- `W4-P85-P9-EVIDENCE-SSOT-v1`（跨线 GA 索引 · 须 link 回本檔 §1）

---

## 3. Advisory ≠ prod gate（快速對照）

| 读者误解 | 正确 tier 表述 |
|----------|----------------|
| 「`bridge-smoke.yml` 已 merge 到 main」 | **CI-advisory landing** only |
| 「本机 14/14·7/7 过了」 | **L-local** · Scenario1 validated（非遠端） |
| 「Actions 里看得见 workflow」 | **CI-advisory** 就位 · **≠ GA-remote** |
| 「advisory job 绿了」 | 若 run 在 GitHub 上：**GA-remote** 候选 · 仍 **≠ required CI · ≠ prod** |
| 「MP-SMOKE 七步 OK」 | **L-local** · 支撑 P8/P8.9 接線叙事 · 不单独支撑 P8.5 bridge prod |

---

## 4. 与 Observability contract 的边界

| 文档 | 职责 |
|------|------|
| **本 Index** | **证据分层** · 何时可说 validated / GA / advisory · Phase% 门坎 |
| **`p8_p89_delivery_observability_contract_v1.md`**（W3-P89-OBS） | **trace 字段** · artifact 路径 · success/failure signals · CLI inspect |
| **`docs/P7_ADVISORY_CI_INDEX.md`** | P7 advisory CI 专线索引 |

施工时：**tier** 查本 Index · **字段/路径** 查 OBS contract · **P7** 查 P7 Index。

---

## 5. Phase% 上调 · 证据门坎（本 Wave 不执行上调）

> **纪律**：Wave 3 **不改** `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 数字。下表供 **未来** Governance / Reviewer 调整 Phase% 或 closure 叙事时对照。

| 目标 | 最低证据组合 | 不足时 |
|------|--------------|--------|
| **维持 P8 80% / P8.9 81% 叙事**（现状） | **L-local** MP-SMOKE + P8.9 bundle + 子票 STATE 对齐 | 仅 **CI-advisory landing** 不可单独支撑 |
| **P8/P8.9 能力「implementation validated」** | **L-local** 全绿 + unittest 引用 +（可选）OBS contract spot-check | **CI-advisory**  alone → 最多「advisory 就位」脚注 |
| **「advisory CI 曾远端跑过」**（仍 non-gate） | **GA-remote** run URL + job log + Progress append · Reviewer 认可 | **CI-advisory landing** or **L-local** → **不可** |
| **P8.5 Scenario2 closure / wave-H+2 叙事** | **EVD-GR-P85-S2** 完成 + ops-run **`done`** + 无 over-claim | Scenario2 **blocked** 时维持 Dashboard「closure-scribe blocked」 |
| **「prod-ready / INT Tier-A / required CI」** | **不在本 Index 范围** — 须尚书省批文 + 另开 G8 / WC-PRE 票 | 任何 tier **均不够** |

**补充叙事 vs Phase% 上调**：

| Tier | 可支撑「补充叙事」（Progress / Dashboard 脚注） | 不可单独支撑 Phase% 上调 |
|------|-----------------------------------------------|-------------------------|
| **L-local** | 是 — 实现完成 · 回归 sanity · cross-ref 命令 | 是 — 已有 Phase% 已计 L-local 基线 |
| **CI-advisory** | 是 — 「workflow 就位 · non-blocking 观测」 | 是 — landing ≠ 远端 pass |
| **GA-remote** | 是 — 「远端 once-run 物证」· closure 前置 | 视 Reviewer — 仍 **≠ prod** · bridge stub gap 仍在 |

---

## 6. 索引维护

| 动作 | 负责 | 规则 |
|------|------|------|
| 新增 P8/P8.9 smoke 路径 | Implementer 票 | 追加 §2 表行 · **不得**新 tier 名 |
| GA 首跑后 | ops + Scribe | 填 **EVD-GR-*** · append Progress · 更新 ops-run STATE |
| Wave 4 runbook / GA spec | W4 Implementer | **必须** `cross-ref: docs/p8_p89_evidence_index_v1.md` §1–§2 |
| Reviewer 收口 | W3-P89-EVD D_REPORT | 对照 §3 误解表 · inspector §3.3 |

---

## Changelog

| 日期 | 变更 |
|------|------|
| 2026-06-26 | v1 初版 · `W3-P89-EVD-scenario1-bridge-evidence-index-v1` Implementer 交付 · Scenario1 L-local 14/14·7/7 · bridge CI-advisory landing · GA-remote pending/blocked |
