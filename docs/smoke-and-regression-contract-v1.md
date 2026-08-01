# Smoke and Regression Contract v1

> **Ticket lane**: G6 · Lane B Implementer · MP/MC/CI-SMOKE + matrix alignment  
> **Scope**: `run_multi_phase_smoke_v1.py` · `run_multi_case_smoke_v1.py` · `run_ci_smoke_check_v1.py` · `routing/toolchain_smoke_matrix_v1.yaml`  
> **INT gate SSOT**（分轨）: `docs/phase6-int-regression-gate-contract-v1.md`  
> **Dashboard 索引**: `docs/WAVE_PROGRESS_DASHBOARD.md` §Multi-phase smoke · **不改 Phase%**  
> **Date**: 2026-06-26

---

## 1. Purpose

统一 **三类 release sanity smoke** 的契约边界：

| ID | Runner | 粒度 |
|----|--------|------|
| **MP-SMOKE** | `scripts/run_multi_phase_smoke_v1.py` | 单 case · 七步 orchestration |
| **MC-SMOKE** | `scripts/run_multi_case_smoke_v1.py` | 多 case · 逐案调用 MP-SMOKE |
| **CI-SMOKE** | `scripts/run_ci_smoke_check_v1.py` | 单 case · MP-SMOKE + MP-METRICS + pass/fail policy |

并说明其与 **INT regression gate** · **toolchain smoke matrix** · **PR CI mandatory trio** 的关系。

**NonScope**：不把任一 smoke 升格为 PR required check · 不替代 INT Tier-A · 不宣称 GA/prod-ready。

---

## 2. Gate 分层（L-local · CI-advisory · INT）

```text
  PR CI mandatory trio          CI-advisory (optional wiring)        L-local recommended
  ┌────────────────────┐        ┌─────────────────────────┐        ┌──────────────────────────┐
  │ core-agent-smoke   │        │ CI-SMOKE (when wired to │        │ MP-SMOKE · MC-SMOKE      │
  │ eval-gate-ci       │        │  workflow w/ continue-  │        │ toolchain smoke matrix   │
  │ (routing dry-run)  │        │  on-error · non-required)│        │ INT Tier-A (assembly)    │
  └────────────────────┘        └─────────────────────────┘        └──────────────────────────┘
         │                                    │                                    │
         └──────────────── PR merge blocks ───┴── does NOT block merge by default ──┘
```

| 层 | 代表命令 | `gate_class` | `blocks_merge` | 与 INT Tier-A |
|----|----------|--------------|----------------|---------------|
| **L-local** | MP/MC-SMOKE · INT `--tier A` | optional（smoke）/ local mandatory（INT 装配变更） | **否** | INT **独立**；smoke **不覆盖** Tier-A 模块 |
| **CI-advisory** | CI-SMOKE in advisory workflow · P7/P85/P9 yml | optional / shadow | **否**（默认 `continue-on-error`） | 绿 **≠** Tier-A 绿 |
| **PR mandatory** | `_core_agent_smoke.py --tier PR` · eval-gate | mandatory（WA-T3 表内） | **是** | 绿 **≠** Tier-A 绿 |

**关键结论**

- MP-SMOKE 七步绿 **≠** 「过 INT gate」（见 phase6 contract §2）。
- CI-SMOKE exit 0 **≠** branch protection 已挂 required check（WC-PRE-07 blocked）。
- MC-SMOKE 含 `phi_demo` 时 **预期** 部分 case fail — release pass 路径用 `--cases demo_phase,sampleco`。

---

## 3. MP-SMOKE（Multi-Phase Smoke v1）

### 3.1 目的与场景

- **目的**：在**单一 case** 上串起 P7.5 → Phase 8 → P8.9 主链，**不修改**底层 CLI。
- **场景**：发版前深挖 · CI-SMOKE 内核 · P75/P8/P8.9 接線 sanity · operator backlog 可读。

### 3.2 七步固定序列

| # | `step_id` | 行为摘要 |
|---|-----------|----------|
| 1 | `gate_preview` | Intake gate preview |
| 2 | `gate_run_notify` | Gate run + `intake.gate_decision` notify |
| 3 | `std_case_experiment` | Standard-case experiment orchestrator |
| 4 | `workflow_events_inspect` | Workflow events 只读 |
| 5 | `feedback_ingest_dry_run` | Feedback ingest dry-run |
| 6 | `p89_verification_bundle` | P8.9 verification bundle collect-only |
| 7 | `operator_backlog` | Operator backlog 列表 |

### 3.3 典型命令

```bash
python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json
python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --enable-dispatch --format json
```

### 3.4 输出契约（`multi_phase_smoke_v1`）

