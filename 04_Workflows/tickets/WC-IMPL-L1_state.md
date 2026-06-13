# TICKET STATE · WC-IMPL-L1 · governance-snapshot-advisory-enforcement-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。
> **定位**：在 L0 `generate_toolchain_governance_snapshot.py` + CI 集成之上，追加「最弱约束」L1 advisory；**不**升格 merge gate。

---

## FRAME

- Goal: 将 `toolchain_governance_snapshot_v1` 从 L0 纯观测升级为 **最弱约束 L1 advisory**——对快照中「关键信号缺失」给出结构化、高可见度 PR 告警，但 **CI job 仍始终 pass**（`exit 0` · `continue-on-error: true` 不变）。
- Scope:
  - 在 `scripts/generate_toolchain_governance_snapshot.py` 内新增 **advisory 评估层**（`evaluate_governance_advisory()` 或等价函数），输入 snapshot payload，输出 `advisory_findings[]`。
  - 明确定义「缺失信号」规则（见下 **MissingSignalRules**）；每条 finding 含 `code` · `severity` · `message` · `remedial_action`。
  - 扩展 snapshot schema：`advisory_level`（`none` | `warn` | `critical`）· `advisory_findings` · `advisory_summary`；Markdown artifact 增 **Advisory** 节。
  - CI 日志：对 `critical` 级 finding 打印 `::warning title=...::...`（GitHub Actions annotation）；保留现有 L0 trailer，追加 L1 advisory block。
  - 新增/扩展 unittest：`tests/test_toolchain_governance_snapshot_v1.py` 覆盖各 missing-signal 规则与 **non-blocking exit 语义**。
  - 更新 `docs/governance/WC_PRE_06_07_rollout_plan.md` §3.6（与本票 rollout 小节对齐）。
- NonScope:
  - **禁止**改 PR job pass/fail（不得移除 `--non-blocking`、不得让 snapshot step 成为 required check、不得改 `exit` 语义使 advisory 触发 fail）。
  - **禁止**改 branch protection / required checks 配置（含 GitHub repo settings）。
  - **禁止**将 `aggregated_health_score` 或 advisory 结论升格为 SLA / merge blocker。
  - **不**在本票接入 `run_toolchain_health_dashboard.py` 独立 CI step 或 smoke matrix execute step（属 rollout CH-30/32 · 可后续票）。
  - **不**改 `run_toolchain_health_dashboard.py` 评分逻辑、P3.5 正文、INT Tier-A runner。
- AllowedPaths:
  - `scripts/generate_toolchain_governance_snapshot.py`
  - `tests/test_toolchain_governance_snapshot_v1.py`
  - `docs/governance/WC_PRE_06_07_rollout_plan.md`（§3.6 小节）
  - `.github/workflows/eval-gate-ci.yml` · `.github/workflows/core-agent-smoke.yml`（**仅**允许在既有 snapshot step 内追加 annotation 友好输出；不得改 step 的 `if`/`continue-on-error`/required 语义）
- BlockedPaths:
  - GitHub branch protection / repo settings
  - `docs/phase3-5-cost-model-governance-contract-v1.md` §2 正文表（须独立 `WA-T3-AMEND` 票）
  - `scripts/run_toolchain_health_dashboard.py`（评分与 section 逻辑）
  - `core/wave7_regression_gate.py` · MVP mainline regression 路径
- Dependencies:
  - **WC-PRE-06** — `docs/toolchain-observability-governance-upgrade-v1.md`（L0→L1 治理语义 · `approval_status` 参考；本票为 snapshot advisory 子集，可在 L1 批文前先行落地 observability）
  - **WC-PRE-07** — smoke matrix CI 设计 / `optional_ci` tier 语义（advisory 规则中 `optional_ci` not_observed 分类依赖矩阵 SSOT）
  - **L0 已交付** — `generate_toolchain_governance_snapshot.py` + `eval-gate-ci.yml` / `core-agent-smoke.yml` snapshot step（2026-06-13 现状）
- MissingSignalRules（v1 · 施工冻结）:

  | code | severity | 触发条件 | remedial_action（摘要） |
  |------|----------|----------|-------------------------|
  | `MS-MATRIX-LOAD` | critical | `smoke_matrix.loaded_ok != true` | 检查 `routing/toolchain_smoke_matrix_v1.yaml` 存在与 YAML 合法；本地 `python scripts/run_toolchain_smoke_matrix.py --list --format json` |
  | `MS-MATRIX-EMPTY` | critical | `coverage.smoke_entries_total == 0` | 确认 matrix `entries` 非空；勿删 SSOT YAML |
  | `MS-HEALTH-ASSEMBLY` | critical | `toolchain_health_embed.ok != true` | 本地 `python scripts/run_toolchain_health_dashboard.py --format json --dry-run --no-write` 看 `message` |
  | `MS-HEALTH-SECTIONS` | critical | `toolchain_health_embed.sections_populated < 3` | 补齐 outbox 数据源（agent_ci / metrics_summary / catalog）；见 `docs/toolchain-health-dashboard-v1.md` |
  | `MS-CI-SMOKE-MISSING` | critical | 当前 `ci_context` 下，`_CI_OBSERVED_SMOKES[ci_context]` 中任一 smoke 在 `components` 里 `last_result == "not_observed"` **且**无 `--smoke-results-json` 外部结果 | 确认 hosting workflow 已跑对应 smoke；core-agent-smoke 路径检查 `smoke_ci_summary.json` 是否传入 |
  | `MS-CI-SMOKE-FAILED` | critical | 当前 `ci_context` 关联 smoke（含 external JSON）`last_result == "failed"` | 读 `error_summary` / artifact；修对应 unittest 或 smoke runner |
  | `MS-OPTIONAL-CI-GAP` | warn | `tier == "optional_ci"` 的 matrix entry 全部 `last_result == "not_observed"` | 预期：WC-PRE-07 smoke CI step 未上或未跑；本地 `--tier optional_ci --dry-run` |
  | `MS-HEALTH-DEGRADED` | warn | `toolchain_health_embed.degraded_sections` 非空 | 分类 infra_gap vs regression；见 rollout plan §4.1 outbox 空档缓解 |
  | `MS-SNAPSHOT-ARTIFACT` | warn | `--write` 但 `output_paths.json` 缺失（写盘失败） | 检查 `output/toolchain/` 权限与 workflow upload path |

  - **advisory_level 聚合**：存在任一 `critical` → `critical`；否则存在 `warn` → `warn`；否则 `none`。
  - **non_blocking 不变**：即使 `advisory_level=critical`，CLI 在 `--non-blocking` 下 **必须 exit 0**。
