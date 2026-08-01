# W5-A-RUNTIME-03 LIMITED-DENY plan

> **狀態**：本文件為 **Phase B 設計文檔**，定義從 Phase A（preview-only）切換到有限 blocking canary 的條件、範圍、kill-switch 與 rollback 流程。**不**包含具體 YAML、CI 配置或程式碼實作。
>
> **關聯**：
> - `observability/enf-preview/README.md` — Phase A 現行唯讀 preview 層
> - `tools/enf_preview_wrapper.py` — ENF-RULE-1 / ENF-RULE-2 / C3-05 L1 實作
> - `tools/print_enf_env.py` — governance env 註冊表（`ENF_ENABLE`、`GOV_ENF_ENABLE`、`GOV_ENF_BLOCKING_CANARY`）

---

## §4  Phase B: Limited blocking canary conditions

### §4.1  Overview

Phase B 引入 **limited blocking canary**：針對 **ENF-RULE-1 的 would_block 記錄**，在特定 job + branch 上將 preview 行為升級為真正的 exit 1（CI job fail）。其餘規則（ENF-RULE-2、C3-05 L1、edge_unknown）維持 preview-only 不變。

本節描述啟動 canary 前**必須滿足**的所有前置條件、canary 的**作用範圍**、**kill-switch 機制**與**異常 rollback 流程**。任何人要開啟 blocking 都必須對照本節文字，**不得繞過 Enforceability Ladder（L0~L3）與事先驗證階段直接啟用 blocking**。

### §4.2  Enforceability Ladder 回顧

| 層級 | 名稱 | 行為 | 本 Phase 對應 |
|------|------|------|---------------|
| L0   | Observability | 唯讀收集數據，不影響 CI | Phase A 前驅動 |
| L1   | Advisory | 印 warning（不 exit 1） | C3-05 L1 (已實作) |
| L2   | Limited blocking | 特定規則 + 特定範圍 exit 1 | **Phase B 本節目標** |
| L3   | Full enforcement | 所有規則全域 blocking | Phase C（未來） |

### §4.3  前置條件（Prerequisites）

以下條件**全部滿足**後，方可啟用 limited blocking canary。任一條件不滿足則 blocking canary **不得上線**。

#### P-1  CI data pipeline v0 穩定

- **條件**：`shadow_batch` → `k2_shadow_spool` 管線（`scripts/fetch_latest_shadow_batch.sh`）已在 `eval-shadow-nightly` job 中穩定運行至少 **連續 7 次 nightly 執行無錯誤**。
- **驗證方式**：檢查近期 CI 日誌，確認 `[SHADOW-PIPELINE] mode=shadow batch=<stamp>` 每夜正確出現，無 `mode=fixture` fallback（除無 batch 可用的合法場合外）。
- **理由**：shadow pipeline 不穩定會導致 blocking 基於不完整的 fixture 數據決策，增加誤擋風險。

#### P-2  tags pipeline / dryrun tag preserve 已修正

- **條件**：tags pipeline 中 `dryrun` 階段的 tag 保留邏輯已修正，確保 `gate_fail_deny`、`error_type`、風險 tag（如 `infra_risk`）等關鍵欄位在 `[DRYRUN-LOG]` JSONL 輸出中**正確出現**。
- **驗證方式**：選取至少 3 次 nightly 的 `per_record.jsonl`，抽查 `dryrun_rule=gate_fail_deny` 記錄的 tag 完整性。
- **理由**：tag 殘缺會使 ENF-RULE-1 的 would_block 計數失真（可能漏判或誤判）。

#### P-3  至少兩輪 policy mining 認可 ENF-RULE-1 做 L2 候選

- **條件**：已完成 **POLICY-MINING-03** 及 **POLICY-MINING-03.1** 兩輪分析，雙方結論一致同意：
  - ENF-RULE-1 暫維持 **L2 候選**（非 L0/L1 降級）。
  - ENF-RULE-1 **不可對 infra_risk 成功案例做 deny**（由 C3-05 L1 單獨處理 warning）。
- **驗證方式**：查閱兩輪 mining 的輸出報告，確認規則結論無衝突或未解決的 disagreement。
- **理由**：blocking 決策需經過多輪獨立驗證，單輪 mining 不足以排除盲點。

#### P-4  C3-05 L1 規則已實作並經過至少 N 次 nightly 觀察，無顯著 FP

