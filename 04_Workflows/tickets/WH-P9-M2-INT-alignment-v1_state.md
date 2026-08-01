# WH-P9-M2-INT-alignment-v1 — Ticket State

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> **票型**：Wave-H · P9 M2 INT / 真人 HITL 對齊 · **doc-only · FRAME**  
> **父上下文**：WD-P9-T1（demo E2E runner）· WD-P9-T2（HITL fixture execute）· WC-T7（E2E runbook · accepted_with_gaps v2）· Wave-G（`p9-wc-m2-fixture-execute` advisory CI）  
> **本票不改 code / tests / CI**；僅設計與文檔對齊矩陣。

---

## FRAME

> **角色**：Wave-C / INT 對齊設計師（Orchestrator 開票 · Scribe 落盤）  
> **索引**：`docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` · `docs/phase6-int-regression-gate-contract-v1.md` · `04_Workflows/WAVE7_INT_REGRESSION_GATE_v0.1.md` · `docs/wave_c/WC_T5_automation_coverage_contract.md`

### 1. Background

#### 1.1 M2 demo skeleton 現況（P9 已交付）

Wave-D/E/G 已把 WC M2 Control Plane 鏈收斂為 **demo / 非 prod** 三種執行路徑（runbook v0.3 檔頭「執行路徑分工」）：

| 模式 | 命令要點 | 已能做什麼 |
|------|----------|------------|
| **Dry-run 編排骨架** | `--dry-run` | 預覽 §0–§5 步驟命令；可建空 `artifacts/e2e/<ticket>/`；**不寫** comms / `orders.jsonl` |
| **Manual HITL walkthrough** | `--execute`（預設） | 真人編輯 live `*_state.md`（§1/§3/§4）；跑 eligibility → dispatch cards → comms → order intake；產物限 `artifacts/e2e/` + demo 票 |
| **Demo fixture execute** | `--execute --use-hitl-fixtures` | 從 `tests/fixtures/e2e_walkthrough/` materialize HITL 快照；自動走 step 3 comms + step 4 order；**不寫** live STATE；CI advisory（Wave-G · `continue-on-error: true`） |

**驗收證據（引用，非本票重跑）**：`tests.test_run_wc_m2_e2e_walkthrough` **11/11 OK**（fixture execute 預設至 DRAFT）；加 **`--include-payment`** 時 runner step `6-payment` 可一鍵 **DRAFT→PENDING_PAYMENT→PAID**（WC-DEMO-* · sandbox only · 2026-06-24 · **25/25** payment 相關 unittest OK）。**non-claims**：sandbox happy-path **≠** prod 金流 · **≠** INT Tier-A · **≠** required CI。

**護欄（已實裝）**：僅 `WC-DEMO-*` ticket；artifacts 限 `artifacts/e2e/`；拒絕 prod 票；不寫 `artifacts/order_ledger/` 預設路徑；不啟用真金流 API。

**文檔骨架（WC-T7 v2）**：runbook 含 WC-T5 `path_id` 附錄表 A/B；文末 §INT gate 對齊為 **草稿 v0.1**（改動類型 × 推薦驗證，**非**逐步矩陣）。

#### 1.2 與 INT Tier-A / 真人 HITL 的 gap

| Gap 類型 | 現況 | 風險 |
|----------|------|------|
| **職責混淆** | runbook 已聲明「Control Plane E2E pass ≠ INT Tier-A pass」，但 **逐步** 對照表缺失 | 團隊可能把 fixture execute CI 綠燈誤讀為 INT 或 prod gate |
| **HITL 模式未制度化** | T5 定義 `wc.m2.state.write_ticket` = **forbidden**；P9-T2 fixture 僅寫 artifact 副本；**缺**「何時必須真人 HITL vs 何時可 fixture vs 何時僅 dry-run」的單頁 SSOT | Multi-Chat Reviewer/Orchestrator 無法依同一 checklist 驗收 |
| **INT 覆蓋邊界不清** | INT Tier-A 守 Wave 6/7/8 **裝配層**（envelope/manifest/QA/orchestrator/runner）；**不**覆蓋 dispatch cards / comms JSONL / order ledger 鏈 | 改 Control Plane CLI 的人可能只跑 INT、漏跑 M2 E2E；反之亦然 |
| **Tier-B 未映射** | INT Tier-B 為更重集成（Wave 8 orch + Markdown）；M2 walkthrough **無**對應行 | release checklist 缺「M2 改動是否需 Tier-B」判斷 |
| **PR CI 第三軌未對齊** | `core-agent-smoke.yml` + `eval-gate-ci.yml` **≠** INT Tier-A **≠** M2 demo E2E | 三軌 pass 語意未收斂成可審計 matrix |
| **升格路徑未定義** | Wave-G advisory 已接 fixture execute，但 **non-blocking**；缺「升格 required check / INT 綁定」的設計票入口 | 易在未批文情況下假設 merge gate 已開 |

