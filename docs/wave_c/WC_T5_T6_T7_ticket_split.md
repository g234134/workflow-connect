# Wave C T5/T6/T7 · 票務拆分建議（Lane C · Control Plane）

> **成文日期**：2026-06-13  
> **角色**：Orchestrator 規劃索引  
> **SSOT 交叉**：`docs/wave_c/overview.md` · 各票 `04_Workflows/tickets/*_state.md`

> **與 overview 既有票號對照**：overview 中 WC-T6＝skill distillation、WC-T7＝E2E runbook。本檔採 **Lane C 商業化閉環** 三分法（用戶指令），兩套命名 **並存**——實作時以 FRAME 標題區分子能力，禁止 silent rename。

---

## WC-T5 · Automation Coverage / Readiness Contract

| 欄位 | 內容 |
|------|------|
| **Goal** | 為 Control Plane M2 鏈建立可機器引用的 **auto / HITL / forbidden** 矩陣與驗證命令綁定；宣告 readiness（哪些路徑可本地重跑、哪些必須人工）。 |
| **Scope** | `WC_T5_automation_coverage_contract.md` 路徑矩陣 + JSON 附錄；`test_wc_t5_automation_coverage_contract_v1.py`；與 T1–T4 CLI 的 `path_id` 對齊。 |
| **NonScope** | PR required gate 授權；prod SLA；自動寫 live STATE；INT Tier-A 替代驗收。 |
| **AC** | 1) 契約 JSON 附錄與測試 `IMPLEMENTED_PATH_IDS` 1:1；2) 每條 `auto` 路徑有 `verification_command`；3) `forbidden` 含 `wc.m2.state.write_ticket` · `wc.m2.chat.open_cursor`；4) unittest 全綠。 |
| **依賴前票** | WC-T1 · WC-T2 · WC-T3 · WC-T4（路徑主體已存在） |
| **並行** | **可**與 WC-PRE/C1 Observability 軌並行；**可**與 WC-T6 閉環實作並行（契約先寫 path_id 占位） |

**現況**：契約 + 16 path 測試已落盤；本輪補 `wc.m2.loop.order_handoff` · `wc.m2.comms.order_event`。

---

## WC-T6 · Dispatch / Order / Ticket Comms 閉環

| 欄位 | 內容 |
|------|------|
| **Goal** | 單票 **接單→開單→狀態/回報** 可腳本化：eligibility + dispatch 上下文 + order intake + order-event comms，本地一條命令驗收。 |
| **Scope** | `control_plane_loop/handoff.py`；`ticket_comms/order_events.py`；`run_control_plane_order_handoff.py`；`WC_T6_control_plane_comms_loop.md`；`test_control_plane_order_handoff.py`。 |
| **NonScope** | 真支付；完整 Order 狀態機；寫 `*_state.md`；自動開 Cursor chat；REST 對外 API。 |
| **AC** | 1) ready fixture → `ok:true` + order JSONL + comms `order_created`；2) not-ready + `--skip-eligibility` → `order_rejected` comms；3) `--dry-run` 零 ledger 寫盤；4) unittest 全綠；5) T5 契約含 handoff path_id。 |
| **依賴前票** | WC-T1 · WC-T2 · WC-T4；WC-T3 建議完成（dispatch 上下文可讀 plan，v0.1 僅 bucket/role） |
| **並行** | **可**與 WC-T5 契約補 path 並行；**不可**與「自動寫 STATE」需求合併（forbidden） |

**現況**：**本輪已實作** v0.1 最小閉環（見 `WC_T6_control_plane_comms_loop.md`）。

---

## WC-T7 · External Intake / Stub / Handoff API 邊界

| 欄位 | 內容 |
|------|------|
| **Goal** | 定義 **外部請求**（web form / partner stub / CLI wrapper）進入 Control Plane 的邊界契約：請求 shape、auth 占位、handoff 回傳、與內部 `execute_order_handoff` 的映射；附 stub server 或 OpenAPI skeleton。 |
| **Scope** | 設計稿 `WC_T7_external_intake_boundary.md`；可選 `scripts/run_external_intake_stub.py`（localhost only · 無真 auth）；與現有 `run_order_intake` / `run_control_plane_order_handoff` 的 adapter 層；E2E runbook 交叉引用（overview 既有 `WC_T7_e2e_walkthrough_runbook.md` 保留）。 |
| **NonScope** | 生產 API 暴露；OAuth/Stripe；寫 live ticket STATE；multi-tenant billing。 |
| **AC** | 1) 外部請求 JSON schema + 內部 handoff dict 映射表；2) stub 接受 sample POST → 返回 `{ ok, ticket_id, order, comms_ref }`；3) 契約標 `HITL` 啟動 stub；4) unittest 覆蓋 stub happy path + validation error；5) T5 新增 `wc.m3.intake.external_stub` path。 |
| **依賴前票** | WC-T4 · **WC-T6 閉環**（handoff 編排 SSOT） |
| **並行** | **可**與 WC-PRE-06/07 治理軌並行；**可**與 Observability C1-P3+ 並行；**須**在 T6 閉環穩定後開 API 邊界 |

**現況**：規劃態；overview 內 WC-T7 E2E runbook 已存在，本票為 **外部 intake 子能力**（建議子票 `WC-T7-EXT` 或擴展 WC-T7 FRAME）。

---

## 實作優先序建議

| 順序 | 票 | 理由 |
|------|-----|------|
| 1 | **WC-T6 閉環** | 直接提升「开单→回报」；模組已齊，差編排與 order comms |
| 2 | **WC-T5 補 path** | 閉環落地後回寫契約，防回歸 |
| 3 | **WC-T7 外部邊界** | 依賴 T6 handoff；contract-first 可先做 schema |

---

*Wave C T5/T6/T7 Ticket Split · Lane C · 2026-06-13*
