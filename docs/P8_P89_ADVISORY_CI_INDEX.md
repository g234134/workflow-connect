# P8 / P8.9 · Advisory CI SSOT Index (v1)

> **Ticket**: `W3-P8-ADV-advisory-ci-ssot-index-v1` · **Wave 3** · **doc-only**  
> **Authority**: P8 / P8.9 線 advisory CI 與本機 smoke 路徑的**誠實索引**；**不**改 workflow · **不**升格 required check。  
> **分線**：P7 advisory 歸 Wave 2 `docs/P7_ADVISORY_CI_INDEX.md` · **本檔僅 P8/P8.9**。

---

## Non-claims（必讀）

| 聲明 | 狀態 |
|------|------|
| 本索引所列 GitHub Actions / 本機腳本均為 **advisory · local-gate · non-prod**（非 branch protection required） | **是** |
| `bridge-smoke.yml` landing `origin/main` = Scenario1/2 **GA pass** | **否**（遠端 GA 證據另見 P8.5 ops-run · 常缺 run URL） |
| `run_ci_smoke_check_v1.py` exit 0 = GitHub **required workflow** 綠 | **否**（**repo local release sanity** · **無** workflow 綁定為 required check） |
| `run_multi_phase_smoke_v1.py` 綠 = prod-ready / INT Tier-A | **否** |
| 本索引就緒 = Phase% 上調 · required CI 升格 | **否**（須 WC-PRE-06/07 + 尚書省批文） |

對照 Reviewer：`04_Workflows/review_checklists/wave-next-code-inspector-v1.md` **§3.2**（CI advisory · bridge stub · 無 required 升格）。

---

## 索引表（≥3 條）

| # | 路徑 | ci_class | 角色 | 觸發 | 結果類型 | 標籤 |
|---|------|----------|------|------|----------|------|
| 1 | `.github/workflows/bridge-smoke.yml` | **advisory CI** | P8.5 minimal bridge Smoke A/B（unittest + 可選 HTTP） | PR paths · `workflow_dispatch` | job exit · Actions UI | **advisory · continue-on-error（若適用）· 非 branch protection required** |
| 2 | `scripts/run_ci_smoke_check_v1.py` | **local-only** | 單 case 串跑 MP-SMOKE + MP-METRICS · fail → exit 1 | 本機／可選 CI job 呼叫 | text/json · process exit | **repo local release sanity · ≠ GitHub required workflow**（無 required 綁定） |
| 3 | `scripts/run_multi_phase_smoke_v1.py` | **local-gate** | 七步跨 phase 接線 sanity（gate→…→backlog） | 本機 · 被 CI-SMOKE／MC-SMOKE 呼叫 | `multi_phase_smoke_run.json` | **local-gate · non-prod · ≠ merge gate** |

### bridge-smoke.yml 誠實句（AC-2）

- **landing `origin/main` ≠ GA pass**。Actions 可見 P85 Bridge Smoke A/B (advisory) **僅**代表 workflow 已落地。
- Scenario1／Scenario2 **遠端 GA** 證據另見 Wave 4 / Wave-H：`W4-P85-S2-GA-RUNBOOK-v1` · `WH-P85-CI-LAND-v1` ops-run；**無 run URL 時不得宣稱 GA pass**。
- 技術細節 SSOT：`docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3（本索引不重寫 job 步驟）。

### run_ci_smoke_check_v1.py（AC-3）

- **角色**：**repo local release sanity**（MP-SMOKE + metrics 規則）。
- **≠** GitHub **required** / branch protection check。
- 現況：**無**將本腳本掛為 required check 的 workflow 綁定；若某 advisory job 呼叫之，仍 **≠** merge gate（除非未來 WC-PRE 批文另開票）。

---

## Cross-refs

| 文件 | 用途 |
|------|------|
| `04_Workflows/WORKFLOW_INDEX.md` §1.46 | 本索引的 INDEX 入口 |
| `docs/P7_ADVISORY_CI_INDEX.md` | P7 分線（勿混讀） |
| `wave-next-code-inspector-v1.md` §3.2 | Reviewer non-claims |
| `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1` | Global #4 對齊 |
| `docs/phase-8-operator-backlog-v1.md` | 腳注：backlog CLI ≠ prod gate |
| `docs/p8_9-verification-bundle-v1.md` | 腳注：bundle 綠 ≠ required CI |

---

## Changelog

| 日期 | 說明 |
|------|------|
| 2026-07-09 | 初版 · W3-P8-ADV |