**本票要填的洞**：在 **不改 code** 前提下，把 WC-T7 §INT gate 草稿 **升格為** 可審計的 **HITL × fixture × INT tier 對照矩陣 + runbook section**，並列出下游實作票。

---

### 2. Goal / Scope

#### 2.1 Goal（一句話）

產出 **WC M2 walkthrough 逐步對齊矩陣**（真人 HITL / demo fixture / INT Tier-A / Tier-B / PR CI），作為 Wave-C Control Plane 與 Wave 6–8 INT gate 的 **設計 SSOT**；**不修改** runner、tests、workflow。

#### 2.2 Scope（本票只做設計 & 文檔）

| 交付物 | 說明 | 建議落點 |
|--------|------|----------|
| **D1 · 對齊矩陣（主交付）** | 逐步列出 runbook §0–§5 + runner step_id；欄位見 §4 AC | 新建 `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md`（建議名）**或** WC-T7 runbook 新節「§INT / HITL 對齊矩陣 v1」 |
| **D2 · 三軌 gate 語意表** | M2 demo E2E · INT Tier-A/B · PR CI smoke 的 pass 語意、mandatory 場景、互斥聲明 | 併入 D1 或 `docs/phase6-int-regression-gate-contract-v1.md` cross-ref 段（**引用**為主，不重寫 INT contract） |
| **D3 · HITL 模式決策樹** | dry-run / manual HITL / fixture execute 選路；M2/M3 驗收 vs CI advisory vs release checklist | D1 首節或 runbook 檔頭「執行路徑分工」後追加 **決策表** |
| **D4 · 下游實作票草案** | 至少 2 張 follow-up 票 FRAME 摘要（見 §4 AC-4） | 本票 FRAME / D_REPORT |
| **D5 · 索引同步（Scribe）** | `docs/wave_c/overview.md` M2 E2E 段一句 cross-ref；Progress **末尾** append | Scribe 收口 |

#### 2.3 矩陣必須回答的問題

1. **哪些步驟必須真人 HITL**（寫 live STATE、Orchestrator 裁決、`--force-eligibility` 留痕等）？
2. **哪些步驟可 fixture 化**（P9-T2 已覆蓋 vs 仍 skeleton）？
3. **哪些步驟對應 INT Tier-A / Tier-B / 不適用**？
4. **改動類型 → 最低驗證組合**（例如：只改 `run_order_intake.py` → §5 單測 + 可選 fixture execute；改 Wave 7 orch → mandatory INT Tier-A）？

#### 2.4 AllowedPaths（本票）

- `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md`（新建 · 主 SSOT）
- `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md`（**僅**新增/修訂 §INT/HITL 對齊節；不動 §1–§6 命令正文）
- `docs/wave_c/overview.md`（一句 cross-ref）
- `04_Workflows/tickets/WH-P9-M2-INT-alignment-v1_state.md`（本票 state）
- `04_Workflows/00_Agent_Work_Progress.md`（**末尾 append** · Scribe）

#### 2.5 BlockedPaths

- `scripts/**` · `tests/**` · `.github/workflows/**`
- `core/**` · 暗部 venv 樹 · live `04_Workflows/tickets/*_state.md`（本票 state 除外）
- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md` · `.cursor/rules/**`（制度變更須 governance-guard 另票）
- `docs/phase6-int-regression-gate-contract-v1.md` **正文改寫**（僅允許「見 WC M2 對齊矩陣」級 cross-ref；INT SSOT 歸 INT contract 票）

---

### 3. Non-goals

- **不啟用**任何 production 金流、真實支付 API 或 prod order ledger 寫入。
- **不把** demo skeleton（含 fixture execute · Wave-G advisory CI）**宣稱為** prod gate、PR required check 或 INT Tier-A pass。
- **不改** `run_wc_m2_e2e_walkthrough.py`、walkthrough tests、HITL fixture 檔案或 CI workflow。
- **不升格** branch protection / mandatory CI / INT 接入 PR CI（僅在 D4 提案票中描述門檻）。
- **不取代** WC-T5 `wc_t5_paths_v0.1` JSON 附錄（本票 **引用** T5；衝突以 T5 為準）。
- **不實作** Cursor chat 開啟（`wc.m2.chat.open_cursor` 仍 forbidden）。
- **不開** CP-AUTO L3 或 WC-GOV-EXEC-ARTIFACTS-LLM 實作（僅 cross-ref）。

---

### 4. Acceptance Criteria

#### AC-1 · 對齊矩陣完整且可審計

交付 **一張主矩陣**（Markdown 表），**至少**含下列欄位：

| 欄位 | 說明 |
|------|------|
| `step` | runbook § 或 runner `step_id`（如 `0` · `2` · `3-hitl` · `3` · `4-hitl` · `4` · `5`） |
| `step_summary` | 一步話摘要（eligibility / dispatch / comms / order / unittest） |
| `wc_m2.path_id` | T5 SSOT（若適用；forbidden 行標 `wc.m2.state.write_ticket` 等） |
| `automation_tier` | T5 語意：`auto` · `HITL` · `forbidden` |
| `demo_fixture` | `none` · `partial` · `full` — fixture execute 能否替代（對照 P9-T2 三檔 fixture） |
| `real_HITL_required` | `yes` · `no` · `conditional` — M2/M3 **真人驗收**是否必須 |
| `INT_tier` | `N/A` · `A-indirect` · `A-direct` · `B` · `PR-smoke-only` — 與 INT/PR 關係（見 AC-2 定義） |
| `recommended_verification` | 可重跑命令（引用 T5 / runbook / INT gate，**不發明**新路徑） |
| `pass_means` | 該步驟 pass 的 **誠實語意**（demo 链 / 模組回歸 / 裝配不變量） |

**覆蓋下限**：runbook §0–§5 每一步至少一行；runner 三模式（dry-run / manual / fixture）在矩陣首節有 **總表**；WC-T5 附錄表 A 關鍵行 **100% 有對應矩陣行**（可合併但不可漏 `state.write_ticket` 三處）。

#### AC-2 · INT tier 欄位定義（本票須寫清）

| 值 | 含義 |
|----|------|
| `N/A` | 該步驟不在 INT gate 覆蓋範圍（Control Plane CLI 链） |
| `A-indirect` | 不直接測該步驟，但改動若觸及 Wave 6/7/8 裝配，**mandatory** 跑 `python 04_Workflows/_wave7_regression_gate.py --tier A` |
| `A-direct` | INT Tier-A 模組 **直接**守該域不變量（罕見於 M2 逐步；若無則全表可為 N/A + A-indirect 組合） |
| `B` | pre-release 建議 `--tier B`（Wave 8 orch 集成等） |
| `PR-smoke-only` | 僅 `core-agent-smoke` / `eval-gate-ci` 覆蓋；**明示 ≠ INT Tier-A** |

**必須**含 **三軌對照小表**（改動類型 × 最低驗證），擴展 WC-T7 現有 §INT gate 草稿表至少 **5 行**（Control Plane CLI · 模組單測 · Wave 6/7 裝配 · PR merge · M2 demo E2E）。

#### AC-3 · HITL 誠實邊界

文檔 **明示**（逐條可勾選）：

- Manual HITL 是 **唯一** 觸及 live `04_Workflows/tickets/*_state.md` 的 walkthrough 路徑。
- `--use-hitl-fixtures` **不**移除真人 HITL runbook；僅供 CI advisory / 本地無 HITL 煙測。
- `p9-wc-m2-fixture-execute` **non-blocking**；pass **不**代表 INT Tier-A 或 production HITL gate。
- fixture execute **預設** `order_status` 止于 **DRAFT**；加 **`--include-payment`** 可 sandbox 一鍵至 **PAID**（WC-M3 · mock adapter · **≠ prod 金流**）。**REFUNDED** 仍 optional · sandbox-only。

#### AC-4 · 下游實作票草案（至少 2 張）

本票 D_REPORT 須列出 **FRAME 摘要**（各 5–15 行），例如：

| 候選票 id | 類型 | 目的 |
|-----------|------|------|
| **WH-P9-M2-INT-gate-impl-v1**（示例） | 實作 | 將矩陣中 `A-indirect` 觸發條件接入 release checklist CLI / `_ops_cycle.py` 自檢鉤子（**仍非** PR required，除非批文） |
| **WH-P9-M2-HITL-runbook-automation-v2**（示例） | 實作 | 真人 HITL checklist 半自動化：before/after 快照 diff 提示、STATE 欄位校驗 script（**不**写 live STATE） |
| **WH-P9-M2-fixture-ci-tier-mapping-v1**（可選第三張） | CI 設計 | 評估 fixture execute 升格 advisory→required 的 G1–G8 證據模板（**blocked_on_approval**） |

每張須標：`depends_on` = 本票 · `allowed_paths` 草案 · `non_goals` 一句。

#### AC-5 · 驗證（doc-only）

- 矩陣每一行 `recommended_verification` 指向 **已存在** 命令或 SSOT 路徑（Reviewer 抽查 ≥3 行可重跑或可追溯）。
- `python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v` 仍綠（**本票不改測試**；確認 T5 引用未過期）。
- Scribe：Progress 末尾有一行索引本票 + 矩陣路徑。

#### AC-6 · 角色收口

- **Orchestrator**：凍結 FRAME · 指定矩陣落盤路徑（D1 獨立檔 vs runbook 新節）。
- **Implementer（文檔）**：撰寫 D1–D3；不觸 code。
- **Reviewer**：核對 AC-1–AC-3 無「demo pass = INT pass」表述；矩陣與 T5 forbidden 行一致。
- **Scribe**：D5 索引 + D_REPORT。

---

### 5. Dependencies

| 依賴 | 狀態 | 關係 |
|------|------|------|
| **WD-P9-T1** | done · `accepted_with_gaps` | runner 雙模式基線 |
| **WD-P9-T2** | done · `accepted_with_gaps` | fixture execute · 11 tests |
| **WC-T7 / WC-T6-T7-v2** | done · `accepted_with_gaps (v2)` | runbook v0.3 · T5 附錄 |
| **WC-T5** | done · accepted | `wc.m2.*` automation_tier SSOT |
| **Wave-G `p9-wc-m2-fixture-execute`** | done · advisory | CI 行為須寫入矩陣 |
| **INT contract + WAVE7 gate** | 現行 SSOT | Tier-A/B 定義 **引用** |
| **WC-GOV-EXEC-ARTIFACTS-LLM** | FRAME | CP-AUTO L0–L3 分轨；本票不升格 L3 |

**非阻塞**：WC-T1-INTEGRATION Reviewer 狀態；W4-MEM-01。

---

### 6. VerificationCommands（本票 · doc-only）

```bash
# Reviewer 抽查：T5 契約仍綠（確認引用路徑有效）
python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v

# Reviewer 抽查：矩陣引用的 M2 demo 命令仍與 runbook 一致（可選重跑）
python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --execute --use-hitl-fixtures --json

# Reviewer 抽查：INT Tier-A 命令與 contract 一致（gov_core venv 可用時）
python 04_Workflows/_wave7_regression_gate.py --tier A
```

---

### 7. 附錄 · 矩陣草稿（FRAME 預覽 · 實施票須展開為 AC-1 完整版）

> 以下為 **設計起點**，落盤時須補全 `recommended_verification` / `pass_means` 與 §5 單測交叉列。

| step | step_summary | wc_m2.path_id | automation_tier | demo_fixture | real_HITL_required | INT_tier |
|------|--------------|---------------|-----------------|--------------|-------------------|----------|
| §0 / `0` | 環境與隔離目錄 | — | auto | partial（dry-run 可 mkdir 空目錄） | no | N/A |
| §1 setup | 手工創建初始 STATE | `wc.m2.state.write_ticket` | forbidden | none（fixture 不寫 live） | **yes**（M2 驗收） | N/A |
| §1 預檢 | eligibility implementer | `wc.m2.eligibility.check_role` | auto | full | no | N/A · PR-smoke 部分覆蓋 |
| §2 | dispatch cards + gate | `wc.m2.dispatch.refresh_and_cards` | auto | full | conditional（`--force-eligibility` 須 HITL 留痕） | N/A |
| §3-hitl | STATE → review / reviewer | `wc.m2.state.write_ticket` | forbidden | partial（artifact 副本 only） | **yes** | N/A |
| §3 | comms JSONL | `wc.m2.comms.state_transition` | auto | **full**（P9-T2） | no | N/A |
| §4-hitl | STATE → ready_for_order | `wc.m2.state.write_ticket` | forbidden | partial | **yes** | N/A |
| §4 | order create/lookup/replay | `wc.m2.order.create` / `lookup` | auto | **full**（P9-T2） | no | N/A |
| §5 / `5` | 模組 unittest 對照 | （多 path_id） | auto | n/a（單測非 E2E） | no | A-indirect（若並改 Wave 7 裝配則 mandatory Tier-A） |
| runner | step 5 Cursor chat | `wc.m2.chat.open_cursor` | forbidden | none | yes（Multi-Chat 人工） | N/A |
| CI | fixture execute job | — | auto | full | no | N/A · **明示 ≠ INT Tier-A** |
| 改 Wave 6/7/8 裝配 | envelope/manifest/QA/orch | — | — | — | conditional | **A-direct / mandatory Tier-A** |
| pre-release | Wave 8 orch 集成 | — | — | — | optional | **B** |

---

### 8. 建議角色與工時

| 角色 | 職責 |
|------|------|
| Orchestrator | 開票 · 凍結 FRAME · 裁定 D1 獨立檔 vs runbook 合併 |
| Implementer（文檔） | 撰寫矩陣 + 決策樹 + 三軌表 |
| Reviewer | AC-1–AC-3 誠實性 · 與 T5/INT contract 一致性 |
| Scribe | overview / Progress 索引 |

**估算**：doc-only · 1–2 session（視矩陣展開深度）。

---

## STATE

- **overall_status**: `done_with_gaps`
- **current_owner**: scribe
- **next_action**: 下游實作票（§7 草案）依 Orchestrator 優先序開票；**不**升格 fixture CI 為 required
- **last_updated**: 2026-06-24 · DOCSYNC（sandbox payment 口徑同步）
- **notes**: doc-only 對齊矩陣 SSOT 已收口；sandbox happy-path DRAFT→PAID（`--include-payment`）已交付；**未**宣稱 INT gate 已接入 CI · **未**觸 prod 金流
- **status_by_role**:
  - **Orchestrator (A)**: done — D1 落盤路徑裁定：獨立檔 `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md`
  - **Implementer (B)**: done — 2026-06-22 D1–D3 + cross-ref + B_REPORT
  - **Reviewer (C)**: done — 2026-06-23 · **`accepted_with_gaps`**
  - **Scribe (D)**: done — 2026-06-23 · D_REPORT 收口

---

## B_REPORT (Implementer)

- **written_date**: 2026-06-22
- **author_role**: Wave-H Implementer (B) · doc-only
- **deliverable_path**: `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md`

### §1 變更檔案

| 檔案 | 變更 |
|------|------|
| `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md` | **新建** — 主對齊矩陣 SSOT（§1 範圍 · §2 三模式總表 · §3 決策樹 · §4 INT tier 定義 · §5 主矩陣 · §6 三軌表 · §7 下游票草案） |
| `docs/wave_c/WC_T7_e2e_walkthrough_runbook.md` | §INT gate 對齊草稿處追加 cross-ref 至新矩陣（一句） |
| `docs/wave_c/overview.md` | M2 段落追加 cross-ref 至新矩陣（一句） |
| `04_Workflows/tickets/WH-P9-M2-INT-alignment-v1_state.md` | 本 B_REPORT + STATE 更新 |

### §2 AC 覆蓋自檢

| AC | 狀態 | 證據 |
|----|------|------|
| **AC-1** 主矩陣完整可審計 | **是** | §5 主矩陣 **20 行**（§0–§5 逐步 + runner HITL/chat + CI job + Wave 6/7/8 装配 + Tier-B）；含全部必填欄位；`wc.m2.state.write_ticket` 三處（§1 setup · §3-hitl · §4-hitl）+ runner HITL 行均有對應 |
| **AC-2** INT tier 定義 + 三軌小表 | **是** | §4 INT tier 五值定義；§6 三軌對照 **7 行**（≥5 行下限）；§6.1 pass 語意防誤讀表 |
| **AC-3** HITL 誠實邊界 | **是** | §2 四条可勾选声明；§3 決策樹；§6.1 fixture ≠ INT ≠ manual HITL 明示 |
| **AC-4** 下游票草案 | **是** | §7 三张 FRAME 摘要（2 张实作 + 1 张可选 CI 设计） |
| **AC-5** doc-only 驗證 | **是** | `python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v` → **12/12 OK**（2026-06-23 Reviewer 重跑） |
| **AC-6** 角色收口 | **是** | Reviewer C + Scribe D 完成 |

### §3 skeleton / placeholder

| 項 | 狀態 |
|----|------|
| 下游實作票（§7） | **草案 only** — 未開票施工 |
| INT gate 接入 CI / release checklist | **placeholder** — 见 WH-P9-M2-INT-gate-impl-v1 提案 |
| Progress 末尾索引 | **待 Scribe (D)** |

### §4 驗證（本輪）

- Reviewer 重跑：`python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v` → **12/12 OK**
- 矩陣 `recommended_verification` 抽查 §3 comms · §5 unittest · Wave 7 Tier-A 命令 — 路徑與 runbook/INT SSOT 一致（doc-only · 未重跑 M2 runner / INT gate）

### §5 阻塞

無 blocking。

### §6 下一步

1. **Reviewer (C)**：核對 AC-1–AC-3 无「demo pass = INT pass」表述；矩阵与 T5 forbidden 行一致。
2. **Scribe (D)**：`00_Agent_Work_Progress.md` 末尾 append 本票 + 矩阵路径索引。

---

## C_REPORT (Reviewer)

- **review_date**: 2026-06-23
- **reviewer_role**: P9 M2 INT alignment Reviewer (C)
- **verdict**: **`accepted_with_gaps`**
- **scope**: `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md` · WC-T7 cross-ref · overview 索引 · AC-1–AC-3 誠實性
- **conclusion**: 主矩陣 20 行 · 三軌表 · HITL 決策樹與 T5 forbidden 行一致；**無**「demo pass = INT pass」表述。
- **verification**: `python -m unittest tests.test_wc_t5_automation_coverage_contract_v1 -v` → **12/12 OK**
- **gaps（non-blocking）**: §7 下游實作票仍草案 · INT gate 接入 CI / release checklist **未實作** · prod 金流 / 真人 HITL 全链 **未闭环**

---

## D_REPORT (Scribe)

- **handoff_date**: 2026-06-23
- **deliverable**: `docs/wave_c/WC_M2_INT_HITL_alignment_matrix_v1.md`（主 SSOT）
- **索引**: `docs/wave_c/overview.md` · `WC_T7_e2e_walkthrough_runbook.md` cross-ref 已同步
- **next_tickets**: §7 三张 FRAME 摘要（INT-gate-impl · HITL-runbook-automation-v2 · fixture-ci-tier-mapping 可選）

**P9 sandbox payment closure 票索引（2026-06-24 同步）**

| 票 id | 狀態（2026-06-24） | 類型 |
|-------|-------------------|------|
| `WH-P9-PROD-payment-closure-bootstrap-v1` | `design_accepted` | bootstrap/gov · WC-M3 scope SSOT |
| `WH-P9-PROD-order-status-transition-impl-v1` | `implementer_done_pending_review` | impl · DRAFT→PAID 狀態機 |
| `WH-P9-PROD-payment-sandbox-adapter-v1` | `implementer_done_pending_review` | impl · mock provider |
| `WH-P9-PROD-payment-happy-path-execute-v1` | **`done_with_gaps`** | execute · sandbox happy-path + 戰報 |
| `WH-P9-M2-runner-step6-payment-v1` | **`done_with_gaps`** | runner `step_id=6-payment` · **`--include-payment`** |
| `WH-P9-WC-T7-runbook-payment-section-v1` | **`done_with_gaps`** | WC-T7 runbook §4+ payment 正文 |
| `WH-P9-CI-payment-sandbox-smoke-v1` | `frame_ready` | advisory CI smoke 设计（**未施工**） |
| `WH-P9-PROD-real-provider-v1` | **`blocked`** | prod 真实 provider · **等待尚书省批文** |

**sandbox 已交付**：WC-DEMO-* · DRAFT→PAID · runner **`--include-payment`** 一鍵 walkthrough OK · runbook §4+ 完整。**仍 non-claims**：非 prod 金流 · 非真 provider · 非 INT Tier-A · 非 required CI。
- **explicit_non_claims**: demo fixture execute · Wave-G advisory CI **≠** INT Tier-A · **≠** prod 金流 gate
- **Progress**: 本輪未 append `00_Agent_Work_Progress.md`（任務邊界）；Scribe 可另輪 append

#### 2026-06-24 · payment sandbox 補記

- **happy-path execution 現況**：`WH-P9-PROD-payment-happy-path-execute-v1` 已 **`done_with_gaps`**（2026-06-24 · Reviewer `accepted_with_gaps`）。在 **sandbox only** 護欄下（僅 `WC-DEMO-*` · `artifacts/e2e/<ticket>/` 隔離），**DRAFT→PENDING_PAYMENT→PAID** 可重跑；`Progress` 已有 2026-06-24 戰報；unittest **25/25 OK**。
- **runner step 6 現況**：`WH-P9-M2-runner-step6-payment-v1` 已 **`done_with_gaps`** — M2 runner 内建 `step_id=6-payment`；fixture execute 加 **`--include-payment`** 可一鍵至 **PAID**（无需手工 transition/pay CLI）。
- **runbook §4+ 現況**：`WH-P9-WC-T7-runbook-payment-section-v1` 已 **`done_with_gaps`** — `WC_T7_e2e_walkthrough_runbook.md` §4+ payment 可复制正文已落盘。
- **與本 alignment 票關係**：alignment matrix §4+ 行与 AC-3 已同步为「**默认 DRAFT · `--include-payment` 可 sandbox PAID**」；**仍属 demo / sandbox 链**，未改本票 doc-only 邊界，亦未升格 INT gate 或 prod closure。
- **下游票状态（2026-06-24 DOCSYNC）**：

  | 票 id | 狀態 | 角色 |
  |-------|------|------|
  | `WH-P9-M2-runner-step6-payment-v1` | **`done_with_gaps`** | runner `step_id=6-payment` · **`--include-payment`** 一鍵 DRAFT→PAID |
  | `WH-P9-WC-T7-runbook-payment-section-v1` | **`done_with_gaps`** | WC-T7 runbook §4+ payment 可复制正文 |
  | `WH-P9-CI-payment-sandbox-smoke-v1` | `frame_ready` | advisory · non-blocking CI smoke 设计（**未施工**） |
  | `WH-P9-PROD-real-provider-v1` | **`blocked`** | prod 真实 provider / prod ledger · **等待尚书省批文** |

- **派工順序（sandbox 线）**：happy-path execute ✅ · runner step 6 ✅ · runbook §4+ ✅ → CI smoke（**待施工**）；prod provider **另轨 · 批文前不得施工**。
- **explicit non-claims（仍有效）**：
  - sandbox happy-path **≠ prod 金流** · **≠ INT Tier-A pass** · **≠ PR required / merge-blocking CI**；
  - `--use-hitl-fixtures` + payment CLI **≠** 真人 HITL 全链 · **≠** 真 payment provider；
  - Wave-G `p9-wc-m2-fixture-execute` advisory CI **仍不覆盖** payment 步（默认无 `--include-payment`）；payment CI 待 `WH-P9-CI-payment-sandbox-smoke-v1`（**frame_ready · 未施工**）。
- **D_REPORT 口徑修正**：2026-06-23 段「`WH-P9-PROD-payment-happy-path-execute-v1` = `frame_ready`」** superseded ** — 以本補記與該票 2026-06-24 STATE / B_REPORT 為準。

#### Reviewer 提示 · P9 payment 可信度（2026-06-24）

- **可信**：sandbox happy-path（`WC-DEMO-*` · DRAFT→PAID · runner **`--include-payment`** · mock adapter · 25/25 tests · Progress 战报）已可审计重跑；**不可信 / 未交付**：prod 金流、真 provider、prod ledger、INT Tier-A、required CI — prod 线 **`WH-P9-PROD-real-provider-v1` 仍 blocked（等待尚书省批文）**。
- **下次审 P9 payment 时优先看两类票**：（1）**sandbox 收编** ✅ 已完成：`WH-P9-M2-runner-step6-payment-v1` + `WH-P9-WC-T7-runbook-payment-section-v1` — 核查 non-claims 仍诚实；（2）**prod 升格 gate**：`WH-P9-PROD-real-provider-v1` — 无批文不得施工；有批文时查 sandbox/prod 分轨、env gate default off、无 secret 泄露。
- **勿误读**：sandbox `done_with_gaps` **≠** WC-M3 prod closure **≠** INT Tier-A；`WH-P9-CI-payment-sandbox-smoke-v1` 即使落地也须保持 advisory · non-blocking。
