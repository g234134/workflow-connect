# Agent-Run 標準線治理觀點 v2 — Wave 7 對齊

> **版本**: v2.0 治理設計稿（W7-T4 Design Convergence）  
> **票號**: W7-T4 · update-ninety-five-percent-blueprint-and-skills-wave7-v1  
> **適用**: Agent-run Standard Case Experiment Line（W6-T3~T8 + W7-T1/T2/T3）  
> **日期**: 2026-06-10  
> **上游依據**: `docs/agent-standard-line-governance-view-v1.md` · `docs/ninety-five-percent-automation-blueprint-v2.md` · W7 交付物

---

## §1 目的與 Wave 7 治理增量

### 1.1 v1 → v2 變更摘要

| 維度 | v1 | v2（Wave 7） |
|------|----|--------------|
| 支援案型 | 2（demo_phase · sampleco） | **4** preview · **2** run path |
| S7–S12 | 多數 stub/mock | **run path live**（demo bundle · sampleco stop CP-B） |
| S15 | human-only stub | **experimental simulated**（W7-T3） |
| 決策 allowlist | W5-T1 兩 profile | +2 experimental profile（decision 仍 needs_review） |
| 風險類型 | R1–R5 | **+R6–R8**（通知／跨客戶／run path 越界） |

### 1.2 本文檔目標

1. 更新 **15 步決策權矩陣**（含 run mode 覆蓋）
2. 擴充 **audit log** 清單（notify experiment · run_execution）
3. 新增 **R6–R8 風險** 與 safeguard 草案
4. 標明 Wave 8 治理升格門檻

---

## §2 決策權分佈：人類 vs Agent（v2）

### 2.1 15 步決策權矩陣

| 步驟 | 名稱 | 驅動者 | 決策者 | Wave 7 變更 |
|------|------|--------|--------|------------|
| S1 | Intake Upload | Human | **Human** | 不變 |
| S2 | Index Refresh | Script | **Auto** | 不變 |
| S3 | Decision Evaluate | Agent | **Agent** | +2 fixture → experimental needs_review |
| S4 | Checkpoint A | Agent + Human | **Human** | **run 模式可寫 state** |
| S5 | Route Planning | Script | **Auto** | 不變 |
| S6 | Tool Selection | Agent | **Auto** | 不變 |
| S7 | Gate Validation | Script | **Auto** | **run path 真執行** |
| S8 | Cleaning Execution | Script | **Auto** | **run path 真執行** |
| S9 | Outbox Write | Script | **Auto** | **run path 真寫入** |
| S10 | Bundle Build | Script | **Auto** | demo run only |
| S11 | Output Guard | Script | **Auto** | **live read**（run） |
| S12 | Checkpoint B | Agent + Human | **Human** | **W6-T6 整合 live** |
| S13 | Delivery Approval | Human | **Human** | **W8-T3 一鍵 CLI**（preview + `--confirm`） |
| S14 | Ledger Update | Script | **Auto** | partial · 未接 experiment |
| S15 | Client Notify | Script | **Agent（experimental）** | W7-T3 **simulated only** |

### 2.2 案型 × Run 模式決策覆蓋

| case_ref | preview | run（W7-T2） | Notify（W7-T3） |
|----------|---------|--------------|-----------------|
| `demo_phase` | Agent 規劃 + CP-A would_pause | Agent 執行至 bundle + live CP-B | ✅ simulated allowlist |
| `sampleco/2026-0001` | mock guard + CP-B would_trigger | Agent 執行至 CP-B stop | ✅ simulated allowlist |
| `additional_demo` | needs_review · controlled run | ✅ run → CP-B stop · `controlled_experimental` | ❌ |
| `sandbox_client` | needs_review · controlled run | ✅ run → cleaning_preview + live guard | ❌ |

**治理原則**：run 模式僅 **明確列入 `_RUN_PATH_PROFILES`** 的案型可觸發 executor side effect；其餘 allowlist case 僅 preview。

### 2.3 Agent 決策邊界（不變 + 擴充）

**仍嚴格規則驅動（無自由裁量）**：S3 · S7 · S11

**Wave 7 新增 Agent 動作（有 side effect，需 audit）**：

