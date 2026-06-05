# Ticket Memory — W4-A-FIX-01-GATE-TRACE-ALIGN

> **票号**：`W4-A-FIX-01-GATE-TRACE-ALIGN`
> **lane**：`planning`（本票：只产 plan，不执行实装修补）
> **父票**：`CHK-W4-WAVE4-CLOSURE`（GAP-1：gate checklist trace 键名不一致）
> **切片性质**：planning-only / readonly-only
> **本票输出**：仅本文文件 `workflow_v2/40_ticket_memory/W4-A-FIX-01-GATE-TRACE-ALIGN.memory.md`
> **执行票**：另开 `W4-A-FIX-01-RUNTIME`（`lane=runtime`）执行下述 Cursor brief

---

## Scope / non-goals

### Scope（本票分析范围）
1. 盘查 gate checklist key、rollout trace step 名称、ART-REL JSON 栏位名之间的不一致
2. 给出一张「现行 key / 建议 key / 所在档 / 是否需 alias / 风险」对照表
3. 产出一份可直接交给 Cursor 的最小 patch 计划（implementation brief skeleton）
4. 明确哪些 gap 能解、哪些因缺 override 历史 run 仅标不解

### Non-goals（本票不做）
- 不修改任何 `.github/workflows/**`
- 不修改任何 `run_records/**`（历史证据不可改写）
- 不修改 `workflow_v2/00_master_plan.md`、`90_run_queue.md`、`99_latest_status.md`
- 不修改 `rollout_pipeline_config.json`、`W4-A_release_stream.json`（core logic）
- 不预先实作 rename / mapping / patch — 本票只产 plan
- 不解 `canary_cohort_state.json` 落点问题 → `W4-A-FIX-03`
- 不解 `override_record.json` 缺样例 run → `W4-A-FIX-04`
- 不解 `runs/` vs `run_records/` 双路径架构问题 → 属 wave 5 结构票

---

## Evidence inspected

| # | 文件 | 用途 |
|---|------|------|
| 1 | `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` | Gate 勾选范式，§0 命名对照表，A/B/C/D/E 段 |
| 2 | `workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md` | Shadow/canary/rollback/override 权威步骤描述 |
| 3 | `workflow_v2/tools/wf_k2_rollout_run.ps1` | 主执行器，trace 写入逻辑 |
| 4 | `workflow_v2/tools/wf_k2_rollout_canary_sim.py` | Cohort 模拟；DEC/EXEC JSON 生成；rollback_path_valid 硬编码 |
| 5 | `workflow_v2/tools/wf_k2_rollout_gate_trace.py` | Gate ↔ trace 对齐 helper（只读），消费 config `trace_contract` |
| 6 | `workflow_v2/20_pilot/W3-A/rollout_pipeline_config.json` | 固定流配（k2_phases, shadow_step, canary_step, override, rollback） |
| 7 | `workflow_v2/20_pilot/W3-A_case/W4-A_release_stream.json` | 流指针 |
| 8 | `workflow_v2/20_pilot/W3-A_case/07_art_rel_dec.json` | ART-REL-DEC 实产 |
| 9 | `workflow_v2/20_pilot/W3-A_case/08_art_rel_exec.json` | ART-REL-EXEC 实产 |
| 10 | `workflow_v2/20_pilot/W3-A_case/_TEMPLATE_art_rel_dec.json` | DEC 模板（W3-A 年代，stale） |
| 11 | `workflow_v2/20_pilot/W3-A_case/_TEMPLATE_art_rel_exec.json` | EXEC 模板（W3-A 年代，stale；rollback_path_valid=true） |
| 12 | `workflow_v2/20_pilot/W3-A_case/rollback_record.json` | Rollback 产出（action/primary_source/traffic_percent） |
| 13 | `run_records/2026-05-29_111042/rollout_trace.jsonl` | 最新 full run trace（shadow sub-steps + canary） |
| 14 | `run_records/2026-05-29_111042/shadow_state.json` | Shadow state（标准 schema） |
| 15 | `run_records/2026-05-29_111025/rollout_trace.jsonl` | 同结构 trace（确认 schema 稳定） |
| 16 | `run_records/2026-05-29_110959/rollout_trace.jsonl` | 早期 schema（`k2_shadow` / `eval_ci_check_fixture`，有 `phase` 字段） |
| 17 | `run_records/2026-05-29_111011/rollout_trace.jsonl` | Rollback-only trace（`step=rollback`，无 `phase`） |
| 18 | `run_records/2026-05-31_083827/rollout_trace.jsonl` | Dry-run trace（有 `phase` + `kind=phase_summary`） |
| 19 | `runs/w4a-int-20260529-pilot/canary_cohort_state.json` | Cohort state（非 run_records 路径；独立 schema） |
| 20 | `runs/w4a-int-20260529-pilot/shadow_state.json` | Shadow state（双路径版；不同 stream_id） |
| 21 | `runs/rollout_trace.jsonl` | 粗粒度 trace（`step=shadow`/`step=canary`；与 checklist coarse 命名一致） |
| 22 | `CHK-W4-WAVE4-CLOSURE.memory.md` | 父票，GAP-1 ~ GAP-5 定调 |

