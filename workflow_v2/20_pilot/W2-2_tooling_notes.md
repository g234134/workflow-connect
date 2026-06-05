# W2-2 — Helper tooling 与最小 QA gate 说明

> **角色**：可复用 runbook + 脚本索引；**非** CI pipeline。  
> **来源**：W2-1 `05_art_eng_wr.md` §4、`06_art_qa_rev.json` evidence AC-1～AC-4。  
> **配套**：`W2-2_imp_state_schema.md`；`tools/wf_check_cross_ref.ps1`。

---

## 1. 快速开始

从**战车根**执行（优先 `rg`；无 `rg` 时自动回退 **Select-String**）：

```powershell
powershell -NoProfile -File workflow_v2/tools/wf_check_cross_ref.ps1
```

**W2-1 案卷 QA 复验（显式 case 标签，可选）**：

```powershell
powershell -NoProfile -File workflow_v2/tools/wf_check_cross_ref.ps1 -Scope G8Recon -CaseId W2-1
```

| 参数 | 说明 |
|------|------|
| `-Scope G8Recon` | 默认；W2-1 同款 AC-1～AC-4 交叉引用包（`Default` 同义） |
| `-CaseId W2-1` | 案卷标签；映射到 `G8Recon` scope（见 `-ListScopes`） |
| `-RepoRoot <path>` | 显式战车根（默认：由脚本位置推断） |
| `-G7Dir` / `-G8EngFile` | 覆盖 scope 内路径（未来 G8-RECON 变体票） |
| `-ListScopes` | 列出内置 scope 与 CaseId 预设后退出 0 |
| `-Strict` | 失败时 exit 1（与默认相同；预留给 CI gate） |

**期望输出**：7 行 `[PASS]`（AC-1；AC-2a/b/c；AC-3；AC-4a/b）→ `Summary: ALL PASS (7 checks) | exit 0`。

### 1.1 在 QA 流程中何时调用

| 阶段 | 动作 |
|------|------|
| **NBT-T02**（独立重跑 AC-1～AC-4） | 在 **Read diff 之前或之后** 各跑一次均可；结果写入 `ART-QA-REV.evidence[]`（`id`=AC-*，`key_output`=命中数 + 日期） |
| **与 Eng EVD 对账** | 脚本汇总须与 `05_art_eng_wr.md` §4 `key_results` 一致；不一致 → `blocked` 或记录差异 |
| **禁止** | 仅跑本脚本即标 `accepted`（仍须 NBT-T03/T04/T05，见 §4） |

**脚本职责边界**：**只检查交叉引用字面量**（grep 级）；**不负责** G7-3 跳关语义、CHG 定义、IMP exit 是否被变相改写 — 属 **AC-5**，checker **必须**人工 Read diff（§2 末段、§4 NBT-T04）。

### 1.2 退出码与输出映射

| exit code | 含义 |
|-----------|------|
| **0** | 全部 7 项 probe 通过 → AC-1～AC-4 **grep 侧**可记 `exit_ok: true` |
| **1** | 至少 1 项 `[FAIL]` → 对应 AC 组不可标通过；查控制台 `matches=` 行 |
| **2** | 战车根／G7／G8 路径配置错误 |

控制台每行 `[PASS]`/`[FAIL]` 的 probe ID（如 `AC-2b`）可原样填入 evidence 子项；rollup 时 **AC-2** = AC-2a **且** AC-2b **且** AC-2c 全绿。

---

## 2. AC-1～AC-4 与脚本映射

| ID | 检查意图 | 脚本内检查 | W2-1 手工命令（等价） |
|----|----------|------------|----------------------|
| **AC-1** | G7-2 无 `ART-REL-RECORD` 残留 | `rg ART-REL-RECORD` → G7-2 entry 文件 0 命中 | 同左 |
| **AC-2** | G7 entry/exit 无 stale `待 G8-1/2/5` | 脚本内 AC-2a/b/c（字面量 `待 G8-1`…`5`）；或 `rg "待 G8-[125]"` | 同左 |
| **AC-3** | G7-3 无裸 `待 G10-2` | `rg "待 G10-2"` → G7-3 文件 0 命中 | 同左 |
| **AC-4a** | G8-3 无错误文件名 `10_states` | `rg 10_states` → `30_engineering.md` 0 命中 | 同左 |
| **AC-4b** | G8-3 引用正式 `10_workflow_states` | `rg 10_workflow_states` → ≥1 命中 | 同左 |

**AC-5（未入脚本）**：人工 diff review（G7-3 跳关表、G6 引用、IMP exit 语义未改）— checker **必须**保留 Read diff，见 §4 NBT-T04。

---

## 3. 无 `rg` 时的可复制命令块

