# P1–P6 → 接近 100% — 衝刺執行計畫（增量）

> **角色**：HQ 規劃／協調 · **日期**：2026-07-14  
> **目標**：以 Dashboard Gauge 為準，把 **P1–P6** 從現況推到 **誠實 ~95–100%**（非空口標語）  
> **Phase% SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md`（寫入僅 W-PROG + `_phase_pct_apply.py apply --authorize`）  
> **母本對照**：`multi-phase-80-percent-execution-plan.md`（P7.5／P8／P8.9 · **本檔不重複**）· `full-line-to-100-wave-plan-2026-07-13.md`（全線 Wave · **本檔收窄為 P1–P6**）

---

## 0. 與既有計畫的 delta（不要重寫）

| 既有計畫 | 覆蓋 | 本檔增量 |
|----------|------|----------|
| `multi-phase-80-percent-execution-plan.md` | P7.5／P8／P8.9 →80% | **不改**；P1–P6 不在其內 |
| `full-line-to-100-wave-plan-2026-07-13.md` | 全線 Wave 0–6；P5／P7.5／P8.9 已有 DoD | **抽取** P1–P6 缺口；補 P1／P2／P3／P4／P6 專票批；P5 對齊「stub 已落地 → soak／UI」 |
| WAVE_A（歷史） | P1 README／P2 index／P5 soak | **保留** A-P0／A-P1 思路；數字改以 **07-13 Gauge** 為準 |

**誠實邊界（計劃級 non_claims）**

- ≠ 本檔寫入即抬 Dashboard %  
- ≠ prod ingest／真 Grafana／Langfuse–PG 全對齊已完成  
- ≠ DarkOps 解禁；碰暗部 core／PG live 須另授權  
- ≠ P6 未滿 nightly 7/7 即 uplift 83→91  
- P3.5（成本治理 · 現 **55%**）**不在本衝刺主線**；僅作 P3 相鄰註記

---

## 1. 現況盤點（2026-07-14 · 證據鏈）

**來源**：`python 04_Workflows/_phase_pct_apply.py read` · `master_status.md`「2026-07-14 Phase% 敘事同步」· Dashboard「当前」列 · Progress 末尾（P6 72↔83 稽核）

| Phase | 標題 | 當前 % | 距 ~100 | 已驗收（摘要） | 主要缺口類型 |
|-------|------|--------|---------|----------------|--------------|
| **P1** | 治理層 | **90** | ~10 | 憲法／合約／boot／Multi-Chat 制度；定稿令歷史 Done | 運營閉環／接戰自檢一貫性；INDEX 殘留敘事 |
| **P2** | 知識層／Index | **66** | ~34 | WA-T1 契約 · T1/T6 thin hook（fixture dry-run）· Tabular C2-P2 **≠** 全局 | **最大缺口**：`--execute` blocked · 全局 RAG job · E2E 問答 runtime · GraphRAG 僅狀態機 doc |
| **P3** | 可觀測性／Trace | **82** | ~18 | gov-trace-v2 · observability 主幹 · Tabular run log | Langfuse↔PG 對齊 **deferred**；營運表覆蓋非全 |
| **P4** | 多智能體協作 | **77** | ~23 | phase4 契約 · Multi-Chat／W5 編排資產（07-13 +2） | **編排 ≠ prod multi-agent runtime**；dispatch／replay 硬化 |
| **P5** | Dashboard／離線健康度 | **72** | ~28 | toolchain health · `GET /metrics` · Grafana/JSON **stub**（wave013 +2） | 真 Grafana／**PG soak** 仍 placeholder；UI 消費 Wave 4 |
| **P6** | 測試／回歸 gate | **83** | ~17 | INT Tier-A · Track B nightly + Track A PR **optional** CI | nightly **2/7**（`WF-P6-INT-NIGHTLY-MONITOR`）→91；PR **mandatory**／agent-lines deferred 另表 |

**P1–P6 簡單平均**：(90+66+82+77+72+83)/6 ≈ **78.3%**  
**第一結論**：離「整體 ≈100%」差在 **P2（−34）+ P5（−28）+ P4（−23）**；P1／P3／P6 已高，以「關門＋證據」為主。

---

## 2. 每 Phase 缺口 Top（skeleton vs 已驗收）

### P1 · 90% → ~100%

| # | 缺口 | 狀態 | 建議票 |
|---|------|------|--------|
| 1 | 接戰自檢一鍵綠（`_ops_cycle.py checklist --mode full`）與 Onboarding／INDEX 無假陰性 | **部分已有** · 需收口票 | `P1-OPS-CHECKLIST-CLOSURE-v1` |
| 2 | 治理「完成」敘事：blind／Phase1 finalization 殘項清冊 | 歷史 Done · 需 **核銷清單** | `P1-GOV-RESIDUAL-CHECKOFF-v1`（doc） |
| 3 | K-2／遠端 rollout **不**納入本衝刺 100%（另軸） | deferred | 不開票 |

### P2 · 66% → ~100%（關鍵路徑）

| # | 缺口 | 狀態 | 建議票 |
|---|------|------|--------|
| 1 | index hook **本地可寫**（sandbox corpus · 非 prod Qdrant／非暗部根） | T6：`--execute`→`execute_blocked` **by design** | `P2-HOOK-LOCAL-SANDBOX-EXECUTE-v1`（須尚書省明示允許寫 fixture index） |
| 2 | 排程／job 狀態可觀測（run_id 腳註 → agent_runs） | GAP-OBS-INDEX | `P2-INDEX-OBS-FOOTNOTE-v1`（薄）∥ #1 |
| 3 | RAG E2E 問答 **runtime**（非僅 FRAME） | T3 FRAME done · runtime gap | `P2-RAG-E2E-MVP-v1`（串行 #1） |
| 4 | GraphRAG jobs 狀態機 → thin runner | T4 **doc** done · skeleton | `P2-GRAPHRAG-THIN-RUNNER-v1`（∥ 或後置；≠ primary retrieval） |
| 5 | corpus 擴面 | T5 blocked on PM | 後置 |

### P3 · 82% → ~100%

| # | 缺口 | 狀態 | 建議票 |
|---|------|------|--------|
| 1 | 本地 trace CLI／jsonl 與契約一致性 hardening | 已有 CLI · 可加嚴 | `P3-TRACE-LOCAL-HARDEN-v1` |
| 2 | Langfuse ↔ PG 對齊 | **deferred** · 常需 infra／暗部 | `P3-LANGFUSE-PG-ALIGN-FRAME-v1`（先 FRAME；實作另授權） |
| 3 | P3.5 成本覆蓋 | 55% · **本衝刺不主攻** | 另開 P3.5 票批 |

### P4 · 77% → ~100%

| # | 缺口 | 狀態 | 建議票 |
|---|------|------|--------|
| 1 | Multi-Chat／Wave Master **可重跑驗收包**（commands + skill + one ticket walkthrough） | 編排已落地 · 缺統一 runner 敘事 | `P4-MULTI-CHAT-SMOKE-PACK-v1` |
| 2 | same_chat／dispatch 最小 runtime（非 prod crew） | 契約有 · runtime 薄 | `P4-DISPATCH-REPLAY-MIN-v1` |
| 3 | prod multi-agent（crewai 等） | **禁主艙重套件** · 不納入 | 明確 non-goal |

### P5 · 72% → ~100%

| # | 缺口 | 狀態 | 建議票 |
|---|------|------|--------|
| 1 | stub → **可重複 health bundle**（health+metrics+stub 一命令） | stub accepted | `P5-HEALTH-BUNDLE-CLI-v1` |
| 2 | PG live soak／真 Grafana | **placeholder** · 常碰 infra | `P5-PG-SOAK-AUTHORIZED-v1`（須授權；可對齊 WAVE_A A-P1-1） |
| 3 | Operator UI 讀欄位 | Wave 4 · 等照片凍結 | 跟 `full-line-to-100` Wave 4 · **不**本批強開 |

### P6 · 83% → ~100%

| # | 缺口 | 狀態 | 建議票 |
|---|------|------|--------|
| 1 | nightly **7/7 綠** → 治理 uplift **83→91** | **2/7** · human-ops | 續 `WF-P6-INT-NIGHTLY-MONITOR`（**不**新開重複票） |
| 2 | PR optional → **required**（合併門檻） | deferred／批文 | `P6-INT-PR-REQUIRED-GOV-v1`（治理票 · 滿 7/7 後） |
| 3 | agent-lines nightly 等 deferred 表 | `phase6-agent-lines-nightly-deferred-index-v1` | 按索引逐項另票 · 勿 silently 宣稱 100 |

---

## 3. 優先序與依賴

```text
                    ┌─ P6 nightly 鐘（human · 並行 · 不擋編碼）
                    │
