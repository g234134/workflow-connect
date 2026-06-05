# W3-C-CI-GATE-WIRE — CI / nightly 接线设计（v0.1 文档与示例）

> 本票在 Wave 3 阶段只交付「接线设计 + 可复制命令/解析示例」；**Wave 4（W4-C）已将本设计接入真实 CI**（见 §0.1）。  
> 仍遵守 v0.1 边界：不实现 deny engine runtime；不把 `wf_gov_gate.ps1` 的 `deny` 直接升级为所有 PR hard fail（指标优先，fail-on-deny 留 Wave 5+）。

## 0.1 Wave 4 实装状态（W4-C-CI-INTEGRATION）

已实装（真实 CI workflow）：

- CI workflow：`.github/workflows/gov-gate-metrics.yml`
- JSONL emitter（复用 PR / nightly / manual / agent）：`workflow_v2/tools/wf_emit_gov_gate_metrics.ps1`
- Observability 落点：`workflow_v2/observability/gov_gate_metrics/YYYY-MM-DD.jsonl`
- CI artifact 名：`gov-gate-metrics`

真实行为（v1，保持“吞 exit，不置红”）：

- **PR**：仅跑 `wf_check_cross_ref.ps1`（warning 语义；但 JSONL 仍写 `verdict=allow/deny`）。
- **Nightly**：固定顺序跑 3 段（cross-ref → Gate A → Gate B），任何非 0 exit **不**让 job 置红，但会把 `VERDICT=` / `CHECKS_FAILED=` / `exit_code` 写入 JSONL。
- **Manual / Agent**：通过 `workflow_dispatch` 选择 `scenario=manual|agent`，保持与 nightly 相同的 stdout 解析与 JSONL 写入约定（仅改变 `pipeline` 字段）。

## 0. 设计范围与约束（对齐 v0.1）

- PR：只跑 `wf_check_cross_ref.ps1`，以 warning 模式收集指标（不 fail PR）。
- Nightly：跑 `wf_check_cross_ref.ps1` + `wf_gov_gate.ps1`，把 `wf_gov_gate` stdout/exit code 解析为 `gov-metrics-0.1` JSONL 行（job 不因 `deny` 失败）。
- Manual / Agent：仅说明如何按 SOP 触发 gate/helper 并写 JSONL；本票不改 agent 或 runtime。

涉及脚本（repo 相对路径）：

- `workflow_v2/tools/wf_check_cross_ref.ps1`
- `workflow_v2/tools/wf_gov_gate.ps1`

指标 schema（权威）：`workflow_v2/20_pilot/W3-C_metrics_schema.md`（gov-metrics-0.1）。

## 1. PR 场景（只跑 cross-ref，warning 模式）

### 1.1 推荐调用（命令级示例）

`wf_check_cross_ref.ps1` v0.1 **不支持** `-CaseDir` 参数；用于标注案卷只需用 `-CaseId`（对应内部默认 scope 映射）。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_check_cross_ref.ps1 `
  -Scope G8Recon `
  -CaseId W2-1