```powershell
# 在战车根；每项期望见 W2-1 05_art_eng_wr.md §4 key_results

rg "ART-REL-RECORD" workflow_v2/10_governance/G7_state_machine/20_entry_conditions.md
rg "待 G8-[125]" workflow_v2/10_governance/G7_state_machine/
rg "待 G10-2" workflow_v2/10_governance/G7_state_machine/30_exit_and_transitions.md
rg "10_states" workflow_v2/10_governance/G8_artifact_contract/30_engineering.md
rg "10_workflow_states" workflow_v2/10_governance/G8_artifact_contract/30_engineering.md
```

将命中数记入 **ART-ENG-EVD**／**ART-QA-REV** `evidence[]`（`id` = AC-*，`key_output` = 命中数 + 日期）。

---

## 4. 最小 no-blind-trust tooling checklist（QA / Release）

> 对齐 G10-2 **NBT-***；v0.1 为 **人工 + 轻量脚本**，非自动化 gate。  
> 正式制度 → `10_governance/G10_governance_rulebook/20_no_blind_trust.md`。  
> **G8 契约**：`10_governance/G8_artifact_contract/40_qa.md` §5（checker 可勾选 + verdict 裁決指引）。  
> **实现索引**：G10-2 §1.2 末句 → 本节 + G8 §5。

**在做 QA 或 Release 收口前，至少完成：**

| Step | 动作 | 对应 NBT | 通过标准 | 推荐字段（`tooling_checks.*`） |
|:----:|------|----------|----------|-------------------------------|
| **NBT-T01** | **不**因 `90_run_queue` 本票 `DONE` 或 Eng `ok: true` alone 放行 | NBT-RT-01、NBT-AI-01 | 已读 P0 `imp_state` 与 P1 迁移日志；与票面 IMP exit 一致 | `no_queue_or_eng_ok_only` |
| **NBT-T02** | **独立重跑** AC-1～AC-4（脚本或 §3 命令） | NBT-RT-03 | 与 Eng EVD 一致或记录差异；写入 ART-QA-REV `evidence[]` | `re_ran_ac_grep` |
| **NBT-T03** | **亲自 Read** 本票 diff（或 Eng WR §1 变更清单 + spot-check 文件） | NBT-RT-04 | `scope_check.within_ticket` 可辩护 | `read_diff_or_change_list` |
| **NBT-T04** | 完成 **AC-5** 语义审查（跳关／CHG 未变相改写） | NBT-AI-06 | QA JSON 含 AC-5 或等效 `manual` evidence 行 | `ac5_semantic_review` |
| **NBT-T05** | 核对 **artifact 存在性**：票面 **ART-*** 路径在案卷可索引 | G8 各轨 §4 | 缺件 → `rejected` 或 `blocked`，不前进 `imp_state` | `ticket_artifacts_indexed` |
| **NBT-T06** | 读 **ART-QA-REV** `gaps[]`（若 `accepted_with_gaps`） | NBT-GC-03 | gaps owner 与 `blocks_release` 已判 | `gaps_owner_and_release_judged` |
| **NBT-T07** | Release 前确认 **ART-REL-DEC** 与 **imp_state** 匹配 G7-3 | NBT-H-03 | 非 queue Notes 自述「已发布」 | `release_dec_aligns_imp_state` |

### 4.1 字段载体（推荐 · 非必填）

checker 在 **ART-QA-REV** 收口前，建议写入可选子对象 **`tooling_checks`**（与 G8 `dod_checklist` 并列，**不**替代四流派 DoD）：

```json
{
  "tooling_checks": {
    "checklist_id": "W2-2-NBT-T01-T07-v0.1",
    "no_queue_or_eng_ok_only": true,
    "re_ran_ac_grep": true,
    "read_diff_or_change_list": true,
    "ac5_semantic_review": true,
    "ticket_artifacts_indexed": true,
    "gaps_owner_and_release_judged": null,
    "release_dec_aligns_imp_state": null,
    "notes": "T06/T07 N/A — not accepted_with_gaps; pre-release QA only"
  }
}
```

| 规则 | 说明 |
|------|------|
| **载体** | 首选 **ART-QA-REV** 顶层 `tooling_checks`；次选 **ART-QA-DOD** 扩展键 `tooling_checks`（与四键并列，勿混进 `context_source` 等语义） |
| **类型** | 各 **T01–T05** 为 `boolean`；**T06**／**T07** 在未触发时用 `null` 或省略 + `notes` 说明 **N/A** |
| **证据** | **T02**／**T04** 仍须在 `evidence[]` 留痕（`id`: `AC-*`／`AC-5`）；`tooling_checks` 为 **勾选摘要**，不代替 `evidence` |
| **别名** | 历史草案可用 `qa_checks.*`；新案统一 **`tooling_checks.*`**（见上表列名） |

**NBT-Txx → 字段速查**