---

## Key alignment findings

### Finding 1：Trace `phase` 字段写入不完整（ps1 bug）

| 现状 | 问题 |
|------|------|
| `k2_shadow_unittest` 有 `"phase":"shadow"`（ps1 L97） | OK |
| `ibridge_exporter_shadow` **无** `phase` 字段（ps1 L128） | 缺 |
| `eval_ci_check_shadow` **无** `phase` 字段（ps1 L150） | 缺 |
| `internal_canary` **无** `phase` 字段（ps1 L213） | 缺；应带 `"phase":"canary"` |

- Checklist §0 写「子步可带 `phase`」— 实际仅第 1 步子步带，其余缺失。
- 旧 schema（110959）三道 trace 行皆带 `phase`；当前 ps1 退化。
- Dry-run（083827）恢复了 `phase` + `kind=phase_summary`，证明修复方向已知但未合入主线 ps1。
- **根因**：`wf_k2_rollout_run.ps1` 仅在 `k2_shadow_unittest` 写入 `phase`，其他三个 trace 写入点缺该字段。

### Finding 2：Trace 细步名与 checklist / runbook 对账

| 层 | checklist / runbook 用名 | 实际 trace 用名 | 对账 |
|----|--------------------------|-----------------|------|
| 粗 VERDICT | `step=shadow` | ps1 stdout `VERDICT=OK step=shadow` | OK |
| 粗 VERDICT | `step=canary` | ps1 stdout `VERDICT=OK step=canary` | OK |
| 细 shadow sub-step 1 | `k2_shadow_unittest`（checklist §0） | `k2_shadow_unittest` | OK |
| 细 shadow sub-step 2 | `ibridge_exporter_shadow`（checklist §0） | `ibridge_exporter_shadow` | OK |
| 细 shadow sub-step 3 | `eval_ci_check_shadow`（checklist §0） | `eval_ci_check_shadow` | OK |
| 细 canary sub-step | `internal_canary`（checklist §0） | `internal_canary` | OK |
| 旧 schema shadow | — | `k2_shadow`、`eval_ci_check_fixture`（110959） | 已迁移不适用 |
| Dry-run summary | `kind=phase_summary` + `step=canary` | ✓ 存在（083827） | OK（v0.2+ 功能） |

- 粗/细命名**当前**已基本对齐 checklist §0，不再算 gap。
- 但 `runs/rollout_trace.jsonl` 使用 `step=shadow`/`step=canary`（粗粒度），与 `run_records/` 细粒度双重 schema — 见 Finding 5。

### Finding 3：`runs/rollout_trace.jsonl` vs `run_records/<id>/rollout_trace.jsonl` 双 schema

| 项目 | `runs/rollout_trace.jsonl` | `run_records/<id>/rollout_trace.jsonl` |
|------|---------------------------|----------------------------------------|
| 粒度 | 粗（phase 层：`step=shadow`/`step=canary`） | 细（子步层：`k2_shadow_unittest` 等） |
| 字段 | `ts`, `step`, `release_id`, `ok`, `artifact` / `artifacts`, `traffic_percent` | `step`, `phase`, `exit_ok`, `note`, `kind`（可选） |
| 来源 | 非 ps1/sim 写入；疑似手动或独立 helper | ps1 / sim 直接写入 |
| checklist 引用 | 未记录 | §0 表已记录细步名 |
| 影响 | checklist A6/B8 检查时需确定用哪个 trace | gate_trace.py 消费此路径 |