```

### 1.2 预期行为（PR job 不 fail）

- `wf_check_cross_ref.ps1` stdout：
  - 以 `[PASS]` / `[FAIL]` 展示 AC 探针。
  - 最后输出 `Summary: ... | exit <0|1|2>`。
- verdict 口径（写入 JSONL 时）：
  - exit code `0` → `verdict="allow"`
  - exit code `1` → `verdict="deny"`
  - exit code `2` → `verdict="deny"`（这里按 “配置/路径错误” 也记 deny，且由 CI 上层处理为 warning）
- PR 的检查结果（GitHub Actions 等）：
  - 使用 `continue-on-error: true` 或在脚本外层 `|| exit 0`，保证 PR checks 只显示 warning、不 fail。

### 1.3 cross-ref JSONL 行（示例）

```json
{"schema_version":"gov-metrics-0.1","ts":"<ISO8601>","pipeline":"pr","helper":"wf_check_cross_ref","gate":"GATE-CROSS-REF-G8RECON","scope":"G8Recon","case_id":"W2-1","verdict":"deny","checks_failed":["AC-2b"],"checks_passed":3,"checks_total":7,"exit_code":1,"message":"Summary: 1 / 7 FAILED | exit 1"}
```

## 2. Nightly 场景（cross-ref + gov gate，写 JSONL）

Nightly 建议至少包含两段：

1. `wf_check_cross_ref.ps1`：写一条 cross-ref JSONL 行（`helper=wf_check_cross_ref`）。
2. `wf_gov_gate.ps1`：对每个 gate 调用一次，分别写两条 gate JSONL 行（`helper=wf_gov_gate`）。

> 关键：由于 `wf_gov_gate.ps1` exit code 对应 `allow=0`、`require-human-override=1`、`deny=2`，CI 步骤必须吞掉非 0 exit（或使用 `continue-on-error`），确保 job 不因 deny 置红。

并且需要“固定响铃”以验证 metrics pipeline：

- Gate A（`GATE-RISK-EXIT`，W2-3 pilot）每天至少跑一次。
- Gate B（`GATE-REL-ENTRY`，W2-1 case + 输入 `W2-3_case/art_gov_risk.json`）每天至少跑一次。

### 2.0 固定 nightly “响铃”（硬约束 · v0.1）

Nightly job **每天至少**执行以下两条 `wf_gov_gate` 调用（用于验证 metrics pipeline 的 JSONL 写入与 schema correctness；**不是**重判 W2-1 / W2-3 历史事实）：

- **Gate A：`GATE-RISK-EXIT`（W2-3 pilot）**
  - 目标：
    - `-Gate GATE-RISK-EXIT`
    - `CaseDir = workflow_v2/20_pilot/W2-3_case`
    - `-ImpState IMP-RISK-VALIDATION`
    - 默认 **不传** `-AllowFallback`
  - 预期（来自 W2-3 pilot 收口）：
    - `VERDICT=require-human-override`
    - `CHECKS_FAILED` 含 `fallback_used`
- **Gate B：`GATE-REL-ENTRY`（W2-1 case + GOV artifact=W2-3）**
  - 目标：
    - `-Gate GATE-REL-ENTRY`
    - `CaseDir = workflow_v2/20_pilot/W2-1_case`
    - `-GovRiskPath workflow_v2/20_pilot/W2-3_case/art_gov_risk.json`
  - 预期（已知限制）：
    - 很可能为 `VERDICT=require-human-override`（W2-1 当时无 `tooling_checks`）
    - `CHECKS_FAILED` 允许出现 `fallback_used` / `tooling_checks_missing` 等

### 2.1 Gate A：GOV-RISK-EXIT（W2-3 pilot）

#### 2.1.1 调用（命令级示例）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_gov_gate.ps1 `
  -Gate GATE-RISK-EXIT `
  -CaseDir workflow_v2/20_pilot/W2-3_case `
  -ImpState IMP-RISK-VALIDATION