| ID | `tooling_checks` 键 | 条件 |
|----|---------------------|------|
| NBT-T01 | `no_queue_or_eng_ok_only` | 每票 QA |
| NBT-T02 | `re_ran_ac_grep` | 每票 QA（治理／交叉引用类票必 true） |
| NBT-T03 | `read_diff_or_change_list` | 每票 QA |
| NBT-T04 | `ac5_semantic_review` | 每票 QA（含语义／跳关风险时必 true） |
| NBT-T05 | `ticket_artifacts_indexed` | 每票 QA |
| NBT-T06 | `gaps_owner_and_release_judged` | 仅 `verdict: accepted_with_gaps` |
| NBT-T07 | `release_dec_aligns_imp_state` | 仅 Release 轨／`IMP-RELEASE-DECISION` 前 |

### 4.2 W2-1 与后续案卷

**W2-1**（`20_pilot/W2-1_case/06_art_qa_rev.json`）已 **手动** 执行 T01–T05 等价步骤（独立 grep、`AC-5` evidence、`NBT` evidence 行），**未** 写入 `tooling_checks` 对象——视为 v0.1 实验结果，**不** retro-fit。  
**后续 pilot／生产案卷**：checker 建议改用 §4.1 字段化记载，便于 W3 gate／CI 只读校验（本票 **不** 实现 gate）。

**禁止（tooling 层）**：

- 仅跑 `wf_check_cross_ref.ps1` 即标 QA `accepted`（缺 T03/T04/T05）。  
- 仅看 `06_art_qa_rev.json` 的 `ok: true` 不再跑 grep（缺 T02）。  
- 用 `_ops_cycle.py checklist` **代替** 本票 acceptance（NBT-RT-06）。

---

## 5. `imp_state` 半自动更新（人工主导）

1. 完成本态 ART 与（若 Eng）§4 EVD。  
2. 对照 G7-3 确认 **合法下一态**。  
3. 编辑案卷 `*_case.md`：更新 §2 `imp_state` + § 迁移日志一行。  
4. 施工票 Notes 写：`IMP exit → IMP-…`（**不**改 queue Status 语义为 IMP）。  

机读校验留 **W2-2-IMP-FIELD** 施工票。

---

## 6. 未来案卷 / 新 Scope（hook，非 CI）

1. **同类 G8-RECON 票**：默认 `-Scope G8Recon`；若 G7/G8 路径不同，仅覆盖 `-G7Dir` / `-G8EngFile`。  
2. **新 CaseId**：在脚本 `$CaseScopeMap` 增加一行（如 `"W2-3" = "G8Recon"`）；不必改 QA 契约主干。  
3. **全新 pattern 包**：在 `wf_check_cross_ref.ps1` 增加 scope 函数 + `Get-ChecksForScope` 分支；在本文 §2 补 AC 映射表。  
4. **Wave 3+ CI**：见 §8；本票**不**接入 pipeline。

---

## 7. 文件索引

| 路径 | 用途 |
|------|------|
| `workflow_v2/tools/wf_check_cross_ref.ps1` | AC-1～AC-4b 批量 grep（scope / CaseId） |
| `workflow_v2/tools/wf_gov_gate.ps1` | 只读治理 gate（`GATE-RISK-EXIT`／`GATE-REL-ENTRY`）；**不**替代 cross-ref；REL 可读 `ART-QA-REV.tooling_checks`（`W2-3_minimal_gate_design.md` §7） |
| `workflow_v2/20_pilot/W2-2_imp_state_schema.md` | `imp_state` v0.1 |
| `workflow_v2/10_governance/G7_state_machine/40_imp_state_field_v0.1.md` | G7 附录（字段约定索引） |
| `workflow_v2/20_pilot/W2-1_case/05_art_eng_wr.md` §4 | W2-1 证据样板 |

---

## 8. 日后接入 CI / gate 时注意

| 项 | 建议 |
|----|------|
| **命令** | `powershell -NoProfile -File workflow_v2/tools/wf_check_cross_ref.ps1 -Scope G8Recon -Strict` |
| **工作目录** | 战车根；或 `-RepoRoot` 指向含 `workflow_v2` 的目录 |
| **rg** | CI 镜像可预装 `rg`；无则脚本自动 Select-String（较慢但等价） |
| **范围** | 仅 AC-1～AC-4；**勿**用本 job 代替 AC-5／NBT-T03～T07 |
| **证据** | job 日志归档 + `evidence[]` 仍须人工或 checker 写入 ART-QA-REV |
| **闸门** | 建议独立 job 名 `wf-cross-ref-g8recon`；失败 exit 1 阻断 merge 前须尚書省批准 gate 制度 |

---

## 9. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | v0.1：脚本 + NBT-T01～T07 清单 + W2-1 命令抽象 |
| 2026-05-27 | v0.2：Scope/CaseId、QA 调用小节、exit 映射、§8 CI 备忘 |
| 2026-05-27 | W2-2-QA-CHECKLIST：§4.1 `tooling_checks` 字段映射；G8 §5 交叉引用 |