- checklist §0 **缺** `runs/rollout_trace.jsonl` 的说明 — 该文件恰与 checklist 粗 `step=shadow`/`step=canary` 命名完全相同，值得补记。

### Finding 4：`rollback_path_valid` checklist B6 vs EXEC vs TEMPLATE vs code — 三方不一致

| 源 | 值 | 说明 |
|----|-----|------|
| checklist B6 | 要求 `true`（「须 true」） | gate 准入条件 |
| `08_art_rel_exec.json` | `false` | 实际产出 |
| `_TEMPLATE_art_rel_exec.json` | `true` | 模板语义 |
| `wf_k2_rollout_canary_sim.py` L122 | 硬编码 `False` | 代码行为 |

- 语义分歧：TEMPLATE 认为 rollback path 有效（已演练），代码硬编码 `False`（因 W4-A 属 CHG-OBS-ONLY 且未接真实 infra rollback）。
- CHK-W4 已标记为 GAP-2 → `W4-A-FIX-02`。
- **本票不解决**此 gap，但需在对账表中明确记录三方的 field name 一致（都用 `rollback_path_valid`），分裂点仅在**值语义**，不在命名。

### Finding 5：`canary_cohort_state.json` 落点与 checklist C1 不一致

| 源 | 路径 |
|----|------|
| checklist C1 隐含 | 案卷根（`W3-A_case/canary_cohort_state.json`） |
| 实际落点 | `W3-A_case/runs/w4a-int-20260529-pilot/canary_cohort_state.json` |
| 额外问题 | 该文件非 sim.py 产出；`active=true` 但 trace `cohort=0/5`（语义矛盾） |

- CHK-W4 已标记为 GAP-3 → `W4-A-FIX-03`。
- **本票不解决**落点问题，仅记录 field name 一致性：文件内字段 `traffic_percent`、`primary_source`、`active` 与 config `k2_phases.internal_canary` 中 `traffic_percent`（5）、`primary_source`（k2）对账一致，口径无命名冲突。

### Finding 6：`_TEMPLATE_art_rel_*` 模板 stale（W3-A → W4-A 未同步）

| 字段 | `_TEMPLATE_art_rel_dec.json` | `07_art_rel_dec.json`（实际） |
|------|------------------------------|------------------------------|
| `ticket_id` | `W3-A-CANARY-PILOT` | `W4-A-K2-ROLLOUT-INTEGRATION` |
| `release_id` | `w3a-p2-canary-YYYYMMDD` | `w4a-p2-canary-2026-05-29` |
| `decided_at` | `YYYY-MM-DD` | `2026-05-29` |

| 字段 | `_TEMPLATE_art_rel_exec.json` | `08_art_rel_exec.json`（实际） |
|------|-------------------------------|-------------------------------|
| `ticket_id` | `W3-A-CANARY-PILOT` | `W4-A-K2-ROLLOUT-INTEGRATION` |
| `rollback_path_valid` | `true` | `false` |
| 缺字段 | 无 `pilot_stream_id`, `run_id`, `canary_assignments` | 有 |

- 模板仍标 W3-A 票号，未更新至 W4-A。
- EXEC 模板缺 `pilot_stream_id`、`run_id`、`canary_assignments` 三个 sim.py 实际产出的字段。
- 不影响 runtime（sim.py 内联结构决定产出，不读模板），但影响 Cursor / 人类审查时对字段口径的理解。

### Finding 7：`shadow_state.json` 双路径 schema 差异

