# dispatch_executor live scan — 红测登记（2026-06-14）

> **范围**：`tests.test_dispatch_executor.TestDispatchLiveScan.test_build_plan_classifies_w1_tickets`  
> **关联实现**：`04_Workflows/dispatch_executor.py` · `tests/test_dispatch_executor.py`  
> **绑定票号（建议）**：`W-next-DISPATCH-CARDS-MVP`（Control Plane dispatch_executor MVP 栈）· Wave 1 票 `W1-T1` / `W1-T3` 为 live scan 数据源

---

## 现象

```
python -m unittest tests.test_dispatch_executor.TestDispatchLiveScan.test_build_plan_classifies_w1_tickets -v
```

- **期望**：`build_dispatch_plan(..., ticket_filter="W1-T")` 的 `in_review_ids` 含 `W1-T1`；`done_ids` 含 `W1-T2`；`suggested_next["W1-T1"].recommended_role == "reviewer"`。
- **实际**：`in_review_ids == {'W1-T3'}`；`W1-T1` 不在 `in_review` 桶。

---

## 根因分析（只读 · 未改代码）

| 票号 | `04_Workflows/tickets/*_state.md` 当前 STATE | `classify_ticket` 结果 | 与测试期望 |
|------|-----------------------------------------------|------------------------|------------|
| **W1-T1** | `overall_status: done` · `implementation_status: done` · `current_owner: scribe` · `last_updated: 2026-06-07` | **`done`**（`DONE_STATUSES` 命中） | 测试仍假定 **`in_review`** — **不一致** |
| **W1-T2** | `overall_status: done` · `current_owner: scribe` | **`done`** | 与测试一致 |
| **W1-T3** | `overall_status: in_review` · `current_owner: reviewer` · `implementation_status: in_review` | **`in_review`**（`_is_waiting_reviewer`） | 测试未断言；executor **行为符合票面** |

**可疑来源**：

1. **Phase 1 既有 ticket state 已前进**：`W1-T1` 于 2026-06-07 收口为 `done`，live scan 读 repo 真值，不再处于 `in_review`。
2. **测试快照陈旧**：`test_build_plan_classifies_w1_tickets` 绑定 live repo 扫描，但未随 Wave 1 票状态更新期望（仍写死 W1-T1=reviewer / in_review）。
3. **分类规则本身**：`classify_ticket` 对 `overall_status in DONE_STATUSES` 优先归 `done`；对 `current_owner == reviewer` 或 `implementation_status == in_review` 归 `in_review` — 与当前 W1-T* 票面 **语义一致**，未见需在本轮修正的业务逻辑证据。

---

## 待定项（TBD）

| 项 | 结论 |
|----|------|
| **修测 vs 修逻辑** | **TBD** — 倾向 **「测试期望需要更新」**（刷新 W1-T* 断言或改用工单 fixture 隔离 live scan）；**「业务逻辑需要修正」** 暂无票面/AC 支撑，保留待定。 |
| **绑定票** | **W-next dispatch executor MVP**（`W-next-DISPATCH-CARDS-MVP_state.md` · M2 栈）；Wave 1 数据源票 **W1-T1** / **W1-T3**。`WC-T1-INTEGRATION` 明确 **不改** `dispatch_executor.build_dispatch_plan` 分桶（入口 C · 后续票）。 |
| **优先级** | **低于** 组 1（W4-MEM-01）/ 组 5a（WC-T1）Reviewer 收口；**不 block** 上述两 commit。 |

---

## 本轮声明

- **本轮未对 `dispatch_executor` 代码做任何修改。**
- **本轮仅将该问题登记为「待修测 or 待调整期望」，由后续 ticket 专门处理。**

---

## 追加登记（2026-06-14 · 组 5b-2 · 无 commit）

| 项 | 内容 |
|----|------|
| **关联票号** | `W-next-DISPATCH-CARDS-MVP`（M2 dispatch 栈）· Wave 1 数据源 `W1-T1` / `W1-T3` |
| **状态** | **测试期望待更新 or fixture 待调整** — `test_build_plan_classifies_w1_tickets` 仍红（`W1-T1` 票面已 `done`，live scan 归 `done` 桶，测试仍断言 `in_review`） |
| **复验** | `python -m unittest tests.test_dispatch_executor.TestDispatchLiveScan.test_build_plan_classifies_w1_tickets -v` → **FAIL**（2026-06-14） |
| **本轮声明** | **仍不修改** `dispatch_executor` 代码，**也不修改** 对应 unittest；待后续票单（建议绑定 `W-next-DISPATCH-CARDS-MVP` 或 Wave1-T 刷新子票）专门处理 |
