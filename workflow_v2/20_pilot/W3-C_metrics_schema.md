# W3-C — Gate / Helper 接入矩阵与指标 Schema（v0.1）

> **票号**：**W3-C-ORCH**（主线 C 总控交付）  
> **状态**：编排定稿；**CI 接线** → `W3-C-CI-GATE-WIRE`；**案卷补完** → `W3-C-GOV-RISK-PILOT`  
> **权威**：`00_master_plan.md` §13.3–13.5；`W2-3_minimal_gate_design.md`；`W2-2_tooling_notes.md` §8  
> **硬边界**：**无** deny engine runtime；**无** prod deploy；**无** 监控平台 SDK 集成；**不改** G6/G7/G8/G10 正文

---

## 1. Wave 3 主线 C 目标（一句话）

把 W2 已交付的 **`wf_check_cross_ref.ps1`**（交叉引用 helper）与 **`wf_gov_gate.ps1`**（治理 gate 原型）**接入一条真实 pipeline**（CI 或 nightly），并开张 **v0.1 JSONL 指标**，使 Wave 3 DoD「至少响过一次」可索引、可审计。

| 已完成（W2） | 本 Wave 补什么 |
|--------------|----------------|
| gate 设计 + 脚本原型 | 接入矩阵 + 指标 schema + 子票施工摘要 |
| `W2-3_case/art_gov_risk.json` pilot | [`W2-3_case/gov_risk_pilot_notes.md`](20_pilot/W2-3_case/gov_risk_pilot_notes.md)（W2-1 对齐 + fallback 路线）；CI 接线见 `W3-C-CI-GATE-WIRE` |
| cross-ref AC 脚本 | PR **warning**；nightly **可记 deny/override** |

---

## 2. Gate / Helper 优先接入点矩阵

### 2.1 总览

| 接入点 | 脚本 | 默认严厉度 | 阻断 merge？ | Wave 3 目标 |
|--------|------|------------|:------------:|-------------|
| **PR** | `wf_check_cross_ref` | **warning**（`continue-on-error`） | 否 | 养成习惯；收集 `checks_failed` 趋势 |
| **PR** | `wf_gov_gate` | **不接入**（v0.1） | — | 案卷路径未稳定；避免误伤 doc-only PR |
| **Nightly** | `wf_check_cross_ref` | warning → 可选 `-Strict`（尚書省批后） | 否（初版） | 全库 G8Recon 探针 + JSONL |
| **Nightly** | `wf_gov_gate` | **allow / override / deny 均落指标**；job **不因 deny 失败**（v0.1） | 否 | 满足 §13.3「真实响铃」 |
| **Agent SOP** | 两者 | 人工裁決 | 视场景 | 副官／checker 接战／封存前自检 |
| **Manual（案卷收口）** | `wf_gov_gate` | 人类按 verdict 停工 | 人工 | `IMP-RISK-VALIDATION` exit 前 |

```text
                    ┌─────────────────────────────────────┐
  PR (workflow_v2)  │  wf_check_cross_ref  →  warning    │
                    │  wf_gov_gate          →  (skip)     │
                    └─────────────────────────────────────┘
                    ┌─────────────────────────────────────┐
  Nightly           │  wf_check_cross_ref  →  JSONL      │
                    │  wf_gov_gate (cases) →  JSONL      │
                    └─────────────────────────────────────┘
                    ┌─────────────────────────────────────┐
  Agent / Manual    │  按 SOP 选 gate + helper；写案卷   │
                    └─────────────────────────────────────┘
```

### 2.2 PR 级（`workflow_v2/**` 变更触发）

| 项 | 说明 |
|----|------|
| **触发** | PR diff 含 `workflow_v2/`（建议 path filter；不含 `10_governance` 以外全库） |
| **输入** | **无案卷目录**；`-Scope G8Recon`（默认）；可选 `-CaseId W2-1` 作回归标签 |
| **命令（建议）** | `powershell -NoProfile -File workflow_v2/tools/wf_check_cross_ref.ps1 -Scope G8Recon -Strict` |
| **输出** | **stdout**（`[PASS]`/`[FAIL]` + `Summary`）；可选 append **JSONL**（见 §3） |
| **失败策略** | **`continue-on-error: true`** → 记 warning badge / annotation；**不** fail PR check（v0.1） |
| **Owner** | **ENG**（workflow_v2 tooling）；复核 **QA**（checker 文化：warning ≠ accepted） |
| **禁区** | 不得用 PR job 代替 NBT-T03～T07；不得用 cross-ref 绿标宣称 GOV signed |

