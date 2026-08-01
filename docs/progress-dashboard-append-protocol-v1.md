# Progress／Dashboard／master_status 写入边界协议（v1）

> **Ticket**: `FP-G1-T5-constitution-progress-append-protocol-v1` · Full-Phase G1 · P1／P10 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10  
> **对齐**：宪法 §6.2–§6.3 · `OPS_CYCLE.md`／`_ops_cycle.py` · Multi-Chat Scribe · inspector

---

## non_claims（置顶 · 必读）

| 本协议 **不是** | 说明 |
|-----------------|------|
| ≠ **已改 Dashboard／master_status 正文** | 本页只定边界；**不**改 Phase% 数字格 |
| ≠ **替代 `_ops_cycle.py`** | 战报校验／append 仍走 OPS_CYCLE 工具链 |
| ≠ **授权 lane chat 改 Phase%** | 明确 **禁止**；普通票只提案 Δ |
| ≠ **Phase closure** | 协议齐 ≠ 任一 Phase 结案 |

**位阶**

| 文件 | 角色 |
|------|------|
| **本档** | append-only／Governance 独占字段 **SSOT** |
| [`docs/phase-progress-impact-protocol-v1.md`](./phase-progress-impact-protocol-v1.md) | Phase 影響 · **提案 Δ vs 寫入 %** |
| [`docs/lane-progress-append-template-v1.md`](./lane-progress-append-template-v1.md) | Progress 末尾条目形状（含 Phase 影響） |
| `04_Workflows/HARNESS_CONSTITUTION.md` **§6.2–§6.3** | Progress 末尾追加；master_status／handoff Governance 独占 |
| `04_Workflows/OPS_CYCLE.md` · `_ops_cycle.py` | 战报 JSON 校验／append |
| [`docs/WAVE_PROGRESS_DASHBOARD.md`](./WAVE_PROGRESS_DASHBOARD.md) | Phase% **唯一数字 SSOT**（lane **只读**） |
| Multi-Chat Scribe（`multi_chat_roles.mdc`） | Progress **仅末尾**；不重排历史 |
| inspector／over-claim spotcheck | 防 over-claim；可链本协议 |

---

## 1. Purpose

为 Multi-Chat **Scribe**／lane chat 提供：谁可写 Progress／Dashboard／master_status、末尾模板字段、以及 **禁止改 Phase%** 的 enforcement 句。

---

## 2. 谁可写（权限表）

| 目标 | 谁可写 | 怎么写 | 谁不可写 |
|------|--------|--------|----------|
| `04_Workflows/00_Agent_Work_Progress.md` | **Scribe**（建议）· Orchestrator 确认后；worker 阻塞条（Rule 10） | **append-only 末尾**；禁止删改／重排既有段（§6.2） | Implementer／Reviewer 不得重写历史；lane 不得覆盖中段 |
| `docs/WAVE_PROGRESS_DASHBOARD.md` **Phase% 数字格** | **Governance／尚书省授权票** | 仅授权治理票；须留痕 | **lane chat／Scribe／Implementer 一律禁止** |
| Dashboard **叙事脚注**（非数字） | Governance 或明示授权 doc 票 | 最小触及；不改 % | 默认禁止顺手改 |
| `project_status/master_status.md` | **Governance 独占**（§6.3） | 里程碑段由治理追加 | Multi-Chat 四角色默认 **不写** |
| `handoff.md` | **Governance 独占**（§6.3） | 同上 | 同上 |

### Enforcement（lane chat · 必读）

> **Lane chat／Implementer／Reviewer／Scribe 禁止修改 `WAVE_PROGRESS_DASHBOARD.md` 的 Phase% 数字格。**  
> 若需 uplift：开 Governance／尚书省 **W-PROG** 票；本协议 **不**构成改 % 授权。  
> 违反 → Reviewer `needs_changes`／Orchestrator 回滚叙事；Progress 末尾留痕（Rule 12）。

---

## 2.1 提案 Δ vs 写入 %（分栏）