- **條件**：
  - C3-05-L1-INFRA-RISK-SUCCESS（`tools/enf_preview_wrapper.py`）已實作完成。
  - 至少 **7 次連續 nightly 執行**（或 **14 天連續觀察**，取較長者）未發現顯著 false positive。
  - 觀察報告（`W5-A-RUNTIME-03-C3-05-OBS-REPORT-01`）已產出，確認 C3-05 行為符合預期，FP 列表與調整建議已清楚記錄。
- **驗證方式**：讀取觀察報告全文與 `[GOV-ENF-PREVIEW]` 日誌 C3-05 計數。
- **理由**：C3-05 若產生 FP，會干擾 ENF-RULE-1 的 blocking 分析（因為 ENF-RULE-1 需要準確的 infra_risk tag 作為輸入）。

#### P-5  GOV_ENF_BLOCKING_CANARY env 已就位

- **條件**：`tools/print_enf_env.py` 中 `GOV_ENF_BLOCKING_CANARY` 已註冊為有效 env（已完成——見 `GOVERNANCE_ENV_SPECS`）。
- **驗證方式**：`python -m tools.print_enf_env --json` 輸出包含 `GOV_ENF_BLOCKING_CANARY` 條目。
- **理由**：kill-switch env 須在 blocking 上線前存在，否則無法緊急關閉。

#### P-6  (非強制但強烈建議) 試跑一次 blocking canary 在 dry-run 模式

- **條件**（建議但非強制）：在 staging 或 branch-specific CI 中，以 `GOV_ENF_BLOCKING_CANARY=1` 但 wrapper **仍 exit 0** 的模式試跑一次，確認 blocking 日誌與計數符合預期。
- **驗證方式**：日誌出現 `[GOV-ENF-PREVIEW] event=blocking_canary_dryrun would_block=<N>` 而 CI job 仍為綠色。
- **理由**：降低首次真 blocking 的心理風險與 CI 誤報成本。

---

### §4.4  Canary 作用範圍（Scope）

啟用 blocking canary 後，以下範圍**生效**；範圍外所有行為維持 Phase A preview-only。

| 維度 | 範圍 | 說明 |
|------|------|------|
| **CI Job** | `eval-shadow-nightly` only | 非 `eval-gate-ci.yml` 中其他 job，亦非 `gov-gate-metrics.yml`、`PR-cross-ref` 等 workflow |
| **Branch** | `main`（或指定 canary branch） | 在 canary 初期可選用一個特定 canary branch（如 `canary/enf-block-v1`），確認行為後切至 `main`。**不得**同時在多個 branch 啟用。 |
| **規則** | 僅 ENF-RULE-1 的 `would_block` | ENF-RULE-2 維持 would_warn（preview-only），C3-05 L1 維持 L1 warning，`edge_unknown` 維持 would_noop。 |
| **記錄條件** | `dryrun_rule=gate_fail_deny` + `error_type` 非空 + 風險 tag + `trace_completeness_score ≥ min-score` | 與 Phase A ENF-RULE-1 條件一致；**不**放寬或額外收緊 |
| **例外** | infra_risk 成功案例不做 deny | 已由 C3-05 L1 獨立處理 warning；ENF-RULE-1 的 would_block 計數中不包含此類記錄 |

#### 升級路線（非當前 Phase 範圍）

- 若 canary 在 `eval-shadow-nightly` + `main` 穩定運行 ≥ 7 天無異常，可考慮擴大到 `PR-cross-ref` workflow。
- 若 ENF-RULE-1 blocking 穩定，可考慮啟用 **ENF-RULE-2** 的 would_warn → would_block 升級。
- 以上每一步都需開新票，不得逕自修改本節範圍。

---

### §4.5  Kill-switch 與 Rollback

#### 4.5.1  Kill-switch env 定義

| Env | 用途 | 預設值 | 可接受值 |
|-----|------|--------|----------|
| `GOV_ENF_ENABLE` | **Master enforcement kill-switch** — 設為 `0` 或 `off` 時**完全關閉所有** blocking（含 canary），wrapper 退回 preview-only exit 0 行為 | `0` | `0` / `off` = disable；`1` / `on` = enable |
| `GOV_ENF_BLOCKING_CANARY` | **Canary 子開關** — 設為 `1` 時啟用 limited blocking canary；設回 `0` 時退回 preview-only。注意：`GOV_ENF_ENABLE=0` 時此開關無效（master 優先） | `0` | `0` / `off` = disable；`1` / `on` = enable |