| 動作 | 模組 | 人工覆寫 |
|------|------|---------|
| Run path tool 執行 | `_execute_run_path_tools` | `--auto-approve-intake` 僅跳 CP-A，不跳 CP-B |
| Notify payload 生成 | `run_controlled_notify_experiment` | `dry_run=true` 預設；allowlist 閘門 |
| CP-B auto_approve | `maybe_create_checkpoint_b(auto_approve=...)` | 僅 flag；不發真 notify |

---

## §3 審計材料（v2 擴充）

### 3.1 新增 Audit 類型

| 類別 | 檔案路徑 | Wave | 保留 |
|------|----------|------|------|
| **Run execution** | orchestrator output → `run_execution.tool_results[]` | W7-T2 | 隨 regression JSON |
| **Regression artifact** | `outbox/agent_experiment_regression/{ts}_{case}.json` | W6-T8/W7 | 建議 90d |
| **Notify experiment** | `outbox/{case_ref}/notify_experiment_{ts}.json` | W7-T3 | 永久（sandbox） |
| **Live output guard** | `cases/{case}/reports/cleaning_stats.json` | W7-T2 | 永久 |

### 3.2 Notify Experiment Record 必填鍵（審計）

```json
{
  "schema_version": "controlled_notify_experiment_v1",
  "simulated": true,
  "external_dispatch": false,
  "notify_channel": "experiment_log",
  "case_ref": "demo_phase",
  "delivery_sources": { "signoff": "...", "report": "..." },
  "notify_payload": {
    "subject": "...",
    "external_dispatch": false
  }
}
```

**審計要求**：任何 S15 相關 incident 調查須先查 `external_dispatch`；若為 `true` 且無 Wave 8 批文 → **P0 違規**。

---

## §4 風險類型與 Safeguard（v2）

### 4.1 風險矩陣（v1 + v2 新增）

| 代碼 | 風險名稱 | 階段 | 影響 | Wave 7 機率 |
|------|----------|------|------|------------|
| R1 | 錯接案 | S1–S3 | 資源浪費 | 中 |
| R2 | 錯路由 | S4–S6 | 工具選錯 | 低 |
| R3 | 錯清洗 | S7–S8 | 資料損壞 | 中 |
| R4 | 錯交付 | S11–S13 | 客戶損失 | 高 |
| R5 | 狀態遺失 | S4 · S12 | 無法 resume | 低 |
| **R6** | **通知誤送（Notify Misdelivery）** | S15 | 錯誤對外訊息／資料外洩 | 低（W7 simulated） |
| **R7** | **跨客戶資料混用（Cross-Client Mix）** | S8–S15 | A 客戶 bundle 送 B 客戶 | 中（run path 擴面後↑） |
| **R8** | **Run Path 越界（Unauthorized Execution）** | S7–S10 | 未授權案型寫 outbox/改 cleaned | 低 |

### 4.2 新風險 Safeguard 草案

#### R6 — 通知誤送

| 層級 | Safeguard | 位置 |
|------|-----------|------|
| **Prevention** | `ALLOWLIST_CASE_REFS` 僅 demo/sampleco | `controlled_notify_experiment_v1` |
| **Prevention** | `external_dispatch=false` 硬編碼 + unittest | 同上 |
| **Prevention** | `sensitivity=internal` 必填 | `is_experiment_case_allowed()` |
| **Prevention** | 封鎖 `acme` / `*-prod` client_ref | 同上 |
| **Detection** | outbox record 必含 `simulated=true` | schema 斷言 |
| **Response** | Wave 8 正式 gateway 須雙閘門 env + 人工 enable | **planned W8-T4** |

#### R7 — 跨客戶資料混用

| 層級 | Safeguard | 位置 |
|------|-----------|------|
| **Prevention** | `case_ref` 由目錄解析，禁止 CLI 覆寫 | `resolve_case_ref` |
| **Prevention** | run path 使用 `outbox_root_override` 隔離 regression scratch | regression runner |
| **Prevention** | notify summary 嵌入 `client_ref` + `case_id` 雙重校驗 | `generate_client_summary` |
| **Detection** | regression artifact 含 `case_ref` + `case_dir` 對照 | JSON schema |
| **Response** | 混用 suspicion → 停 notify + 人工核對 signoff | runbook（Wave 8） |

