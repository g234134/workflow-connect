# TICKET STATE · WC-L2-CI-DESIGN · Control Plane CI/INT Gate 架構設計（L2/L3 FRAME）

> Phase：Wave C · Control Plane · Lane C · **設計票**（doc-only · FRAME）  
> 父依據：**WC-GOV-EXEC-ARTIFACTS-LLM**（`frame_frozen`）· `docs/governance/WC_GOV_EXEC_ARTIFACTS_LLM_governance_contract.md` §2.4 L3 / §5.2 L2→L3 升格門檻  
> 兄弟票：**WC-PRE-06/07**（toolchain L2 · blocked_on_approval · 分軌）· **WC-IMPL-L2**（toolchain CI · 分軌）  
> 索引：`docs/wave_c/overview.md` §M4 governance design queue

---

## FRAME

### Goal
在不動 toolchain L2 的前提下，設計 CP-AUTO L2/L3 的 CI/INT 接入方案：L2 定義「可選/半自動」Control Plane E2E/nightly smoke 的 CI job 語義與隔離機制；L3 定義升格 mandatory CI/INT gate 的條件、觀察期、rollback 路徑與審計欄位。

### Scope

#### L2 設計範圍（Optional / Semi-Automatic CI Jobs）
針對以下現有命令/runner 設計「可選/半自動」CI job 語義：

| Runner / 命令 | 現況 | L2 設計目標 |
|---------------|------|-------------|
| `run_wc_m2_e2e_walkthrough.py` | WC-T7 v0.1 本地 E2E · nightly optional | CI job（optional · non-blocking）· sandbox artifacts 隔離 · 審計 log 輸出 |
| `run_wave_c_nightly_smoke.sh` | WC-T6-T7-v2 nightly smoke · local | CI job（scheduled · optional）· 僅掃描 allowlisted artifacts · 不寫 live STATE |
| `--execute` 寫 B_REPORT 草稿 | WC-GOV L1 設計 | CI job 中僅寫 sandbox 副本（`artifacts/e2e/**`）· 人工審閘門後才准寫入 |
| `artifacts/control_plane/**` 增量掃描 | WC-GOV L2 設計 | CI job（dedup manifest 產出）· read-only 索引 · 不掃暗部/PII |

#### L3 設計範圍（Mandatory CI / INT Gate 升格條件）
設計以下 gate 類型與升格條件（僅 FRAME，不實作）：

| Gate Type | 設計內容 |
|-----------|----------|
| **pre-merge optional job** | 設計條件：何時從 L2「scheduled optional」改為「PR trigger optional」· 不 block merge |
| **post-merge checks** | 設計條件：何時在 merge 後自動觸發 CP-AUTO E2E · 失敗時通知但 rollback 人工 |
| **nightly mandatory reporting** | 設計條件：何時 nightly smoke 失敗須開 incident ticket · 觀察期統計 |
| **INT Tier-A gate（提案）** | 設計條件：CP-AUTO E2E pass 何時可「影子跟隨」INT Tier-A（shadow mode）· 不取代 |
| **rollback 圖** | 設計：L3→L2 降級 playbook · CI required 移除步驟 · 不影響 branch protection 其他 gate |

#### 設計交付物
- CP-AUTO Tier × CI Job Type 矩陣表
- L2/L3 觀察期設計（天數 · 零 P0 · 人工審比例）
- 審計欄位設計（`ci_run_id` · `job_type` · `gate_tier` · `shadow_int_tier_a` 等）
- Rollback 決策樹（L3→L2→L1→L0）

### NonScope

本票為 **純設計票**，以下項目明確禁止：

- **不改** `.github/workflows/**` 任何檔案（YAML / required checks / branch protection）
- **不改** GitHub Environments / deployment protection rules
- **不改** toolchain L2（WC-PRE-06/07）或 `WC-IMPL-L2` 範圍
- **不改** `wc_t5_paths_v0.1` JSON 或 automation_tier 欄位
- **不開** PRE-06/07 與 CP-AUTO L3 的捆綁升格票
- **不寫** 任何 production runner 的 `--execute` 實作
- **不改** live `04_Workflows/tickets/*_state.md`（本票除外）

### AllowedPaths

| 路徑類型 | 具體路徑 | 用途 |
|----------|----------|------|
| **本票 state** | `04_Workflows/tickets/WC-L2-CI-DESIGN_state.md` | FRAME / STATE / C_REPORT / D_REPORT |
| **治理設計檔** | `docs/governance/WC_CP_AUTO_CI_L2_L3_design.md`（建議名）| L2/L3 架構設計 SSOT |
| **索引更新** | `docs/wave_c/overview.md` §M4 design queue | 一行 cross-ref |
| **父契約引用** | `docs/governance/WC_GOV_EXEC_ARTIFACTS_LLM_governance_contract.md` | 只讀對照 L3 門檻 |
| **runbook 引用** | `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` | 只讀對照 E2E 語義 |

### BlockedPaths

