# Wave Cross-Rollup Inspector v1

> **Ticket**: `W5-T4-wave-plan-reviewer-checklist-v1` · **Wave 5**  
> **用途**：Wave 1–4 **施工完成後**，Master Reviewer / Orchestrator **只讀** spot-check smoke／metrics／Progress 匯總。  
> **啟用時機**：**執行階段**（規劃階段可標 N/A · gaps 預期）。  
> **trace_fields SSOT**：`docs/wave-evidence-ingestion-spec-v1.md` §3（**W5-T3**）— **本檔不重複定義**。

---

## 0. 與其他 checklist 分界

| 檔 | 職責 |
|----|------|
| `wave-master-plan-reviewer-v1.md` | 規劃層 Master Plan |
| `wave-next-code-inspector-v1.md` | 戰術 lane 施工 |
| **本檔** | 跨 Wave **證據 rollup**（消費 W5-T3） |

---

## 1. 引用 W5-T3 trace_fields（不重定義）

只讀消費下列鍵（定義見 W5-T3 spec）：

- `run_id`
- `ticket_id`
- `ga_run.url`
- `notifications_failed_ack_count`
- `evidence_type`
- `gap_reason`

Observer CLI：

```bash
python scripts/observe_wave_evidence_v1.py --wave W1 --format json
python scripts/observe_wave_evidence_v1.py --wave W5 --format json
```

---

## 2. Rollup 檢查項（執行階段）

| # | 檢查項 | 證據 | ☐ |
|---|--------|------|---|
| R1 | 目標 Wave 子票 `B_REPORT.verification` 非空（或 honest gap） | observer `b_report_verification` / `gaps` | ☐ |
| R2 | 已知 smoke 邏輯路徑存在或標 `artifact_missing` | `multi_phase_smoke_run` · `multi_case_smoke_run` | ☐ |
| R3 | human-only run URL **未**被標 `verified` | `ga_run_url_placeholder.verified=false` | ☐ |
| R4 | Progress 末尾有對應票號（或 gap `not_found_in_progress_tail`） | `progress_append` | ☐ |
| R5 | 無 Phase% 因 rollup 上調宣稱 | Dashboard 數字格未改 | ☐ |

規劃階段：R1–R4 可全部為 gaps → **不**視為工具失敗。

---

## 3. Over-claim 攔截

- [ ] 無「observer 綠 = prod observability 完備」
- [ ] 無「gaps 空 = human GA 已完成」
- [ ] 無重定義 W5-T3 / P7.5 trace 欄位名

---

## Changelog

| 日期 | 說明 |
|------|------|
| 2026-07-09 | 初版 · W5-T4 · 引用 W5-T3 |