| 字段 | `run_records/111042/shadow_state.json` | `runs/w4a-int-.../shadow_state.json` |
|------|----------------------------------------|--------------------------------------|
| `schema_version` | `w4a-shadow-state-v0.1` | `w4a-shadow-state-v0.1` |
| `ok` | ✓ | ✓ |
| `eval_message` | ✓ | ✓ |
| `recorded_at` | ✓ | ✓ |
| `phase` | **缺** | `"shadow"` |
| `stream_id` | **缺** | `"W4-A-INTERNAL-K2-STREAM-v1"` ← **错值** |
| `release_id` | **缺** | ✓ |
| `export_ref` | **缺** | ✓ |
| `shadow_run_ref` | **缺** | ✓ |

- `runs/` 版 `stream_id` 为 `W4-A-INTERNAL-K2-STREAM-v1`，与权威 config `W4-A-PILOT-RELEASE-STREAM-v0.1` 不一致 — **命名冲突**。
- `runs/` 版非 ps1/sim 产出，来源不明；本票仅记录此冲突，不解决。

### Finding 8：`rollback_record.json` 字段名与 checklist / config 对照

| 字段 | `rollback_record.json` | config `rollback` | checklist C1 |
|------|------------------------|-------------------|--------------|
| 流量归零 | `traffic_percent: 0` | `default_action: ask_only_cohort_zero` | "将 cohort 置 0" |
| 主源回退 | `primary_source: ask` | 隐含 | — |
| 动作名 | `action: ask_only_cohort_zero` | `default_action` | — |
| 记录名 | `rollback_record.json` | `record_filename: rollback_record.json` | — |

- 字段口径一致，**无命名冲突**。
- 但 rollback 不写 `canary_cohort_state.json`（未更新 `active=false`）— 语义 gap 属 FIX-03。

### Finding 9：`wf_k2_rollout_gate_trace.py` 依赖 config `trace_contract` — config 缺失该 key

- Helper（L40-42）：读取 `config["trace_contract"]["phases"]`。
- 实际 config 无 `trace_contract` 键 → `_phase_cfg` 返回空 dict → shadow sub_steps 默认为 `[]`。
- 导致 `_sub_steps_ok` 对 shadow 永远返回 `False`（无 sub_steps 清单可校对）。
- **影响**：helper 无法正确校验 111042 trace（该 trace 无 `kind=phase_summary` 行，只能靠 sub_steps 校验，而 sub_steps 清单为空）。
- **本票记录**：config 缺 `trace_contract` 是 helper 可用性的门控缺陷，但属配置增强（wave 5），不属本票命名修复范围。

### Finding 10：checklist §0 命名对照表完备性

当前 §0 表已记录：
- VERDICT stdout `step=shadow` / `step=canary`
- Trace 细步名
- `kind=phase_summary` 行
- Trace `phase` 字段
- ART-REL DEC `k2_phase` = `internal_canary`

当前 §0 表**缺失**：
- `runs/rollout_trace.jsonl` 粗粒度 trace（`step=shadow`/`step=canary`）
- `runs/` 下 shadow_state / canary_cohort_state 路径与 `run_records/` 版的差异
- `phase` 字段的义务说明：checklist 写「子步可带」，但实际应改为「子步须带」（以 aligned schema 为目标）
- Dry-run `kind=phase_summary` 的 step 名（`step=canary` 非 `step=internal_canary`）

---

## Proposed normalization strategy

### 策略总纲

**最小修补面**：只做命名/字段口径对齐，不改 core logic、不改 CI、不改历史 run_records。

原则：
1. Checklist 文案优先向 **实际产出** 对齐（减少改 tool 的风险）
2. Tool 只在明显「少写了一个无害字段」时补字段（补 `phase`）
3. 模板只更新 ticket_id / 补缺失字段，不改变任何代码读取模板的逻辑
4. 不引入 alias/mapping 层 — 命名直接统一
5. 所有修改文件 ≤ 5 个

### 具体修改分区

#### Zone A：改 tool（ps1 + sim.py）— 最小字段补写

| 文件 | 修改 | 理由 |
|------|------|------|
| `tools/wf_k2_rollout_run.ps1` | 在 `ibridge_exporter_shadow`、`eval_ci_check_shadow`、`internal_canary` 的 trace 行补 `phase` 字段 | 旧 schema（110959）和三步中第一步均有 `phase`，后三步缺失是退化 bug，非设计意图 |
| `tools/wf_k2_rollout_canary_sim.py` | 不改（`rollback_path_valid` 值语义属 FIX-02） | 命名本身一致 |