| 路徑 | 禁止原因 |
|------|----------|
| `.github/workflows/**` | 實作票範圍（`WC-GOV-EXEC-ARTIFACTS-LLM-IMPL-L3`） |
| `scripts/run_wc_m2_e2e_walkthrough.py` | 實作票範圍 |
| `scripts/run_wave_c_nightly_smoke.sh` | 實作票範圍 |
| `tests/**`（新增/修改） | 實作票範圍 |
| `.github/CODEOWNERS` | 實作票範圍 |
| `04_Workflows/tickets/*_state.md`（本票除外） | 禁止自動/人工誤寫 |
| `docs/governance/WC_PRE_06_07_rollout_plan.md` | toolchain L2 分軌 · 不交叉修改 |
| `docs/governance/WC_TOOLCHAIN_GOVERNANCE_L2_design_draft.md` | toolchain L2 分軌 · 不交叉修改 |

### AcceptanceCriteria

#### AC-L2CI-1（L2 可選/半自動語義）
設計文件明確區分以下 CI job 類型：
- `scheduled-optional`：nightly · 不 block PR · 失敗開 incident（人工決策）
- `pr-trigger-optional`：PR 觸發 · 不 block merge · 僅報告
- `post-merge-check`：merge 後觸發 · 失敗通知 · rollback 人工

#### AC-L2CI-2（L3 Mandatory Gate 升格條件）
設計文件定義 L3 升格的 **≥4 條可驗證門檻**：
- L2 觀察期 ≥14 日且零 P0
- shadow INT Tier-A 模式運行 ≥21 日（並行比對無分歧）
- rollback 演練 ≥2 次（含降級路徑）
- 獨立 gate_id 設計（不占用 `OG-WAVE7-REGRESSION-A`）
- 批文：`approval_status.CP_AUTO_L3=approved`

#### AC-L2CI-3（矩陣表）
設計文件含 **CP-AUTO Tier × CI Job Type** 矩陣表：
- 行：L0 / L1 / L2 / L3
- 列：scheduled / pr-trigger / post-merge / required / INT-shadow
- cell：✓ 允許 / ✗ 禁止 / Δ 條件允許

#### AC-L2CI-4（Rollback 圖）
設計文件含 **L3→L2→L1→L0 降級決策樹**：
- 每節點條件（如：連續 N 次失敗 / P0 incident / 批文撤銷）
- 每節點動作（如：停 CI job / 改 optional / 通知）
- 不影響 toolchain L2 的其他 gate

#### AC-L2CI-5（觀察期與審計）
設計文件定義：
- L2 觀察期：7–14 日 · 零 P0 mis-write · 審計 log 抽查
- L3 觀察期：14–30 日 · shadow mode · 人工審比例 100%→10%
- 審計欄位：`ci_run_id` · `job_type` · `gate_tier` · `shadow_int_tier_a` · `rollback_ref`

#### AC-L2CI-6（分軌聲明）
設計文件 **三處** 聲明：
- Control Plane E2E CI ≠ INT Tier-A（pass 不等價）
- CP-AUTO L3 CI ≠ WC-PRE-06/07 toolchain L2 CI（獨立 gate_id）
- 本設計不改 `.github/workflows/**`（實作票範圍）

#### AC-L2CI-7（後續票規劃）
設計文件列出 IMPL 票拆分建議：
- `WC-L2-CI-IMPL`：sandbox optional CI job 實作
- `WC-L3-INT-GATE-IMPL`：mandatory gate / shadow INT 實作
- `WC-L3-ROLLBACK-PLAYBOOK`：rollback 演練與文件

---

## 粗略規劃（後續票拆分建議）

### 票 1：WC-L2-CI-IMPL（L2 Optional CI Job 實作）

**範圍**：
- 實作 `run_wc_m2_e2e_walkthrough.py` 的 CI optional job（sandbox artifacts · 審計 log）
- 實作 nightly smoke CI job（scheduled · 不 block PR）
- 實作 `artifacts/e2e/**` 隔離副本寫入機制

**主要風險點**：
- sandbox artifacts 路徑與 production `artifacts/` 隔離不足
- nightly job 失敗時通知機制可能 spam
- `--execute` 與 dry-run 的切換開關可能誤觸

### 票 2：WC-L3-INT-GATE-IMPL（L3 Mandatory Gate 實作）

**範圍**：
- 實作 pre-merge optional → required 的升格機制（獨立 gate_id）
- 實作 shadow INT Tier-A 模式（並行比對 · 不影響生產決策）
- 實作 L3 審計欄位與 incident 自動開票

**主要風險點**：
- mandatory gate 失敗可能阻塞所有 PR（影響面大）
- shadow INT 比對邏輯錯誤可能導致誤判
- gate_id 與現有 `OG-WAVE7-REGRESSION-A` 混淆

### 票 3：WC-L3-ROLLBACK-PLAYBOOK（Rollback 演練與文件）

**範圍**：
- 實作 L3→L2→L1→L0 降級 CLI / 腳本
- 執行 ≥2 次 rollback 演練並留痕
- 更新 runbook 與 D_REPORT

**主要風險點**：
- rollback 過程中可能遺留 sandbox artifacts
- 降級後 token 吊銷不全
- 演練與生產環境差異

---

## STATE

- overall_status: frame_draft
- current_owner: orchestrator
- next_action: Reviewer 審 FRAME 草案；通過後進 `design_ready` 可開 `WC-L2-CI-IMPL`
- last_updated: 2026-06-14
- status_by_role:
  - orchestrator: done
  - implementer: n/a
  - reviewer: pending
  - scribe: pending

---

## B_REPORT

<!-- pending -->

---

## C_REPORT

<!-- pending Reviewer -->

---

## D_REPORT

<!-- pending Scribe -->
