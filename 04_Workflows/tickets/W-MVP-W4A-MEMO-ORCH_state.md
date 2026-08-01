# TICKET STATE · W-MVP-W4A-MEMO-ORCH · Wave 4A · 轻量记忆 lookup FRAME 冻结

> handoff 摘要档；跨 chat 交棒以本档为准，不是完整工作日志。  
> Wave：**Wave 4A — Memory lookup FRAME only**（规划／复用盘点；**禁止代码施工**）

---

## FRAME

- Goal: 冻结「轻量记忆 lookup」的 FRAME（索引字段、查询入口、验收口径）；只做规划与复用盘点，为后续 LOOKUP／SCRIBE 子票提供 SSOT。
- Scope:
  - Step 0 — Module Reuse Check（B_REPORT）
  - Step 1 — 定义 lookup 能回答的 3 类问题
  - Step 2 — 定义 `cases/index.json` 最小字段集与用途
  - Step 3 — 定义 lookup CLI 最小接口与 JSON 输出形状
  - Step 4 — 验收口径（AC1–AC4）
  - Step 5 — B_REPORT 交付摘要与 next_tickets
- NonScope:
  - **不建向量库、不改 core pipeline、不自动推荐 cleaner**
  - 不改 gate / cleaning / bundle 主链（W2 P2–P4 · W3 E2E）
  - 不实现 CLI、不填充 index、不写 docs（留给 LOOKUP／SCRIBE 子票）
  - 禁止新功能开发、禁止改 `core/*`、禁止改任意 `.py`／`.md`（本票除外 state）
- AllowedPaths:
  - `04_Workflows/tickets/W-MVP-W4A-MEMO-ORCH_state.md`（FRAME / STATE / B_REPORT）
- BlockedPaths:
  - `core/*`、`skills/*`、`config/*`、`tests/*`、`scripts/*`
  - `cases/index.json`（本票只定契约，不填充）
  - `AGENTS.md`、`.cursor/rules/*`、`04_Workflows/00_Agent_Work_Progress.md`
- Dependencies:
  - W-MVP-W1-INVENTORY（H 类 Case history · extend · registry 缺口）
  - W-MVP-W2 P1–P4（`cases/` 结构、gate、runner、bundle · done）
  - W-MVP-W3-E2E-VALIDATION · W-MVP-W3-INTAKE-CLI（E2E DoD · 建案 CLI · done）
  - `cases/index.json` stub · `cases/_TEMPLATE_case/` · `cases/demo_phase/` · `cases/sampleco/2026-0001/`
  - `docs/MVP_CASE_E2E_DoD_v0.1.md` · `docs/C2-P2_RUNBOOK.md` · `cases/README.md`
  - Progress Wave 4 判定（轻量记忆层 partial · 2026-06-08）
- AcceptanceCriteria:
  - **AC1**：存在一段清晰的「lookup 能回答三类问题」描述（见 §LookupQuestions）。
  - **AC2**：定义了 `cases/index.json` 的最小字段集合，并解释其如何支持三类问题（见 §IndexFields）。
  - **AC3**：约定了 lookup CLI 的入口参数与 JSON 输出结构（见 §LookupCLI）。
  - **AC4**：明确写清「不做的事」：不建向量库、不改 core pipeline、不自动推荐 cleaner（见 NonScope 与本节）。
  - **AC5**（本票附加）：B_REPORT 含 module_reuse_summary、frame_summary、next_tickets；无 `.py`／`.md` 代码施工。

### 边界声明（Wave 4A 定位）

**本 Wave 4A 只在「索引 + lookup」层工作，不改 gate / cleaning / bundle 主链。**

---

### §LookupQuestions — lookup 至少要回答的 3 类问题

> 本节只定义**问题类别**，不设计实现细节。

| # | 问题类别 | 用户意图（自然语言） | lookup 应返回什么（概念层） |
|---|----------|----------------------|----------------------------|
| **Q1** | **有没有历史案例** | 「这个 client / SKU / 案号以前做过吗？」 | 按 `client_ref`、`product_sku` 或 `case_dir` 罗列已登记 case；无匹配时明确空集 |
| **Q2** | **schema 是否见过** | 「这组表头／这个 case 的结构以前处理过吗？」 | 给定 header 列表或某 `case_dir`，列出 schema 相近或同 SKU 的历史案（含 gate 与清洗 profile 提示） |
| **Q3** | **已知限制与备注** | 「这个 SKU／这条 demo 规则有什么坑？」 | 返回 `known_limits[]` 与 case 级 notes（如 Phase demo 单行假设、sampleco 实验勉强可用） |

