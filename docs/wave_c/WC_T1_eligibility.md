# WC-T1 · Ticket Eligibility & Acceptance

> **票号**：WC-T1  
> **实现**：`04_Workflows/ticket_eligibility.py`  
> **CLI**：`scripts/run_ticket_eligibility.py`  
> **依赖**：`04_Workflows/dispatch_executor.py`（只读解析 + 分桶逻辑）

---

## 1. 目的

在现有 Multi-Chat **ticket state markdown** 结构上，提供最小可用的「智能接单 / Eligibility」判断：

- 输入：ticket id + 可选补充 context
- 输出：`eligible` / `ineligible` + `reasons[]`
- **不**写入 `*_state.md`、**不**调用 LLM、**不**自动开 chat

与 W5-T1 `routing/intake_decision_rules_v1.py`（Tabular case intake）**不同**：本模块面向 **工单票务**（`04_Workflows/tickets/*_state.md`）。

---

## 2. 数据来源（SSOT）

| 层级 | 路径 | 说明 |
|------|------|------|
| Ticket state | `04_Workflows/tickets/<ticket_id>_state.md` | FRAME + STATE 区块 |
| 解析器 | `dispatch_executor.parse_ticket_state_markdown` | → `TicketRecord` |
| Done 集合 | 扫描全部 `*_state.md` 中 `overall_status ∈ {done, accepted, accepted_with_gaps}` | 用于依赖解析 |

Wave / Phase **不**读 Dashboard 或 DB；仅从 **ticket id 命名** 或调用方 context 覆盖推断。

---

## 3. 使用的字段清单

### 3.1 STATE（主判断）

| 字段 | 用途 |
|------|------|
| `ticket_id` | 票标识（文件头 + 文件名） |
| `title` | 回显 |
| `overall_status` | done / blocked / draft / in_progress / review / scribe |
| `implementation_status` | 是否 `in_review` |
| `current_owner` | orchestrator / implementer / reviewer / scribe |
| `next_action` | 是否等待 reviewer、infra_unblock、assign 等 |
| `status_by_role` | 各角色 pending / in_progress / done |

### 3.2 FRAME（依赖）

| 字段 | 用途 |
|------|------|
| `Dependencies` | 前置票列表；未 done → `dependency_unresolved:<id>` |

### 3.3 派生 / 复用 dispatch_executor

| 派生项 | 来源 |
|--------|------|
| `bucket` | `classify_ticket` → runnable_now / blocked / in_review / done / draft |
| `recommended_role` | `recommend_role` |
| `unresolved_dependencies` | FRAME deps ∩ 非 done 集合 |

### 3.4 补充 context（可选）

| 字段 | 用途 |
|------|------|
| `requested_role` | implementer / reviewer / scribe / orchestrator |
| `wave` / `phase` | 覆盖 id 推断 |
| `notes` | 附加 reason 备注 |

---

## 4. 判定规则（v1）

| 条件 | 结果 | 典型 reason |
|------|------|-------------|
| `overall_status` 为 done 类且非 scribe 收尾 | ineligible | `ticket_already_done` |
| done + `requested_role=scribe` + scribe 待办 | eligible | `done_ticket_pending_scribe` |
| `overall_status=blocked`（非 infra_unblock） | ineligible | `overall_status_blocked` |
| 未满足 FRAME Dependencies | ineligible | `dependency_unresolved:<id>` |
| `requested_role=implementer` 且 review 关口活跃 | ineligible | `waiting_reviewer_gate` |
| `requested_role=reviewer` 且 in_review | eligible | `review_gate_active` |
| `overall_status=draft` 且未 assign implementer | ineligible（implementer） | `draft_not_assigned` |
| bucket 为 runnable_now / in_review（角色匹配） | eligible | `bucket_runnable_now` 等 |

规则与 `docs/control_plane_dispatch_executor.md` 分桶表对齐，并增加 **按 requested_role 过滤** 的接单语义。

---

## 5. API

### 5.1 纯函数

```python
from ticket_eligibility import evaluate_ticket_eligibility, EligibilityContext
from dispatch_executor import parse_ticket_state_markdown

record = parse_ticket_state_markdown(text, path)
result = evaluate_ticket_eligibility(
    record,
    done_ids={"WB-T1", "WB-T2"},
    context=EligibilityContext(requested_role="implementer"),
)
# result["eligible"] → "eligible" | "ineligible"
# result["reasons"] → list[str]
```

### 5.2 CLI

```bash
python scripts/run_ticket_eligibility.py --ticket TEST-BLK --requested-role implementer
python scripts/run_ticket_eligibility.py --ticket W1-T1 --requested-role reviewer --format text
python scripts/run_ticket_eligibility.py --ticket W1-T2 --context-json '{"requested_role":"scribe"}'
```

### 5.3 REST（可选本地）

```bash
python scripts/run_ticket_eligibility.py --serve 8765
```

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/v1/tickets/<ticket_id>/eligibility?requested_role=implementer` | 查询单票 |
| POST | `/api/v1/tickets/eligibility` | Body: `{"ticket_id":"W1-T2","context":{"requested_role":"implementer"}}` |

成功响应 `ok: true`；票文件不存在时 `ok: false`，`eligible: ineligible`。

### 5.4 输出形状

```json
{
  "ok": true,
  "ticket_id": "TEST-BLK",
  "eligible": "ineligible",
  "reasons": ["overall_status_blocked", "dependency_unresolved:W9-T9"],
  "bucket": "blocked",
  "recommended_role": null,
  "wave": null,
  "phase": null,
  "requested_role": "implementer",
  "message": "ineligible · 2 reason(s)"
}
```

---

## 6. 测试

```bash
python -m unittest tests.test_ticket_eligibility -v
```

覆盖场景（≥5）：

1. in_progress → implementer **eligible**
2. blocked overall_status → **ineligible**
3. 未解决依赖 → **ineligible**
4. done 票 + implementer → **ineligible**
5. review 关口 + implementer → **ineligible**
6. in_review + reviewer → **eligible**
7. done + scribe → **eligible**

Fixtures：`tests/fixtures/dispatch/*.md`（与 dispatch_executor 共用）。

---

## 7. 非范围

- 不改 `*_state.md`、不自动更新 STATE
- 不替代 `_route_task.py`（HQ worker 路由）
- 不替代 W5-T1 case intake decision
- 不接 Cursor API / 不开 chat

---

## 8. Integration plan: from tool to gate

> **现状**：WC-T1 已交付纯函数 + CLI/REST（§5）；**入口 A** 已由 **WC-T1-INTEGRATION** 实现（`generate_cards` + CLI flags）。入口 B/C 仍为设计稿。  
> **目标**：把 Eligibility 从「可手动查询的工具」升级为「Orchestrator / 开 chat 前的硬/软关口」。  
> **实施票**：`04_Workflows/tickets/WC-T1-INTEGRATION_state.md`

### 8.1 推荐挂载入口（优先级序）

| # | 场景 | Entry point | 调用方式 | ineligible 行为（建议） | 状态 |
|---|------|-------------|----------|-------------------------|------|
| **A** | Orchestrator 生成 Implementer 指令卡前 | `04_Workflows/_dispatch_cards.py` → `generate_cards()`（由 `scripts/run_dispatch_cards.py` 触发） | 对每个 plan entry，在 `build_card_input` / 写卡前调用 `check_ticket_eligibility(tid, repo_root, context={"requested_role": entry["recommended_role"]})` | **硬拒绝**：`--eligibility-gate block` 跳过该票 card（计入 `cards_skipped`），写入 run summary 的 `eligibility_blocked[]`；`--eligibility-gate warn` 写卡但标 warning；`--eligibility-gate off` 不拦截；`--force-eligibility` 人工 override 并留痕 | **implemented**（WC-T1-INTEGRATION） |
| **B** | 新建 Multi-Chat / 用户首条 prompt 含 ticket id | `.cursor/hooks/capture_session_context.py` → `main()`（`beforeSubmitPrompt` hook） | 在 `infer_ticket_id` 成功后调用 `check_ticket_eligibility(...)` | **软警告（默认）** 或 env 硬闸 | **planned** |
| **C** | Orchestrator 刷新 dispatch plan 前 | `04_Workflows/dispatch_executor.py` → `build_dispatch_plan()` | 对 plan 条目附加 eligibility annotate | annotate + 降级 | **planned** |

**原则**

- **FRAME 仍权威**：Eligibility 只读 `*_state.md`；不覆盖 AllowedPaths / Dependencies 解析。
- **与 dispatch_executor 分桶对齐**：reason 语义见 §4；plan bucket 与 eligibility 冲突时，以 **更保守**（ineligible）为准。
- **默认 non-blocking**：首接入口 B 建议软警告；入口 A/C 由 Orchestrator 显式跑脚本，适合硬拒绝。
- **override 留痕**：任何 `--force` / env 绕过须写入 `dispatch_cards_run.latest.json` 或 Progress 末尾，不 silent skip gate。

### 8.2 入口 A — `generate_cards` 接入（Implementer 卡）· **implemented**

Repo Orchestrator → Implementer handoff 脚本链：

```text
scripts/run_dispatch_cards.py
  → _dispatch_cards.generate_cards(...)
      → check_ticket_eligibility (gate != off)
      → build_card_input → render_card_markdown → write *.cursor.md
```

**CLI（已实现）**：

```bash
python scripts/run_dispatch_executor.py --pretty
python scripts/run_dispatch_cards.py --role implementer --limit 5 --eligibility-gate block --pretty
python scripts/run_dispatch_cards.py --ticket TEST-BLK --force-eligibility --dry-run --pretty
```

| Flag | 行为 |
|------|------|
| `--eligibility-gate off` | 不调用 gate；与集成前一致 |
| `--eligibility-gate warn` | ineligible 仍写卡；summary + card Provenance 含 `eligibility_warning` |
| `--eligibility-gate block`（默认） | ineligible 跳过写卡；`eligibility_blocked[]` |
| `--force-eligibility` | block 模式下仍写卡；summary `eligibility_override: true` |

**summary JSON 字段**：`eligibility_gate`、`eligibility_blocked[]`、可选 `eligibility_override` / `eligibility_overridden_tickets[]`。

### 8.3 伪代码：入口 B — session hook（planned · 第二阶段）

```python
# .cursor/hooks/capture_session_context.py — after infer_ticket_id()

from pathlib import Path
import sys
_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "04_Workflows"))
from ticket_eligibility import check_ticket_eligibility

if ticket_id:
    role = infer_role_from_prompt(prompt)  # 新 helper；无则 None
    elig = check_ticket_eligibility(ticket_id, _REPO, context={"requested_role": role})
    context["eligibility"] = {
        "eligible": elig.get("eligible"),
        "reasons": elig.get("reasons"),
    }
    if elig.get("eligible") == "ineligible":
        print(f"[eligibility] ineligible: {elig.get('reasons')}", file=sys.stderr)
        if os.environ.get("GOV_TICKET_ELIGIBILITY_GATE") == "1":
            print(json.dumps({
                "continue": False,
                "user_message": f"Ticket {ticket_id} ineligible: {elig.get('reasons')}",
            }))
            return 0
```

Hook 改动触 `.cursor/hooks/*` 与 fail-open 契约，建议 **晚于入口 A** 单独子票或 env 门控试点。

### 8.4 验收口径（Integration DoD 摘要）

| AC | 条件 |
|----|------|
| AC-1 | `run_dispatch_cards.py --eligibility-gate block` 对 fixture 中 blocked / dependency 票不写卡，summary 含 `eligibility_blocked` |
| AC-2 | eligible 票行为与 WC-T1 未接前一致（card 内容不变） |
| AC-3 | `--force-eligibility` 或 summary 中 `override: true` 可审计 |
| AC-4 | 单元测试：`tests/test_dispatch_cards.py` 增 eligibility gate cases（mock 或 fixture ticket） |
| AC-5 | 文档：`docs/control_plane_dispatch_executor.md` § Dispatch Cards 增「Eligibility gate」交叉引用本档 §8 |

### 8.5 与后续 WC-T 票关系

| 票 | 关系 |
|----|------|
| **WC-T1**（本档） | 工具层 Done；§8 入口 A implemented |
| **WC-T1-INTEGRATION** | 入口 A Done（gate flags + tests）；入口 B/C deferred |
| WC-T2 comms | ineligible 时可选用 `message_generator` 发 Orchestrator 通知（非本票范围） |
| WC-T3+ order intake | 订单模型与 eligibility context 扩展（`wave`/`phase`/`notes`） |
