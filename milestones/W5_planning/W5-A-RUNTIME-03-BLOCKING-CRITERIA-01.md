# W5-A-RUNTIME-03-BLOCKING-CRITERIA-01 — First Blocking Canary Criteria (Plan-Only)

> **票號**：W5-A-RUNTIME-03-BLOCKING-CRITERIA-01  
> **類型**：plan-only · doc-only  
> **狀態**：設計稿（**不啟用 blocking**、**不修改**任何程式／CI／env 語意）  
> **上游**：`docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md`（值班判讀；只讀）  
> **下游**：未來 `W5-A-RUNTIME-03-LIMITED-DENY-*` 實作票（尚未開票）

---

## 1. Background & Scope

### 1.1 目前狀態（Phase 2 · shadow-only）

ENF enforcement preview 已接入 nightly CI pipeline，形成可重複的觀測閉環：

| 能力 | 現況 |
|------|------|
| Nightly 產出 | `eval-shadow-nightly` 每日執行；dry-run 後由 `enf_preview_wrapper` 印 **`[GOV-ENF-SHADOW-SUMMARY]`**（單行 JSON） |
| 控制面 | `GOV_ENF_ENABLE=1`、`GOV_ENF_BLOCKING_CANARY=0`；wrapper **永遠 exit 0**，不影響 job pass/fail |
| 聚合工具 | `tools/analyze_enf_shadow_summaries` 可跨日匯總 `total` / `would_block` / `would_warn` / per-rule 計數 / Samples |
| Policy 來源 | ENF-RULE-1／2 來自 POLICY-MINING-01 §3.1（C-01、C-03）；C3-05 為 L1 觀測（C-05） |

**Shadow 觀測摘要（policy-mining + analyzer 窗口；非 blocking 批准）**

- 在累積 per-record 樣本中，**約 700 筆對應 ~7 筆 `would_block`**（約 **1%** block rate）為目前可接受的 shadow 基線量級。
- `would_block` **幾乎全部**來自 **ENF-RULE-1**；觸發 tags 集中在 **`infra_risk`** 與 **`security:critical`**。
- Samples 傾向 `dryrun_rule=gate_fail_deny` + 具體 `error_type`（timeout、crash、healthcheck 類）+ 上述 risk tags。
- **尚未**完成：跨月穩定性驗證、系統化 false positive 率、min_score sensitivity 分析。

### 1.2 本文件範圍

| 在範圍內 | 不在範圍內 |
|----------|------------|
| 定義**第一條 blocking canary** 的 readiness 條件、rollout 階梯、kill-switch／rollback **要求** | 任何程式、workflow、config 變更方案 |
| 鎖定**極窄**第一波候選：**ENF-RULE-1** 且 risk tag ∈ **`{infra_risk, security:critical}`** | ENF-RULE-2、C3-05、或其他 rule 的 L2 blocking |
| 描述 Phase A（blocking simulation）與 Phase B（limited canary）的**流程形狀** | 宣告啟用時點或尚書省批文 |
| 列出 open questions，供後續實作票與 governance 裁決 | 修改 `docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md` |

**生效聲明**：本文件成文**不代表**任何環境已滿足 blocking 門檻，也**不觸發** `GOV_ENF_BLOCKING_CANARY=1`。

---

## 2. Enforceability Ladder 回顧（L0 / L1 / L2）

> 以下重述 **W5-A-RUNTIME-03-LIMITED-DENY** 設計中的三級 enforceability 語意；**不修改**原設計，僅為本 criteria 提供共同詞彙。

| 級別 | 定位 | 對 pipeline／verdict | 現行 W5-A Phase 2 |
|------|------|----------------------|-------------------|
| **L0** | Observability-only | 只產出 log／summary；**零**判決影響 | `[GOV-ENF-SHADOW-SUMMARY]`、`would_*` 計數；`exit_policy=preview_only` |
| **L1** | Warning / advisory | 結構化 warn 行、報表、值班告警；**不**改 pass/fail | ENF-RULE-2（`would_warn`）、C3-05（`[ENF-WARN]`） |
| **L2** | Blocking eligibility | **二元 deny**；觀測穩定、誤攔低、具 rollback；可影響 job 結果 | **未啟用**；ENF-RULE-1 為**候選**，非已批准 rule |