**優先級**：`GOV_ENF_ENABLE=0` > `GOV_ENF_BLOCKING_CANARY` — 若 master switch 為 off，canary 無論設為何值都不生效。

#### 4.5.2  Rollback 標準流程

發現 blocking canary 造成異常（誤擋正常記錄、FP 暴增、下游客戶 CI 中斷等）時，依序執行：

1. **第一步（秒級）**：在 CI workflow 或 runner 環境中將 `GOV_ENF_ENABLE` 設為 `0`。此操作**立即**將 wrapper 行為退回 preview-only，終止所有 blocking。
   - CI workflow 層面：在 `eval-shadow-nightly` step 的 `env:` 區塊頂部插入 `GOV_ENF_ENABLE: "0"`（覆蓋 repo/organization-level secret）。
   - 若 CI 不可及：直接 revert 開 blocking canary 的 commit，push 後 CI 自動回退。

2. **第二步（分鐘級）**：確認 rollback 生效。
   - 檢查後續 CI run：`[GOV-ENF-PREVIEW]` 日誌仍存在但無 blocking（exit 0）。
   - 確認 `waiting_blocked_*` 計數降至 0。

3. **第三步（小時級）**：根因分析。
   - 收集誤擋記錄的完整 JSONL trace。
   - 判定問題來源：rule 條件過鬆？tag 缺失？data pipeline 異常？
   - 記錄 incident 並更新對應文件（rule、前置條件、CI config 等）。

4. **第四步（日級）**：在問題修正後，重新走 §4.3 前置條件確認，無誤後方可再次啟用 canary。

#### 4.5.3  Rollback trigger 條件

以下任一發生時，**自動觸發 rollback 流程**：

| Trigger | 判斷方式 | 動作 |
|---------|----------|------|
| blocking canary 上線後首次 nightly 中 `would_block` 計數 > 上週 daily average × 3 | 比較 `[GOV-ENF-PREVIEW] event=summary` 行 | 關 `GOV_ENF_BLOCKING_CANARY` |
| blocking canary 上線後收到任何下游客戶的 CI 中斷投訴 | 人工確認 | 關 `GOV_ENF_ENABLE` |
| data pipeline 異常（shadow_batch 載入失敗、spool 為空、fixture fallback） | 日誌 `[SHADOW-PIPELINE] mode=fixture` 或 `[ERROR]` | 關 `GOV_ENF_ENABLE` |
| tag pipeline 出現已知的 tag 丟失 bug | 人工確認 | 關 `GOV_ENF_BLOCKING_CANARY` 並暫停 blocking 直到 tag 修正 |

---

### §4.6  安全公告

1. **任何人**不得在不符合 §4.3 前置條件的情況下啟用 blocking canary。
2. **任何人**不得修改 §4.4 的作用範圍而不開新票討論。
3. **任何人**不得繞過 rollback 流程直接重新啟用 blocking。
4. 本節文字若與後續實作細節有衝突，以本節文字為準，實作需對齊後更新。

---

## §5  部署操作備忘（作業時參考）

> 本節僅為未來操作者在啟用 canary 時的參考步驟。**不**構成「立即啟用」的指令。

### 5.1  啟用 canary 的手動步驟（僅在 §4.3 全部滿足時執行）

1. 在目標 branch（`main` 或指定 canary branch）的 `eval-gate-ci.yml` 中：
   - 在 `enf_preview_wrapper` step 的 `env:` 區塊設 `GOV_ENF_ENABLE: "1"`。
   - 設 `GOV_ENF_BLOCKING_CANARY: "1"`。
2. 確認 wrapper 的 blocking 邏輯讀取這兩個 env：`env_false` 時不 exit 1；`env_true` 且符合 ENF-RULE-1 would_block 時 exit 1。
3. 開一個新的 blocking canary 觀察票，記錄每晚的 `would_block` 計數與有無 FP 回報。

### 5.2  監控指標（建議）

- nightly CI run 中 `[GOV-ENF-PREVIEW] event=summary` 行 → 追蹤 `would_block` / `would_warn` / `would_noop` 數列。
- blocking canary 啟用後，額外印 `[GOV-ENF-PREVIEW] event=blocking_canary active=jobs=eval-shadow-nightly branch=<branch> rule=ENF-RULE-1` 以利區分 run。
- 設定 simple cron（或 GitHub Actions schedule）每天拉取 `would_block` 計數，超過 threshold 時送通知。

---

*End of W5-A-RUNTIME-03-LIMITED-DENY_plan.md*