### 2.3 Nightly（主验收路径 · 满足 W3-C DoD）

| 项 | `wf_check_cross_ref` | `wf_gov_gate` |
|----|------------------------|---------------|
| **触发** | 每日 cron / `schedule` workflow | 同 nightly workflow **或** 紧随 cross-ref job |
| **输入** | `-Scope G8Recon`；`-RepoRoot` 战车根 | **Case 列表**（见下表）；每 case 1～2 gate |
| **Case 列表（v0.1）** | — | `20_pilot/W2-3_case` → `GATE-RISK-EXIT`；`20_pilot/W2-1_case` + `-GovRiskPath W2-3_case/art_gov_risk.json` → `GATE-REL-ENTRY` |
| **参数** | `-Strict`（可选，第二批） | `-AllowFallback` 仅当票面/queue Notes 明示；`-ImpState` 当 `*_case.md` 缺失 |
| **输出** | stdout + **JSONL** `helper=wf_check_cross_ref` | stdout + **JSONL** `helper=wf_gov_gate`；解析 `VERDICT=` / `CHECKS_FAILED=` |
| **verdict 语义** | `ok=true` ⇔ exit 0 | `allow` / `require-human-override` / `deny` 原样入库 |
| **失败策略** | job exit **0**（v0.1 指标优先） | **同上**；`deny` **不** 使 nightly 红（留 Wave 4 升级） |
| **Owner** | **ENG** | **GOV**（case 内容）+ **ENG**（job 维护） |
| **升级路径** | 尚書省批后可改 `-Strict` + fail job | 可选：仅 `deny` 计数 > 阈值时 fail（**非** v0.1） |

### 2.4 Agent SOP（人工触发）

| 场景 | 调用 | 输入 | 输出落点 | Owner |
|------|------|------|----------|-------|
| **接战／IMP-RISK 前** | `wf_gov_gate -Gate GATE-RISK-EXIT` | 当前案卷 `CaseDir` + `art_gov_risk.json` | 控制台 + 可选 JSONL；案卷 Notes 一行 | **副官**（施工） |
| **QA 收口（NBT-T02）** | `wf_check_cross_ref -CaseId <id>` | Scope 由 `$CaseScopeMap` 解析 | `ART-QA-REV.evidence[]`（AC-* 行） | **checker** |
| **Release 前（NBT-T07）** | `wf_gov_gate -Gate GATE-REL-ENTRY` | `CaseDir` + GOV 路径 | `tooling_checks` / Notes；**不**改 QA verdict | **checker** + **governance** |
| **封存** | 两者择需 | 见 `W3-C-AGENT-SOP` 交付稿 | `04_Workflows` 战报或 OPS_CYCLE JSON | **副官** |
| **Cursor guard 后** | 一般不自动跑 gate | guard JSON ≠ gate 输入 | — | **governance-guard** 人工 |

**原则**：Agent **可以**跑 helper；**不能**用 gate `allow`  alone 关票（G10-2；`40_qa.md` §5）。

### 2.5 接入点 × 输入 artifact 对照

| 接入点 | `*_case.md` | `art_gov_risk.json` | `06_art_qa_rev.json` | `05_art_eng_wr.md` | G7/G8 树 |
|--------|:-----------:|:-------------------:|:--------------------:|:------------------:|:--------:|
| PR cross-ref | — | — | — | — | ✓ |
| Nightly cross-ref | — | — | — | — | ✓ |
| Nightly gov gate | 软（可 `-ImpState`） | ✓ P0 | REL 时 ✓ | ✗（v0.1 不解析） | — |
| Agent gov gate | ✓ | ✓ | REL 时 ✓ | 人读 only | — |
| Agent cross-ref | 标签 `-CaseId` | — | 写入 evidence | — | ✓ |

---

## 3. 指标 Schema（v0.1 · JSONL）

### 3.1 设计原则