**L2 准入原則（設計約束，非本票新定義）**

1. **可二元化**：同一輸入必須穩定映射為 allow 或 deny，不得依賴人工即時判斷。
2. **觀測先行**：須先在 L0 累積足夠 nightly 證據，且 pattern 可解釋。
3. **誤攔可接受且可回退**：預期 block rate 低；須有單一 kill-switch 可立即退回 L0。
4. **範圍極窄**：第一波僅限已 shadow 驗證的最小 case 集合。

**本 criteria 的目標**：從現有 shadow 訊號中，挑出**第一組符合 L2 資格、且值得進 blocking canary 討論**的 case 集合——即 **ENF-RULE-1 × {infra_risk, security:critical}**。

---

## 3. Candidate Space for First Blocking Canary

### 3.1 從 analyzer / policy-mining 看到的候選空間

| Rule | 現行 shadow outcome | 觸發摘要 | 是否納入第一波 blocking canary |
|------|---------------------|----------|--------------------------------|
| **ENF-RULE-1** | `would_block` | `gate_fail_deny` + `error_type` 非空 + risk tag + `trace_completeness_score ≥ 0.7` | **是（唯一 L2 候選）** |
| ENF-RULE-2 | `would_warn` | `gate_fail_needs_review` + `high_retry` + `retry_count ≥ 2` | **否**（維持 L1） |
| C3-05-L1-INFRA-RISK-SUCCESS | `would_warn` / `[ENF-WARN]` | allow + `infra_risk` tag | **否**（維持 L1；與 RULE-1 deny path 互斥設計） |

ENF-RULE-1 的 risk tag 在程式中限定為 **`infra_risk`** 與 **`security:critical`**。第一波 blocking canary **不得**擴張到其他 tag 或新 rule，直至獨立 POLICY-SELECTION／governance 票批准。

### 3.2 第一波鎖定表（First Canary Scope）

| rule_id | risk_type（tag） | 觀測 block rate 範圍 | 誤攔正常 case 跡象 | 第一波 canary |
|---------|------------------|----------------------|--------------------|---------------|
| ENF-RULE-1 | `infra_risk` | 約 **0.5–1.5%**（窗口依賴 nightly 累積；700 筆中 ~5–7 筆為參考量級） | **目前預期為無**；尚未完成系統化 FP 抽檢 | **納入** |
| ENF-RULE-1 | `security:critical` | 約 **0–0.5%**（樣本較少，常與 infra 事故共現） | **目前預期為無**；樣本少 → 需更長觀測 | **納入**（與 infra_risk 同 rule 包，不拆票） |
| ENF-RULE-2 | `high_retry` | warn rate 高於 block rate | 不適用（非 block 候選） | **排除** |
| C3-05 | `infra_risk`（allow path） | 通常 0 或極低 warn | 故意觀測「成功但帶風險 tag」 | **排除** |

**鎖定句（給 reviewer）**：第一條 blocking canary 只針對 **「ENF-RULE-1 會 would_block 且 tags 含 infra_risk 或 security:critical 的 gate_fail_deny case」**；其餘一律維持 shadow／L1。

---

## 4. Blocking Readiness Criteria（門檻清單）

> 以下為**未來**尚書省／governance 批准 limited deny **之前**須滿足的前提。  
> **明確聲明**：截至本文件成文，這些是**門檻定義**，**不是**「已全部滿足」的事實陳述。

### 4.1 Observation window & stability

| # | 門檻 | 量化建議 | 驗證方式 |
|---|------|----------|----------|
| O-1 | **連續觀測窗口** | ≥ **14 個自然日** nightly summary 且 `status=ok` | `runs loaded` ≥ 14；無長期 skip |
| O-2 | **block rate 穩定** | 14 日窗口內 ENF-RULE-1 block rate **大多落在 0.5–2%**；無連續 3 日單邊飆升（如 >5%） | analyzer 跨日聚合 + 日線圖 |
| O-3 | **pattern 穩定** | Samples 中 ≥ **80%** would_block 的 `tags` 含 `infra_risk` 或 `security:critical`，且 `dryrun_rule=gate_fail_deny` | 人工／報表 tag 分布 |
| O-4 | **資料品質** | 每日 `total records` ≥ **30**（理想 ~100）；`status=skipped` 日佔比 < **10%** | summary JSON + CI 健康 |

