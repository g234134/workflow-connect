# TICKET STATE · W-MVP-W3-E2E-VALIDATION · 单案 E2E 验收路径 + DoD

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 3 · E2E Validation — 串联 P1–P4，不改业务逻辑。

---

## FRAME

- Goal: 对单一 case 实现「intake → gate → clean → bundle」端到端可重复验证，并落盘 DoD 文档。
- Scope:
  - `scripts/run_case_e2e_validation.py`（E2E 驱动脚本）
  - `docs/MVP_CASE_E2E_DoD_v0.1.md`（验收条件）
  - 本 ticket state 档 B_REPORT
- NonScope:
  - 清洗算法、gate 规则、bundle 结构变更
  - 新功能开发、CI 集成、多 case 批量
- AllowedPaths:
  - `scripts/run_case_e2e_validation.py`
  - `docs/MVP_CASE_E2E_DoD_v0.1.md`
  - `04_Workflows/tickets/W-MVP-W3-E2E-VALIDATION_state.md`
- BlockedPaths:
  - `notebooks/csv_cleaning/case_eligibility.py`（gate 逻辑）
  - `notebooks/csv_cleaning/clean_phase_demo.py`（清洗逻辑）
  - `notebooks/csv_cleaning/case_delivery_bundle.py`（bundle 逻辑）
  - `core/*`、`AGENTS.md`、`.cursor/rules/*`
- Dependencies:
  - W-MVP-W2-P1（case 目录结构）
  - W-MVP-W2-P2（eligibility gate）
  - W-MVP-W2-P3（cleaning runner）
  - W-MVP-W2-P4（delivery bundle）
- AcceptanceCriteria:
  - `cases/demo_phase` 成功执行一轮 e2e，有结构化输出
  - e2e 命令序列可复制执行
  - DoD 文档存在且可引用

---

## STATE

- overall_status: in_progress
- current_owner: implementer
- next_action: Reviewer 对照 AC 与 DoD 验收 demo_phase e2e 输出
- last_updated: 2026-06-08 · implementer
- status_by_role:
  - orchestrator: pending
  - implementer: done
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

### 理想 E2E 链路（Step 0）

针对单一 `case_dir`（默认 `cases/demo_phase`）：

1. **准备 case**：确保 `intake.json`、`raw/`、`cleaned/`、`reports/`、`delivery_signoff.md` 结构存在。
2. **运行 gate（P2）**：
   ```bash
   python scripts/check_case_eligibility.py --case-dir cases/demo_phase --json
   ```
3. **运行 cleaning（P3）**：
   ```bash
   python notebooks/csv_cleaning/clean_phase_demo.py \
     --case-dir cases/demo_phase --skip-eligibility --force
   ```
   > gate 已在步骤 2 单独执行，cleaning 用 `--skip-eligibility` 避免重复 gate；`demo_phase` 为 `review_needed`，需 `--force`。
4. **运行 bundle（P4）**：
   ```bash
   python scripts/build_case_delivery_bundle.py --case-dir cases/demo_phase --json
   ```

### changed_files

- `scripts/run_case_e2e_validation.py`（新建 · E2E 驱动）
- `docs/MVP_CASE_E2E_DoD_v0.1.md`（新建 · DoD v0.1）
- `04_Workflows/tickets/W-MVP-W3-E2E-VALIDATION_state.md`（本档）

### artifacts

- DoD：`docs/MVP_CASE_E2E_DoD_v0.1.md`

### e2e_command_sequence（最终版）