具体 patch（ps1）：
- L128-129：`@{ step = "ibridge_exporter_shadow"; exit_ok = ... }` → 加 `phase = "shadow"`
- L150：`@{ step = "eval_ci_check_shadow"; exit_ok = ...; note = ... }` → 加 `phase = "shadow"`
- L213-217：`@{ step = "internal_canary"; exit_ok = ...; note = ... }` → 加 `phase = "canary"`

风险评估：极低 — `phase` 为纯标记字段，不影响任何 gate 判定逻辑；`wf_k2_rollout_gate_trace.py` 的 `_phase_summary_ok` 已按 `phase` 字段匹配。

#### Zone B：改 checklist 文案 — 补充缺失说明

| 文件 | 修改 | 理由 |
|------|------|------|
| `W4-A_gate_checklist.md` §0 表 | 新增行：「`runs/rollout_trace.jsonl`（粗粒度）」：`step=shadow` / `step=canary` | 双 trace 路径事实存在，checklist 应记录 |
| `W4-A_gate_checklist.md` §0 表 | `trace phase 字段` 行：改「子步可带」→「子步须带（v0.1.1+）」 | 对齐 Finding 1 修复后的预期 |
| `W4-A_gate_checklist.md` §0 表 | 新增行：「`shadow_state.json`（run_records 版）」字段列表 | 补全 §0 对 state 文件的索引 |
| `W4-A_gate_checklist.md` C1 | 加注：`canary_cohort_state.json` 当前落 `runs/w4a-int-20260529-pilot/`（非案卷根），路径对账见 FIX-03 | 已知 gap 留痕 |

#### Zone C：改模板 — 同步 W3-A → W4-A

| 文件 | 修改 | 理由 |
|------|------|------|
| `_TEMPLATE_art_rel_dec.json` | `ticket_id` → `W4-A-K2-ROLLOUT-INTEGRATION`；`release_id` → `w4a-p2-canary-YYYYMMDD`（保持模板占位符风格） | 模板 stale，影响人类阅读 |
| `_TEMPLATE_art_rel_exec.json` | `ticket_id` → `W4-A-K2-ROLLOUT-INTEGRATION`；新增 `pilot_stream_id`、`run_id`、`canary_assignments` 占位字段；`rollback_path_valid` 保持 `true`（模板语义与代码分歧属 FIX-02，不在此票改模板值） | 补全字段索引 |

风险评估：模板仅被人类阅读，不被任何代码消费；修改零风险。

#### Zone D：不改 — 标注 follow-up

| 项目 | 不改原因 | follow-up |
|------|----------|-----------|
| `rollback_path_valid` 值语义 | 属 FIX-02 | `W4-A-FIX-02` |
| `canary_cohort_state.json` 落点 | 属 FIX-03 | `W4-A-FIX-03` |
| `override_record.json` 缺样例 | 属 FIX-04 | `W4-A-FIX-04` |
| `wf_k2_rollout_gate_trace.py` 缺 config `trace_contract` | 属配置增强（wave 5） | 标记 known_gap |
| `runs/` vs `run_records/` 双路径 | 属架构票 | wave 5 结构对齐票 |
| `runs/shadow_state.json` 中 `stream_id` 错值 | 非 tool 产出，来源不明 | 调查后单独处理 |

---

## Allowed file edit set

Cursor 实施 `W4-A-FIX-01-RUNTIME` 时，**最多**可触以下文件：

| # | 文件 | 修改类型 | 理由 |
|---|------|----------|------|
| 1 | `workflow_v2/tools/wf_k2_rollout_run.ps1` | 补 3 处 `phase` 字段 | 退化 bug 修复；零逻辑影响 |
| 2 | `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` | 文案补全（§0 表 + C1 注） | 文档对齐实际产出 |
| 3 | `workflow_v2/20_pilot/W3-A_case/_TEMPLATE_art_rel_dec.json` | `ticket_id` 更新 | 模板 stale |
| 4 | `workflow_v2/20_pilot/W3-A_case/_TEMPLATE_art_rel_exec.json` | `ticket_id` + 补字段 | 模板 stale + 缺字段 |