### 4.2 Concentration & coverage

| # | 門檻 | 說明 |
|---|------|------|
| C-1 | **集中於目標 risk_type** | 窗口內 ENF-RULE-1 `would_block` 的 **≥95%** 落在 `infra_risk` 或 `security:critical`（其餘 tag 視為 scope 外溢，須先排除） |
| C-2 | **覆蓋率合理** | 預期 canary block 對**整體 nightly 流量**影響 ≤ **2%**（與 shadow block rate 同量級）；若 shadow 已 >3% 則**不得**進 canary |
| C-3 | **rule 邊界清晰** | ENF-RULE-2 warn 與 ENF-RULE-1 block **無大量重疊同一 task**（避免 L1/L2 雙重解讀同一 case） |

### 4.3 False positive & human review

| # | 門檻 | 量化建議 |
|---|------|----------|
| F-1 | **人工抽樣** | 至少 **20 條** would_block samples（跨多日）；其中 ≥ **85%** 在 reviewer 共識下「若 L2 生效也應 deny」 |
| F-2 | **無明顯正常 case 誤攔** | 抽樣中 **0 條**為「gate 已 pass、無 infra/security 語意、僅因 score/tag 邊界誤觸」 |
| F-3 | **require-human-override 路徑已設計** | 實作票須定義：canary 期誤攔時的**人工 override／豁免**流程（本 plan 只要求「必須存在」，不寫步驟） |

### 4.4 Governance & operational readiness

| # | 門檻 | 說明 |
|---|------|------|
| G-1 | **尚書省／governance 批文** | 獨立 limited-deny 實作票 + rollback playbook **演練記錄** |
| G-2 | **Kill-switch 設計評審** | `GOV_ENF_BLOCKING_CANARY_DISABLE`（或等價）可 **≤5 分鐘**內全局退回 preview-only |
| G-3 | **值班 runbook 更新** | shadow operations guide 的 escalation 章節已引用本 criteria；canary 期有專人 on-call |
| G-4 | **與主線 PR 隔離** | 第一波 canary **不得**預設作用於 `eval-gate`（PR/push）job |

**Go / No-Go 規則**：**全部** O/C/F/G 門檻滿足 → 可**提議**進入 Rollout Phase A；任一未滿足 → **延長 shadow**，本文件不產生 blocking 授權。

---

## 5. Rollout Strategy（Phase A / Phase B）

### 5.1 Phase A — Preview-only blocking simulation

**目的**：在**仍不 fail pipeline** 的前提下，顯式標記「若 L2 生效會 deny 的 subset」，累積 canary 專用指標，與現有 `would_block` 對照。

| 維度 | 要求 |
|------|------|
| 行為 | 對 **ENF-RULE-1 + {infra_risk, security:critical}** 子集計算 **`would_block_if_L2`**（或語意等價欄位）；**仍 exit 0** |
| 與現有 shadow 關係 | 現有 `would_block` **保留**；L2 模擬欄位為**子集或等價重標**（不擴大 rule 範圍） |
| 報表 | analyzer／summary JSON 可呈現：`would_block_if_L2`、`l2_eligible_rate`、與 `would_block` 的 **delta** |
| 觀測期 | 建議 **≥7 日** Phase A，且與 Phase 2 shadow 窗口**重疊**但不替代 O-1～O-4 |
| 成功標準 | Phase A 期間 `would_block_if_L2` rate 與 shadow block rate **偏差 <0.5 絕對百分點**；無未解釋 spike |

**報表呈現構想（plan-level）**

```
Overall
  would_block (shadow)     : N
  would_block_if_L2        : M    ← Phase A 新增
  l2_eligible_rate         : M/total_records

Per-Rule (L2 scope only)
  ENF-RULE-1 / infra_risk       : ...
  ENF-RULE-1 / security:critical: ...
```

### 5.2 Phase B — Limited blocking canary

**目的**：在**最小 blast radius** 下，讓 ENF-RULE-1 L2 **真正**影響**特定 job** 的 pass/fail。

| 維度 | 要求 |
|------|------|
| 啟用面 | **僅** `eval-shadow-nightly`（或明示的 canary workflow／branch）；**不**包含 PR `eval-gate` |
| 啟用條件 | Phase A 成功 + §4 全部門檻 + governance 批文 |
| 旗標 | `GOV_ENF_BLOCKING_CANARY=1` **且** scope 限定 ENF-RULE-1 L2 subset（不得順便開 RULE-2/C3-05） |
| 最大影響 | 單日 canary deny 筆數 **硬上限**（建議 ≤ 當日 `total records` 的 **3%** 或絕對上限 5 筆，取較嚴；由實作票參數化） |
| 失敗語意 | deny 時須有結構化 log（rule_id、task_id、tags、reason code）；**不得**靜默 fail |
| 觀測期 | 建議 **≥7 日** Phase B；每日 reviewer 簽 off 或一鍵 rollback |

**Phase 順序（不可跳級）**

```
Phase 2 shadow-only (現況)
    ↓  §4 門檻滿足
Phase A  L2 simulation (仍 exit 0)
    ↓  Phase A 成功 + governance
Phase B  limited canary (nightly only)
    ↓  穩定 + 擴面票
（未來）更廣 limited deny — 不在本 criteria 範圍
```

---

## 6. Kill-switch & Rollback Expectations

> 本節描述**未來實作票必須提供**的能力；**不包含**具體操作步驟或指令。

### 6.1 立即關閉 blocking

| 要求 | 說明 |
|------|------|
| **Primary kill-switch** | 單一 env：`GOV_ENF_BLOCKING_CANARY_DISABLE=1`（優先）或 `GOV_ENF_BLOCKING_CANARY=0`；生效後下一 run 起 **pure preview-only** |
| **Secondary kill-switch** | `GOV_ENF_ENABLE=0` 可完全跳過 ENF（已有 shadow 行為）；canary 期**優先**用 canary disable，避免連 L0 觀測一起消失 |
| **生效時間** | 配置變更後 **下一 CI run** 必須反映；不得需 redeploy 多服務才生效 |
| **可觀測** | kill-switch 觸發時 log 須印 audit 行（沿用 `[ENF] WARNING:` 模式） |

### 6.2 發現誤攔時的 rollback

| 階段 | 預期 rollback 形狀 |
|------|-------------------|
| Phase A | 無 pipeline 影響；停止 Phase A 報表欄位或標記 `[ENF] simulation_paused` 即可 |
| Phase B | **立即**設 kill-switch → 當日及後續 run 回到 exit 0；**已 fail 的 run** 由 governance 決定是否 manual rerun（本 plan 不規定） |
| 事後 | 誤攔 samples 寫入 progress／ticket；**不得**在未修 criteria 前重新開 canary |

### 6.3 Rollback playbook（實作票交付物）

未來 limited-deny 實作票須附 **one-page rollback playbook**，至少包含：

1. 誰有權拉 kill-switch  
2. 哪個 env／哪個 workflow job 要改  
3. 如何確認已回到 shadow-only（看哪條 log）  
4. 誤攔 sample 要交給誰、記在哪  
5. 重新進入 canary 的 **最低冷却期**（建議 ≥14 日 shadow 重觀測）

---

## 7. Open Questions & Risks

### 7.1 樣本與統計

| 問題 | 風險 | 緩解方向 |
|------|------|----------|
| **700 / 7 是否足夠？** | 單窗口 ~1% 可能為小樣本噪音 | 要求 O-1 **14 日+** 且累積 **≥1000** per-record 後再評估 Phase A |
| **`security:critical` 樣本偏少** | FP/FN 估計不可靠 | Phase B 可要求分 tag 報告；critical 單獨人工抽檢 |
| **nightly 常 fallback fixture** | 統計不代表 prod traffic | C-4 新增：`[SHADOW-PIPELINE] mode=fixture` 日不得計入 O-1 |

### 7.2 報表與工具缺口

| 缺口 | 影響 |
|------|------|
| analyzer **無** per-tag block rate | 難驗證 C-1 concentration |
| analyzer **無** `would_block_if_L2` | Phase A 需新欄位或 sibling 工具 |
| **無** structured FP 登記簿 | F-1 人工抽樣結果易散落 |
| Samples 上限 5 條／run | 長窗口 FP 審計可能不足 |

### 7.3 組織與流程風險

| 風險 | 說明 |
|------|------|
| **pressure to ship blocking** | shadow 1% 易被誤讀為「可以擋了」 | 本 plan 與 shadow guide 均強調：criteria 是門檻，非現狀 |
| **canary 波及 PR** | 若誤開 eval-gate，會阻斷主線 merge | G-4 硬排除 PR job |
| **L1/L2 語意混淆** | C3-05 warn 與 RULE-1 block 同見 infra_risk | 值班 training：C3-05 為 allow path only |
| **min_score=0.7 未做 sensitivity** | 0.65 vs 0.75 可能改變 block rate 倍數 | 實作票前須 shadow 掃描 threshold band |

### 7.4 是否需要額外 fixture / 回放

| 能力 | 是否需要 |
|------|----------|
| 固定 JSONL **replay**（離線重跑 RULE-1 分類） | **建議有**；用於 FP  regression，非 blocking 必要條件 |
| 合成 **edge case fixture**（boundary score、tag 組合） | **建議有**；在 Phase A 前補齊 |
| Prod traffic **重放** | Nice-to-have；nightly shadow 已覆蓋主徑 |

---

## 8. Non-Goals

本文件**明確不做**以下任何事：

| Non-goal | 說明 |
|----------|------|
| **不定義程式碼或 CI 修改方案** | 不含 patch、step 順序、exit code 實作、新檔案路徑 |
| **不宣告 blocking 啟用時點** | 無日期、無「下一 sprint 上線」 |
| **不更改現有 rule 行為或 env 語意** | ENF-RULE-1 條件、min_score、現有 `GOV_ENF_*` 解析邏輯維持不變 |
| **不擴張第一波 scope** | 不含 ENF-RULE-2 L2、C3-05 L2、新 rule、新 tag |
| **不取代尚書省裁決** | 本 plan 為 reviewer 讀物；批准 canary 須獨立批文 |
| **不修改 shadow operations guide** | 值班手冊維持 Phase 2 權威；本票僅為 planning 層 |

---

## Appendix — Reviewer 速查（30 秒版）

**第一條 blocking canary 鎖定誰？**  
→ **ENF-RULE-1**，且 tags 含 **`infra_risk`** 或 **`security:critical`** 的 `gate_fail_deny` case。

**要多長、看什麼才敢開？**  
→ **≥14 日** nightly OK；block rate **0.5–2%** 穩定；**≥95%** 集中在上述 tags；**20 條**人工抽樣 **≥85%** 認可；kill-switch + rollback playbook 就緒。

**rollout 長什麼樣？**  
→ **Phase A**：`would_block_if_L2` 模擬，仍 exit 0 → **Phase B**：僅 nightly job、canary 旗標、硬上限 → 失敗即 kill-switch 回 preview-only。

**本文件會不會現在就擋 pipeline？**  
→ **不會。** 純 plan-only；現網仍 `GOV_ENF_BLOCKING_CANARY=0`。

---

## 引用索引

| 資源 | 用途 |
|------|------|
| `docs/W5-A-RUNTIME-03-ENF-SHADOW-OPERATIONS-GUIDE.md` | 值班、escalation 原則（只讀） |
| `tools/enf_preview_wrapper.py` | ENF-RULE-1/2、C3-05 條件與 summary 形狀 |
| `tools/analyze_enf_shadow_summaries.py` | 跨 run 聚合欄位 |
| `observability/enf_config.py` | `GOV_ENF_*` 旗標語意 |
| `.github/workflows/eval-gate-ci.yml` | nightly vs PR job 分界 |
| `observability/enf-preview/README.md` | Phase A preview 層定位 |
| POLICY-MINING-01 §3.1 C-01 / C-03 / C-05 | Rule 來源 |

---

*版本：W5-A-RUNTIME-03-BLOCKING-CRITERIA-01 plan-only · 不具 blocking 授權效力 · 成文日 2026-05-31*