```

#### 2.1.2 预期 verdict 与 checks_failed（对齐 pilot 收口说明）

依据 `workflow_v2/20_pilot/W2-3_case/art_gov_risk.json`：

- `fallback_used: true`
- **不传 `-AllowFallback`（本接线 nightly 默认）**：
  - 预期 `VERDICT=require-human-override`（exit code `1`）
  - 预期 `CHECKS_FAILED` 含 `fallback_used`
- **如未来某次 run 传 `-AllowFallback`**：
  - 预期 `VERDICT=allow`（exit code `0`）

#### 2.1.3 gate JSONL 字段映射（建议）

- `pipeline="nightly"`
- `helper="wf_gov_gate"`
- `gate="GATE-RISK-EXIT"`
- `case_id="W2-3"`
- `case_dir="workflow_v2/20_pilot/W2-3_case"`
- `imp_state="IMP-RISK-VALIDATION"`（从调用参数；也可从 stdout `imp_state:` 抓取）
- `gov_artifact="ART-GOV-RISK-W2-3-PILOT"`（从 stdout `gov_artifact:` 抓取）
- `verdict` / `checks_failed`：
  - 从 stdout 行 `VERDICT=...` 与 `CHECKS_FAILED=...` 解析

### 2.2 Gate B：RELEASE-ENTRY（W2-1 case + GOV artifact = W2-3）

#### 2.2.1 调用（命令级示例）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_gov_gate.ps1 `
  -Gate GATE-REL-ENTRY `
  -CaseDir workflow_v2/20_pilot/W2-1_case `
  -GovRiskPath workflow_v2/20_pilot/W2-3_case/art_gov_risk.json
