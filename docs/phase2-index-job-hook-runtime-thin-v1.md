# Phase 2 Index Job Hook — Thin Runtime v1（FP-G2-T6）

> **版本**：v1.0（Full-Phase G2 · FP-G2-T6）  
> **日期**：2026-07-13  
> **上游**：FP-G2-T1 skeleton · `docs/phase2-index-job-hook-v1.md`  
> **性質**：在 T1 dry-run skeleton 上加 **本地 fixture thin runtime** · ≠ 生產 ingest · ≠ cron 部署

---

## §0 non_claims

| 禁止宣稱 | 說明 |
|----------|------|
| thin runtime **≠** 生產 index job | 無 cron／無 core ingest 寫入 |
| fixture digest **≠** 已索引 | 僅本地哈希預覽 |
| 本票 **≠** T5 corpus 擴檔 · ≠ GraphRAG | 見 NonScope |
| 本票 **≠** P2 closure | 僅 +1～+2 提案級增量 |

---

## §1 Goal

1. CLI：`scripts/run_index_job_hook_runtime_thin_v1.py`（預設 dry-run）  
2. 讀本地 fixture（`tests/fixtures/index_job_hook_thin_v1/`）  
3. 回傳穩定 dict：`ok`／`planned_jobs`／`fixture_digest`／`writes_index=false`  
4. 裸 `--execute` 仍 blocked（ok=false · `execute_blocked`）
5. `--execute --sandbox`：僅寫 allowlist 本地 stub（`artifacts/p2_sandbox_index/` 或 fixture `_sandbox_out/`）· `writes_production_index=false` · ≠ Qdrant／PG／`03_RAG_Database`／core ingest

---

## §2 與 T1 關係

```text
T1 skeleton ──plan_only jobs──► overlay metadata
T6 thin     ──fixture plan.json──► planned_jobs + fixture_digest
                ├── dry-run：writes_index=false
                ├── --execute：execute_blocked
                └── --execute --sandbox：local stub under allowlist only
```

---

## §3 CLI

```text
python scripts/run_index_job_hook_runtime_thin_v1.py --dry-run --format json
python scripts/run_index_job_hook_runtime_thin_v1.py --execute --sandbox --format json
python -m unittest tests.test_index_job_hook_runtime_thin_v1 -v
```

清理 sandbox 產物：刪除對應 `sandbox_run_dir` 或整個 `artifacts/p2_sandbox_index/`。

---

## §4 解阻（仍屬另票）

生產 execute／core ingest／live Qdrant 須另開票 + infra／PM 解阻（同 T1 §3）。  
本檔 sandbox 路徑 **≠** Wave B 完整 RAG-E2E／全局 index；僅供尚書省裁決可寫邊界。