**一键（推荐）**：

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
```

**手动逐步**：见 DoD §3.2 或上方「理想 E2E 链路」。

### verification

```bash
python scripts/run_case_e2e_validation.py --case-dir cases/demo_phase --json
# exit 0 · overall_ok: True
# gate: review_needed (exit 2, reason=rows<100)
# cleaning: ok [forced]
# bundle: ok · eligibility_status=review_needed
# artifacts: cleaned/Phase_cleaned.csv, reports/report.json, reports/eligibility_result.json, delivery_signoff.md
```

### behavior_notes

- E2E 驱动默认 `--force-review`（=`--force-review` / 无 `--no-force-review`）：当 gate 返回 `review_needed` 时，cleaning 自动加 `--force`。
- Gate 步骤始终先跑；cleaning 一律 `--skip-eligibility`（gate 结果已在步骤 1 记录）。
- Gate `rejected` 时跳过 cleaning/bundle，exit 1。
- `demo_phase` 特判：`rows<100` + `size<1024` → `review_needed`，E2E 允许 forced 继续（**仅内部测试**；生产须人工 review）。

### known_issues

- `demo_phase` 行数过小，gate 永远 `review_needed`；非 bug，见 DoD §5。
- 无 CI workflow 集成；后续票可接 `.github/workflows/`。
- 仅覆盖 Phase 表结构 runner；其他 SKU/runner 需另开 E2E 票。

### deferred_items

- 多 case 批量 E2E（遍历 `cases/index.json`）
- CI gate 集成
- gate `rejected` 分支自动化测试 fixture

---

## C_REPORT

- **verdict**: accept_with_minor_edits
- **reviewed_at**: 2026-06-08 · reviewer
- **review_basis**: `docs/MVP_CASE_E2E_DoD_v0.1.md`、`scripts/run_case_e2e_validation.py`、B_REPORT verification；本机复跑 E2E（exit 0 · `overall_ok: true` · gate `review_needed` exit 2 · cleaning `[forced]` · bundle ok）

### strengths

- **链路短、可复制**：一键命令 + DoD §3.2 手动逐步并列，gate → clean（`--skip-eligibility`）→ bundle 顺序与脚本一致，新人可照抄验收。
- **结构化输出充分**：`--json` 返回 `steps.gate/cleaning/bundle`、`artifacts` 清单；human summary 含 `[forced]` 标记，与 B_REPORT 记录一致。
- **demo 特例有留痕**：B_REPORT `behavior_notes` / `known_issues` 与 DoD §5 对齐，说明 `rows<100` → `review_needed` 非 bug、仅内部测试可 `--force`。
- **边界清晰**：脚本不碰 gate/clean/bundle 业务逻辑；`rejected` 跳过下游、`--no-force-review` 时 cleaning 正确 skip（exit 1），行为可预期。

### gaps_or_ambiguities

1. **DoD §3.1 未点名 `--force-review`**：§5 已写默认行为，但 §3.1 一键命令块旁缺一句「默认 `--force-review`；真实 prod 见 §5」——读者可能不知 flag 存在。
2. **Gate exit code 2 易误判为失败**：DoD §4 #1 只写 `ok: true`，未说明 `review_needed` 时 gate **CLI exit=2 仍属正常**（B_REPORT 有写，DoD 未同步）。
3. **真实客户 case 期望行为略隐**：B_REPORT 已写「生产须人工 review」，但未显式对比「真实案一般 gate=`accepted` 时无需 `--force` 即应继续清洗」——建议在 DoD §5 或 B_REPORT `behavior_notes` 补一句。

### required_edits

| 位置 | 建议（一句话） |
|------|----------------|
| `docs/MVP_CASE_E2E_DoD_v0.1.md` §3.1 | 在命令块下追加：「默认 `--force-review`（`review_needed` 时 cleaning 加 `--force`）；禁用见 `--no-force-review`。」 |
| `docs/MVP_CASE_E2E_DoD_v0.1.md` §4 #1 | 补注：「`review_needed` 时 gate 进程 exit code 为 2，仍计为 gate 步骤成功（JSON `ok: true`）。」 |
| `docs/MVP_CASE_E2E_DoD_v0.1.md` §5 或 B_REPORT `behavior_notes` | 追加：「真实客户 case：gate=`accepted` 时不应依赖 `--force`；仅 demo/internal 小样本允许 forced 路径。」 |

*以上均为文档措辞，不要求改 gate/clean/bundle 逻辑或 E2E 脚本。*

### mvp_e2e_confidence

**足以作为 v1 最小验收标准**：单案、低风险 CSV、P1–P4 四步可一键复现，通过条件与 artifact 清单明确；demo_phase 特例已文档化。待 Scribe/Orchestrator 收敛 §3.1/§4/§5 三处措辞后即可对外引用 DoD v0.1。

### known_issues（记录供后续票，本票不修）

- 无 E2E 单元测试（`tests/test_case_e2e_validation.py` 未建）；可后续票补 smoke。
- E2E 结构预检仅验 `intake.json` + `raw/`，弱于 DoD §2 全结构表；P1 缺目录时可能到 clean/bundle 才失败（可接受于 MVP，后续可加强预检文档说明）。
- CI 集成、多 case 批量、gate `rejected` fixture — 已在 B_REPORT `deferred_items`，同意 defer。

### recommended_next_steps（供 Orchestrator）

- 建议 **STATE** 更新：`status_by_role.reviewer: done`；`current_owner: scribe`；`next_action: Scribe 依 required_edits 收敛 DoD / MVP v1 说明，Orchestrator 关票`。
- 若 Implementer 或 Scribe 采纳 required_edits，无需回 B；文档小改可在 Scribe 棒或 follow-up 文案票完成。
- **overall_status** 可在 Scribe 完成后由 Orchestrator 置 `done`。

**Scribe note（2026-06-08）：** 已按本 C_REPORT 的 `required_edits` 更新 `docs/MVP_CASE_E2E_DoD_v0.1.md` §3.1 / §4 措辞（`--force-review` 默认行为、gate exit=2 与 demo/internal 通过条件）；未对任何脚本逻辑做改动，等待 Orchestrator 更新 STATE。

---

## D_REPORT

<!-- Scribe 填 -->