**总计：4 个文件，无 core logic 变更，无 CI 变更。**

---

## Explicit no-touch set

以下文件/目录**禁止**本票（含后续 RUNTIME 执行票）修改：

| 类别 | 路径 |
|------|------|
| CI | `.github/workflows/**` |
| 历史证据 | `run_records/**`（含所有 `2026-05-29_*` 及 `2026-05-31_*`） |
| 全局黑板 | `workflow_v2/00_master_plan.md`、`90_run_queue.md`、`99_latest_status.md` |
| Core config | `rollout_pipeline_config.json`、`W4-A_release_stream.json` |
| 实产 ART-REL | `07_art_rel_dec.json`、`08_art_rel_exec.json` |
| 其他 tools | `wf_k2_rollout_canary_sim.py`、`wf_k2_rollout_gate_trace.py` |
| 任何 production / pilot runtime 行为档 | 包括 `canary_cohort_state.json`、`rollback_record.json`、所有 runs/ 下文件 |

---

## Risks / rollback notes

| 风险 | 等级 | 缓解 |
|------|------|------|
| ps1 补 `phase` 字段后，旧 trace 与新 trace 字段不一致（历史 run_records 不改） | 低 | gate_trace.py 已实现 `_sub_steps_ok` fallback（不依赖 `phase` 字段），新旧兼容 |
| `_TEMPLATE_*` 更新后与 `07`/`08` 实产细微差异（如 `rollback_path_valid`） | 无 | 模板不被代码消费 |
| checklist §0 补全后与未更新的旧 run_records 描述有出入 | 低 | §0 加注「v0.1.1+」区分 schema 版本 |

**回退**：ps1 的 `phase` 字段补写可用 `git revert` 一键回退，不影响任何 gate 判定（gate_trace.py 不依赖此字段做决策，仅做标记）。

---

## Cursor brief skeleton

以下是可直接交给 Cursor（`implementation-worker`）的执行 brief 骨架：

```
票号: W4-A-FIX-01-RUNTIME
目标: 对齐 gate checklist 与 rollout trace / ART-REL 的命名口径（4 文件最小修补）

文件 1: workflow_v2/tools/wf_k2_rollout_run.ps1
  修改: 在 3 个 trace 写入点补充 "phase" 字段
  位置: L128-129 (ibridge_exporter_shadow), L150 (eval_ci_check_shadow), L213-217 (internal_canary)
  变更: 各加 `phase = "shadow"` 或 `phase = "canary"` 至对应的 @{} hashtable

文件 2: workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md
  修改: §0 命名对照表
  - 新增行: runs/rollout_trace.jsonl（粗粒度 step=shadow/canary）
  - 修改行: "子步可带 phase" → "子步须带 phase（v0.1.1+ 起）"
  - 新增行: shadow_state.json（run_records 版）字段列表
  - C1 行加注: canary_cohort_state.json 当前落 runs/ 子路径（FIX-03）

文件 3: workflow_v2/20_pilot/W3-A_case/_TEMPLATE_art_rel_dec.json
  修改: ticket_id: "W3-A-CANARY-PILOT" → "W4-A-K2-ROLLOUT-INTEGRATION"

文件 4: workflow_v2/20_pilot/W3-A_case/_TEMPLATE_art_rel_exec.json
  修改: ticket_id → "W4-A-K2-ROLLOUT-INTEGRATION"
  新增字段: pilot_stream_id, run_id, canary_assignments（占位值）

验证: 修改后运行:
  git diff --stat  (确认仅 4 个文件)
  grep -n "phase" workflow_v2/tools/wf_k2_rollout_run.ps1  (确认 4 处 phase 写入点)
  python workflow_v2/tools/wf_k2_rollout_gate_trace.py --config ... --trace ...  (确认 gate_trace 仍 PASS)
```

---

## Reviewer checklist

以下为 `checker-reviewer` 审阅本票产出时的检查项：