#### R8 — Run Path 越界

| 層級 | Safeguard | 位置 |
|------|-----------|------|
| **Prevention** | 無 profile → run 不執行 executor | `_can_start_run_execution` + profile lookup |
| **Prevention** | `stop_before_delivery` 剝除 bundle tool | `_execute_run_path_tools` |
| **Detection** | unittest：`additional_demo` run 無 outbox side effect | W7 tests |
| **Response** | blocked case → `final_status=blocked` + 無 write | orchestrator |

### 4.3 Safeguard 分層總覽（更新）

```
R6 通知誤送 ──→ allowlist + simulated + dry_run 預設 ──→ Wave 8 雙閘門
R7 跨客戶混用 ──→ case_ref 解析 + scratch outbox + signoff 校驗
R8 run 越界 ──→ _RUN_PATH_PROFILES 白名單 + stop_before_delivery
R4 錯交付 ──→ CP-B live（W7）+ S13 仍 human（Wave 8 一鍵）
R1 錯接案 ──→ CP-A live + experimental profile 不 auto_accept
```

---

## §5 升級路徑治理（Wave 7 → Wave 8）

### 5.1 現況自動化（Wave 7 實測）

| 指標 | 值 |
|------|-----|
| 實驗線 auto+HITL 加權率 | **~87%** |
| S15 狀態 | experimental（不計入達標） |
| Production 主鏈 | **未改** |

### 5.2 Wave 8 升格門檻（治理 Gate）

| 升格項 | 前置條件 | 治理批准 |
|--------|---------|---------|
| S15 → auto（真 notify） | W7-T3 連續 50 次 dry-run 無 leak · 雙閘門 env 設計评审 | 尚書省 + W8-T4 |
| +2 fixture run path | decision v2 allowlist · 主鏈 regression 6/6 | W8-T1/T2 |
| S13 一鍵 approve | CP-B live 14 日無 P0 · rollback playbook | **W8-T3 done** |
| CI 納入 experiment regression | G1–G7 eval guide 全綠 | W8-T8 |
| 非 Tabular shadow | routing catalog 擴面 · 僅 shadow 不寫主鏈 | W8-T5 |

### 5.3 永不開放給 Agent（延續 v1）

| 邊界 | 原因 |
|------|------|
| DarkOps 解禁 | 憲法 §7 |
| Production config / env | 維運風險 |
| `external_dispatch=true` 無批文 | R6 |
| 新客戶 **prod** profile 首次接入 | 業務風險 |
| removal_ratio > 90% 自動放行 | 品質風險 → CP-B 強制 |

---

## §6 決策權流程圖（v2 · 含 run path）

```
[S1 Intake] Human
    │
[S3 Decision] Agent ──→ reject → STOP
    │
    ├── additional_demo/sandbox (experimental) → CP-A would_pause (preview)
    │
    └── demo/sampleco
            │
            ├── preview → mock S11 → CP-B planned
            │
            └── run (W7-T2)
                    │
                    [CP-A] Human or auto_approve
                    │
                    [S7-S10 executor] Auto (profile-bound)
                    │
                    [S11 live guard] Auto
                    │
                    [CP-B] Human (sampleco stop / demo optional)
                    │
                    [S13 W8-T3] Human (one-click CLI · confirm required)
                    │
                    [S15 W7-T3] Agent simulated (allowlist + dry_run default)
```

---

## §7 參考索引

| 文件 | 用途 |
|------|------|
| `docs/agent-standard-line-governance-view-v1.md` | v1 基線 |
| `docs/ninety-five-percent-automation-blueprint-v2.md` | S1–S15 v2 分佈 |
| `docs/skill-cards-v2.md` | Card N safeguard |
| `delivery/controlled_notify_experiment_v1.py` | R6 實作 |
| `scripts/run_agent_standard_case_experiment.py` | R8 run path |
| `docs/agent-run-experiment-eval-guide-v1.md` | G1–G7 門檻 |

---

*AGENT-STANDARD-LINE-GOVERNANCE-VIEW-v2 · W7-T4 · 2026-06-10*