```

#### 2.2.2 预期行为（对齐已知限制）

- 由于 W2-1 当时可能缺 `tooling_checks`，`GATE-REL-ENTRY` **很可能**返回：
  - `VERDICT=require-human-override`（exit code `1`）
- 本接线把 W2-3 的 `ART-GOV-RISK` 作为 gate 输入；因此 W2-1 的 require-human-override 在此处是预期现象，不 retro 改 W2-1 历史 verdict。
- 实际 `checks_failed` 数组至少可能包含：
  - `fallback_used`（来自 W2-3 风险 artifact；取决于 gate baseline 检查）
  - `tooling_checks_missing`（来自 W2-1 的 `06_art_qa_rev.json` 缺失 tooling_checks）

#### 2.2.3 gate JSONL 字段映射（建议）

- `pipeline="nightly"`
- `helper="wf_gov_gate"`
- `gate="GATE-REL-ENTRY"`
- `case_id="W2-1"`
- `case_dir="workflow_v2/20_pilot/W2-1_case"`
- `gov_artifact="ART-GOV-RISK-W2-3-PILOT"`（从 stdout `gov_artifact:` 抓取）
- `qa_verdict`（可选：从 stdout `qa_verdict:` 抓取，schema 允许）
- `verdict` / `checks_failed`：从 stdout 解析

## 3. JSONL 写入契约（与 schema_v0.1 对齐）

### 3.1 推荐落点与命名

路径（repo 相对）与 schema 一致（见 `W3-C_metrics_schema.md` §3.5）：

- P0（推荐）：`workflow_v2/observability/gov_gate_metrics/YYYY-MM-DD.jsonl`
- P1（可选）：`workflow_v2/observability/gov_gate_metrics/latest.jsonl`（可覆盖或追加最新行）
- CI artifact 名称建议：`gov-gate-metrics`

写入责任：

- 在 CI / nightly job 内对每个 helper 调用生成一行，然后 `Add-Content` 追加到 P0。

### 3.2 统一信封字段（公共）

- `schema_version="gov-metrics-0.1"`
- `ts`：`[DateTime]::UtcNow.ToString("o")`
- `pipeline`：`pr` | `nightly` | `manual` | `agent`
- `helper`：`wf_gov_gate` | `wf_check_cross_ref`
- `run_id`（可选）：例如 `GITHUB_RUN_ID` 或 `nightly-<yyyymmdd-HHMMSS>`
- `repo_ref`（可选）：可用 git sha（非本票重点）

### 3.3 gate 行（wf_gov_gate 产物）字段列表（最终落地）

必填（schema v0.1）：

- `gate`（`GATE-RISK-EXIT` 或 `GATE-REL-ENTRY`）
- `case_id`（`W2-3` / `W2-1` 等）
- `verdict`（`allow` | `require-human-override` | `deny`）
- `checks_failed`（array；无失败 `[]`）
- `ts`、信封字段
- `exit_code`（int）

建议（schema 允许）：

- `case_dir`
- `ticket_id`（如 `W3-C-GOV-RISK-PILOT`）
- `imp_state`
- `gov_artifact`
- `qa_verdict`（仅 `GATE-REL-ENTRY` 可选）
- `message`（可用 stdout summary 截断）

### 3.4 cross-ref 行（wf_check_cross_ref 产物）字段列表（最终落地）

必填（schema v0.1）：

- `gate`：固定 `GATE-CROSS-REF-G8RECON`
- `scope`：如 `G8Recon`
- `verdict`：`allow`（exit 0）| `deny`（exit 1/2）
- `checks_failed`：失败探针 ID 数组（如 `["AC-2b"]`）
- `ts`、信封字段
- `exit_code`（int）

可选：

- `case_id`（若 PR/nightly 调用了 `-CaseId`）
- `checks_passed`
- `checks_total`（v0.1 固定 7；也可从 summary 解析）
- `message`

### 3.5 stdout 解析要点（可复制实现思路）

#### 3.5.1 `wf_gov_gate.ps1` 解析

脚本最后会打印两行：

- `VERDICT=<allow|require-human-override|deny>`
- `CHECKS_FAILED=<comma-separated|none>`

另有可选字段：

- `imp_state: <...>`
- `gov_artifact: <...>`
- `qa_verdict: <...>`

CI step 内的建议处理逻辑（示例片段）：

```powershell
$out = & powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_gov_gate.ps1 `
  -Gate GATE-RISK-EXIT `
  -CaseDir workflow_v2/20_pilot/W2-3_case `
  -ImpState IMP-RISK-VALIDATION 2>&1
$exitCode = $LASTEXITCODE

$verdict = (($out | Select-String -Pattern '^VERDICT=' | Select-Object -First 1).Line -replace '^VERDICT=','').Trim()
$checksCsv = (($out | Select-String -Pattern '^CHECKS_FAILED=' | Select-Object -First 1).Line -replace '^CHECKS_FAILED=','').Trim()
$checksFailed = @()
if ($checksCsv -and $checksCsv -ne 'none') { $checksFailed = $checksCsv.Split(',') }

# 组织 JSONL record（字段名按 W3-C_metrics_schema.md 对齐）
$ts = [DateTime]::UtcNow.ToString('o')
$record = @{
  schema_version = 'gov-metrics-0.1'
  ts = $ts
  pipeline = 'nightly'
  helper = 'wf_gov_gate'
  gate = 'GATE-RISK-EXIT'
  case_id = 'W2-3'
  case_dir = 'workflow_v2/20_pilot/W2-3_case'
  verdict = $verdict
  checks_failed = $checksFailed
  exit_code = $exitCode
  gov_artifact = 'ART-GOV-RISK-W2-3-PILOT'
  imp_state = 'IMP-RISK-VALIDATION'
}
$json = ($record | ConvertTo-Json -Compress)

# 追加到每日 JSONL（CI 里按你的路径实现 Add-Content）
Add-Content -Encoding UTF8 -Path $jsonlPath -Value $json

# 关键：吞掉 gate exit code，避免 deny 置红
exit 0
```

#### 3.5.2 `wf_check_cross_ref.ps1` 解析

解析思路：

- `exitCode`：`$LASTEXITCODE` → `verdict`
  - `0` → `allow`
  - `1/2` → `deny`
- `checks_failed`：从 stdout 中匹配 `^\[FAIL\]\s+(AC-[0-9a-z]+)` 抽取探针 ID。
- `message`：取 `Summary:` 行原文。

示例片段（示意用；字段按 schema 落地）：