- **一行一事件**（NDJSON / JSONL）；nightly 可 append 多 case、多 gate。
- **最少字段**满足 §13.3「可索引」：`gate`、`case_id`、`verdict`、`checks_failed`、`ts`。
- **不**写入密钥、`.env`、完整 WR 正文。
- 与脚本 stdout 并存；**指标是审计索引**，不替代 ART-QA-REV / ART-GOV-RISK。

### 3.2 公共信封（所有 helper）

| 字段 | 必填 | 类型 | 说明 |
|------|:----:|------|------|
| `schema_version` | ✓ | string | 固定 **`gov-metrics-0.1`** |
| `ts` | ✓ | string | ISO-8601 UTC 或带 offset |
| `pipeline` | ✓ | enum | `pr` \| `nightly` \| `manual` \| `agent` |
| `run_id` | — | string | CI `GITHUB_RUN_ID`、nightly 批次 UUID、或 `manual-<ticket>` |
| `helper` | ✓ | enum | `wf_gov_gate` \| `wf_check_cross_ref` |
| `repo_ref` | — | string | git sha（短）；PR 构建可选 |

### 3.3 `wf_gov_gate` 行（gate 指标）

| 字段 | 必填 | 类型 | 说明 |
|------|:----:|------|------|
| `gate` | ✓ | string | `GATE-RISK-EXIT` \| `GATE-REL-ENTRY`（与设计 §2 一致） |
| `case_id` | ✓ | string | 逻辑案卷 ID，如 `W2-3`、`W3-C-PILOT-001` |
| `case_dir` | — | string | repo 相对路径，如 `workflow_v2/20_pilot/W2-3_case` |
| `ticket_id` | — | string | queue 票号，如 `W3-C-GOV-RISK-PILOT` |
| `verdict` | ✓ | enum | `allow` \| `require-human-override` \| `deny` |
| `checks_failed` | ✓ | array | 字符串列表；无失败则 `[]` |
| `exit_code` | ✓ | int | 脚本退出码 0/1/2/3 |
| `imp_state` | — | string | 探测到的 IMP-* |
| `gov_artifact` | — | string | `artifact_instance_id` |
| `qa_verdict` | — | string | 仅 `GATE-REL-ENTRY` |
| `message` | — | string | `summary` 首句或截断 |

**示例**

```json
{"schema_version":"gov-metrics-0.1","ts":"2026-05-27T12:00:00Z","pipeline":"nightly","run_id":"nightly-20260527","helper":"wf_gov_gate","gate":"GATE-RISK-EXIT","case_id":"W2-3","case_dir":"workflow_v2/20_pilot/W2-3_case","ticket_id":"W2-3-GOV-RISK-PILOT","verdict":"require-human-override","checks_failed":["fallback_used"],"exit_code":1,"imp_state":"IMP-RISK-VALIDATION","gov_artifact":"ART-GOV-RISK-W2-3-PILOT","message":"fallback_used=true; default require-human-override"}
```

```json
{"schema_version":"gov-metrics-0.1","ts":"2026-05-27T12:01:00Z","pipeline":"nightly","run_id":"nightly-20260527","helper":"wf_gov_gate","gate":"GATE-REL-ENTRY","case_id":"W2-1","case_dir":"workflow_v2/20_pilot/W2-1_case","verdict":"require-human-override","checks_failed":["tooling_checks_missing"],"exit_code":1,"imp_state":"IMP-OBSERVING","gov_artifact":"ART-GOV-RISK-W2-3-PILOT","qa_verdict":"accepted_with_gaps"}
```

### 3.4 `wf_check_cross_ref` 行（helper 指标）

| 字段 | 必填 | 类型 | 说明 |
|------|:----:|------|------|
| `gate` | ✓ | string | 固定 **`GATE-CROSS-REF-G8RECON`**（逻辑名，非脚本 gate） |
| `case_id` | — | string | `-CaseId` 若提供 |
| `scope` | ✓ | string | 如 `G8Recon` |
| `verdict` | ✓ | enum | `allow`（全 pass）\| `deny`（有 FAIL） |
| `checks_failed` | ✓ | array | 失败 probe ID，如 `["AC-2b"]` |
| `checks_passed` | — | int | 通过数 |
| `checks_total` | — | int | 总 probe 数（v0.1 = 7） |
| `exit_code` | ✓ | int | 0/1/2（2=路径/配置错误） |
| `message` | — | string | `Summary:` 行原文 |

