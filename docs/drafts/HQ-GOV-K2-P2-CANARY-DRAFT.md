# 尚書省批文（草案）— K-2 Phase 2 Internal Canary

> **批文編號**：`HQ-GOV-K2-P2-CANARY-DRAFT`  
> **性質**：治理批文 · **草案 · 暫不生效**  
> **母本**：`docs/k2_deployment_governance.md`（Chat C）  
> **對照 Phase 1**：`HQ-GOV-K2-P1-SHADOW-20260525`（已生效 · 本地演練）  
> **擬議狀態**：待 Phase 1 出門指標連續 7 日達標 + 本批文定稿後，方得開實作票（`K2-phase2-internal-canary` 等）

---

## 一、裁決摘要

| 項 | 草案內容 |
|----|----------|
| **裁決** | **有條件批准（草案）** — Phase 2 internal canary；用戶可見主答案在內部 cohort 內可由 K-2 提供 |
| **生效條件** | 本檔定稿 + §四 Phase 1→2 出門證據包通過 + §五技術前置全滿或 risk accepted 留痕 |
| **擬議啟用日** | *（待定 · 不早於 Phase 1 觀測窗結束日 + 升格審查通過後 1 工作週）* |
| **範圍邊界** | **在範圍**：內部 staff／allowlist 5%→10% canary；本地 prod-like 演練延續。**不在範圍**：遠端 prod 叢集自動 rollout、C 端用戶、>10% 全域流量、Phase 3 擴面 |

**單點切換**：canary 僅經 `merge_ask_and_k2`（或治理批准的 `primary_source=k2` 變體）與 `ASK_MERGE_INTERFACE` 配置；禁止在 ask 圖內散落分支（繼承 `k2_merge_strategy.md` §1.1）。

---

## 二、流量與參數（對齊治理 §4.3）

| 參數 | 草案初值 | 說明 |
|------|----------|------|
| Canary 比例 | **5%** → 驗證後 **10%** | 僅 `internal` / `staff` tenant 或 allowlist |
| 主答案來源 | canary cohort 內 `primary_source=k2` | 須覆蓋合流 S1–S7；非 cohort **100% ask** |
| Shadow | **保留** | Phase 1 非 canary 流量繼續 async shadow + spool |
| 自動回退 | **開啟** | `docs/k2_deployment_governance.md` §7.1 R1–R5 |
| 用戶延遲預算 | p99 較 shadow 基線惡化 **≤20%** | 超過觸發 R5 |

**產品動作（進門前必備）**：內部 cohort 定義、acceptable 答案差異標準（mock `answer_similarity ≥ 0.25` 僅 dev 基線；live 另定）。

---

## 三、範圍表

| 在範圍 | 不在範圍 |
|--------|----------|
| 內部 cohort canary 分流與 merge（本地 prod-like） | 遠端 prod SSH/K8s/systemd 自動 rollout |
| canary 專用 eval export + `eval_ci_check`（§6.4 參數） | 修改 user-facing `/api/ask` schema（slim envelope 策略未批前不外洩 `k2_eval_metadata`） |
| 5%→10% 漸進；on-call 自動／手動回退演練 | Phase 3 tenant／>30% 擴面 |
| Progress / `00_master_plan` §4.8 / `90_run_queue` 留痕 | Phase 4 full switch |
| Phase 1 shadow **持續**（非 canary 流量） | 跳過 Phase 1 直接 canary |

---

## 四、Phase 1→2 出門證據（升格進門 · 須同時滿足）

> 權威：`docs/k2_deployment_governance.md` §6.3「Phase 1 → 2」；觀測窗以 Phase 1 批文啟用日為準（本地：**2026-05-26 06:00 UTC** 起 **7 自然日**）。

### 4.1 連續 7 日每日門檻（shadow 分母）

| 指標 | 連續 7 日要求 | 備註 |
|------|----------------|------|
| **infra_risk** | 計數 **= 0**／日 | 任一觸發當日調查；對齊 `--fail-on-tags infra_risk` |
| **unacceptable** | **= 0**／日 | `classification.unacceptable`；shadow 硬回歸 |
| **needs_review** | 7 日滾動 **≤ 60%** | 且較觀測窗**首日**下降或持平 |
| **merge_safe** | **≥ 95%** | `k2_behavior_profile.md` §2；週報 `compare_shadow_profiles` |
| **N（樣本量）** | 決策日 **≥ 30**；建議 **≥100 條/日** 或 **≥500/週** | N&lt;30 **不得**做升格裁斷 |
| **產品 + 治理** | 書面無異議 | 附於升格申請包 §8 |

### 4.2 Phase 1 進門前置（已滿足 · 引用）

§5 清單 P1–P6（merge/shadow 測試、策略對賬、P+-eval-ci-wire、回退 runbook、禁區）— 見 `HQ-GOV-K2-P1-SHADOW-20260525` 戰報。

### 4.3 升格申請包最低內容（§8）

當前 Phase、目標 Phase 2、過去 7 日指標表、`eval_ci_check` JSON、shadow 週報摘要、已知 risk（selector/answer）、回退聯絡人。

---

## 五、Phase 2 啟用前技術前置清單（必要非充分）

> 治理 §5 末句、§6.3 Phase 2→3、`k2_merge_strategy.md` §4。  
> **升格前須 closed 或 Progress 末尾 risk accepted 留痕**（合約 Rule 12）。

