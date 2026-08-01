# P8.5 Optional Bridge Stub / Smoke C Checklist v1

> **票**：`W4-P85-OPTIONAL-BRIDGE-SMOKE-C-v1`  
> **性質**：closure gaps → **可驗收小票** · docs ± advisory 測 · **≠** required CI · **≠** prod browser  
> **權威 runbook**：`docs/phase8_5-bridge-smoke-runbook-v1.md`  
> **上游 gaps**：`docs/p85_h2_closure_prep_checklist_v1.md` §4 Optional follow-ups

---

## 0. non_claims

| 本票 **不是** | 說明 |
|---------------|------|
| ≠ required CI 默升 | Smoke C **永不**進 branch-protection required |
| ≠ prod Playwright／真 browser | bridge 仍為 in-memory stub（見 runbook Non-goals） |
| ≠ Phase closure／Phase% | 旁線票 · 僅把 gaps 做成可勾清單 |
| ≠ 重開 WH-P85 wave-H2 | H2 已 `done_with_gaps`；本票只收 optional 缺口 |

---

## 1. Gap → 驗收映射

| Gap（closure prep） | 本票驗收項 | 狀態定義 |
|---------------------|------------|----------|
| bridge 仍 stub | **G-STUB**：文件明示 in-memory stub 可接受；Smoke A/B 綠即可 | docs + A/B advisory |
| Smoke C manual matrix | **G-SMOKE-C**：下方手跑矩陣；結果記 Progress／票 STATE | manual only |
| bridge 持久化 | **OUT-OF-SCOPE** | 另開票 · 本票不碰 |
| Bridge CI hardening | 已由 `WH-P85-bridge-ci-hardening-v2` 收口 | 本票僅 cross-ref |

---

## 2. Smoke C 手跑矩陣（manual · optional）

> cwd = `gov_core_system` venv root（路徑見 `Master_Map.json` cabin 邏輯名）。  
> **勿**把本矩陣寫進 `.github/workflows` required checks。

| # | 步驟 | 期望 | 填寫（人類／ops） |
|---|------|------|-------------------|
| C1 | 第二殼 `uvicorn app_api:app --host 127.0.0.1 --port 8000` | 進程起來 | `______` |
| C2 | curl accept-without-browser（runbook Smoke C 範例） | HTTP **200** · `schema_version=orchestration_bridge_v1` · `browser.skipped=true` | `______` |
| C3 | curl `{"intake":{}}` | HTTP **422** · FastAPI `detail` | `______` |
| C4 | 記 run 時間／操作者於 Progress 末尾一句 | 有留痕 | `______` |

**Advisory 對照（可自動化 · 非 Smoke C）**

```powershell
# cwd: gov_core_system venv root — advisory only
python -m unittest tests.test_minimal_orchestration_bridge -v
python -m unittest tests.test_app_api_orchestration_bridge -v
```

期望：Smoke A **20/20** · Smoke B **7/7**（與 runbook §0.3 一致）。

---

## 3. Stub bridge 聲明（可勾）

- [x] In-memory browser plan 為設計邊界（非 Playwright）— runbook Non-goals  
- [x] Outbox PG 測試預設 OFF — `GOV_CORE_ORCHESTRATION_BRIDGE_OUTBOX_PG_ENABLED=false`  
- [x] Smoke C 維持 manual；CI advisory 僅 A/B  
- [ ] （可選）人類完成 §2 C1–C4 並 Progress 留痕

---

## 4. Cross-ref

- `docs/phase8_5-bridge-smoke-runbook-v1.md`（Smoke A/B/C）  
- `docs/p85_h2_closure_prep_checklist_v1.md`  
- `04_Workflows/tickets/W4-P85-OPTIONAL-BRIDGE-SMOKE-C-v1_state.md`  
- `WORKFLOW_INDEX.md` §1.4
