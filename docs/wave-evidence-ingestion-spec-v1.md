# Wave Evidence Ingestion Spec v1

> **Ticket**: `W5-T3-evidence-ingestion-observer-v1` · **Wave 5** · **Master CP** · P10 / P10.5  
> **性質**：跨 Wave **只讀**證據匯入契約 + observer CLI 骨架說明。  
> **非**：production metrics backend · Grafana · 自動關 human-blocked 票 · P10 runtime 閉環。

---

## Non-claims（必讀）

| 聲明 | 狀態 |
|------|------|
| observer CLI 可只讀彙總既有 smoke / B_REPORT / Progress 證據 | **是**（skeleton · L-local） |
| 本 spec 就緒 = P10 S15 notify / intake API / prod 閉環已交付 | **否** |
| 本 spec 就緒 = P10.5 skill 蒸餾已 prod | **否**（僅可索引既有 skeleton 路徑） |
| human-only 證據（GA run URL 占位符）可由 AI 偽造為已驗證 | **否** |
| 靜默忽略空 B_REPORT.verification | **否**（須 honest `gaps`） |
| Phase% 因本票上調 | **否** |

---

## 1. 證據類型表

| evidence_type | 邏輯路徑／來源 | AI 可驗證？ | human-only？ | 典型消費者 |
|---------------|----------------|-------------|--------------|------------|
| `multi_phase_smoke_run` | `outbox/verification/<case_slug>/multi_phase_smoke_run.json` | **是**（檔存在 + `ok` 欄） | 否 | MP-SMOKE · CI-SMOKE · W5-T3 |
| `multi_case_smoke_run` | `outbox/verification/multi_case_smoke_run.json` | **是** | 否 | MC-SMOKE · W5-T3 |
| `b_report_verification` | `04_Workflows/tickets/<ticket_id>_state.md` → `## B_REPORT` → `verification` | **是**（段落非空） | 否 | Reviewer · W5-T3 |
| `ga_run_url_placeholder` | 子票 B_REPORT / Progress 中的 run URL 欄（常為 placeholder） | **否**（僅偵測占位／缺席） | **是** | Wave-H · P8.5 / P9 ops |
| `progress_append` | `04_Workflows/00_Agent_Work_Progress.md` **末尾**條目（含票號） | **部分**（存在性） | 否 | Scribe · Orchestrator |

> **分界（AC-4）**：AI 可驗證 = 本機／repo 內可重跑命令或檔案欄位；**human-only** = 須 Ops 在 Actions UI `workflow_dispatch` 後回填真實 run URL，observer **不得**把 placeholder 標成 `verified`。

---

## 2. 邏輯路徑約定

| 類別 | 約定 | 備註 |
|------|------|------|
| Smoke 產物 | `outbox/verification/**` | 相對戰車根；**禁止**硬編磁碟絕對路徑 |
| Ticket STATE | `04_Workflows/tickets/*_state.md` | 讀 `B_REPORT.verification` · `overall_status` |
| Progress | `04_Workflows/00_Agent_Work_Progress.md` | **append-only**；observer 只掃末段關鍵字 |
| Trace SSOT（P7.5） | `docs/p75-intake-gate-control-plane-trace-v1.md` | 消費欄位名 · **不**重定義 |
| Playbook observability | `docs/wave-master-ticketing-playbook.md` §4.3 | success/failure_signals 對齊 |

路徑權威：見 `Master_Map.json`；本檔僅相對路徑。

---

## 3. `trace_fields` 標準鍵

| 鍵 | 語意 | 來源示例 |
|----|------|----------|
| `run_id` | 單次 smoke／CI run 識別 | smoke JSON · Actions run |
| `ticket_id` | 子票 ID | `*_state.md` 檔名／FRAME |
| `ga_run.url` | 遠端 GA run URL（常 human） | B_REPORT · Progress |
| `notifications_failed_ack_count` | 失敗 ack 計數 | `export_std_case_metrics_v1` · CI-SMOKE |
| `evidence_type` | 上表類型枚舉 | observer 輸出 |
| `gap_reason` | 誠實缺口原因 | observer `gaps[]` |

對齊 playbook §4.3：`verify_commands` · `evidence_artifacts` · `success_signals` · `failure_signals`。

**P7.5 上游補充（只消費 · 不重定義）**：`intake.gate_decision` · `decision` · `reason_codes` — SSOT → `docs/p75-intake-gate-control-plane-trace-v1.md`。

---

## 4. success / failure signals（對齊 playbook §4.3）

```yaml
observability:
  success_signals:
    - "CLI ok=true 且 gaps 對缺失證據 honest 標註"
    - "已知 demo 路徑可列 evidence_summary 或 gaps（無檔不 crash）"
    - "human-only 證據標 human_only=true · 非 verified"
  failure_signals:
    - "靜默忽略 B_REPORT 空 verification"
    - "偽造 run URL 為已驗證"
    - "硬編磁碟絕對路徑"
```

---

## 5. Observer CLI（skeleton）

| 項 | 值 |
|----|-----|
| 腳本 | `scripts/observe_wave_evidence_v1.py` |
| 輸入 | `--wave W1|…|W5` 或 `--ticket-id` · `--format json|text` |
| 輸出 | `{ ok, wave, tickets[], evidence_summary[], gaps[], message }` |
| 行為 | **只讀**掃描 tickets + 已知 smoke 邏輯路徑 |
| 不做 | 寫 DB · 改 smoke runner · ingest secret · 關票 |

```bash
python scripts/observe_wave_evidence_v1.py --wave W5 --format json
python scripts/observe_wave_evidence_v1.py --ticket-id W5-T5-cross-wave-playbook-index-v1 --format text
python -m unittest tests.test_observe_wave_evidence_v1 -v
```

---

## 6. Planning 階段 gaps（預期）

Wave 1–4 票 ID 未施工或 STATE 缺 B_REPORT 時，observer **應**回報 `gaps`（RSK-W5-T3-01 accept）。  
**不得**因此將 CLI 標 `ok=false`（缺證據 ≠ 工具故障）；工具故障才 `ok=false`。

---

## Changelog

| 日期 | 說明 |
|------|------|
| 2026-07-09 | 初版 · W5-T3 MVP（spec + CLI skeleton + unittest） |