| # | 工單／檢查項 | 驗證方式 | 狀態（草案填寫時） |
|---|--------------|----------|-------------------|
| T1 | **Selector 桥接**（K-2 尊重 ask greeting skip-RAG） | 單測 + shadow `test_shadow_greeting_selector_skip` 行為對齊 | **open** |
| T2 | **Answer adapter / LLM 对齐**（非 stub 主答案語義） | shadow live 抽樣 + 產品簽字 acceptable 標準 | **open** |
| T3 | **retrieve_timeout → error_type 映射** | `merge_safe` 週報無新增 unacceptable；或 mapping 工單 closed | **open**（fixture 已知 gap） |
| T4 | **`ASK_MERGE_INTERFACE.entry.context_mode`** 切換批准 | 治理書面 + Progress override 留痕 | **待批** |
| T5 | **Canary 分流實作**（allowlist / 5–10% / `primary_source=k2`） | 代碼 review + 單元／整合測試 | **未開票** |
| T6 | **Canary eval export 路徑** | `eval_ci_check` §6.4 在 canary 導出上 exit 0（`--max-needs-review-ratio 0.45`） | **未開票** |
| T7 | **自動回退 R1–R5 接線** | 演練記錄：觸發後 canary→0、ask-only | **未開票** |
| T8 | `tests/test_k2_merge_adapter` + `tests/test_k2_ask_shadow` 全綠 | unittest | **預期已綠**（持續回歸） |
| T9 | **內部 cohort + on-call** | 產品 cohort 表；Progress 補齊聯絡通道 | **部分**（P1 on-call 待補） |
| T10 | 未觸憲法 §7 禁區 | 治理簽字 | 每輪確認 |

**說明**：Wave 3 `J-selector-context-governance` 為 **ask 側** done；**K-2 側桥接**仍屬 T1，不得與 ask 工單混為已關閉。

---

## 六、Phase 2 觀測期指標（啟用後 · 7 日再議 Phase 3）

> 權威：§6.2「Phase 2 canary」欄 + §6.3「Phase 2 → 3」。

### 6.1 建議驗收命令

```bash
python -m observability.eval_ci_check <canary_eval_export_path> \
  --limit 100 \
  --min-samples 30 \
  --max-needs-review-ratio 0.45 \
  --fail-on-tags infra_risk

python -m unittest tests.test_k2_merge_adapter tests.test_k2_ask_shadow -v
```

### 6.2 連續 7 日 canary 門檻（出門 Phase 3 前）

| 指標 | Phase 2 canary 建議 |
|------|---------------------|
| **needs_review** 比例 | **≤ 45%**（連續 7 日） |
| **infra_risk** | **0**（連續 7 日） |
| **observability_gap** | ≤ **15%** |
| **high_retry** | ≤ **20%** |
| **many_handoffs** | ≤ **10%** |
| **ask 主路徑 ok 率** | ≥ **99%** |
| **merge_safe** | ≥ **98%** |
| **unacceptable** | **0 件/週** |
| **N** | ≥ **50** canary 請求/日 |
| **產品反饋** | 無 P0（錯誤答案、不可接受延遲） |

---

## 七、回退（摘要）

- **自動**（§7.1）：`gate_result=fail` + `ci_fail`、1h 內 canary `infra_risk`≥1、ok 率較基線 +2pp、p99 惡化 >20%、canary 上 `eval_ci_check` fail 等 → **canary=0，ask-only**；**保留 shadow**。
- **手動**：needs_review 連續 3 日超當 Phase 上限、產品 P0/P1、shadow 新增 unacceptable、安全事件。
- **動作**：flag→0、確認無 K-2 主路徑殘留、shadow 日誌保留 7 日、Progress + `00_master_plan` 回退。

---

## 八、角色與留痕

| 決策 | 最終批准 |
|------|----------|
| 打開 partial rollout / canary（≥1% 真實 K-2 主答案） | **尚書省**（本批文定稿後） |
| 緊急回退 ask-only | **工程 on-call**（24h 內報備尚書省與產品） |

每次 Phase 升格或回退 **必須**：`04_Workflows/00_Agent_Work_Progress.md` **末尾**戰報；`00_master_plan.md` §4.8 一行；觸生產配置則 Rule 12 override 留痕。

---

## 九、擬議實作票（定稿後開 · 本草案不授權施工）

| 票據 ID（擬） | 標題 | 依賴 |
|---------------|------|------|
| `K2-phase2-internal-canary` | Phase 2 本地 internal canary T+0 + 7d 觀測 | 本批文定稿 + §四出門 |
| `K2-phase2-canary-routing` | allowlist / 比例分流 + `primary_source=k2` | T5 |
| `K2-phase2-canary-export` | canary eval export + nightly | T6 |
| `K2-selector-bridge` | K-2 selector 桥接 | T1 |
| `K2-answer-llm-align` | Answer LLM 对齐 | T2 |
| `K2-error-type-mapping` | retrieve_timeout error_type | T3 |

---

## 十、草案聲明

- 本文 **不構成生效批文**；不得作為啟用 canary、修改 prod 配置或關閉 Phase 1 shadow 之依據。
- 指標數值為 `k2_deployment_governance.md` 建議範圍；定稿時尚書省可調 N 或比例（須 Progress 留痕）。
- 本輪戰役：**僅文檔與前置**；遠端 prod rollout 仍排除，與 Phase 1 本地演練邊界一致。

---

**起草**：大唐副官 · K-2 Phase 2 canary 準備戰  
**日期**：2026-05-25  
**狀態**：**草案 · 暫不生效**