- AcceptanceCriteria:
  1. `python -m unittest tests.test_toolchain_governance_snapshot_v1 -v` 全绿，含 advisory 规则正反例。
  2. 本地 `python scripts/generate_toolchain_governance_snapshot.py --ci-context eval-gate-pr --write --non-blocking --print-ci-summary` 产出含 `advisory_findings` 的 JSON；日志含 L1 advisory block。
  3. 模拟 critical finding（unittest fixture）时，stdout 含 GitHub `::warning` 行；**exit code = 0**（`--non-blocking`）。
  4. 现有 workflow snapshot step **未**移除 `continue-on-error: true`；**未**新增 required check。
  5. rollout plan §3.6 与本票 MissingSignalRules 一致。

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: closed · WC-IMPL-L1 关票；L1 观察期自 2026-06-13 起算（见 D_REPORT · rollout plan §3.6）；L2 升格待 G1–G8 + 批文
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `scripts/generate_toolchain_governance_snapshot.py` — `evaluate_governance_advisory()` / `attach_governance_advisory()`；MissingSignalRules v1；L1 CI log block + `::warning` annotations
  - `tests/test_toolchain_governance_snapshot_v1.py` — 9×MS-* 正反例 + advisory 聚合 + non-blocking exit
  - `.github/workflows/eval-gate-ci.yml` · `.github/workflows/core-agent-smoke.yml` — snapshot step 标注 WC-IMPL-L1（语义不变）
  - `docs/governance/WC_PRE_06_07_rollout_plan.md` — 新增 §3.6 与 MissingSignalRules 对齐
- artifacts:
  - `output/toolchain/governance_snapshot.json`（含 `advisory_level` / `advisory_findings` / `advisory_summary`）
  - `output/toolchain/governance_snapshot.md`（Advisory 节）
- verification:
  - `python -m unittest tests.test_toolchain_governance_snapshot_v1 -v` → 全绿（17 tests）
  - `python scripts/generate_toolchain_governance_snapshot.py --ci-context eval-gate-pr --write --non-blocking --print-ci-summary` → JSON 含 advisory 字段；stdout 含 L1 block
- behavior_notes:
  - `advisory_level` 聚合：critical > warn > none
  - `--non-blocking` 下无论 `advisory_level` 均 exit 0
  - CI step `continue-on-error: true` 未改；未新增 required check
- deferred_items:
  - CH-30/32 独立 health/smoke matrix CI step（本票仅 snapshot advisory 子集）
  - `run_toolchain_health_dashboard.py` 评分逻辑变更

---

## C_REPORT

- conclusion: accepted
- blocking_issues: none
- checks_summary:
  - AC-1：`python -m unittest tests.test_toolchain_governance_snapshot_v1 -v` 全绿，含 MissingSignalRules v1 正反例（9×MS-* + 聚合 + non-blocking exit；假定上一轮 17 tests OK）
  - AC-2：本地 `--write --non-blocking --print-ci-summary` 产出含 `advisory_findings` JSON 与 L1 advisory log block
  - AC-3：critical finding fixture 时 stdout 含 `::warning` 行且 **exit code = 0**（`--non-blocking`）
  - AC-4：`eval-gate-ci.yml` · `core-agent-smoke.yml` snapshot step **未**移除 `continue-on-error: true`；**未**新增 required check
  - AC-5：`docs/governance/WC_PRE_06_07_rollout_plan.md` §3.6 与 MissingSignalRules v1 一致
  - NonScope 遵守：advisory 不升格 merge gate；branch protection 未改
- risk_level: low
- suggestions: 启动 L1 观察期（设计稿 §4 门槛）；CH-30/32 独立 health/smoke CI step 另票；L2 见 WC-IMPL-L2 FRAME 冻结态

---

## D_REPORT

- docs_updates:
  - `docs/governance/WC_PRE_06_07_rollout_plan.md` §3.6 — 已与 MissingSignalRules v1 对齐（B_REPORT）；Scribe 确认 L1 advisory 语义索引可见
  - `docs/toolchain-observability-governance-upgrade-v1.md` — `approval_status.L1` 可标 observability 已落地（实施非 merge gate）
- progress_entry: WC-IMPL-L1 关票：toolchain governance snapshot L1 advisory 上线；MissingSignalRules v1 覆盖 MS-MATRIX/HEALTH/CI-SMOKE/OPTIONAL 等 9 条；**CI 仍 non-blocking exit 0**。
- followup_suggestions:
  - **L1 观察期起始日：2026-06-13**（关票日）；观察期证据收集位点见 WC-IMPL-L2 D_REPORT G1–G8
  - L2 selective mandatory 须等观察期满 + rollback 演练 + 尚書省 `approval_status.L2=approved`
