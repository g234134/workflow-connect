# Wave 4 Lane A · 轻量记忆与真样本护栏收口 · 执行计划 v0.1

> **Lane**：最小接案 MVP Wave 4（≠ Tabular MVP Wave 4 routing glue）  
> **状态依据**：`04_Workflows/00_Agent_Work_Progress.md` →「最小接案 MVP · Wave 1–4」  
> **日期**：2026-06-13

---

## 1. 背景与缺口

Wave 2–3 已交付 case 结构、gate、清洗 runner、bundle 与 E2E 驱动。Wave 4 剩余两项：

| 缺口 | 现状（2026-06-08 判定） | 目标 |
|------|-------------------------|------|
| 轻量记忆 | 无结构化历史索引 | 只读查 case / 规则 / 模板 / 已知限制 |
| 真样本护栏 | sampleco 115→8 行仍 `pass_with_warnings` 且 gate `accepted` | schema 歧义与低 output 比例可见；可选升格 review |

**不建**向量 RAG、long-term agent memory、prod 远程服务。

---

## 2. 票拆分（2～3 张）

### 票 1 · `W4-MEM-01` — 轻量 case 记忆索引（高优先 · 本 Lane 先交付）

| 项 | 内容 |
|----|------|
| **FRAME 一句话** | 扩展 `cases/index.json` + 只读 lookup CLI，供接案前查历史 case、清洗 profile、规则摘要、交付模板与 `known_limits`。 |
| **NonScope** | 无向量检索；不改 gate/cleaning/bundle；不自动推荐 cleaner；不扫全 `cases/` 树（登记列表 frozen）。 |
| **AcceptanceCriteria** | AC1 `build_cases_index.py` 写入 `cleaning_profile` / `cleaning_rules_applied` / `delivery_template_ref` / `schema_notes` / `qa_status` / `accepted_ratio` /  enriched `known_limits`；AC2 lookup 默认返回 profile + limits， `--verbose` 返回规则与模板；AC3 sampleco `known_limits` 含 `multi_row_export` 或等价标签 + `low_accepted_ratio`；AC4 unittest 全绿。 |
| **交付形态** | **只读 CLI + JSON 索引**（`build_cases_index.py` · `lookup_case_history.py`） |
| **是否接 gate** | **否** — 索引构建时只读 `eligibility_result.json` / `report.json`；可选只读调用 `check_case_eligibility` 取 `schema.notes`，不写 gate 产物 |

**别名**：承接 `W-MVP-W4A-MEMO-LOOKUP` 未完成的 FRAME 字段（`cleaning_profile` 等）。

---

### 票 2 · `W4-GUARD-01` — 真样本护栏升格草案（设计 + 可选 sidecar）

| 项 | 内容 |
|----|------|
| **FRAME 一句话** | 在既有 W4B schema 探针 + output ratio sidecar 之上，定义何时从 warning-only 升格为 `review_needed` / delivery `blocked`，并给出接入点草案。 |
| **NonScope** | 不改 `clean_phase_demo` 去重；不默认 fail E2E；不 prod 远程 gate；阈值最终值需 Orchestrator / 尚書省裁定（TODO）。 |
| **AcceptanceCriteria** | AC1 文档化三条触发：schema mismatch、`accepted_ratio` 过低、`pass_with_warnings` 不可信；AC2 明确接入点（gate vs bundle `output_guard` vs 新 `qa_guard` sidecar）；AC3 sampleco 对照表：现行 vs 提案；AC4 至少 1 条 unittest 骨架或 contract test（可 skeleton）。 |
| **交付形态** | **票 state + spec 草案**；实现可拆 `W4-GUARD-01-IMPL` |
| **是否接 gate** | **必须** — 升格逻辑最终须写入 `case_eligibility.py` 或 bundle 前置检查；本票先 doc + TODO |

**前置**：`W-MVP-W4B-GUARD-SCHEMA`（accepted）· `W-MVP-W4B-GUARD-RATIO`（accepted · warning-only sidecar）。

---

### 票 3 · `W4-MEM-02` — Scribe 收口与 demo  walkthrough（可选 · 低优先）

| 项 | 内容 |
|----|------|
| **FRAME 一句话** | 将 lookup + guard 侧车写入 demo walkthrough / DoD / Progress 末尾，形成对外「会做什么 / 不会做什么」话术。 |
| **NonScope** | 不改 CLI 行为；不新开 MVP 主链功能。 |
| **AcceptanceCriteria** | `docs/MVP_DEMO_WALKTHROUGH_v0.1.md` 或等价文档含 lookup 一步 + sampleco 黄灯解读；Progress 末尾 Wave 4 partial → done 建议句。 |
| **交付形态** | **docs only** |
| **是否接 gate** | 否 |

**别名**：可合并进 `W-MVP-W4A-MEMO-SCRIBE` / `W-MVP-W4C-DEMO-WALKTHROUGH`。

---

## 3. CLI vs gate 接入矩阵

| 能力 | 只读 CLI / JSON | 须接 gate / QA runner |
|------|-----------------|------------------------|
| 历史 case 目录 | `lookup_case_history.py` | — |
| schema 是否见过 | lookup `--schema-headers` | — |
| 已知限制 / 规则摘要 | index + lookup `--verbose` | — |
| schema mismatch 探针 | — | `check_case_eligibility`（已交付 · warning in notes） |
| output ratio 黄灯 | — | `output_guard` on bundle/E2E（已交付 · warning-only） |
| 升格 review_needed / blocked | — | **W4-GUARD-01-IMPL**（未决 · TODO 阈值） |
| E2E 主链 exit code | `run_case_e2e_validation.py` 不变 | 升格票须显式 opt-in 才改 exit |

---

## 4. 推荐实施顺序

1. **W4-MEM-01**（本 chat）— 索引字段补齐 + spec + tests  
2. **W4-GUARD-01** — 升格草案 ticket + spec TODO（不硬改 gate）  
3. **W4-MEM-02** — Scribe 文档收口（可并行）

---

## 5. 设计分歧 TODO（不硬拍板）

| # | 分歧 | 选项 | 建议默认 |
|---|------|------|----------|
| T1 | `multi_row_export` 是否升格 gate `review_needed` | A warning-only（现行） / B 升格 review | **A** 至 W4-GUARD-01 批文 |
| T2 | `accepted_ratio` 阈值 | 0.5（现行 sidecar） / 0.1（sampleco 专用） / SKU 表 | **0.5 sidecar**；升格用 **0.1 + schema_flags** 组合（待批） |
| T3 | `pass_with_warnings` 是否 block delivery | A 仅 notes / B CP-B blocked | **A** MVP；B 留给 HITL Checkpoint B |
| T4 | index 自动发现 `cases/*/*` | frozen list / glob scan | **frozen list** MVP；glob 留 W4-MEM-03 |

---

## 6. 验证命令（Lane A smoke）

```bash
python scripts/build_cases_index.py --json
python scripts/lookup_case_history.py --list-all
python scripts/lookup_case_history.py --client-ref sampleco --verbose
python -m unittest tests.test_lookup_case_history tests.test_build_cases_index -v
python scripts/check_case_eligibility.py --case-dir cases/sampleco/2026-0001 --json
python scripts/run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json
```

---

*Wave 4 Lane A · Orchestrator planning · doc-only SSOT*