**示例锚点（供 LOOKUP 票填充 index 时引用，非实现）**

- Q3 · `cases/demo_phase`：Phase demo cleaner 假设「每个 Phase 值一行」；行数 &lt;100 时 gate 常 `review_needed`（见 DoD §5）。
- Q3 · `cases/sampleco/2026-0001`：真实 milestone 多行导出；gate `accepted` 但 115→8 行、`qa_status=pass_with_warnings`；清洗质量**勉强可用**，非 prod 语义。

---

### §IndexFields — `cases/index.json` 最小字段集（契约草案）

> 字段名草案；不规定 JSON 嵌套深度或填充脚本，只定**每条 case 记录**至少应能表达的信息。

| 字段 | 必填 | 用途 · 支持的问题 |
|------|------|-------------------|
| `case_dir` | 是 | repo 相对路径（如 `cases/demo_phase`）；Q1 罗列、Q2 指定案、CLI `--list-all` 主键 |
| `client_ref` | 是 | 客户／项目 slug；Q1 按客户过滤 |
| `product_sku` | 是 | 产品 SKU（如 `CLEAN-BASIC`）；Q1／Q2 按 SKU 过滤 |
| `created_at` | 否 | ISO8601；Q1 排序／「最近一案」人工参考 |
| `schema_headers` | 是* | 字符串数组，来自 raw CSV 表头或 `intake.json` 推导；Q2 header 相近匹配 |
| `schema_fingerprint` | 否 | 可选规范化指纹（排序 header 的 hash 或 join 串）；Q2 精确／快速等同判断 |
| `gate_status` | 是 | 枚举：`accepted` · `review_needed` · `rejected`（对齐 P2 `eligibility_result`）；Q1／Q2 过滤「可示范案」 |
| `cleaning_profile` | 是 | 清洗策略名称（如 `phase_demo_v1` · `clean_basic_demo`）；Q2 同 SKU 不同 profile 区分 |
| `known_limits` | 是 | 字符串数组，简短标签；Q3 直接返回 |

\* `schema_headers` 与 `schema_fingerprint` 至少其一必填；推荐两者并存（headers 人读、fingerprint 机器比对）。

**与现有 stub 的关系**

- 现行 `cases/index.json`（`gov-cases-index-v0.1`）含 `cases[]` 但仅登记 `demo_phase`；字段为 `status`／`notes` 而非上表完整契约。
- LOOKUP 票实施时：**extend** stub 结构（保留 `schema_version`／`naming`／`required_paths` 顶层元数据），将 `cases[]` 条目对齐上表；并纳入 `sampleco/2026-0001` 等已跑通案。

**字段 → 三类问题映射**

| 问题 | 主要字段 | 辅助字段 |
|------|----------|----------|
| Q1 历史案例 | `client_ref` · `product_sku` · `case_dir` | `created_at` · `gate_status` |
| Q2 schema 见过 | `schema_headers` · `schema_fingerprint` · `product_sku` | `cleaning_profile` · `gate_status` |
| Q3 已知限制 | `known_limits[]` | `case_dir` 级 freeform notes（可映射为 limits 来源，不另开 DB） |

---

### §LookupCLI — 薄 CLI 接口形状（契约 only）

| 项 | 约定 |
|----|------|
| **脚本名（建议）** | `scripts/lookup_case_history.py` |
| **运行目录** | repo 根（与 `cases/` 同级） |
| **索引来源** | 只读 `cases/index.json`（不扫描全库、不读 RAG） |

**主参数（均可选；无参数时行为 = 需显式 `--list-all` 或报错，由 LOOKUP 票实现二选一并在 Scribe 文档化）**

