# TICKET STATE · W-MVP-W4C-DEMO-WALKTHROUGH · MVP 对外 demo 走查文档

> handoff 摘要档；跨 chat 交棒以本档为准，不是完整工作日志。  
> Wave：Wave 4C · W-MVP — Demo walkthrough Scribe（**仅 docs/** · **不改代码**）

---

## FRAME

> 冻结来源：Wave 4 MVP 收口 · 依赖 W4A lookup · W4B schema/ratio 护栏

- Goal: 写出 MVP 对外 demo 走查文档草版，串起 demo_phase + sampleco，讲清主链、lookup、护栏黄灯与诚实边界。
- Scope:
  - 新建或迭代 `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`
  - 本票 state（B_REPORT scribe 定位 · D_REPORT scribe_note）
- NonScope:
  - 不改任何 `.py` / tests / cases 数据
  - 不承诺 prod pipeline 或 7×24 服务
  - 不引入 RAG / 长记忆描述
  - 不调整 `docs/MVP_CASE_E2E_DoD_v0.1.md` 通过标准正文（仅交叉引用）
- AllowedPaths:
  - `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`
  - `04_Workflows/tickets/W-MVP-W4C-DEMO-WALKTHROUGH_state.md`
- BlockedPaths:
  - `scripts/*` · `notebooks/*` · `core/*` · `tests/*`
  - `cases/index.json`（逻辑层）
  - `AGENTS.md` · `.cursor/rules/*`
- Dependencies:
  - W-MVP-W4A-MEMO-LOOKUP（lookup B_REPORT）
  - W-MVP-W4A-MEMO-SCRIBE（cases/README · DoD 交叉引用）
  - W-MVP-W4B-GUARD-SCHEMA（schema 探针 · C_REPORT accepted）
  - W-MVP-W4B-GUARD-RATIO（output_guard · `tests/test_output_guard.py` 证据）
  - `cases/demo_phase/**` · `cases/sampleco/2026-0001/**`（只读对照）
- AcceptanceCriteria:
  - 文档含 §1 场景概览 · §2 命令链 · §3 护栏 · §4 sampleco 故事 · §5 会/不会
  - 命令块标注 demo_phase / sampleco 适用性
  - scribe_note 声明未改代码；Reviewer 可按文档冷启动跟跑

---

## STATE

- overall_status: reviewer_done
- current_owner: orchestrator
- next_action: Scribe 依 C_REPORT `doc_gaps[]` 补文档；Orchestrator 裁定 Wave 4C / MVP v1 demo ready
- last_updated: 2026-06-08 · reviewer
- status_by_role:
  - orchestrator: pending
  - implementer: n/a
  - reviewer: done
  - scribe: done

---

## B_REPORT

### Reviewer · W-MVP-W4C-DEMO-ACCEPT — Step 0 新人视角 self-check

本验收**仅**依赖 `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`、`docs/MVP_CASE_E2E_DoD_v0.1.md`、`cases/README.md` 与 repo 内 `cases/` 目录；**不**读 chat log、**不**读 `04_Workflows/tickets/` 票纲或 B_REPORT 实测值。凡 walkthrough 未写清、需翻 ticket 或猜参数/预期字段之处，一律记为**文档缺口**。工作目录：repo 根；Python 3.x；Windows PowerShell（命令单行执行，未用 bash `\` 续行）。

### Reviewer — Step 1 · demo_phase 跟跑

| 步骤 | 命令（简写） | 关键信号 vs 文档 |
|------|--------------|------------------|
| Step 0 lookup | `build_cases_index.py` · `lookup --list-all` · `--schema-headers Phase,名稱` | 2 案可见；demo_phase `gate_status=review_needed` + 4 条 `known_limits` 与 §1/Step 0 表一致 |
| Step 2 gate | `check_case_eligibility.py --case-dir cases/demo_phase --json` | `eligibility=review_needed` · `reason_code=rows<100` · `schema.notes=[phase_like, phase_demo]` · exit **2** ✓ |
| Step 3 clean | `clean_phase_demo.py --case-dir cases/demo_phase --skip-eligibility --force` | exit 0 · `input_rows=7` · `output_rows=5` ✓；`qa_status=pass_with_warnings` 在 `reports/report.json`，**不在** clean stdout |
| Step 4 bundle | `build_case_delivery_bundle.py --case-dir cases/demo_phase --json` | `ok=true` · `output_guard.status=ok` · `ratio=0.7143` ✓ |
| Step 5 E2E | `run_case_e2e_validation.py --case-dir cases/demo_phase --json` | `ok=true` exit 0 · `eligibility=review_needed` · `steps.cleaning.forced=true` · `output_guard.status=ok` ✓ |

**需猜之处**：无（`--force` 与 skip 建案在 §2 已写明）。gate exit 2 若未读 DoD/walkthrough 旁注，新人可能误以为 gate 失败——文档已解释。

### Reviewer — Step 2 · sampleco 跟跑

| 步骤 | 命令（简写） | 关键信号 vs 文档 |
|------|--------------|------------------|
| Step 0 lookup | `lookup --client-ref SAMPLECO` | 1 match · `gate_status=accepted` · `known_limits=[]` ✓（与 §1/§4 诚实说明一致：索引层看不到 schema 歧义） |
| Step 2 gate | `check_case_eligibility.py --case-dir cases/sampleco/2026-0001 --json` | `accepted` · `schema.notes=[phase_like, multi_row_export, schema_ambiguous]` · warnings 含 `phase_like_headers_but_multi_row_or_sprint_pattern` ✓ |
| Step 3 clean | `clean_phase_demo.py --case-dir cases/sampleco/2026-0001 --skip-eligibility` | 115→8 ✓；`duplicate_rows_removed=106` · 20× RANGE-ANOMALY 在 `report.json` |
| Step 4 bundle | `build_case_delivery_bundle.py --case-dir cases/sampleco/2026-0001 --json` | `output_guard.status=warning` · `ratio=0.0696` · `schema_flags=[multi_row_export, schema_ambiguous]` ✓ |
| Step 5 E2E | `run_case_e2e_validation.py --case-dir cases/sampleco/2026-0001 --json` | `ok=true` exit 0 · `forced=false` · `output_guard.status=warning` ✓ |

**sampleco 体验**：§1.2 与 §4 在跑命令前已预告「gate 绿灯 + 115→8 + output_guard warning + 勉强可用」；跟跑后 E2E JSON 与 §3 对照表一致。新人若**只**做 Step 0 lookup 可能暂时以为 sampleco「无限制」——§1/Step 0 表与 §4.2 已点明 lookup 局限，建议在 demo 话术里仍要显式切到 gate/bundle。

### Reviewer — Step 3 · 文档完整性评估

**Q1 — 不熟悉代码的工程师能否仅凭文档 + DoD 跑完两案？**  
**基本可以。** §2 Path A 命令顺序完整、适用性速查表清晰；DoD 与 walkthrough 对 `review_needed` + `--force` + E2E `--force-review` 交叉一致。扣分项：Windows 环境无 shell 提示（bash `\` 续行不可用）；Step 3 部分预期信号（`qa_status`、`duplicate_rows_removed`）需打开 `reports/report.json`，文档未指明读取位置。

**Q2 — sampleco「勉强可用」叙事是否诚实、不易误解为生产可用？**  
**是。** §4 事实摘要、gate 仍为 accepted 的原因、推荐对外措辞与 §5.2 NonScope 形成闭环；实测 E2E 仍 `ok=true` 与「warning 不阻断」声明一致，§4.3 明确「不建议直接对外客户交付」。

**Q3 — §5 会/不会列表是否与 MVP 现状一致？**  
**一致。** Reviewer 实测：lookup 只读、schema/ratio 为 warning-only 侧车、无 UI/RAG/prod SLA、sampleco 证明语义错配风险——均与 §5 及 DoD §7 未来扩展边界相符。

**缺口清单（供 Scribe，不本票改文档）**

| # | 缺口 | 严重度 |
|---|------|--------|
| G1 | 无 **Windows / PowerShell** 提示：§2 命令块用 bash `\` 续行；Windows 应单行或注明 PowerShell 反引号 | 对外 demo **建议修** |
| G2 | Step 0 `build_cases_index.py` 预期表写 `ok=true` · `cases_written=2`，默认 stdout 为人类可读一行；结构化 JSON 需加 **`--json`**（脚本支持但未文档化） | 建议修 |
| G3 | Step 3 清洗「预期关键信号」含 `qa_status` / `duplicate_rows_removed`，**clean CLI stdout 不输出**；应注明查看 `reports/report.json` 或 bundle/E2E JSON | 建议修 |
| G4 | §6 验收建议第 2 条写 `output_guard.ok`，实际字段为 **`output_guard.status`** | 建议修（笔误） |
| G5 | §0「相关文档」列 internal ticket state 路径；新人冷启动不必读，可移到脚注或「维护者索引」 | 可选 |
| G6 | sampleco 黄灯故事分散在 §1 / Step 0 表 / §4；可在 §2 sampleco 小节加一句「跑前必读 §4」交叉链接 | 可选 |

### Step 0 — 文档位置（Scribe 锁定）

**决策**：新建 `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`（repo 内此前无 `MVP_DEMO_WALKTHROUGH_v0.x` 草版）。

**与既有文档关系**

| 文档 | 关系 |
|------|------|
| `docs/C2-D1_DEMO_WALKTHROUGH.md` | C2-D1 单案产品向深度导览；本档为 Wave 2–4 **双案 MVP 主链**走查 |
| `docs/MVP_CASE_E2E_DoD_v0.1.md` | 验收权威；本档交叉引用，**未改 DoD 正文** |
| `cases/README.md` | lookup 操作细节；本档引用不重复全文 |

### changed_files（Scribe · 仅文档）

- `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`（新建）
- `04_Workflows/tickets/W-MVP-W4C-DEMO-WALKTHROUGH_state.md`（本档 · scribe 状态与 note）

### scope_out（Step 6）

- **不**承诺 prod pipeline 或 7×24 服务。
- **不**引入 RAG、长记忆描述（轻量 lookup 已在 W4A 票说明，本档仅引用）。
- **不**调整 DoD 正文通过标准（只做交叉引用与叙事）。
- **未改**任何 `.py`、tests、`cases/` 数据文件。

### verification

Scribe 票无代码 runner；文档依据以下来源交叉核对：

| 来源 | 用途 |
|------|------|
| `cases/demo_phase/reports/*.json` | demo_phase 行数 / qa_status |
| `cases/sampleco/2026-0001/reports/*.json` | sampleco 115→8 / qa_status |
| W-MVP-W4A-MEMO-LOOKUP B_REPORT | lookup CLI 与 index 字段 |
| W-MVP-W4B-GUARD-SCHEMA C_REPORT | schema notes 实测值 |
| `tests/test_output_guard.py` | ratio guard demo_phase ok / sampleco warning |

---

## C_REPORT

**verdict**: `no_with_gaps`

**demo_phase_summary**: 按 §2 逐步与一键 E2E 均顺畅；`review_needed` + `forced=true` + `output_guard.status=ok` 与 walkthrough/DoD 完全一致。

**sampleco_summary**: gate `accepted` + schema notes/warnings + bundle/E2E `output_guard.status=warning`（ratio 0.0696 + schema_flags）与 §3/§4 护栏叙事一致；§4 诚实边界足以防止误读为生产交付。

**doc_gaps[]**:

- G1：补 Windows/PowerShell 执行说明（单行命令或续行语法）
- G2：`build_cases_index.py` 预期信号表对齐实际 stdout，或文档化 `--json`
- G3：Step 3 清洗预期信号注明从 `reports/report.json`（或后续 bundle/E2E）读取 `qa_status` 等
- G4：§6 将 `output_guard.ok` 改为 `output_guard.status`
- G5（可选）：§0 内部 ticket 引用移出新人主路径
- G6（可选）：§2 sampleco 路径增加「跑前读 §4」提示

**recommendations**（**必须修**才能对外 demo）:

- **G1 + G2 + G3 + G4** 为 Scribe 小改即可闭环；无需改代码或 DoD 通过条件。
- G1 对本仓库主要 Windows 受众优先级最高。

**recommendations**（verdict 升格后可选）:

- Wave 5+ 再加 UI、更多样本案、lookup 写入 `schema_notes`（walkthrough 已 deferred 声明）。
- CI 集成 E2E 仍属 DoD §7 未来扩展，不在本票范围。

**scope out（Reviewer · W-MVP-W4C-DEMO-ACCEPT）**:

- 本票**未**修改 `docs/`、代码或 cases 数据；仅更新本 state。
- **不**评价 UI、RAG、prod pipeline 等未来功能；只评 MVP v1 当前可演示性。
- **不**改变 `docs/MVP_CASE_E2E_DoD_v0.1.md` 通过条件或正文。

**orchestrator_note**: 主链与护栏实测全绿、叙事诚实；在 Scribe 补完 **G1（Windows）与 G2–G4** 四个文档缺口后，可将 Wave 4C 标为 done，并视为 **MVP v1 可对外 demo**（仍须现场强调 INTERNAL / NOT PROD 与 sampleco 非交付案）。

### scribe_note

**修改的文档路径**

| 路径 | 章节 |
|------|------|
| `docs/MVP_DEMO_WALKTHROUGH_v0.1.md` | §0 定位 · §1 场景概览 · §2 标准主链（命令链） · §3 护栏与信号 · §4 sampleco 勉强可用 · §5 会/不会 · §6 Reviewer 验收建议 · §7 变更记录 |

**代码变更声明**：**未改任何代码**（无 `.py` / tests / cases 逻辑层变更）。

**给 Reviewer 下一棒建议**

1. 按 `docs/MVP_DEMO_WALKTHROUGH_v0.1.md` §2 **从零冷启动**跟跑：先 lookup → 再分别 E2E `demo_phase` 与 `sampleco`。
2. 核对 §3 对照表与实际 stdout JSON 是否一致（尤其 sampleco 的 `schema.notes` 与 `output_guard.warning`）。
3. 若信息不足（缺命令参数、预期值错误或章节跳转困难），在 W-MVP-W4C-DEMO-ACCEPT C_REPORT 列 gap，**不必**在本 Scribe 票返工代码。

---

## D_REPORT

- docs_updates:
  - `docs/MVP_DEMO_WALKTHROUGH_v0.1.md` — Wave 4C MVP 双案 demo 走查初稿 v0.1
- progress_entry: Wave 4C demo walkthrough 文档就绪：`docs/MVP_DEMO_WALKTHROUGH_v0.1.md` 串联 demo_phase + sampleco、lookup、schema/ratio 护栏与诚实边界；Scribe 完成，待 Reviewer 冷启动验收。
- followup_suggestions:
  - Reviewer 票 **W-MVP-W4C-DEMO-ACCEPT** 按 §6 验收
  - 可选：Orchestrator 在 Progress Wave 4 表追加本档链接
  - deferred：`cases/index.json` 写入 `schema_notes`（W4B GUARD-SCHEMA deferred · lookup 消费端后续票）
