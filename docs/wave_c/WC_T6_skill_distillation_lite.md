# WC-T6 · Skill Distillation / Learning Lite

> **Ticket**: WC-T6 · Control Plane skill distillation (v0.1 skeleton)  
> **Status**: In Progress — local heuristics only, no LLM / network  
> **SSOT**: `04_Workflows/tickets/WC-T6_state.md` · CLI `scripts/distill_control_plane_skills_lite.py`

---

## 1. Background

Wave C M2 已跑通 **eligibility → dispatch cards → STATE comms → order intake** 链。Multi-Chat handoff 会在三类产物里留下可复用的操作经验：

| 输入源 | 典型路径 | 可提炼内容 |
|--------|----------|------------|
| **cards** | `artifacts/**/cards/*.cursor.md` | 角色指令、AllowedPaths、VerificationCommands、eligibility gate 用法 |
| **comms** | `artifacts/**/comms/ticket_comms.jsonl` | STATE 变更摘要、owner 交棒、review 关口信号 |
| **reports** | `04_Workflows/tickets/*_state.md` 的 B_REPORT / C_REPORT | 实际变更文件、验证命令、Reviewer 结论与 gap |

WC-T6 v0.1 **不**调用 LLM 或外部服务，仅用本地启发式扫描上述输入，输出 `patterns`（建议复用）与 `anti_patterns`（应避免），供 Orchestrator / Scribe 人工审阅后写入 skills 或 runbook。

每条 pattern / anti-pattern 含 **`path_id`**（T6 源命名 `cp.*`，便于回溯）与 **`canonical_path_id`**（对齐 WC-T5 契约 `wc.m2.*` 矩阵；见文末映射表）。

---

## 2. Output contract (v0.1)

```json
{
  "ok": true,
  "patterns": [
    {
      "id": "pat-eligibility-gate-block",
      "title": "Dispatch with eligibility gate block",
      "description": "...",
      "source_type": "card",
      "path_id": "cp.dispatch_cards.eligibility_gate",
      "canonical_path_id": "wc.m2.dispatch.eligibility_gate_warn",
      "recommendation": "...",
      "source_refs": [
        {"ticket_id": "DEMO-ELIG", "path": "tests/fixtures/skill_distillation/cards/one_card.cursor.md"}
      ]
    }
  ],
  "anti_patterns": [
    {
      "id": "anti-skip-verification",
      "title": "Card without VerificationCommands",
      "description": "...",
      "source_type": "card",
      "path_id": "cp.dispatch_cards.generate",
      "recommendation": "...",
      "source_refs": [...]
    }
  ],
  "source_refs": [...]
}
```

| 字段 | 说明 |
|------|------|
| `source_type` | `card` \| `comms` \| `report` |
| `path_id` | T6 源路径 ID（`cp.*`；见 §5） |
| `canonical_path_id` | WC-T5 契约路径 ID（`wc.m2.*`；见 Path id mapping） |
| `source_refs` | 每条 pattern/anti-pattern 必须含至少一条；指向 fixture 相对路径或 `ticket_id` |

---

## 3. Example pattern (fixture scenario)

**场景（伪造）**：demo 票 `DEMO-ELIG` 在生成 Implementer 指令卡时启用 `--eligibility-gate block`，卡内写明 VerificationCommands 与 AllowedPaths。

| 项 | 值 |
|----|-----|
| **描述** | 开 chat 前先跑 eligibility gate，卡内附带可重跑验证命令，减少 implementer 越界改档。 |
| **source_type** | `card` |
| **path_id** | `cp.dispatch_cards.eligibility_gate` |
| **建议做法** | `run_dispatch_cards.py --eligibility-gate block`；FRAME 写清 AllowedPaths；VerificationCommands 指向本票 unittest。 |

---

## 4. Example anti-pattern (fixture scenario)

**场景（伪造）**：某 comms 记录显示票从 `in_progress` 直接跳到 `done`，跳过 `review` 与 `status_by_role.reviewer`。

| 项 | 值 |
|----|-----|
| **描述** | 跳过 reviewer 关口即标 done，导致 dispatch / order intake 链无法对齐 WC-T2/T4 契约。 |
| **source_type** | `comms` |
| **path_id** | `cp.ticket_comms.state_transition` |
| **建议做法** | STATE 变更须经 `in_progress → review → done`（或显式 `ready_for_order`）；comms diff 应含 `current_owner` 与 `status_by_role` 变化。 |

---

## 5. WC-T5 path_id namespace (draft cross-ref)

| path_id | 含义（T5 草案） | T6 v0.1 检测信号 |
|---------|----------------|------------------|
| `cp.dispatch_cards.generate` | 生成 `*.cursor.md` | 卡文件存在；含 Role / Ticket / VerificationCommands |
| `cp.dispatch_cards.eligibility_gate` | eligibility gate 拦截或 warn | 卡内 `eligibility_warning` 或 CLI 使用 gate |
| `cp.ticket_comms.emit` | STATE 变更发 comms | JSONL 行 `schema_version=ticket_comms_v0.1` |
| `cp.ticket_comms.state_transition` | 合法 STATE 交棒 | diff 含 `overall_status` / `current_owner` |
| `cp.ticket_state.b_report` | Implementer 战报 | B_REPORT 含 `verification` 与 `changed_files` |

正式 auto / HITL / forbidden 矩阵以 WC-T5 定稿为准；T6 仅引用 ID，不定义 gate 语义。

---

## 6. CLI usage

```bash
python scripts/distill_control_plane_skills_lite.py \
  --cards-dir tests/fixtures/skill_distillation/cards \
  --comms-jsonl tests/fixtures/skill_distillation/comms/one_comms.jsonl \
  --pretty

# 可选 reports（`*_state.md` 或含 B_REPORT 的 markdown）
python scripts/distill_control_plane_skills_lite.py \
  --cards-dir tests/fixtures/skill_distillation/cards \
  --comms-jsonl tests/fixtures/skill_distillation/comms/one_comms.jsonl \
  --reports-dir tests/fixtures/skill_distillation/reports \
  --json-out artifacts/control_plane/skill_distillation.latest.json
```

---

## 7. Deferred (post-v0.1)

- LLM 摘要与聚类；与 `.cursor/skills` 自动 PR
- 与 WC-T5 矩阵联动：forbidden 路径命中时提升 anti_pattern severity
- 生产 artifacts 目录增量扫描与 dedup

---

## Path id mapping to WC-T5

下表描述 WC-T6 distillation 使用的 `cp.*` path_id 与 WC-T5 契约中 `wc.m2.*` path_id 的对应关系。未列出的 `path_id` 其 `canonical_path_id` fallback 为原值。

| T6 path_id (`cp.*`) | T5 path_id (`wc.m2.*`) | 備註 |
|-----------------------------------|----------------------------------------|------|
| `cp.dispatch_cards.eligibility_gate` | `wc.m2.dispatch.eligibility_gate_warn` | — |
| `cp.dispatch_cards.generate` | `wc.m2.dispatch.cards_generate` | — |
| `cp.ticket_comms.state_transition` | `wc.m2.comms.state_transition` | — |
| `cp.ticket_comms.emit` | `wc.m2.comms.state_transition` | — |
| `cp.ticket_state.b_report` | —（無 T5 等價） | 「無 T5 等價 · forbidden/HITL 語境（非 auto 路徑）」· `canonical_path_id` fallback 為 source `path_id` |

---

*WC-T6 design · v0.2 · 2026-06-14 · WC-T6-v2 gap closure*