| 参数 | 说明 |
|------|------|
| `--client-ref <slug>` | 过滤 `client_ref` |
| `--product-sku <sku>` | 过滤 `product_sku` |
| `--schema-headers <h1,h2,...>` 或多次 `--schema-header` | 与 index 中 headers／fingerprint 做相近或同 SKU 匹配 |
| `--case-dir <path>` | 若提供，从该案 intake／raw 推导 headers 再查历史（实现细节留给 LOOKUP 票） |
| `--list-all` | 列出所有已登记 case（忽略其他 filter 或与之 AND，LOOKUP 票实现时择一并在测试固定） |
| `--json` | 固定 stdout 为 JSON（本 FRAME 假定默认即 JSON，与 P2／E2E CLI 一致） |

**stdout 输出形状（单一 dict）**

```json
{
  "ok": true,
  "matches": [
    {
      "case_dir": "cases/demo_phase",
      "client_ref": "internal-demo",
      "product_sku": "CLEAN-BASIC",
      "gate_status": "review_needed",
      "cleaning_profile": "phase_demo_v1",
      "known_limits": ["phase_one_row_per_value", "not_prod_pipeline"]
    }
  ],
  "notes": [
    "index covers demo_phase and sampleco/2026-0001 only",
    "read-only; does not run gate or cleaning"
  ]
}
```

| 键 | 说明 |
|----|------|
| `ok` | `true`／`false`；索引缺失、JSON 非法、参数冲突时为 `false` + `message`（LOOKUP 票对齐 repo CLI 惯例） |
| `matches[]` | 命中 case 摘要；元素至少含 FRAME 列出的 5 字段；可附加 `schema_headers` 供 Q2 人工比对 |
| `notes[]` | 非 case 级提示（索引覆盖范围、只读声明、stub 免责声明） |

---

### §NonGoals — 明确不做的事（AC4）

1. **不建向量库** — 无 embedding、无 pgvector、无 RAG retrieve；lookup = 结构化 index + 字符串／集合匹配。
2. **不改 core pipeline** — 不碰 `core/*`、不改 `clean_phase_demo.py`／gate／bundle 行为。
3. **不自动推荐 cleaner** — lookup 只返回历史与限制；**不**输出「应使用哪条清洗规则」的决策或 auto-routing。

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: 开 **W-MVP-W4A-MEMO-LOOKUP** Implementer chat，按 FRAME §IndexFields／§LookupCLI 实现 CLI 与 index 填充；并行或随后开 **W-MVP-W4A-MEMO-SCRIBE** 写 docs
- last_updated: 2026-06-08 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: n/a
  - reviewer: n/a
  - scribe: n/a

---

## B_REPORT

> 本票为 Orchestrator 规划交付；无 Implementer 施工轮次。以下内容等同 planning 交付物。

### module_reuse_summary

**一句话**：本 Wave 4A 只在「索引 + lookup」层工作，不改 gate / cleaning / bundle 主链。

| 资产 | 现状 | 本 Wave 4A 复用方式 |
|------|------|---------------------|
| `cases/index.json` | stub（`gov-cases-index-v0.1`）；`cases[]` 仅 `demo_phase` | **extend** — 保留顶层 `schema_version`／`naming`／`required_paths`；LOOKUP 票按 FRAME 字段填充并纳入 `sampleco/2026-0001` |
| `cases/_TEMPLATE_case/` | P1 SSOT：intake · raw/cleaned/reports · signoff | **direct_reuse** — index 字段从 `intake.json`／raw header 推导的契约来源 |
| `cases/demo_phase/` | C2-D1 锚点；E2E 默认 `--case-dir`；gate 常 `review_needed` | **direct_reuse** — Q3 已知限制（Phase 单行、demo 非 prod） |
| `cases/sampleco/2026-0001/` | 首个真实样本；全链 artifact；115→8 · `pass_with_warnings` | **direct_reuse** — Q2／Q3 schema 语义不匹配与「勉强可用」备注 |
| `docs/MVP_CASE_E2E_DoD_v0.1.md` | E2E AC · §5 已知例外 · §7 未来扩展含 index 遍历 | **direct_reuse** — gate 枚举、demo 例外、明确「index 遍历属 Wave 4+」 |
| `docs/C2-P2_RUNBOOK.md` | 四阶段／四签核 SSOT | **adjacent** — lookup 不执行 runbook，仅引用 case 阶段产物路径 |
| `cases/README.md` | case 目录约定 · intake 字段 · 工具索引 | **direct_reuse** — Scribe 票交叉引用 lookup 用法 |
| W-MVP-W1-INVENTORY · **H 类 Case history** | `extend`；缺 tabular registry | **direct_reuse 地图** — 本 FRAME 即 H 类 Wave 4A 收口；不重复建 ticket markdown SSOT |
| W-MVP-W1-INVENTORY · A–G 类 | intake／gate／cleaning／bundle 已 done | **out of scope** — 本票不 extend 主链 |

