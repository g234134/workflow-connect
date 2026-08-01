# Lane Chat — Progress Append Template (v1)

> **Ticket**: `FP-G5-T3-progress-append-template-v1` · Full-Phase G5 · P5 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **对齐**：`W-MASTER-full-phase-plan_state.md#G5` · 宪法 §6.2（Progress 仅末尾追加）· FP-G1-T5 协议（可并行互链）

---

## non_claims（置顶 · 必读）

| 本模板 **不是** | 说明 |
|-----------------|------|
| ≠ 已改 `00_Agent_Work_Progress.md` 历史段 | 模板仅供 **末尾 append**；**禁止**覆盖／重排既有段 |
| ≠ 授权改 Dashboard **Phase%** | lane chat／Scribe **不得**改数字格；仅提案 Δ |
| ≠ 替代 `OPS_CYCLE`／`_ops_cycle.py` | 战报 JSON 校验仍走 OPS_CYCLE；本档是 Progress **条目形状** |
| ≠ **P5 closure**／Round-2 GO | 模板齐 ≠ Phase 结案 |

**位阶**

| 文件 | 角色 |
|------|------|
| **本档** | 多分支 lane chat／Scribe **Progress 末尾**条目模板 |
| [`docs/progress-dashboard-append-protocol-v1.md`](./progress-dashboard-append-protocol-v1.md) | FP-G1-T5：**谁可写** Progress／Dashboard／master_status（协议 SSOT；可并行，完成后互链） |
| [`docs/phase-progress-impact-protocol-v1.md`](./phase-progress-impact-protocol-v1.md) | Phase 影响栏位 · 提案 Δ vs 写入 %（`apply_phase_pct` 默认 false） |
| 宪法 §6.2／§6.3 | Progress append-only；`master_status`／`handoff` Governance 独占 |
| `04_Workflows/OPS_CYCLE.md` | 战报字段与 validate／append-report |

---

## 1. Purpose

统一 Multi-Chat／三分支交棒时 Progress **末尾**写法，强制含 `evidence_tier` · `group_id` · blocked／next，避免改历史或误动 Phase%。

---

## 2. Append-only 硬规则

| MUST | FORBID |
|------|--------|
| 仅在 `04_Workflows/00_Agent_Work_Progress.md` **文末**追加 | 改写／删除／重排既有段落（宪法 §6.2） |
| 条目含 `evidence_tier` · `group_id` · blocked／next · **Phase 影响** | 在 Progress 内改 Dashboard Phase% 或宣称 Phase closure |
| 验证命令与关键结果语义可重跑 | 草稿冒充已跑验收（合约 Rule 11） |
| 金钥仅 `[OK]`／`[FAILED]` 类粮草结果 | 输出密钥原文 |

---

## 3. 模板（复制到 Progress 末尾）

```markdown
---

## YYYY-MM-DD · <TICKET-ID> · `done`|`blocked`|`in_progress`

**角色**：<Orchestrator|Implementer|Reviewer|Scribe> · Multi-Chat  
**票号**：`<TICKET-ID>` · Full-Phase · **group_id**：`<G1|G5|G6|…>` · **evidence_tier**：`<L-local|…>`  
**lifecycle_phase**：<B|O|…> · **Reviewer**：`<accepted|…>` · risk=<low|…>

### 变更

- <路径>：<一句>

### skeleton

- <无 | 列出>

### placeholder

- <无 | 列出>

### 阻塞（blocked）

- <無（本票）| 具体阻塞 + owner>

### 下一步（next）

1. <可执行下一步>
2. <勿碰：human-gated／Phase%／…>

### Phase 影響

- **影響 Phase**：<P? | 無>
- **baseline**：<Dashboard 刷新日／列 · 或 n/a>
- **proposed_delta**：<+N | 0 | n/a>
- **實際上調**：否 | 待 W-PROG | 是（W-PROG · YYYY-MM-DD）
- **non_claims**：…

**验证**：<命令> · <关键结果语义>。**未改** `core/**` · Phase%（除非本條為授權 W-PROG）· 金钥（若适用）。
```

### 字段说明

| 字段 | 要求 |
|------|------|
| `group_id` | 与 QUEUE／FRAME 一致（如 `G5`） |
| `evidence_tier` | 与票 FRAME 一致（doc/spec 多为 `L-local`） |
| `blocked` | 本票阻塞；全局 human-gated 可一句引用 QUEUE `global_blocked` |
| `next` | 可派下一票或明示「仅 human」 |
| **Phase 影響** | 見 [`phase-progress-impact-protocol-v1.md`](./phase-progress-impact-protocol-v1.md)；普通票 `實際上調=否／待 W-PROG` |

---

## 4. 与 FP-G1-T5 交叉引用

| 文档 | 分工 |
|------|------|
| **本档（G5-T3）** | **条目形状**（模板正文 · 含 Phase 影響欄） |
| **G1-T5** `progress-dashboard-append-protocol-v1.md` | **谁可写**哪类文件、Phase% 禁令、Governance 独占 |
| **FP-PHASE-IMPACT** `phase-progress-impact-protocol-v1.md` | FRAME 五欄 · 報告「Phase 影響」小節 · 提案 Δ vs 寫入 % |

两票可并行；任一方 DONE 后应互链。若 G1-T5 尚未落地，lane chat 仍须遵守本档 append-only + 宪法 §6.2。

---

## 5. Mini checklist（Scribe）

- [ ] 只 append 末尾；未触碰历史段  
- [ ] 含 `evidence_tier` · `group_id` · blocked／next · **Phase 影響**  
- [ ] 未改 Phase%／`master_status`／`handoff`（除非授權 W-PROG）  
- [ ] 未宣称 Phase closure／Round-2 GO  

---

## 6. Verification（本票 AC · `rg`）

```bash
rg "evidence_tier|append|template|non_claims|Phase 影響" docs/lane-progress-append-template-v1.md
```

期望命中：`non_claims`、append-only、`evidence_tier`、模板字段、Phase% 否定句、**Phase 影響**。
