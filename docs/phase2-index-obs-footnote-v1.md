# Phase 2 Index Observability Footnote — v1

> **Ticket**: `P2-INDEX-OBS-FOOTNOTE-v1`  
> **Date**: 2026-07-15 · Wave B 可並行薄票  
> **Role**: GAP-OBS-INDEX **敘事／腳註**對齊（≠ 真接线实现）  
> **Contract SSOT**: `docs/phase2-knowledge-indexing-contract-v1.md` §6.4  
> **Gap SSOT**: `docs/phase2-index-contract-gap-audit-v1.md` → **GAP-OBS-INDEX**

---

## §0 non_claims（必讀）

| 禁止宣稱 | 說明 |
|----------|------|
| 本腳註 **≠** ingest job 已攜帶 `run_id` 並寫入 `agent_runs` | contract §6.4 仍標「未來／本層不實現」 |
| Wave B `index_cases`／`kb_index_status` **≠** 全庫 index 排程 SSOT | 僅 eval／pilot 側車就緒度 |
| 本票 **≠** P2 closure／Dashboard Phase% 上調 | `apply_phase_pct=false`；僅 proposed Δ |
| 本票 **≠** 改寫 `WORKFLOW_INDEX.md` 全文 | 對齊 P1-GOV **R4** INDEX 敘事 **explicit defer** |
| 本票 **≠** 改 `core/data_pipeline.py`／他人 core | BlockedPaths |

---

## §1 目的

關閉 gap-audit **GAP-OBS-INDEX** 的**文檔可導航**缺口：

1. 明示 contract §6.4「Future ingest observability」期望：未來 ingest job 應攜帶 `run_id` → 關聯 `agent_runs.id`
2. 與 `docs/observability.md` Wave B `index_cases` **分欄**，避免誤讀為全庫排程已觀測
3. 指向後續真接线票（須另授權）；本票只交付腳註 + 薄測

---

## §2 命名空間對照

| 命名空間 | 含義 | 本票狀態 |
|----------|------|----------|
| contract §6.4 Future ingest observability | ingest `run_id`↔`agent_runs` | **腳註已對齊** · 真接线 **deferred** |
| Wave B `index_cases`／`kb_index_status` | eval／pilot 側車（`docs/observability.md` §9） | **保留既有語義** · ≠ 全庫 SSOT |
| index job hook skeleton | `docs/phase2-index-job-hook-v1.md` §7 | 可提示未來應帶 `run_id` · **仍不寫** `agent_runs` |
| WORKFLOW_INDEX 敘事 | P1-GOV R4 | **explicit defer** 輕修 · 本票不碰 INDEX |

```text
[ingest job · future]
      │  run_id
      ▼
 agent_runs.id     ←── contract §6.4（本票僅腳註）
      │
      ✕ 本票不接线

[Wave B eval sidecar]
      │
      ▼
 index_cases[] / kb_index_status   ←── observability §9（≠ 上列 SSOT）
```

---

## §3 交叉引用（維護清單）

| 檔 | 應出現 |
|----|--------|
| 本檔 | `GAP-OBS-INDEX` · `run_id` · `agent_runs` · `index_cases` |
| `docs/phase2-index-contract-gap-audit-v1.md` | GAP-OBS-INDEX 列指向本檔 |
| `docs/phase2-knowledge-indexing-contract-v1.md` §6.4 | 指向本腳註 |
| `docs/observability.md` | 腳註：`index_cases` ≠ §6.4 全庫 ingest obs |
| `docs/phase2-index-job-hook-v1.md` §7 | 指向本腳註 |

---

## §4 驗收命令

```powershell
python -m unittest tests.test_phase2_index_obs_footnote_v1 tests.test_phase2_knowledge_indexing_contract_v1 -v
# 預期：OK

# 交叉引用抽查（本機可用 rg）
# rg "phase2-index-obs-footnote-v1|GAP-OBS-INDEX" docs/phase2-index-contract-gap-audit-v1.md docs/phase2-knowledge-indexing-contract-v1.md docs/observability.md docs/phase2-index-job-hook-v1.md
```

---

## §5 Phase% proposal（未套用）

| Field | Value |
|-------|-------|
| phase_targets | P2 |
| baseline_pct | 66 |
| proposed_delta_pct | +1 ～ +2 |
| evidence_gate | 本腳註 + 薄測綠 + contract 測仍綠 |
| apply_phase_pct | **false** |

上調僅能由後續 **W-PROG** 票執行。

---

## §6 後續（非本票）

| 項 | 歸屬 |
|----|------|
| `run_id`↔`agent_runs` 真接线 | 另開 obs／ingest 實作票 + 授權 |
| WORKFLOW_INDEX R4 輕修 | 尚書省明示後另開 INDEX doc 票 |
| sandbox index write／RAG E2E | `P2-HOOK-LOCAL-SANDBOX-EXECUTE-v1`／`P2-RAG-E2E-MVP-v1` |

---

*PHASE2-INDEX-OBS-FOOTNOTE-v1 · P2-INDEX-OBS-FOOTNOTE-v1 · 2026-07-15*