| 栏 | 谁 | 写什么 | 权威 |
|----|----|--------|------|
| **提案 Δ**（`proposed_delta_pct`） | 普通票 FRAME／B／C／D／Progress「Phase 影響」 | 建议相对基线的 Δ；`apply_phase_pct: false` | [`phase-progress-impact-protocol-v1.md`](./phase-progress-impact-protocol-v1.md) |
| **写入 %**（Dashboard 数字格） | **仅** Governance 授权 **W-PROG** 刷新票 | 改 `docs/WAVE_PROGRESS_DASHBOARD.md` 当前列／Gauge／跃升脚注；STATE 须标「已授权写入」+ 证据 | 本档 §2 权限表 · 尚书省指令 |

**规则摘要**

1. 普通票 **只提案**；`实际上调=否／待 W-PROG`。  
2. **唯一可写数字格** = 授权 W-PROG／Governance 票（`apply_phase_pct: true`）。  
3. 叙事刷新（脚注／索引句）≠ 数字变更；二者须在战报分栏标明。  
4. 禁止无证据回到已废弃虚高基线（例：06-23 全盘 ~78%／多数 ≥80%）覆盖现行保守 SSOT。

---

## 3. Progress 末尾条目模板

```markdown
## YYYY-MM-DD · <TICKET-ID> · `<overall_status>`

**角色**：<Orchestrator|Implementer|Reviewer|Scribe> · Multi-Chat  
**票号**：`<TICKET-ID>` · group_id: <G?> · evidence_tier: <L-local|…>  
**lifecycle_phase**：<…> · **Reviewer**：`<accepted|…>` · risk=<low|…>

### 变更
- …

### skeleton
- 无 | …

### placeholder
- …

### 阻塞
- 无（本票）。仍 human-blocked：…  
- blocked: …

### 下一步
1. …

### Phase 影响
- 影响 Phase：… · baseline：… · proposed_delta：… · 实际上调：否｜待 W-PROG｜是（W-PROG） · non_claims：…

**验证**：… · run_url: <optional CI／Actions URL 或 `n/a`>  
**未改**：`core/**` · `.github/workflows/**` · Phase%（除非授权 W-PROG）· 金钥
```

### 必填语义字段

| 字段 | 说明 |
|------|------|
| `evidence_tier` | 如 `L-local`／CI／GA-remote |
| `run_url` | 有则填；无则 `n/a`（勿编造） |
| `group_id` | 如 G1／G5／G6 |
| `blocked`／`下一步` | 本票阻塞 + 全局仍挂 human 项（诚实） |
| **Phase 影響** | 影响 Phase · baseline · proposed_delta · 实际上调 · non_claims（见 impact 协议） |

---

## 4. 与 OPS_CYCLE／inspector

- 封存建议：`validate-report` → `append-report`（见 `AGENTS.md` §封存）；本模板字段应对齐 OPS_CYCLE 战报组。  
- Reviewer／inspector：若发现**普通票**改 Phase% 或重排 Progress → 按 over-claim／§6.2 拒绝。  
- 下游模板票：`FP-G5-T3-progress-append-template-v1` 可消费本协议（交叉引用，不替代）。  
- Phase 影响栏位 SSOT：`docs/phase-progress-impact-protocol-v1.md`。

---

## 5. Mini checklist

- [ ] 写 Progress 只用末尾 append  
- [ ] 未碰 Phase% 数字／master_status／handoff（除非授权 W-PROG／Governance 票）  
- [ ] 条目含 evidence_tier · blocked／next · Phase 影響（若有 phase_targets）  
- [ ] 提案 Δ 与写入 % 分栏清楚（本票未擅自写入）  

---

## 6. Verification（本票 AC · `rg`）

```bash
rg "append-only|evidence_tier|Phase%|non_claims|提案 Δ|写入 %" docs/progress-dashboard-append-protocol-v1.md
```

期望命中：`non_claims`、`append-only`、`evidence_tier`、Phase% 禁止句、权限表、**提案 Δ vs 写入 %**。