**示例**

```json
{"schema_version":"gov-metrics-0.1","ts":"2026-05-27T12:00:00Z","pipeline":"pr","run_id":"pr-12345","helper":"wf_check_cross_ref","gate":"GATE-CROSS-REF-G8RECON","scope":"G8Recon","case_id":"W2-1","verdict":"allow","checks_failed":[],"checks_passed":7,"checks_total":7,"exit_code":0,"message":"Summary: ALL PASS (7 checks) | exit 0"}
```

### 3.5 存储路径（W4-C 已实装）

| 优先级 | 路径（repo 相对） | 用途 |
|--------|-------------------|------|
| **P0（推荐）** | `workflow_v2/observability/gov_gate_metrics/YYYY-MM-DD.jsonl` | v2 治理指标主场；按日滚动 |
| **P1** | `workflow_v2/observability/gov_gate_metrics/latest.jsonl` | 指向最近 nightly 摘要（可选 symlink／拷贝） |
| **P2** | CI artifact 名 `gov-gate-metrics` | 不落 repo；仅 GitHub Actions 保留 30d |

**写入责任（当前实现）**：

- CI workflow：`.github/workflows/gov-gate-metrics.yml`
- JSONL emitter：`workflow_v2/tools/wf_emit_gov_gate_metrics.ps1`（吞掉非 0 exit，但把 `exit_code` / `verdict` / `checks_failed` 记入 JSONL）
- artifact 上传：`gov-gate-metrics`

### 3.6 与案卷 / queue 的索引关系

| 消费方 | 用法 |
|--------|------|
| **§13.4 DoD** | nightly `run_id` + 首行 `verdict` 写入 `90` Notes / `99` 战报 |
| **CHK-W3** | 抽查 JSONL 是否存在、是否含 `W2-3` case |
| **W3-A canary** | 软依赖：canary 前至少 1 条 nightly `wf_gov_gate` 行（`02` §8.3） |

---

## 4. W3-C 子票施工摘要

### 4.1 W3-C-GOV-RISK-PILOT

| 项 | 内容 |
|----|------|
| **目标** | 把 W2-3 pilot **补完**为 Wave 3 可消费案卷：保留并精炼 `W2-3_case/art_gov_risk.json`；新增 `20_pilot/W3-C/` 索引与 **W2-1 对齐说明**（retroactive 边界、GAP-GOV-RISK _closure 叙事） |
| **输入** | `W2-1_case/` 全套 ART；`60_gov_risk.md`；现有 `art_gov_risk.json` |
| **产出** | [`20_pilot/W2-3_case/gov_risk_pilot_notes.md`](20_pilot/W2-3_case/gov_risk_pilot_notes.md)；[`art_gov_risk.json`](20_pilot/W2-3_case/art_gov_risk.json)（`ticket_id` → W3-C-*）；可选 `W3-C_case.md` §2 `imp_state` |
| **验收** | 本地 `wf_gov_gate GATE-RISK-EXIT` 可复现；README 说明 **不** 改 W2-1 历史 verdict |
| **禁区** | 不改 W2-1 `imp_state`／QA；不接 CI |
| **Owner** | **GOV** worker |

### 4.2 W3-C-CI-GATE-WIRE

| 项 | 内容 |
|----|------|
| **目标** | **一条** pipeline 真实调用：`wf_check_cross_ref`（PR warning）+ `wf_gov_gate`（nightly 多 case）；append §3 JSONL |
| **输入** | 本文 §2–§3；`wf_*.ps1`；pilot case 路径 |
| **产出** | `.github/workflows/wf_v2_gov_nightly.yml`（或等价）片段 + `20_pilot/W3-C/ci_gate_wire.md`（命令、解析、JSONL 落点与字段映射） |
| **验收** | 至少 **1 次** nightly/手动 workflow 绿 + JSONL 样例行贴 `ci_gate_wire.md`（此票仅完成“接线设计与示例”，不落地 CI 配置） |
| **禁区** | **无** deny engine；**不** fail PR on gov gate；**不** 接 Datadog/Sentry |
| **Owner** | **ENG** worker |

