# Wave 8 – Skill Card Draft Generator Runbook (v0.1)

> **脚本**：`04_Workflows/_wave8_generate_skill_card_draft.py`  
> **性质**：规则化草案生成（无 LLM）；**不**写入 `skills/cards/` 正式目录  
> **前置**：`WAVE8_CLEAN_RUN_SUMMARY_SCHEMA_v0.1.md`、`skill_card_v0.1` 草案字段约定

---

## 1. 用途

从单次 **成功** CLEAN job 的 `run_summary.json` 生成 `skill_card_v0.1` 风格 JSON 草案，供人工审核后另票纳入 Skill Card 库。

---

## 2. 准入条件

| 条件 | 要求 |
|------|------|
| `outcome.qa_status` | 必须为 `pass`（`pass_with_warnings` / `fail` 均拒绝） |
| `outcome.overall_ok` | `true` |
| `outcome.job_status` | `done` |
| `identity.job_id` / `product_sku` | 非空 |

不符合时 stderr 输出 `not eligible for draft generation`，exit **1**。

---

## 3. CLI

```bash
python 04_Workflows/_wave8_generate_skill_card_draft.py \
  --run-summary path/to/run_summary.json \
  --pretty

python 04_Workflows/_wave8_generate_skill_card_draft.py \
  --run-summary path/to/run_summary.json \
  --output path/to/draft.json \
  --pretty
```

| 参数 | 说明 |
|------|------|
| `--run-summary` | 必填，输入 `run_summary.json` |
| `--output` | 可选，同时写入文件（仍打印 stdout） |
| `--pretty` | 可选，缩进 JSON |

---

## 4. 草案字段（摘要）

- `schema_version`: `skill_card_v0.1`
- `card_meta.skill_id`: `draft-{product_sku-lower}-{job_id}`
- `card_meta.confidence_level`: `low`
- `input_profile.complexity_indicators`: 行数 ≥100000 或文件数 ≥10 → `is_high_volume`
- `evidence.historical_success_rate`: `1.0`（单 job 样本）
- 可选 `source_snapshot.runtime_stats`：保留原 run 统计供审阅

---

## 5. 人工后续步骤

1. 审阅 `recommended_actions` / `risk_notes` 占位文案  
2. 补全 `applicable_scenarios`、工具链等（若需要与 registry 卡对齐）  
3. 将草案写入 `skills/drafts/`，用审阅队列晋升或驳回：  
   `04_Workflows/_wave8_skill_card_review_queue.py`（见 `WAVE8_SKILL_CARD_REVIEW_QUEUE_RUNBOOK_v0.1.md`）

**禁止**：本脚本直接写入正式 cards 目录或修改 Skill Registry。

---

## 6. 验证

```bash
python -m unittest tests.test_wave8_generate_skill_card_draft -v
```

---

*v0.1 · 2026-06-05*