- [ ] `W4-A-FIX-01-GATE-TRACE-ALIGN.memory.md` 落盘，字段齐全（ticket/lane/scope/non-goals/evidence/findings/strategy/allowed/no-touch/risks/cursor-brief/checklist）
- [ ] 未修改 runtime / CI / tools / config / run_records / `00`/`90`/`99`
- [ ] Key mismatch 对照表 ≥ 8 条，每条含现状 key / 建议 key / 所在档 / 是否需 alias / 风险
- [ ] Allowed file edit set ≤ 5 个文件，每个有明确理由
- [ ] 明确区分「本票能解」vs「因缺 override 历史 run 仅标不解」的 gap
- [ ] 全文无 TODO / placeholder / TBD
- [ ] Cursor brief skeleton 可直接交付 implementation-worker（含文件路径、具体行号、变更内容、验证命令）

---

## Key mismatch 对照表（精简版）

| # | 现状 key/名称 | 建议 key/名称 | 所在档 | 需 alias? | 风险 | 本票解? |
|---|--------------|--------------|--------|-----------|------|---------|
| 1 | trace 缺 `phase`（ibridge/eval/canary） | 补 `"phase":"shadow"` / `"phase":"canary"` | `wf_k2_rollout_run.ps1` L128/L150/L213 | 否 | 低 | **是** |
| 2 | checklist §0：「子步可带 phase」 | 「子步须带 phase（v0.1.1+）」 | `W4-A_gate_checklist.md` §0 | 否 | 低 | **是** |
| 3 | checklist 缺 `runs/rollout_trace.jsonl` 记录 | 新增粗粒度 trace 行 | `W4-A_gate_checklist.md` §0 | 否 | 无 | **是** |
| 4 | `_TEMPLATE_art_rel_dec.json` `ticket_id: W3-A-...` | `W4-A-K2-ROLLOUT-INTEGRATION` | `_TEMPLATE_art_rel_dec.json` | 否 | 无 | **是** |
| 5 | `_TEMPLATE_art_rel_exec.json` `ticket_id: W3-A-...` + 缺 `pilot_stream_id`/`run_id`/`canary_assignments` | 更新 + 补字段 | `_TEMPLATE_art_rel_exec.json` | 否 | 无 | **是** |
| 6 | `rollback_path_valid: false`（实产） vs checklist B6 要求 `true` | 不改命名（字段名一致）；值语义留 FIX-02 | `08_art_rel_exec.json` / `sim.py` | 否 | 中（gate 准入） | **否** → FIX-02 |
| 7 | `canary_cohort_state.json` 路径：`runs/w4a-int-.../` vs checklist 隐含案卷根 | 不改路径；加注 | checklist C1 / 实际落点 | 否 | 低 | **否** → FIX-03 |
| 8 | `runs/shadow_state.json` `stream_id: W4-A-INTERNAL-K2-STREAM-v1` | 应为 `W4-A-PILOT-RELEASE-STREAM-v0.1` | `runs/w4a-int-.../shadow_state.json` | 否 | 中 | **否** → 独立调查 |
| 9 | Config 缺 `trace_contract` key | 需补（但属配置增强，非命名） | `rollout_pipeline_config.json` | 否 | 中（helper 不可用） | **否** → wave 5 |
| 10 | `wf_k2_rollout_gate_trace.py` 默认 sub_steps=[] | 补 config 后自愈 | helper + config | 否 | 中 | **否** → wave 5 |

---

## 尚未解决 / 需后续票处理

| 项目 | 原因 | 后续票 |
|------|------|--------|
| `rollback_path_valid` 语义（true vs false） | 需改 sim.py 条件逻辑 | `W4-A-FIX-02` |
| `canary_cohort_state.json` 落点 | 路径重构 + rollback 回写 | `W4-A-FIX-03` |
| `override_record.json` 缺样例 run | 需实际执行一次 override | `W4-A-FIX-04` |
| `runs/` vs `run_records/` 双路径 | 架构性问题，非命名 | Wave 5 结构票 |
| Config 缺 `trace_contract` | 配置增强 | Wave 5 配置票 |
| `runs/shadow_state.json` 错 `stream_id` | 来源不明，需调查 | 独立调查票 |

---

## 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-31 | 初始落盘：完整盘点 10 项 mismatch，4 文件最小修补计划，Cursor brief skeleton |