### frame_summary

1. **三类 lookup 问题**冻结为：历史案例罗列（Q1）、schema 是否见过（Q2）、已知限制与备注（Q3）；不设计匹配算法。
2. **`cases/index.json` 最小字段**：`case_dir` · `client_ref` · `product_sku` · `schema_headers`（+ 可选 `schema_fingerprint` · `created_at`）· `gate_status` · `cleaning_profile` · `known_limits[]`。
3. **CLI 契约**：建议 `scripts/lookup_case_history.py`；参数 `--client-ref`／`--product-sku`／`--schema-headers`／`--list-all`；stdout 单一 JSON：`ok` · `matches[]` · `notes[]`。
4. **只读轻量索引**：读 `cases/index.json`；不扫描 RAG、不触发 gate／cleaning。
5. **明确 NonGoals**：无向量库、无 core 改动、无 cleaner 自动推荐。
6. **与 MVP 主链关系**：Wave 2–3 已交付 gate／runner／bundle／E2E；Wave 4A 补「人工接案前查历史」记忆层，不扩 MVP 功能面。
7. **index 覆盖初值**：至少 `demo_phase` + `sampleco/2026-0001`；stub 中 `client_ref` 与 intake 不一致处（index `demo` vs intake `internal-demo`）由 LOOKUP 票以 intake／eligibility 为准统一。

### next_tickets

| 票号 | 角色 | 内容 |
|------|------|------|
| **W-MVP-W4A-MEMO-LOOKUP** | Implementer → Reviewer | 按 FRAME §IndexFields 填充／extend `cases/index.json`；实现 `scripts/lookup_case_history.py` 与 `tests/test_lookup_case_history.py`（最小）；验证 Q1–Q3 三类查询 |
| **W-MVP-W4A-MEMO-SCRIBE** | Scribe | 在 `docs/`（或 `cases/README.md` §）写 lookup 用法、参数示例、index 维护约定；Progress 末尾摘要（可选） |

**刻意留给 Wave 4B+（本 FRAME 不拆票）**：真实样本护栏（gate／QA 识别 schema 不匹配、低 accepted 比例）；见 Progress Wave 4 剩余 scope。

### changed_files

- `04_Workflows/tickets/W-MVP-W4A-MEMO-ORCH_state.md`（新建 · FRAME／STATE／B_REPORT 规划交付）

### artifacts

- 本票 state 文件即 FRAME SSOT；无代码／无 runner 变更

### verification

- 本轮 **仅规划与 state 回写**，无功能施工
- 盘点依据：用户指定已读清单 · `cases/index.json` · `cases/README.md` · `docs/MVP_CASE_E2E_DoD_v0.1.md` · `W-MVP-W1-INVENTORY_state.md` · `cases/demo_phase/**` · `cases/sampleco/2026-0001/**` · Progress Wave 4 判定（2026-06-08）
- 未执行 pytest／lookup CLI（尚未实现，非本票 AC）

### behavior_notes

- Orchestrator 票一次性交付 FRAME + B_REPORT；Implementer／Reviewer 标记 `n/a`
- `cases/index.json` 现有 `client_ref: demo` 与 `demo_phase/intake.json` 的 `internal-demo` 不一致 — LOOKUP 票须以 case 目录内 intake／`eligibility_result.json` 为 SSOT 回填 index

### deferred_items

- index 自动从 filesystem 扫描生成（本 FRAME 选手工／脚本填充 index，不 watch 目录）
- schema 相似度算法（Jaccard／fingerprint 阈值）留给 LOOKUP 票实现，FRAME 不限定
- Wave 4B 护栏票（gate／QA 增强）不在本 FRAME

---

## C_REPORT

<!-- Reviewer 填；本票 O-only 规划，可选跳过或 O 自审 AC1–AC5 -->

- conclusion: <!-- pending | n/a -->
- blocking_issues:
- checks_summary:
- risk_level:
- suggestions:

---

## D_REPORT

<!-- Scribe 填 -->

- docs_updates:
- progress_entry:
- followup_suggestions:
