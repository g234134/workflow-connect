# W4-A Gate Checklist — K-2 shadow / internal canary



> **配套**：`W4-A_rollout_runbook.md` · `wf_k2_rollout_run.ps1` · `rollout_pipeline_config.json` → `trace_contract`  

> **用法**：每次 `-Phase full|shadow|canary` 后勾选；未满足项标阻塞，不得宣称 prod rollout。  

> **对照 helper**（只读）：`python workflow_v2/tools/wf_k2_rollout_gate_trace.py --trace <run_records/<run_id>/rollout_trace.jsonl>`



---



## 0. Trace / phase / ART-REL 命名对照（W4-A-FIX-01）



| 层 | Shadow（P1） | Canary（P2） |

|----|--------------|--------------|

| **Checklist 门** | §A shadow 门 | §B canary 门 |

| **VERDICT stdout** | `step=shadow` | `step=canary` |

| **trace 细步** `run_records/<run_id>/rollout_trace.jsonl` | `k2_shadow_unittest` → `ibridge_exporter_shadow` → `eval_ci_check_shadow` | `internal_canary` |

| **trace phase 摘要**（runner v0.2+） | 行含 `step=shadow` 且 `kind=phase_summary` | 行含 `step=canary` 且 `kind=phase_summary` |

| **trace `phase` 字段**（v0.1.1+） | 子步**须**带 `"phase":"shadow"` | 子步**须**带 `"phase":"canary"` |

| **粗粒度 trace** `runs/rollout_trace.jsonl` | `step=shadow`（`ok`/`release_id`/`artifact`） | `step=canary`（`ok`/`traffic_percent`/`artifacts`） |

| **ART-REL DEC `k2_phase`** | `shadow`（若单独 DEC） | `internal_canary`（≡ checklist「canary 门」≡ trace 细步 `internal_canary`） |



**命名 alias 速记**：checklist「shadow / canary 门」↔ VERDICT `step=shadow|canary` ↔ 粗 trace `runs/rollout_trace.jsonl` 同名字段 ↔ DEC `k2_phase=internal_canary`（canary 侧）↔ 细 trace 子步 `internal_canary`（canary 侧细步名与 DEC alias 同名）。



**双 trace 路径**：`run_records/<run_id>/rollout_trace.jsonl` 为 ps1/sim **细粒度**逐步记录（含 `exit_ok`/`note`/`phase`）；`runs/rollout_trace.jsonl` 为案卷级**粗粒度**摘要（`step=shadow|canary`，字段集不同，非 ps1 直接写入）。Gate A6/B8 以 **run_records** 细 trace 为准；粗 trace 仅作 cross-check。



**旧 trace 例外（v0.1.0）**：2026-05-29 等历史 run（例 `2026-05-29_111042`）中 `ibridge_exporter_shadow`、`eval_ci_check_shadow`、`internal_canary` 行**无** `phase` 字段；验收时可 fallback 至 phase 摘要行或 sub_steps 全绿，**不得** retro 改历史 run_records。



**Gate 判定原则**：A6/B8 验收 **phase 层**（shadow / canary 整段通过），不要求 trace 细步名等于 VERDICT 的 `step=` 字符串；细步清单见 config `trace_contract.phases.*.trace_sub_steps`。



**已知限制（勿在本 checklist 冒充已验）**：



- `rollback_path_valid` 语义与 B6 对账 → **W4-A-FIX-02** 已在 template / runbook 对齐 v0.1 说明；**实产** `08_art_rel_exec.json` 仍为 `false`，不得 retro 修改。

- `canary_cohort_state.json` 落点与 C1 语义 → **W4-A-FIX-03** 已在 checklist C1 / §G 与 runbook §5.2 对齐 v0.1 说明；**实产**仍在 `runs/<release_id>/`，rollback **不**回写该文件。

- `override_record.json` 无样例 run → 票 **W4-A-FIX-04**；C2/C3 在无 override run 时标 **N/A**，不得假造样例。



---



## A. Shadow 门（P1）



| # | 检查项 | 证据 | ✓ |

|---|--------|------|---|

| A1 | `ibridge_exporter --source shadow` exit 0 | `run_records/<run_id>/eval/shadow_ibridge_records.latest.jsonl` 存在 | |

| A2 | `eval_ci_check` exit 0 | `run_records/<run_id>/shadow_state.json` → `"ok": true` | |

| A3 | `infra_risk` 未触发 fail-on-tags | eval stdout `stats.tag_triggered` = false | |

| A4 | user-facing 仍为 ask-only | runbook §3；无 prod 主路径变更 | |

| A5 | `shadow_run_01.md` 已写 | `run_records/<run_id>/shadow_run_01.md` | |

| A6 | **shadow phase** trace 通过 | `run_records/<run_id>/rollout_trace.jsonl`：见 §0 — phase 摘要行 **或** 全部 shadow `trace_sub_steps` 存在且 `exit_ok=true`；**v0.1.1+** 子步须带 `"phase":"shadow"`（旧 run 无 phase 见 §0 例外） | |



---



## B. Canary 门（P2）



| # | 检查项 | 证据 | ✓ |

|---|--------|------|---|

| B1 | shadow gate 或合法 override | `shadow_state.ok` 或案卷根 `override_record.json` | |

| B2 | traffic 5–10% | `07_art_rel_dec.json` → `traffic_percent` | |

| B3 | `ART-REL-DEC` = approve | `07_art_rel_dec.json` → `artifact_id` = `ART-REL-DEC` | |

| B4 | `ART-REL-EXEC` 已发布 | `08_art_rel_exec.json` → `artifact_id` = `ART-REL-EXEC` + `published_at` | |

| B5 | `canary_env.md` 逻辑名一致 | 与 DEC `target_audience_or_env` | |

| B6 | `rollback_path_valid` 语义 | **理想目标**（Wave 5 / W4-A-FIX-02.x）：`true` = 完整自动 rollback 路径已建立且端到端验证。**W4-A v0.1 实际**：`08_art_rel_exec.json` 多为 `false`（sim 默认；代表无完整自动 rollback path）— 本 pilot 可标 **accepted_with_gaps**，见 §F | |

| B7 | `not_in_scope` 含无远端 prod | EXEC 字段 | |

| B8 | **canary phase** trace 通过 | `run_records/<run_id>/rollout_trace.jsonl`：`step=internal_canary` **或** phase 摘要 `step=canary`（`kind=phase_summary`），且 `exit_ok=true`；**v0.1.1+** 子步须带 `"phase":"canary"`（旧 run 无 phase 见 §0 例外） | |



---



## C. Rollback / Override



| # | 检查项 | 证据 | ✓ |

|---|--------|------|---|

| C1 | rollback 将 cohort 置 0 | **理想目标**：案卷根或统一 cohort 状态文件 → `active=false`、`traffic_percent=0`、`primary_source=ask`，且与 `rollback_record.json` 一致。**W4-A v0.1 实际**：`canary_cohort_state.json` 落在 **`runs/<release_id>/canary_cohort_state.json`**（例：`runs/w4a-int-20260529-pilot/canary_cohort_state.json`）；仅含 minimal v0.1 字段（`active`、`traffic_percent`、`primary_source`、`cohort_logical`、`release_id`、`recorded_at`、`schema_version`）；**`-Phase rollback` 不写此文件**（cohort 归零证据见案卷根 `rollback_record.json`）。本 pilot 可标 **accepted_with_gaps**，见 §G | |

| C2 | override 角色在 allowlist | `override_record.json`（无样例 run 时 **N/A** · FIX-04） | |

| C3 | override 含 reason 文本 | 同上 | |



---



## F. Gap / Result — `rollback_path_valid`（W4-A-FIX-02 · CHK-W4 GAP-2 文档对齐）



| 项 | 说明 |

|----|------|

| **CHK-W4 GAP-2** | checklist B6 曾要求 `true`，实产 `08_art_rel_exec.json` 为 `false` — 属**语义**分歧，非字段名错误 |

| **本票（FIX-02）** | 仅对齐 template / checklist / runbook 描述；**不**改 `08_art_rel_exec.json`、**不**改 sim.py 产出 |

| **v0.1 实际状态** | `rollback_path_valid: false` = 有 DEC 草案 + 手动 `-Phase rollback`（写 `rollback_record.json`），但**无**完整自动 rollback 与 cohort 回写验证 |

| **理想目标** | 自动 rollback 流程 + 验证通过后，EXEC 可置 `true`（后续 **W4-A-FIX-02.x** 或 Wave 5 结构票） |

| **Gate 签收** | v0.1 internal canary pilot 在 B6=false 时可 **`accepted_with_gaps`**；不得宣称「rollback path 已完整实作」 |



---



## G. Gap / Result — `canary_cohort_state.json`（W4-A-FIX-03 · CHK-W4 GAP-3 文档对齐）



| 项 | 说明 |

|----|------|

| **CHK-W4 GAP-3** | checklist C1 曾隐含案卷根 `canary_cohort_state.json`；实产落在 **`runs/<release_id>/`** 子路径，与 rollback 无自动回写 |

| **本票（FIX-03）** | 仅对齐 checklist / runbook / schema 描述；**不**移动文件、**不**改 sim.py 产出、**不** retro 改实产 JSON |

| **v0.1 实际路径** | `20_pilot/W3-A_case/runs/<release_id>/canary_cohort_state.json`（当前样例：`runs/w4a-int-20260529-pilot/`）— 设计上的**暂定落点**，非案卷根 |

| **v0.1 实际内容** | `schema_version=w4a-canary-cohort-v0.1`；`active`、`traffic_percent`、`primary_source`、`cohort_logical`、`release_id`、`recorded_at` — **无** per-task 分流明细（明细在 `08_art_rel_exec.json` → `execution_evidence.canary_assignments` 与 `canary_run_01.md`） |

| **产出时机** | 与 `runs/<release_id>/` 案卷 run 目录一并存在；**非** `wf_k2_rollout_canary_sim.py` 写入（sim 写案卷根 `07`/`08`/`canary_env.md` + `run_records/<run_id>/canary_run_01.md`） |

| **rollback 缺口** | `-Phase rollback` 写案卷根 `rollback_record.json`（`traffic_percent=0`），**不**更新 `runs/.../canary_cohort_state.json` 的 `active`/`traffic_percent` — C1 完整验收须 dual-check 或标 gap |

| **理想目标** | 统一 cohort 状态索引（案卷根或别名）、rollback 自动回写、与 trace / EXEC 端到端一致 — 后续 **W4-A-FIX-03.x** 或 Wave 5 结构票 |

| **Gate 签收** | v0.1 internal canary pilot 在 C1 仅 `rollback_record.json` 归零时可 **`accepted_with_gaps`**；可索引、可读 cohort 配置与分布（经 EXEC assignments），但**不构成**完整自动治理证据 |



---



## D. 硬禁区（任一为真 → 停工）



- [ ] 修改了 prod 主 `.github/workflows` release  

- [ ] 宣称远端 prod Phase 3+ 完成  

- [ ] 输出 `.env` / 密钥原文  

- [ ] 修改 `merge_ask_and_k2` / adapter 实现（本票范围外）



---



## E. 签收行



| 字段 | 值 |

|------|-----|

| release_id | |

| checker | |

| date | |

| verdict | `pass` \| `accepted_with_gaps` \| `fail` |


