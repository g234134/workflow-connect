# TICKET STATE · P2-HOOK-LOCAL-SANDBOX-EXECUTE-v1 · Sandbox execute 可寫範圍試跑

> Full-Phase G2 · P2 · **probe / trial** · 2026-07-15  
> 上游：`FP-G2-T6-index-job-hook-runtime-thin-v1` · 計畫：`plans/multi-phase-near-100-p1-p6-execution-plan.md` Wave B  
> **性質**：試跑＋邊界報告 · **≠** 完整 Wave B（RAG-E2E／全局 index）· **≠** Phase% 上調

---

## FRAME

- Goal: 釐清 `--execute` blocked 設計意圖；在 allowlist 內完成一次 sandbox execute 試跑；產出可寫範圍建議供尚書省裁決是否開 Wave B。
- Scope:
  - MUST：試跑 `scripts/run_index_job_hook_runtime_thin_v1.py --execute --sandbox`
  - MUST：最小增量支援 `--sandbox`＋allowlist 寫入
  - MUST：本票 state＋Progress 末尾一行
- NonScope:
  - 不開完整 RAG-E2E MVP · 不寫 live Qdrant／生產 DB／`03_RAG_Database`
  - 不上調 P2 Phase% · 不改 core／暗部／Dashboard 數字格
- AllowedPaths:
  - `scripts/run_index_job_hook_runtime_thin_v1.py`
  - `tests/test_index_job_hook_runtime_thin_v1.py`
  - `docs/phase2-index-job-hook-runtime-thin-v1.md`
  - `artifacts/p2_sandbox_index/**`（試跑產物 · 可刪）
  - `04_Workflows/tickets/P2-HOOK-LOCAL-SANDBOX-EXECUTE-v1_state.md`
  - Progress **末尾 append only**
- BlockedPaths:
  - `core/**` · 暗部 · `.env` · venv · `runtime/checkpoints/**` · live Qdrant／生產 DB · Dashboard %
- AcceptanceCriteria:
  - AC-1：裸 `--execute` → `ok=false` · `mode=execute_blocked`
  - AC-2：`--execute --sandbox` → `ok=true` · `writes_production_index=false` · 寫入僅 allowlist
  - AC-3：unittest PASS（含 sandbox／reject）
  - AC-4：結構化邊界報告交付尚書省（本輪回覆）

---

## STATE

- overall_status: trial_done_awaiting_wave_b_decision
- current_owner: 尚書省（裁決 Wave B）
- next_action: 尚書省勾選可寫範圍後，決定是否正式開 `P2-HOOK-LOCAL-SANDBOX-EXECUTE-v1` 驗收／再串 `P2-RAG-E2E-MVP-v1`
- last_updated: 2026-07-15 · probe agent
- status_by_role:
  - orchestrator: n/a（本輪 probe）
  - implementer: trial_done（最小 `--sandbox`）
  - reviewer: pending（若開正式 Wave B）
  - scribe: pending
- ac_status:
  - AC-1: pass
  - AC-2: pass
  - AC-3: pass
  - AC-4: pass（見 B_REPORT／回覆）

---

## B_REPORT

### 為何 `--execute` 曾 blocked（設計意圖）

| 層 | 行為 | 意圖 |
|----|------|------|
| FP-G2-T1 | `--execute` → `execute_blocked` | skeleton · 無 core ingest 配線 |
| FP-G2-T6 | 同上 | thin runtime 僅 fixture dry-run；禁生產寫入 |
| 本試跑後 | 裸 `--execute` 仍 blocked | 須顯式 `--sandbox` 才寫 allowlist |

### 試跑命令與結果

```text
python -m unittest tests.test_index_job_hook_runtime_thin_v1 -v
# → Ran 8 tests OK

python scripts/run_index_job_hook_runtime_thin_v1.py --execute --format json
# → ok=false · mode=execute_blocked

python scripts/run_index_job_hook_runtime_thin_v1.py --execute --sandbox --format json
# → ok=true · mode=sandbox_execute · writes_production_index=false
# → written_paths under artifacts/p2_sandbox_index/<run_id>/
```

### 結構化結果（dict 語意摘要）

| 鍵 | 值 |
|----|-----|
| `ok` | `true`（sandbox）；裸 execute=`false` |
| `mode` | `sandbox_execute` / `execute_blocked` |
| `written_paths` | `artifacts/p2_sandbox_index/20260715T001539Z/*.chunk.json` + `sandbox_index_manifest.json` + `latest.json` |
| `sandbox_collection` | `sandbox_local_stub`（**非** live Qdrant collection） |
| `reversible` | `true` · cleanup：刪 `artifacts/p2_sandbox_index/<run_id>` 或整樹 |
| `risk.*` | live Qdrant／prod DB／`03_RAG_Database`／core ingest = **false** |

### 建議可寫範圍（供尚書省勾選）

| 項 | 建議 | 勾選 |
|----|------|------|
| `artifacts/p2_sandbox_index/**` | **允許**（預設 sandbox out） | ☐ |
| `tests/fixtures/index_job_hook_thin_v1/_sandbox_out/**` | **允許**（測試／隔離） | ☐ |
| `tests/fixtures/index_job_hook_thin_v1/{plan,sample}*` 讀取 | **允許**（唯讀 fixture） | ☐ |
| live Qdrant／生產 collection | **禁止** | ☐ |
| 生產 PG／暗部 DB | **禁止** | ☐ |
| `03_RAG_Database/**` 寫入 | **禁止**（本輪未碰） | ☐ |
| `core/**` ingest 配線 | **禁止**（另票） | ☐ |
| 全局／全庫 re-index | **禁止**（≠ 本試跑） | ☐ |

### Wave B 建議

| 票 | 建議 | 條件 |
|----|------|------|
| **P2-HOOK-LOCAL-SANDBOX-EXECUTE-v1** | **建議正式開**（本試跑已證明路徑可行） | 尚書省勾選上表 allow／deny；驗收沿用本 CLI＋unittest |
| **P2-RAG-E2E-MVP-v1** | **暫緩** · 串行於上票正式 accepted 後 | 仍限 fixture corpus；禁 live Qdrant 除非另授權 |
| **P2-INDEX-OBS-FOOTNOTE-v1** | **可並行薄票** | 不依賴 write；低風險 |

### Phase 影響

- **不上調** P2 %（`apply_phase_pct=false`）
- non_claims：≠ Wave B 完整交付 · ≠ RAG-E2E · ≠ P2 closure · ≠ production ingest

---

## C_REPORT

- conclusion: trial_accepted_for_boundary_decision
- blocking_issues: 無（待尚書省裁決是否開正式 Wave B）
- risk_level: low（JSON stub · allowlist · reversible）
- suggestions: 正式 Wave B 可把本試跑增量視為實作底稿；Reviewer 複驗 AC 即可

---

## D_REPORT

- docs_updates: `docs/phase2-index-job-hook-runtime-thin-v1.md`（補 `--sandbox`）
- progress_entry: 見 Progress 2026-07-15 本條
- followup: 尚書省裁決 → 正式 Wave B 或僅凍結試跑產物