| 键 | 类型 | 含义 |
|----|------|------|
| `ok` | bool | 全部 step `ok=true` |
| `schema_version` | str | `multi_phase_smoke_v1` |
| `case_ref` | str | case slug |
| `task_type` | str | routing task_type |
| `steps` | array | 每步 `{step_id, ok, message, artifact_paths?, detail?}` |
| `step_ids` | array | 固定七步顺序 |
| `enable_dispatch` | bool | dispatch registry 路径 |
| `artifact_paths` | object | 含 `multi_phase_smoke_run.json` 时写入路径 |

**产物**：`outbox/verification/<case_slug>/multi_phase_smoke_run.json`

### 3.5 Verify / Observe

```bash
python -m unittest tests.test_multi_phase_smoke_v1 -v
python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json
```

---

## 4. MC-SMOKE（Multi-Case Smoke v1）

### 4.1 目的与场景

- **目的**：**Fleet 视角**一次扫多条 profile / gate path。
- **场景**：发版前第一步 · 定位哪条 case 断线 · policy deny 探针。

### 4.2 默认 case 列表

| `case_ref` | 说明 | release pass |
|------------|------|--------------|
| `demo_phase` | 标准 cleaning → bundle | **include** |
| `sampleco/2026-0001` | 受控 profile · CP-B | **include** |
| `phi_demo` | PHI deny 合成 fixture | **exclude**（deny 探针） |

### 4.3 典型命令

```bash
python scripts/run_multi_case_smoke_v1.py --cases demo_phase,sampleco --format json
python scripts/run_multi_case_smoke_v1.py --format json   # 含 phi_demo 探针
```

### 4.4 输出契约（`multi_case_smoke_v1`）

| 键 | 类型 | 含义 |
|----|------|------|
| `ok` | bool | `failed_cases` 为空 |
| `cases` | array | 每 case `{case_ref, ok, failed_steps, operator_status, label}` |
| `failed_cases` | array | 失败 case_ref 列表 |
| `cases_run` | array | 本次运行的 case_ref |

**产物**：`outbox/verification/multi_case_smoke_run.json`

### 4.5 Verify / Observe

```bash
python -m unittest tests.test_multi_case_smoke_v1 -v
python scripts/run_multi_case_smoke_v1.py --cases demo_phase,sampleco --format json
```

---

## 5. CI-SMOKE（CI Smoke Check v1）

### 5.1 目的与场景

- **目的**：单 case 上合并 **MP-SMOKE + MP-METRICS**，输出 **pass/fail** 并 **exit 1** on failure。
- **场景**：本地 release gate · 未来 CI step（**默认未 required**）· 与 MP-METRICS ack 计数联动。

### 5.2 Pass 规则

| 检查 | 条件 |
|------|------|
| `multi_phase_smoke_ok` | smoke `ok=true` |
| `std_case_metrics_ok` | metrics `ok=true` |
| `notifications_failed_ack_count` | **默认（isolated outbox）**：`== 0`（缺失视为 fail） |
| `notifications_failed_ack_count` | **`--use-repo-outbox` 模式**：仅当 **delta > 0**（smoke 运行期间新增 failed ack）时 fail；历史累计值记入 `observations` |

**Outbox 模式**

| 模式 | 触发 | failed_ack 规则 |
|------|------|-----------------|
| **isolated**（默认） | 无 flag；使用 temp outbox | 绝对值 `== 0` |
| **repo** | `--use-repo-outbox` | delta 规则；`demo_phase` 等共享 outbox 上可能存在历史 `tracking_status=failed`（例如 feedback ingest 探针、dispatch 单测残留）——**不**单独构成 CI fail |

**特例说明（demo_phase 漂移）**：共享 `outbox/` 在多次 MP-SMOKE / ingest 单测后可能保留 `notifications_failed_ack_count>0`，而当次 smoke 七步仍全绿。CI-SMOKE **默认 isolated** 避免误判；若需对共享 outbox 做 observability 巡检，使用 `--use-repo-outbox` 并查看 `observations` 行。

### 5.3 典型命令

```bash
python scripts/run_ci_smoke_check_v1.py --format text
python scripts/run_ci_smoke_check_v1.py --case-ref demo_phase --format json
python scripts/run_ci_smoke_check_v1.py --use-repo-outbox --format text
# exit 0 = pass · exit 1 = fail
```

### 5.4 输出契约（`ci_smoke_check_v1`）

| 键 | 含义 |
|----|------|
| `ok` | 全部 checks 通过 |
| `checks` | 三项布尔/计数 |
| `failures` | 人类可读失败列表 |
| `multi_phase_smoke` | 嵌套 MP-SMOKE 结果 |
| `std_case_metrics` | 嵌套 MP-METRICS 结果 |

### 5.5 CI-advisory 默认

- **默认**：L-local CLI · **无** production workflow required 接入。
- **若** 接入 GHA：须 `continue-on-error: true` 或等价 non-required，直至 WC-PRE-07 批文。
- **不得** 在本契约未修订前将 CI-SMOKE 标为 merge gate。

### 5.6 Verify / Observe

```bash
python -m unittest tests.test_ci_smoke_check_v1 -v
python scripts/run_ci_smoke_check_v1.py --format text
```

---

## 6. 典型执行命令链（Release sanity）

**推荐顺序**（与 Dashboard §Multi-phase smoke 对齐）：

```text
Fleet（优先）
  MC-1  run_multi_case_smoke_v1.py --cases demo_phase,sampleco
  MC-2  aggregate_multi_case_metrics_v1.py --format json
  MC-3  (可选) run_multi_case_smoke_v1.py  # 含 phi_demo deny 探针

Single-case（深挖）
  MP-1  run_multi_phase_smoke_v1.py --case-ref demo_phase
  MP-2  export_std_case_metrics_v1.py --case-ref demo_phase
  MP-3  run_ci_smoke_check_v1.py          # 合成 pass/fail + exit code

Optional 扩展
  MP-4  run_multi_phase_smoke_v1.py --enable-dispatch
  INT   04_Workflows/_wave7_regression_gate.py --tier A   # 装配变更时 · 非 smoke 替代
```

**与 INT regression gate**：装配/envelope/manifest 变更 **必须** 另跑 INT Tier-A；**不能**用 MP-1 代替。

---

## 7. Toolchain smoke matrix 栏位含义

**SSOT**：`routing/toolchain_smoke_matrix_v1.yaml`

| YAML 栏 | 含义 |
|---------|------|
| `smoke_id` | 稳定 ID（`TS-*`） |
| `command` | 可复制的本地命令 |
| `tier` | `local_recommended` · `optional_ci` · `release_only` |
| `gate_class` | `mandatory` · `optional` · `shadow`（矩阵内 smoke **均为 optional**） |
| `blocks_mainline` | 解释 Tabular MVP mainline 就绪语义；**非** GitHub merge block |
| `estimated_seconds` | 规划用；**非 SLA** |
| `wa_t3_gate_id` | 对齐 P3.5 optional gate 表；可 null |
| `source_ticket` | 溯源票号 |
| `notes` | 人类说明 · deny 探针等 |

**MP/MC/CI 矩阵条目**（v1 扩展）：`TS-MP-SMOKE` · `TS-MC-SMOKE` · `TS-CI-SMOKE` 及对应 unittest 伴侣 — 见 YAML `entries`。

**执行**：`python scripts/run_toolchain_smoke_matrix.py --list` · `--smoke-id TS-MP-SMOKE`

**与 phase6 附录 A 关系**：附录 A 列 **toolchain/agent-lines** smoke；**本契约**列 **MP/MC/CI release sanity** — 互补，不合并为 INT Tier-A。

---

## 8. Non-Claims

| 禁止 | 正确 |
|------|------|
| smoke 全绿 = Phase 6 closure | L-local release sanity · Dashboard P6 % 见 Governance |
| CI-SMOKE 绿 = PR required 已挂 | 默认 local · advisory wiring 单独披露 |
| MP-SMOKE = P7 Round-2 staging GO | Round-2 仍可能 blocked_on 五顶前置 |
| MC-SMOKE 默认列表全绿 = fleet prod-ready | demo/sampleco 代表性 case only |
| matrix `blocks_mainline=true`（MVP mainline）= GitHub merge block | release checklist 语义 |
| smoke 替代 INT Tier-A | 分轨 · 见 phase6 §5 |

---

## 9. Cross-References

| 文档 | 用途 |
|------|------|
| `docs/phase6-int-regression-gate-contract-v1.md` | INT Tier-A/B · PR trio · 附录 A |
| `docs/wave-progress-dashboard-skeleton-v1.md` | P6 指标槽 · 双轨权责 |
| `docs/toolchain-health-dashboard-v1.md` | P5 health（与 smoke 分轨） |
| `04_Workflows/WORKFLOW_INDEX.md` §1.5 | runner 索引 |
| `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` | G-1–G-5（resume-loop 分轨） |

---

## 10. Verification bundle

```bash
python -m unittest tests.test_multi_phase_smoke_v1 tests.test_multi_case_smoke_v1 tests.test_ci_smoke_check_v1 tests.test_phase6_toolchain_smoke_matrix_v1 -v
python scripts/run_toolchain_smoke_matrix.py --smoke-id TS-MP-SMOKE --dry-run --format json
```

---

*smoke-and-regression-contract-v1 · Lane B · doc-only · 2026-06-26*