### 4.3 W3-C-AGENT-SOP

| 项 | 内容 |
|----|------|
| **目标** | 在 **AGENTS / workflow** 层定义副官、checker、guard **何时跑** helper／gate，输出落哪里 |
| **输入** | `AGENTS.md` 接战／封存；`DISPATCH_GUIDE.md`；`W2-2_tooling_notes.md` §4 |
| **产出** | `20_pilot/W3-C/agent_sop_gate.md`（表格：场景 → 命令 → 禁止）；可选 **1 段** 提案追加 `AGENTS.md`（须 governance 票，本票可只交提案） |
| **验收** | 覆盖接战、IMP-RISK exit、QA T02、Release T07、封存 5 场景 |
| **禁区** | **不改** G10 正文；不宣称 gate=尚書省批准 |
| **Owner** | **E1** worker；**并行**于 GOV-RISK-PILOT |

### 4.4 W3-C-IMP-STATE-LINT

| 项 | 内容 |
|----|------|
| **目标** | **设计** `imp_state` lint（只读）：案卷 `*_case.md` §2 与 G7-3 合法下一态、ART 存在性粗校验 |
| **输入** | `W2-2_imp_state_schema.md`；`G7` `40_imp_state_field_v0.1.md`；`_TEMPLATE_case` |
| **产出** | `20_pilot/W3-C/imp_state_lint.md` + 可选 `workflow_v2/tools/wf_imp_state_lint.ps1` **骨架**（`ok`/`message` dict 形态） |
| **验收** | 设计含：输入、规则表、exit 码、未来接入 **nightly 第二条 job** 的 hook 点 |
| **禁区** | **非**全状态机 CI enforcement；**不** 自动改 `imp_state` |
| **Owner** | **G7** worker；**并行**于 ORCH 后 |

---

## 5. 依赖与执行顺序

```text
W3-C-ORCH (本文)
    ├── W3-C-GOV-RISK-PILOT ──► W3-C-CI-GATE-WIRE ──► CHK-W3 / §13.4
    ├── W3-C-AGENT-SOP (并行)
    └── W3-C-IMP-STATE-LINT (并行)
```

| 硬依赖 | 说明 |
|--------|------|
| `W2-3-MINIMAL-GATE-IMPL` | 脚本已存在 |
| `W2-1-QA-REL` | REL gate 需 `06_art_qa_rev.json` |
| `W3-0-ORCH` | Wave 3 已开盘 |

---

## 6. 风险与 TODO

| # | 风险 | 缓解 | 票 |
|---|------|------|-----|
| R-C1 | PR warning 被忽略 | `99`／周报盯 `checks_failed` 趋势 | CI-GATE-WIRE |
| R-C2 | `fallback_used` 常态 override | 新案卷要求 `signed` + `fallback_used: false` | GOV-RISK-PILOT |
| R-C3 | W2-1 无 `tooling_checks` → REL 恒 override | 文档标明；可选 W3 补 JSON **不** retro W2-1 verdict | AGENT-SOP |
| R-C4 | 指标路径未建导致 job 失败 | CI 先 `mkdir -p` 或仅 artifact | CI-GATE-WIRE |
| R-C5 | 与 W3-A canary 顺序 | nightly 指标在 canary 前留痕（软依赖） | 总控 |

**TODO（子票）**

- [x] `W3-C-GOV-RISK-PILOT`：W2-3_case 案卷 + W2-1 对齐 md（[`gov_risk_pilot_notes.md`](20_pilot/W2-3_case/gov_risk_pilot_notes.md)）
- [x] `W3-C-CI-GATE-WIRE`：接线设计 + 首条 JSONL 样例（未落地 CI 配置 / deny fail-on-deny 仍留 Wave 4）  
- [ ] `W3-C-AGENT-SOP`：`agent_sop_gate.md`  
- [ ] `W3-C-IMP-STATE-LINT`：`imp_state_lint.md`（+ 可选脚本骨架）  
- [ ] （Wave 4）nightly `deny` fail job；PR 接入 `wf_gov_gate`；`GATE-STOP-WORK`

---

## 7. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W3-C-ORCH v0.1：接入矩阵、JSONL schema、四子票摘要 |