Wave A ─────────────┼─ P1 residual checkoff（doc · 並行）
（可並行）          ├─ P5 health bundle（本地 · 並行）
                    └─ P4 multi-chat smoke pack（並行）

Wave B（關鍵路徑）── P2 local sandbox execute ──► P2 RAG E2E MVP
                         │
                         └─∥ P2 GraphRAG thin（可後置）

Wave C（授權／infra）── P3 Langfuse-PG · P5 PG soak · P6 PR-required
                         （DarkOps／§7／批文閘門）
```

| 可並行 | 互相阻塞 |
|--------|----------|
| P1 doc · P4 smoke · P5 bundle · P6 收綠日 | P2 E2E **等** local execute 解阻 |
| P2 GraphRAG thin ∥ P2 obs footnote | P6 91% uplift **等** 7/7 |
| | P5 soak／P3 PG **等** 授權（可能 Z-DARK-OPS／venv） |

**憲法 §7／DarkOps**

- 本衝刺 **預設不碰**：Z-ENV · Z-VENV-TREE · Z-RUNTIME-CP · Z-ORCH-DESTRUCT · Z-DARK-OPS · Z-HQ-LIQUIDATION  
- P2 **sandbox execute** 若只寫 `tests/fixtures/**`／明確 sandbox 產物 → 通常 **不**觸暗部；若要寫 live Qdrant／`03_RAG_Database` 生產樹 → **停工請示**  
- P3／P5 live PG → 常需 `dark.infra`；`assignable:false` 時 **不得施工**

---

## 4. 建議票批（兩波）

### Wave A — 高槓桿／低風險（目標：P1≈95 · P4≈82–85 · P5≈78–80 · P6 證據推進）

| ID | 目標 | 可碰路徑（摘要） | 驗收命令／runner | DoD |
|----|------|------------------|------------------|-----|
| **P1-GOV-RESIDUAL-CHECKOFF-v1** | 核銷 P1→100 殘項清單 | `docs/**` 清冊 · Progress 末尾 · **不**改憲法正文 | `python 04_Workflows/_ops_cycle.py checklist --mode full --pretty` | 殘項表全「done／explicit defer」；proposed P1 +2～+5 · `apply_phase_pct=false` |
| **P4-MULTI-CHAT-SMOKE-PACK-v1** | 四角色＋一票 walkthrough 可重跑 | `.cursor/commands/**` 引用 · `tests/test_*multi_chat*` 或新薄測 · `docs/` | `python -m unittest`（既有 Multi-Chat／ticket schema 測）+ light boot | AC：一頁 runbook + 綠測；≠ prod crew；proposed P4 +3～+5 |
| **P5-HEALTH-BUNDLE-CLI-v1** | health+metrics+stub 一入口 | `scripts/` · `tests/` · `docs/` | 既有 `run_toolchain_health*`／metrics／`tests.test_p5_metrics_grafana_stub_v1` 串線 | CLI `ok=true`；≠ 真 Grafana；proposed P5 +3～+5 |
| **WF-P6-INT-NIGHTLY-MONITOR**（續） | 收 DAY3–7 | `docs/p6-int-nightly-monitor-v1.md` | `gh` run 歷史／artifact | 滿 7/7 後 **另** W-PROG uplift 83→91 |

### Wave B — P2 解阻＋E2E（目標：P2≈80–90 視授權深度）

| ID | 目標 | 可碰路徑 | 驗收 | DoD |
|----|------|----------|------|-----|
| **P2-HOOK-LOCAL-SANDBOX-EXECUTE-v1** | 解除「僅 dry-run」：sandbox fixture **允許寫**本地 index 產物 | `scripts/run_index_job_hook*` · `tests/fixtures/**` · `docs/phase2-*` · **禁**未授權 `core/**`／暗部 | `unittest` + CLI `--execute --sandbox` → `ok=true` · `writes_index` 僅 sandbox | 尚書省明示 sandbox 邊界；proposed P2 +8～+12 |
| **P2-RAG-E2E-MVP-v1** | 問答 E2E MVP（固定 fixture corpus） | `scripts/` · `tests/` · `docs/phase2-rag-*` | `unittest` + 一鍵 CLI；命中 ≥1 | 串行上票；≠ 全庫 indexed；proposed P2 +5～+10 |
| **P2-INDEX-OBS-FOOTNOTE-v1** | run_id／obs 腳註對齊契約 | `docs/` · 薄測 | contract unittest 仍綠 | proposed P2 +1～+2 |

### Wave C — 授權後關門（目標：P3≈90+ · P5≈90+ · P6≈95–100）

| ID | 門檻 |
|----|------|
| P3-LANGFUSE-PG-ALIGN（實作） | 批文 + infra；否則停在 FRAME |
| P5-PG-SOAK-AUTHORIZED | 批文；對齊 WAVE_A A-P1-1 |
| P6-INT-PR-REQUIRED-GOV + W-PROG | 7/7 後 uplift 91；再談 mandatory／deferred 清冊 → ~100 |

---

## 5. 驗證束（P1–P6 回歸基線 · 開工前後可跑）

```powershell
python 04_Workflows/_boot_context.py --text "P1-P6 near-100 sprint" --pretty
python 04_Workflows/_phase_pct_apply.py read --pretty
python 04_Workflows/_phase_pct_apply.py self-test --pretty
python 04_Workflows/_ops_cycle.py checklist --mode full --pretty

python -m unittest tests.test_phase2_knowledge_indexing_contract_v1 tests.test_index_job_hook_runtime_thin_v1 -v
python -m unittest tests.test_p5_metrics_grafana_stub_v1 -v
# P6／INT：依 docs/phase6-int-regression-gate-contract-v1.md 與既有 INT runner（見 Master_Map runners）
```

Phase% 上調：**僅**匯總票 + `apply --authorize`；普通票 `apply_phase_pct=false`。

---

## 6. 第一刀（執行序）

1. **立即**：續 P6 綠日鐘（human）+ 開 **Wave A** 三張薄票（P1／P4／P5）並行。  
2. **同週關鍵**：尚書省裁決 **P2 sandbox execute** 邊界 → 開 Wave B。  
3. **勿先做**：未授權 PG soak、暗部 monitoring 接管、P6 未滿 7/7 的 % 上調、Wave 4 UI。

---

## 7. 參考索引

| 產物 | 路徑 |
|------|------|
| Dashboard SSOT | `docs/WAVE_PROGRESS_DASHBOARD.md` |
| 80% 集成（他線） | `04_Workflows/plans/multi-phase-80-percent-execution-plan.md` |
| 全線 100 Wave | `04_Workflows/plans/full-line-to-100-wave-plan-2026-07-13.md` |
| P2 gap 審計 | `docs/phase2-index-contract-gap-audit-v1.md` |
| P6 nightly | `04_Workflows/tickets/WF-P6-INT-NIGHTLY-MONITOR_state.md` |
| Phase% runner | `Master_Map.json` → `runners.phase_pct_apply_py` |

---

*HQ-Coordinator · P1–P6 near-100 incremental plan · 2026-07-14*
