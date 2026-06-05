# Wave 8 – Skill Card Review Queue Runbook (v0.1)

> **脚本**：`04_Workflows/_wave8_skill_card_review_queue.py`  
> **性质**：目录约定 + 轻量 CLI；**不**改 Submit CLI / Skill Registry 读取逻辑  
> **前置**：`WAVE8_SKILL_CARD_DRAFT_RUNBOOK_v0.1.md`、`_wave8_generate_skill_card_draft.py`

---

## 1. 为什么分三层目录

| 目录 | 含义 | Registry / selector |
|------|------|---------------------|
| `skills/drafts/` | 机器或人工刚生成的 **待审** 草案 | **不**参与检索 |
| `skills/cards/` | 人工 **批准** 后的正式 Skill Card | 由 `load_skill_cards` 加载（仅 `review_status=approved` 等由 registry 规则过滤） |
| `skills/rejected/` | **退回/归档** 的不合格草案 | **不**参与检索 |

分离目的：

1. 避免未审草案进入 Submit 推荐或 selector。  
2. 保留晋升/驳回的 **文件级审计轨迹**（移动 + 少量审阅字段）。  
3. v0.1 无 DB/Web UI，靠目录 + 脚本即可闭环。

---

## 2. 工作流（草案 → 审阅 → 晋升/归档）

```text
run_summary (pass) ──▶ _wave8_generate_skill_card_draft.py ──▶ skills/drafts/*.json
                                                              │
                    人工 checklist 审阅 ◀─────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
     review_queue approve              review_queue reject
              │                               │
              ▼                               ▼
      skills/cards/*.json           skills/rejected/*.json
```

**禁止**：本队列自动改 registry、自动把 draft 纳入 selector、或改写 Submit CLI。

---

## 3. CLI

```bash
# 列出待审草案（仅 skills/drafts/ 下一层 *.json）
python 04_Workflows/_wave8_skill_card_review_queue.py list --pretty

# 批准：移到 skills/cards/，并写入审阅字段
python 04_Workflows/_wave8_skill_card_review_queue.py approve \
  --draft skills/drafts/draft-clean-basic-w8-job-001.json \
  --review-notes "run_summary verified against delivery manifest" \
  --pretty

# 驳回：移到 skills/rejected/
python 04_Workflows/_wave8_skill_card_review_queue.py reject \
  --draft skills/drafts/draft-clean-basic-w8-job-002.json \
  --review-notes "recommended_actions overfit single job" \
  --pretty
```

| 子命令 | 说明 |
|--------|------|
| `list` | 列出 `skills/drafts/` 下所有 `.json`；解析失败项标 `parse_ok: false` |
| `approve --draft PATH` | 校验 JSON → 更新审阅字段 → **移动**到 `skills/cards/` |
| `reject --draft PATH` | 同上 → **移动**到 `skills/rejected/` |
| `--review-notes` | 可选，写入 `review_notes` |
| `--skills-root` | 可选，覆盖 skills 树根（测试用） |
| `--pretty` | stdout JSON 缩进 |

**审阅字段（最小增量）**

- `card_meta.review_status`（若存在 `card_meta`）否则顶层 `review_status`  
- 顶层 `reviewed_at`（UTC ISO-8601）  
- 可选顶层 `review_notes`  

其余字段 **原样保留**，不做大规模重写。

**错误行为**

- 非 `.json`、文件不存在、JSON 解析失败 → stderr `[ERROR]`，exit **1**，**不**移动文件  
- 目标路径已存在同名文件 → exit **1**

---

## 4. 人工审核 checklist

在 `approve` 前逐项确认（任一项不通过应 `reject` 并写 `--review-notes`）：

| 检查项 | 要点 |
|--------|------|
| **run_summary 证据** | `evidence.sample_job_ids` / `source_snapshot` 是否对应真实成功 job；`qa_status`、`overall_ok` 是否与归档 run_summary 一致 |
| **product_sku_scope** | `scope.product_sku_scope` 是否过宽（例如单次 BASIC job 却写成 `both`） |
| **recommended_actions** | `recommended_actions.pre_processing` 是否仅为模板占位、是否过度臆测工具链 |
| **confidence_level** | 单 job 样本（`historical_success_rate: 1.0`）是否仍标 `low`；禁止未补证据就升为 `high` |
| **risk_notes** | `common_pitfalls` 是否提醒「单 job 草案」；高复杂度 job 是否有对应警示 |
| **与正式卡对齐** | 若需进入 selector，批准后是否需补 `skill_id`/`applicable_scenarios` 等扁平字段（另票整理，本脚本不强制） |

---

## 5. 与草案生成器衔接

```bash
# 1) 生成草案到 drafts/
python 04_Workflows/_wave8_generate_skill_card_draft.py \
  --run-summary path/to/run_summary.json \
  --output skills/drafts/draft-clean-basic-myjob.json \
  --pretty

# 2) 列队审阅
python 04_Workflows/_wave8_skill_card_review_queue.py list --pretty

# 3) 批准或驳回（见 §3）
```

---

## 6. 验证

```bash
python -m unittest tests.test_wave8_skill_card_review_queue -v
```

---

*v0.1 · 2026-06-05*