```powershell
$scope = 'G8Recon'
$caseId = 'W2-1'
$out = & powershell -NoProfile -ExecutionPolicy Bypass -File workflow_v2/tools/wf_check_cross_ref.ps1 -Scope $scope -CaseId $caseId 2>&1
$exitCode = $LASTEXITCODE

$verdict = if ($exitCode -eq 0) { 'allow' } else { 'deny' }
$failIds = @()
foreach ($line in $out) {
  if ($line -match '^\[FAIL\]\s+(AC-[A-Za-z0-9-]+)\s') { $failIds += $Matches[1] }
}
$summary = (($out | Select-String -Pattern '^Summary:') | Select-Object -First 1).Line

$ts = [DateTime]::UtcNow.ToString('o')
$record = @{
  schema_version = 'gov-metrics-0.1'
  ts = $ts
  pipeline = 'pr'
  helper = 'wf_check_cross_ref'
  gate = 'GATE-CROSS-REF-G8RECON'
  scope = $scope
  case_id = $caseId
  verdict = $verdict
  checks_failed = $failIds | Select-Object -Unique
  exit_code = $exitCode
  message = $summary
}
$json = ($record | ConvertTo-Json -Compress)
Add-Content -Encoding UTF8 -Path $jsonlPath -Value $json

exit 0
```

## 4. Agent / manual 场景（仅描述，不展开实现）

根据 `W3-C_metrics_schema.md` §2.4（Agent SOP）：

- Agent/人工可以按场景选择 `wf_gov_gate.ps1` 的 `-Gate GATE-RISK-EXIT` 与 `-Gate GATE-REL-ENTRY`，并使用同一套 JSONL 解析/写入约定。
- 本票不新增 agent runtime、不改 deny engine；仅在文档层指出：
  - `pipeline="manual"`：人工按 ticket 执行并写入指标
  - `pipeline="agent"`：自动/半自动触发 gate 后写入指标

## 5. 需要在 CI 层保证的两个“非功能”点（v0.1）

1. **吞掉 gate 的非 0 exit**：即使 `VERDICT=deny`（exit code 2），CI step 也必须保证“作业最终不置红”，只在指标与日志中留痕。
2. **确保 JSONL 可落地**：CI step 要有 `jsonlPath` 变量，并执行目录存在性处理或仅写入 artifact（见 schema 的写入责任备注）。

## 6. 三场景概览（PR / nightly / manual）

- **PR**
  - 仅调用 `wf_check_cross_ref.ps1`（例如 `-Scope G8Recon -CaseId W2-1`）。
  - PR 呈现为 warning；JSONL 中 `verdict` 仍使用 `allow/deny`（映射自 exit code），**不**把 “warning” 当作 `verdict` 字符串。
  - 用 `continue-on-error` 或在 step 内捕获非 0 exit，保证 PR 不因 cross-ref 问题直接 fail。
- **Nightly**
  - 顺序固定为：
    1. `wf_check_cross_ref`（写 cross-ref JSONL）
    2. `wf_gov_gate` / `GATE-RISK-EXIT`（W2-3 pilot）
    3. `wf_gov_gate` / `GATE-REL-ENTRY`（W2-1 + GOV artifact）
  - 对任何非 0 exit：通过 swallow exit / `continue-on-error`，job 不因 deny 而失败，但仍写 JSONL 记录 `VERDICT` / `CHECKS_FAILED`。
- **Manual / Agent**
  - 允许副官/人工依 SOP 手动触发 gate/helper，使用与 nightly 相同的 stdout 解析逻辑写入 JSONL（`pipeline=manual` 或 `pipeline=agent`）。
  - 本票不改 agent runtime、不引入 deny engine runtime。

## 7. Wave 4+ 可演进方向（标记）

- **下一步可做的事**
  - 把本文的 PowerShell 调用与 JSONL 写入片段接入真实 CI workflow（含 artifact 上传 `gov-gate-metrics`）。
  - 视治理决策，将 nightly / 特定路径升级为 `fail-on-deny`（非 v0.1）。
- **当前票刻意不做**
  - 不改任何 CI 配置文件（如 `.github/workflows`）。
  - 不启用 `fail-on-deny`。
  - 不对非 pilot case 强制 gate。

