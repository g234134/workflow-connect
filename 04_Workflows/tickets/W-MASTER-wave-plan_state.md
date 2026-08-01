# W-MASTER-wave-plan — Wave Master Control Plane State

> **handoff 摘要檔** · Wave Master Orchestrator 總調度 · **doc-only · 非功能施工票**。  
> **目的**：將 repo 內**所有未完成工作**整理成可供 Multi-Chat（Chat 1–5）讀取與執行的**總控制平面**；提升工作流完整度與功能性；**不做微優化**；**不重做**已達 80% 且無關鍵缺口的 Phase。  
> **本票不交付功能、不開 Wave 1–5 具體子票**（子票由後續 Wave Planner chat 依本 FRAME 產出）。

---

## META

| 欄位 | 值 |
|------|-----|
| **Phase** | Global · Wave Master planning |
| **Lane** | Master control plane · Multi-Chat 編排 |
| **Owner** | Wave Master Orchestrator |
| **Ticket type** | orchestration · frame · non-functional |
| **Parent context** | `docs/WAVE_PROGRESS_DASHBOARD.md`（06-23 Phase% SSOT）· `W-ORCH-wave-next-control-plane-v1`（Wave-next 戰術編排）· `04_Workflows/plans/multi-phase-80-percent-execution-plan.md` |
| **Playbook SSOT** | `docs/wave-master-ticketing-playbook.md` |
| **Multi-Chat 角色** | `.cursor/rules/multi_chat_roles.mdc` · `docs/phase4-multi-agent-collaboration-contract-v1.md` |

---

## FRAME

### Objective

建立 **Wave Master 總任務框架**，使後續 Chat 1–5（Wave Planner）能在**統一邊界**下：

1. 盤點各自 Wave 區塊內的**關鍵缺口**（非微優化）。
2. 產出 **1–2 個開發循環可完成**的子票（每票可經 B/C/D/O 落地）。
3. 保留 **human-only / infra-only / security-only** 前置的誠實標註。
4. 由 Master Reviewer 依 **Review protocol** 驗收整體 Wave 規劃（非功能驗收）。

**成功判準（本票）**：本 state + playbook 已就緒；Wave 1–5 **ownership 表**與 **shared ticket schema** 已凍結；**Ready-for-parallelization checklist** 全勾可開 Chat 1–5；**尚未**填寫 Wave 1–5 具體 ticket 清單。

---

### Current Baseline

> **Phase% 權威**：`docs/WAVE_PROGRESS_DASHBOARD.md`（2026-06-23 基準；06-24/25 敘事增量見 Dashboard §Wave-next 敘事刷新）。**本票不重算 Phase%。**

#### Phase 完成度快照（規劃用 · 非驗收證據）

| Phase | 當前 % | 規劃姿態 | 關鍵缺口摘要（僅列 blocking / 80% 邊界項） |
|-------|--------|----------|---------------------------------------------|
| **P7** 自動客戶溝通 | **68%** | **補缺口** | Round-2 staging **`blocked`**（governance_dual · Infra slot · Security POST · allowlist · receiver）；sandbox ~90% · prod phase-1 ~54% |
| **P7.5** Intake Gate | **81%** | **>80% · 只補關鍵** | UI / SLO / alert 未做；矩陣 G-1–G-5 resume 測試缺口 |
| **P8** 商業化交付 | **80%** | **>80% · 只補關鍵** | batch approve / resume-latest / webhook **deferred** |
| **P8.5** Browser / CU | **83%** | **補 human-blocked** | Scenario2 GA **未跑** · closure-scribe **`blocked`** · bridge in-memory stub |
| **P8.9** Outbox / Feedback | **81%** | **>80% · 只補關鍵** | HTTP webhook = T4 deferred；INT/real provider 未接 |
| **P9** 訂單 / 金流 | **60%** | **補缺口** | GitHub 首跑 URL 未回填 · prod provider / ledger gap · advisory CI ≠ required |
| **P10** 95% 自動化 | **48%** | **補缺口** | S15 notify / intake API / prod 閉環 gap |
| **P10.5** 學習 / 蒸餾 | **32%** | **補缺口** | 无 prod 蒸馏闭环 · skeleton 為主 |

#### 已達 80%+ 且**無關鍵 blocking 缺口**（本輪 Wave 規劃 **不重做**）

P1 (92%) · P2 (82%) · P3 (95%) · P4 (85%) · P5 (87%) · P6 (90%) · P8.6–P8.8 (82–85%) — 僅允許 **doc 索引 / cross-ref** 級別更新，**禁止**重開大工程或 Phase% 拉升。

#### 既有編排資產（下游須引用 · 不取代）

| 資產 | 路徑 | 用途 |
|------|------|------|
| Wave-next 戰術 control plane | `04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md` | P7/P8.5/P9 並行 lane · 第二/三輪收口 |
| Phase% Dashboard | `docs/WAVE_PROGRESS_DASHBOARD.md` | 唯一 Phase% SSOT |
| Ticket state 機制 | `04_Workflows/tickets/README.md` · `_templates/ticket_state.template.md` | 子票格式 |
| Reviewer checklist | `04_Workflows/review_checklists/wave-next-code-inspector-v1.md` | over-claim 攔截模板 |
| 80% 整合計畫 | `04_Workflows/plans/multi-phase-80-percent-execution-plan.md` | 跨 Phase 依賴參考 |

#### 已知 global blocked（不可包裝成 AI 已完成）

1. **P7 Round-2** — human: governance_dual 批文 · Infra staging slot · Security POST · allowlist · receiver。
2. **P8.5 Scenario2 GA** — human/ops: Actions `scenario=scenario2` dispatch + run URL。
3. **P9 CI 首跑** — human: push + `workflow_dispatch` + run URL 回填。
4. **WC-PRE-06/07 · WC-IMPL-L2** — 尚書省批文前不得改 required CI / branch protection。

---

### Planning Rules

1. **Scope 凍結**：Wave Planner chat **只寫**本 Wave 區塊（見 §Wave ownership table）；**不得**改其他 Wave 的 ticket ID 或 FRAME。
2. **Ticket 粒度**：每張子票必須 **1–2 個開發循環**（O→B→C→D 一輪或 B↔C 一輪 + D）可完成；超 scope 須拆票。
3. **MVP 允許**：可交付 MVP，但 **B_REPORT.verification** 須誠實；skeleton / placeholder 須分欄（合約 Rule 7）。
4. **Evidence-first**：無 runner / 命令輸出 / run URL **不得**宣稱完成（合約 Rule 11）。
5. **Path 權威**：路徑見 `Master_Map.json` · 禁硬編磁碟路徑（Rule 6）。
6. **Progress 寫入**：僅 **末尾 append**（憲法 §6.2）；Scribe lane 或授權 Governance。
7. **Phase%**：Wave Planner **不得**單方面上調 Dashboard Phase% 數字。
8. **ID 命名**：`<WAVE#>-<DOMAIN>-<slug>-v1`（例：`W2-P7-staging-unblock-frame-v1`）；**不得**挪用他 Wave 前綴。
9. **歷史保留**：更新 state 時 **追加** REPORT 段，不刪除歷史。
10. **開票入口**：Orchestrator 複製 `_templates/ticket_state.template.md`；FRAME 必須含 shared schema 擴展欄（見 §Shared ticket schema）。

---

### B/C/D/O Enforcement Rule

> **票級落地循環**（每張子票必須可走完）；與 Multi-Chat 四角色 **映射但不等同**。

| 階段 | 全名 | 產出 | Multi-Chat 映射 | 關卡 |
|------|------|------|-----------------|------|
| **B** | **Build spec** | FRAME 凍結 · AC · Allowed/Blocked paths · 依賴/風險/observability 欄 | **Orchestrator (O)** 開票 | 無 FRAME 不得進 C |
| **C** | **Code or Config** | 實作 diff · **B_REPORT**（`changed_files` + `verification`） | **Implementer (B-*)** | AllowedPaths 外禁止 |
| **D** | **Debug or Verify** | **C_REPORT** · 可 loop back C | **Reviewer (C)** | `needs_changes` → 回 C；**不得**跳過 |
| **O** | **Observe or Trace** | **D_REPORT** · Progress 末尾 · STATE 關票 | **Scribe (D)** + **Orchestrator** 更新 STATE | 無 C=`accepted*` 不得 O 關票 |

**強制規則**

- 每張 ticket **must** 可標示目前處於 B / C / D / O 哪一階；STATE 建議加 `lifecycle_phase`（見 shared schema）。
- **禁止** Implementer 自標 `done`；**禁止** Orchestrator 無 C_REPORT 關票。
- **禁止** 以 chat 口述代替 B/C/D_REPORT 寫檔。
- **O 階**須留 observability 證據：命令、run id、metrics 欄位或 **明確標 human-only**。

---

### Priority Heuristic

**優先補關鍵能力，不做微優化。** 排序（同 Wave 內自上而下）：

1. **Blocking** — 阻斷下游 Wave 或 human 前置已齊但缺執行證據（例：P8.5 run URL · P9 首跑 URL）。
2. **Cross-wave glue** — 斷裂的 workflow 接線（smoke / notify / dispatch registry 未串）。
3. **80% 邊界關鍵缺口** — Phase 已 ≥80% 但 AC 明列的 **最後一個** runtime 能力（非 polish）。
4. **Observability / doc SSOT** — 僅當阻斷 Planner 或 Reviewer 盤點時。
5. **Deferred / nice-to-have** — 預設 **不開票**，除非尚書省明示。

**反模式（禁止開票）**：lint/format · 重命名 · 無 AC 的 refactor · 「提高 Phase%」本身 · 已 validated 能力的重寫。

---

### Phase >80% Handling Rule

| 條件 | 允許 | 禁止 |
|------|------|------|
| Phase **≥80%** 且 Dashboard / 子票 **無 blocking gap** | doc 索引 · cross-ref · Progress 敘事 | 重開大工程 · 架構重做 · 新 mandatory CI |
| Phase **≥80%** 且有 **明確 AC 缺口**（如 P7.5 UI、P8 batch） | **單票** 只補該 AC · MVP 可 | 連帶重寫已 accepted 模組 |
| Phase **<80%** | 依 Priority heuristic 開票 | 一次票包打整 Phase |

**判定 SSOT**：`docs/WAVE_PROGRESS_DASHBOARD.md` 該 Phase 列 + 對應 `*_state.md` `overall_status` / C_REPORT。

---

### Shared Ticket Schema

> 基於 `04_Workflows/tickets/_templates/ticket_state.template.md`；Wave Master 子票 **must** 在 FRAME 追加下列欄位（YAML 或 bullet 均可）。

#### FRAME 必填（標準 + 擴展）

```yaml
Goal: ""              # 一句話 · 可驗收
Scope: []             # MUST 條目
NonScope: []          # 明確不做
AllowedPaths: []      # repo 相對路徑
BlockedPaths: []      # 含憲法 §7 類型引用
Dependencies: []      # 票 ID / human 前置 / 子系統
AcceptanceCriteria: [] # 可執行判定

# --- Wave Master 擴展（必填）---
wave_id: W1|W2|W3|W4|W5
lifecycle_phase: B|C|D|O
phase_targets: []       # 如 P7.5 — 僅引用 Dashboard 名稱
estimated_cycles: 1|2   # 開發循環數上限
mvp_allowed: true|false
human_only_prereqs: []  # 空或列具體負責方 · 不可留空卻隱含 human 已做
infra_only_prereqs: []
security_only_prereqs: []
dependencies_detail:    # 見 playbook §依賴欄位
  upstream_tickets: []
  downstream_waves: []
  blocks_if_missing: []
risks: []               # 見 playbook §風險欄位
observability:          # 見 playbook §observability 欄位
  verify_commands: []
  evidence_artifacts: []
  trace_fields: []      # run_id / metrics keys / log paths（邏輯名）
  success_signals: []
  failure_signals: []
non_claims: []          # 本票禁止宣稱的能力
```

#### STATE 建議欄位

```yaml
overall_status: draft|frame_ready|in_progress|review|scribe|done|blocked|done_with_gaps
lifecycle_phase: B|C|D|O
current_owner: orchestrator|implementer|reviewer|scribe
next_action: ""
last_updated: YYYY-MM-DD
status_by_role: { orchestrator, implementer, reviewer, scribe }
```

#### B/C/D_REPORT

維持 template 結構；**B_REPORT.verification** 必須可重跑；**C_REPORT.checks_summary** 須對照 AC 逐條。

---

### Wave Ownership Table（Wave 1–5）

> **Chat N = Wave N Planner**（只讀全檔 · **只寫** `## Wave N` 區塊 · 見 playbook）。  
> 下列為 **規劃所有權**，不是完成宣告。

| Wave | Chat | 主責 Phase / 域 | 規劃焦點（關鍵能力 · 非微優化） | 典型 blocked / human |
|------|------|-----------------|----------------------------------|----------------------|
| **Wave 1** | Chat 1 | **P7.5 上游功能缺口** | **active 票**：`W1-P75-POLICY-DENY-MVP-v1` · `W1-P75-INTAKE-CLI-MVP-v1` · `W1-P75-TRACE-UPSTREAM-v1` · `W1-P75-UPSTREAM-ENTRY-INDEX-v1`（policy deny · intake CLI · gate→outbox→smoke trace · 入口索引）· **只消費** Wave 5 Master CP schema/commands · **不維護** 模板 SSOT | 無 |
| **Wave 2** | Chat 2 | **P7** · staging 解阻 · HITL matrix | Round-2 **五頂解阻 spec**（W2-T1–T5 · 非 execute）· **規劃承接** G-1–G-5 resume-loop **spec / trace contract**（`W2-P7-matrix-G1-G5-resume-loop-v1` · spec-only）· **規劃承接** P7 advisory CI 誠實索引 | **human** governance_dual · Infra · Security · allowlist · receiver |
| **Wave 3** | Chat 3 | **P8** · **P8.9** · Operator / Outbox | Operator backlog 關鍵 deferred · dispatch registry 與 delivery 接線 · verification bundle 回歸 · P8/P8.9 advisory CI SSOT · **不**做 webhook T4 除非明示 | Governance 對 batch/webhook 裁定 |
| **Wave 4** | Chat 4 | **P8.5** · **P9** · Browser / Payment | Scenario2 GA **證據鏈** · payment sandbox CI 首跑回填 · order ledger prod gap 盤點 · M2 e2e 接線 | **human/ops** GA dispatch · CI workflow_dispatch |
| **Wave 5** | Chat 5 | **Master CP SSOT** · cross-wave observability · **P10 編排資產** | **Master CP 骨架（active）**：`W5-T2` ticket schema 模板 · `W5-T1` Multi-Chat `.cursor/commands` · `W5-T5` lane/playbook 索引 · instruction 擴展（併入 W5-T2/W5-T4）· evidence observer（W5-T3）· Master Plan Review checklist（W5-T4）· **WC-PRE-06/07 批文/設計 doc-only** | 尚書省 CI required 批文 · WC-PRE-06/07 |

#### Wave 1 / Wave 5 去重裁定（2026-06-26 Master Review B-1 · **第三輪 Orchestrator 裁定 · 方案 A** · **不改既有票 FRAME**）

> **裁定（方案 A · RB-1）**：**Wave 5 = Master CP 骨架 SSOT**（schema · commands · lane index · instruction）；**Wave 1 = P7.5 上游功能缺口專線**（四張 `W1-P75-*` active 票）。Wave 1 **只消費、不維護** Master CP 模板；Implementer **不得**在 Wave 1 與 Wave 5 雙份落地同 capability。

| Capability | 權威 Wave | Wave 5 active 票（SSOT） | Wave 1 姿態 | 不再負責 |
|------------|-----------|--------------------------|-------------|----------|
| `ticket_state.template` schema 模板 | **W5** | **W5-T2-wave-master-ticket-template-v1** | 只消費 · 不維護 | Wave 1 **不再負責** schema 主版本（~~W1-T1~~ 已刪） |
| Multi-Chat `.cursor/commands` | **W5** | **W5-T1-multi-chat-commands-v1** | 只消費 · 不維護 | Wave 1 **不再負責** commands 主版本（~~W1-T2~~ 已刪） |
| 四角色 instruction 模板 | **W5** | **W5-T2**（instruction 擴展欄）+ **W5-T4**（reviewer 附页） | 只消費 · 不維護 | Wave 1 **不再負責** instruction 層（~~W1-T4~~ 已刪） |
| 雙 control-plane lane / playbook 索引 | **W5** | **W5-T5-cross-wave-playbook-index-v1** | 只消費 trace/entry cross-ref | Wave 1 **不再負責** lane index / 全 Wave rollup（~~W1-T3~~ 已刪） |
| P7.5 gate trace（上游） | **W1** | W5-T3 消費 trace 欄位 | **W1-P75-TRACE-UPSTREAM-v1**（evolve ~~W1-T5~~） | Wave 1 **不**負責 G-1–G-5 resume-loop **runtime** · notify 接線 |
| P7.5 policy deny / intake CLI | **W1** | — | **W1-P75-POLICY-DENY-MVP-v1** · **W1-P75-INTAKE-CLI-MVP-v1** · **W1-P75-UPSTREAM-ENTRY-INDEX-v1** | Wave 5 **不**施工 P7.5 功能缺口 |
| Evidence observer / Master Review checklist | **W5** | W5-T3 · W5-T4 | — | Wave 5 **不**負責 P10 **runtime**（S15 notify · intake API · prod 閉環） |
| WC-PRE-06/07 批文/設計 | **W5** | **W5-WC-PRE-06** · **W5-WC-PRE-07**（doc-only · design_ready） | — | Wave 5 **不**做 required CI 升格 · **不**改 branch protection · **不** claim approved |

**Wave 1 不再負責（本 Master Plan）**：Master CP skeleton / template / Multi-Chat commands / lane index / instruction 主版本 — **全部歸 Wave 5**（W5-T1/T2/T5）；G-1–G-5 resume-loop **runtime** 歸 **Wave 2** `W2-P7-matrix-G1-G5-resume-loop-v1` 或 P75-G\* 線。

**Wave 5 不再負責（本 Master Plan）**：P7.5 功能缺口（policy deny · intake CLI · gate trace 主施工 — 歸 Wave 1 `W1-P75-*`）；P10/P10.5 **runtime** 自動化閉環 — 本輪 Wave 5 為 **Master CP + 編排/觀測/治理設計** 資產。

#### Wave 2 規劃缺口（2026-06-26 Master Review B-2/B-3 · **下一輪 Chat 2 補票 · 本輪不改 W2-T1–T5**）

| 缺口 | ownership 歸屬 | 與 W1-P75-TRACE 關係 | 狀態 |
|------|----------------|----------------------|------|
| G-1–G-5 resume-loop spec / trace contract | **Wave 2** | **W1-P75-TRACE-UPSTREAM-v1** 只做上游觀測 trace；matrix **spec-only** 由 W2 新票承接 | **planned · Chat 2 第二輪已補** `W2-P7-matrix-G1-G5-resume-loop-v1` |
| P7 advisory CI 誠實索引 | **Wave 2** | 與 Wave 3 P8/P8.9 advisory 分線；`p7-notification-smoke.yml` 歸 P7 | **planned · Chat 2 第二輪已補** `W2-P7-advisory-ci-ssot-index-v1` |
| notify transport 接線 | **本 Master Plan 外 defer** | W3 依既有 P75 gateway/outbox（P75-G2/G4） | **不在 W2 現有票**；見 §Cross-Wave Dependencies |

#### Wave 區塊寫入位置（Planner 產出區 · 預留）

<!-- Wave Planner chats append planned tickets below. Do NOT fill in Master Orchestrator pass. -->

## Wave 1 — Planned Tickets

> **Planner**：Chat 1 · Wave 1 · **第二輪修正**（2026-06-26）  
> **焦點**：P7.5 **上游** — policy deny 路徑 · intake CLI 完整度 · gate→outbox→smoke **trace 契約**（doc/MVP · 非 full gate · 非 prod-ready）  
> **去重**：模板 / commands / instruction / 全 Wave rollup 索引 → **Wave 5**（W5-T1/T2/T5）；本 Wave **不**再開 Master CP 主施工票  
> **規劃日期**：2026-06-26 · **不施工** · **不調 Phase%** · **不涉及 CI/GA/staging 真執行**

### 摘要表

| Ticket ID | 目的（一行） | lifecycle_phase | phase_targets | estimated_cycles | blocked / human |
|-----------|--------------|-----------------|---------------|------------------|-----------------|
| **W1-P75-POLICY-DENY-MVP-v1** | policy deny 路徑 doc + 最小 runtime 探針（phi_demo · reason_code trace） | B | P7.5 | 1 | 无 |
| **W1-P75-INTAKE-CLI-MVP-v1** | intake CLI 完整度 doc + 最小上游接線（case 建立 → gate CLI） | B | P7.5 | 1 | 无 |
| **W1-P75-TRACE-UPSTREAM-v1** | gate→outbox→MP-SMOKE→metrics **上游 trace** 契約（doc-only · G-1–G-5 僅觀測欄） | B | P7.5 | 1 | 无 |
| **W1-P75-UPSTREAM-ENTRY-INDEX-v1** | P7.5 上游入口索引（gate CLI · policy YAML · intake CLI · trace doc） | B | P7.5 | 1 | 无 |

### Removed / merged（第二輪 · 對照 Reviewer）

| 原票 ID | 處置 | 承接 Wave / 票 |
|---------|------|----------------|
| **W1-T1** | **刪除**（defer 主施工） | **W5-T2-wave-master-ticket-template-v1**（schema 模板 + Reviewer 附页） |
| **W1-T2** | **刪除**（defer 主施工） | **W5-T1-multi-chat-commands-v1**（`.cursor/commands` 四角色 + Wave Master slash） |
| **W1-T3** | **刪除**（全 Wave rollup 部分 defer） | **W5-T5-cross-wave-playbook-index-v1**（Wave Master / Wave-next / skill 匯整） |
| **W1-T4** | **刪除**（defer 主施工） | **W5-T2**（instruction 擴展欄 + `ticket_reviewer_checklist.template.md`） |
| **W1-T5** | **合併/evolve** | **W1-P75-TRACE-UPSTREAM-v1**（保留 trace 契約 · 明示 G-1–G-5 僅上游觀測） |

> **B-1 / RB-1 對齊（方案 A）**：Master CP 骨架 SSOT = **Wave 5**（W5-T1/T2/T5）；Wave 1 僅 P7.5 上游四票 · **只消費、不維護** 模板/commands/index。

---

### W1-P75-POLICY-DENY-MVP-v1 — Policy Deny Path Doc + Minimal Runtime Probe

- **Title**：P7.5 policy deny 路徑 doc/MVP（reason_code · phi_demo 探針 · trace 欄位）
- **Goal**：補 P7.5 **policy deny** 上游可審計鏈：從 `intake_gate_policy_v1.yaml` → gate layer merge → MC-SMOKE `phi_demo` 探針 → `intake.gate_decision` trace 欄位；Reviewer 可不跑 staging 即判斷 deny 路徑是否 fail-closed 且可追蹤。
- **Scope**：
  - 新建 `docs/p75-policy-deny-path-mvp-v1.md`：deny `reason_code` 枚舉 · layer merge 規則（policy deny escalates v2 accept）· `phi_demo` / golden `deny_*.json` 對照表
  - 最小 runtime MVP（擇一或組合，**MVP 級**）：強化 `tests/test_intake_gate_policy_integration_v1.py` 或 MC-SMOKE 文檔化 `phi_demo` 預期 `trace_fields`（**不**擴 full gate 功能）
  - cross-ref：`P75-G3` · `routing/intake_gate_policy_v1.yaml` · `MC-SMOKE` `phi_demo` 行 · Dashboard §representative cases
  - `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7 加 **Policy deny upstream** 小節 cross-ref（doc-only）
- **Non-Goals**：
  - **不**重做 P75-G3 policy loader/evaluator（已 `implemented`）
  - **不**做 G-1–G-5 resume-loop **runtime**（留 Wave 2 `W2-P7-MATRIX-G1-G5-resume-loop-v1`）
  - **不**宣稱 prod-ready / full gate / staging POST · **不**拉升 P7.5 Phase%
- **Acceptance Criteria**：
  - AC-1：deny path doc 列 ≥4 個 deny golden fixture 與對應 `reason_code`
  - AC-2：doc 明示 `phi_demo` → gate `reject` → 下游 smoke fail-closed 預期（對齊 MC-SMOKE built-in table）
  - AC-3：trace doc 列出 deny 路徑至少 3 個 `trace_fields`（含 `intake.gate_decision` 或等價鍵）
  - AC-4：non-claims 含「MVP doc/probe ≠ full gate ≠ prod deny SLA」
- **Dependencies**：
  - `P75-G3-intake-gate-policy-allowlist-denylist-v1_state.md`（上游 · implemented）
  - `MC-SMOKE-multi-case-smoke-runner-v1_state.md` · `tests/golden/intake_gate_policy/deny_*.json`
  - downstream：**W1-P75-TRACE-UPSTREAM-v1** 消費 deny trace 欄位
- **Observability**：
  - verify_commands：
    - `python -m unittest tests.test_intake_gate_policy_integration_v1 -v`
    - `python scripts/run_multi_case_smoke_v1.py --cases phi_demo --format json`（文檔引用 · deny 探針）
    - `rg "reason_code|phi_demo|policy deny" docs/p75-policy-deny-path-mvp-v1.md`
  - evidence_artifacts：deny path doc · 可選 B_REPORT unittest 輸出 · matrix §7 cross-ref
  - trace_fields：`intake.gate_decision` · `reason_codes[]` · `gate_checks[]` · `multi_case_smoke_run.cases[].gate_status`
  - success_signals：Reviewer 紙面 traversal deny 路徑無斷點
  - failure_signals：doc 宣稱 deny 已 staging 驗收；缺 failure_signals 節
- **Risks / Edge Cases**：
  - RSK-W1-P75-DENY-01：`phi_demo` ephemeral fixture 與持久 case 混淆 → mitigation：doc 標 ephemeral + release pass 排除；residual：accept
  - RSK-W1-P75-DENY-02：與 W1-P75-TRACE 重疊 → mitigation：本票 focus deny 語意；trace 鏈由 TRACE 票 SSOT；residual：accept
- **Output Artifact**：`docs/p75-policy-deny-path-mvp-v1.md` · matrix §7 增量 · 可選 unittest 增量
- **B/C/D/O Landing Plan**：
  - **Build spec**：FRAME 列 deny golden 清單 + AllowedPaths `docs/**` · `tests/**`（最小）
  - **Code-Config**：Implementer 寫 doc + 可選 probe 測試；B_REPORT verification
  - **Debug-Verify**：Reviewer 對照 P75-G3 AC 與 doc 一致性
  - **Observe-Trace**：Scribe Progress 末尾一條 · cross-ref W1-P75-TRACE-UPSTREAM-v1

| 擴展 meta | 值 |
|-----------|-----|
| wave_id | W1 |
| lifecycle_phase | B |
| phase_targets | P7.5 |
| estimated_cycles | 1 |
| mvp_allowed | true |
| human_only_prereqs | [] |
| infra_only_prereqs | [] |
| security_only_prereqs | [] |
| non_claims | doc/MVP 探針 · 非 full gate · 非 G-1–G-5 runtime · 非 Phase% 上调 |

---

### W1-P75-INTAKE-CLI-MVP-v1 — Intake CLI Completeness Doc + Minimal Upstream Wiring

- **Title**：P7.5 intake CLI 完整度 doc/MVP（`new_cleaning_case` → `run_intake_gate_cli` 上游鏈）
- **Goal**：補 intake CLI **完整度**缺口：人類接案入口（case 建立 + intake 初稿）與 P7.5 gate CLI（`run_intake_gate_cli` / layer merge）之間的 **canonical 上游路徑** doc + 最小可驗收接線，使 MP-SMOKE step 1 與人工接案流程敘事一致。
- **Scope**：
  - 新建 `docs/p75-intake-cli-upstream-mvp-v1.md`：`scripts/new_cleaning_case.py` · `scripts/run_intake_gate_cli.py` · `--run-gate` / `--explain` 組合 · 與 `check_case_eligibility` / P75-G2 outbox 的邊界表
  - 最小 runtime MVP（**1 cycle · MVP**）：例如 `new_cleaning_case.py` 增加 `--run-p75-gate`（或等價）呼叫 gate CLI 並 stdout 打印 `gate_status` + `reason_codes`（**不**強制寫 eligibility_result.json · **不**接 prod dispatch）
  - cross-ref：`W-MVP-W3-INTAKE-CLI` · `P75-G2` · `docs/tabular-intake-tool-path-v1.md`
  - `04_Workflows/WORKFLOW_INDEX.md` 一句 P7.5 intake upstream 入口（可併 UPSTREAM-ENTRY-INDEX）
- **Non-Goals**：
  - **不**建 Local UI · **不**改 `dispatch_executor` · **不**觸發清洗/bundle
  - **不**宣稱 intake CLI 已覆蓋 W4 dispatch / Checkpoint A 全鏈
  - **不**做 notify transport（留 P75-G4 / Wave 2–3）
- **Acceptance Criteria**：
  - AC-1：doc 列 case 建立 → gate CLI 的 ≥3 步 canonical 命令（含 flags）
  - AC-2：最小 runtime MVP 可本地跑通 demo_phase 或 sampleco **accept** 路徑（unittest 或 B_REPORT 命令輸出）
  - AC-3：doc 明示與 `W-MVP-W3` 邊界（何時用 new_cleaning_case vs 僅 gate CLI）
  - AC-4：non-claims 含「upstream MVP ≠ E2E delivery ≠ prod intake API」
- **Dependencies**：
  - `W-MVP-W3-INTAKE-CLI_state.md` · `P75-G2-intake-gate-layer-and-outbox-record-v1_state.md`
  - `scripts/new_cleaning_case.py` · `scripts/run_intake_gate_cli.py`（只讀對照後最小改動）
  - downstream：**W1-P75-TRACE-UPSTREAM-v1** · MP-SMOKE step 1
- **Observability**：
  - verify_commands：
    - `python scripts/new_cleaning_case.py --help`（文檔引用 flags）
    - `python -m unittest tests.test_new_cleaning_case -v`（可擴 1 條 gate 上游測）
    - `rg "run_intake_gate_cli|new_cleaning_case" docs/p75-intake-cli-upstream-mvp-v1.md`
  - evidence_artifacts：intake CLI doc · B_REPORT CLI 輸出樣本 · 可選 unittest diff
  - trace_fields：`case_dir` · `gate_status` · `reason_codes` · `intake.gate_decision`（若 gate 產出）
  - success_signals：Reviewer 無口述即可複製上游接案→gate 命令序列
  - failure_signals：宣稱已接 W4 dispatch；硬編磁碟路徑
- **Risks / Edge Cases**：
  - RSK-W1-P75-CLI-01：與 W-MVP-W3 票 scope 衝突 → mitigation：本票只補 P7.5 gate 上游 · Non-Goals 明示；residual：accept
  - RSK-W1-P75-CLI-02：gate 與 P2 eligibility 雙入口混淆 → mitigation：doc 邊界表 + 引用 tabular-intake-tool-path；residual：accept
- **Output Artifact**：`docs/p75-intake-cli-upstream-mvp-v1.md` · 可選 `new_cleaning_case.py` 最小增量 · WORKFLOW_INDEX 一句
- **B/C/D/O Landing Plan**：
  - **Build spec**：FRAME 列 canonical 命令序列 + AllowedPaths `scripts/new_cleaning_case.py` · `docs/**` · `tests/**`
  - **Code-Config**：Implementer doc + 最小 flag/接線；B_REPORT verification
  - **Debug-Verify**：Reviewer 跑 doc 命令序列 spot-check
  - **Observe-Trace**：cross-ref W1-P75-UPSTREAM-ENTRY-INDEX-v1

| 擴展 meta | 值 |
|-----------|-----|
| wave_id | W1 |
| lifecycle_phase | B |
| phase_targets | P7.5 |
| estimated_cycles | 1 |
| mvp_allowed | true |
| human_only_prereqs | [] |
| infra_only_prereqs | [] |
| security_only_prereqs | [] |
| non_claims | upstream MVP · 非 UI · 非 dispatch · 非 notify transport |

---

### W1-P75-TRACE-UPSTREAM-v1 — Gate→Outbox→MP-SMOKE Upstream Trace Contract (evolved W1-T5)

- **Title**：P7.5 intake gate **上游** observability trace 契約（doc-only · MP-SMOKE 接線 · G-1–G-5 僅觀測欄）
- **Goal**：定義 `intake.gate_decision` 從 gate CLI → outbox → MP-SMOKE step 1–2 → metrics 欄位 → 票 STATE 的 **trace 欄位 SSOT**；**G-1–G-5 resume-loop 僅列上游觀測欄與 matrix 交叉引用**，runtime 測試歸 Wave 2。供 Wave 2 P7 notify 下游與 Master Reviewer 可不跑 staging 即審計 P7.5 控制平面上游接線。
- **Scope**：
  - 新建 `docs/p75-intake-gate-control-plane-trace-v1.md`（承接原 W1-T5 意圖）：event_type · jsonl 路徑邏輯名 · MP-SMOKE step 映射 · `export_std_case_metrics_v1` keys
  - 更新 `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §7.4：**Control-plane trace** + **G-1–G-5 upstream observability only**（列 trace_fields · **不**新增 runtime 測試）
  - 索引：`P75-G2/G3/G4` · `P75-REGRESSION` · `MP-SMOKE` · **W1-P75-POLICY-DENY-MVP-v1** · **W1-P75-INTAKE-CLI-MVP-v1**
  - `docs/wave-master-ticketing-playbook.md` §4.3 observability 加 P7.5 上游範例
- **Non-Goals**：
  - **不**做 G-1–G-5 resume-loop **runtime**（明確 out of scope · Wave 2 `W2-P7-MATRIX-G1-G5-resume-loop-v1`）
  - **不**跑 staging POST · **不**改 `core/**` gate 實作
  - **不**拉升 P7.5 Phase% · **不**宣稱 UI/SLO/alert 已做
- **Acceptance Criteria**：
  - AC-1：trace doc 列 ≥8 個 trace_fields（含 `intake.gate_decision` · `run_id` · smoke step id · metrics ack keys · deny 路徑欄 cross-ref POLICY-DENY 票）
  - AC-2：MP-SMOKE 七步中 step 1–2 各對應至少 1 條 verify_command（引用既有 runner/unittest 名）
  - AC-3：G-1–G-5 標註 **upstream observability only · runtime = Wave 2**（防 scope creep）
  - AC-4：non-claims 含「local slot / smoke ok ≠ staging prod-ready」
- **Dependencies**：
  - `P75-G2` · `P75-G4` · `P75-REGRESSION`（上游能力）
  - `MP-SMOKE` · `scripts/run_multi_phase_smoke_v1.py`（只讀）
  - **W1-P75-POLICY-DENY-MVP-v1** · **W1-P75-INTAKE-CLI-MVP-v1**（上游 deny/CLI trace 欄位）
  - downstream_waves：**W2** 消費 trace 欄位 · **W5-T3** 消費 evidence 匯總
- **Observability**：
  - verify_commands：
    - `python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json`
    - `python scripts/export_std_case_metrics_v1.py --case-ref demo_phase --format json`
    - `rg "intake.gate_decision|trace_fields|G-1" docs/p75-intake-gate-control-plane-trace-v1.md`
  - evidence_artifacts：`outbox/verification/<case>/multi_phase_smoke_run.json` · trace doc
  - trace_fields：`intake.gate_decision` · `notifications_failed_ack_count` · `multi_phase_smoke_run.steps[].ok` · matrix G-1–G-5 **upstream** 欄位名
  - success_signals：Reviewer 對照 doc 可列全上游 trace 鏈無斷點
  - failure_signals：doc 宣稱 G-1–G-5 runtime 已覆蓋；缺 failure_signals 節
- **Risks / Edge Cases**：
  - RSK-W1-P75-TRACE-01：MP-SMOKE 步驟變更導致 doc 過期 → mitigation：引用 matrix §7.4 為 SSOT；v1 版本號；residual：accept
  - RSK-W1-P75-TRACE-02：與 Wave 2 notify 票重疊 → mitigation：Non-Goals 明示 transport 在 W2/W3；本票只上游 trace；residual：accept
- **Output Artifact**：`docs/p75-intake-gate-control-plane-trace-v1.md` · matrix §7.4 增量 · playbook observability 範例
- **B/C/D/O Landing Plan**：
  - **Build spec**：FRAME 列 trace 欄位清單 + 上游 P75 票 ID
  - **Code-Config**：Implementer 寫 doc + matrix/playbook cross-ref（doc-only）
  - **Debug-Verify**：Reviewer 紙面 traversal：gate run → smoke step 2 → metrics 欄位
  - **Observe-Trace**：Scribe Dashboard 敘事 cross-ref（不改 Phase%）

| 擴展 meta | 值 |
|-----------|-----|
| wave_id | W1 |
| lifecycle_phase | B |
| phase_targets | P7.5 |
| estimated_cycles | 1 |
| mvp_allowed | true |
| human_only_prereqs | [] |
| infra_only_prereqs | [] |
| security_only_prereqs | [] |
| non_claims | doc-only trace · 非 G-1–G-5 resume runtime · 非 staging 集成 · 非 Phase% 上调 |

---

### W1-P75-UPSTREAM-ENTRY-INDEX-v1 — P7.5 Upstream Entry Index (doc-only)

- **Title**：P7.5 上游入口索引（gate CLI · policy · intake CLI · trace — **非**全 Wave rollup）
- **Goal**：Planner / Orchestrator 從單頁索引判斷 P7.5 **上游**讀哪幾份 doc/CLI，不混淆 Wave Master 全 Wave 規劃（W-MASTER）與 Wave 5 cross-wave rollup（W5-T5）；補 **W1-T3 縮減遺留** 的可發現性，**不**重複 W5-T5 全索引施工。
- **Scope**：
  - 新建 `docs/p75-upstream-entry-index-v1.md`：≥5 行入口表（gate CLI · policy YAML · intake CLI · deny path doc · trace doc · MP-SMOKE step 1）
  - `04_Workflows/WORKFLOW_INDEX.md` §1.6 追加 **P7.5 upstream entry** 一句（與 W-ORCH entry 並列 · **不**替代 W5-T5 rollup）
  - cross-ref：`W1-P75-*` 四票 output · `P75-G*` 票 ID · Dashboard P7.5 列
- **Non-Goals**：
  - **不**建全 Wave 1–5 rollup INDEX（**W5-T5**）
  - **不**合并 W-MASTER 與 W-ORCH 為單檔
  - **不**跑 dispatch 真掃描 · **不**含 Multi-Chat commands/schema 模板（**W5-T1/T2**）
- **Acceptance Criteria**：
  - AC-1：index 含 P7.5 上游 ≥5 入口行（CLI/doc 各至少 2）
  - AC-2：明確寫「全 Wave playbook rollup → W5-T5；本 index 僅 P7.5 上游」
  - AC-3：WORKFLOW_INDEX 可達本 index + W1-P75-TRACE doc
  - AC-4：non-claims 引用 W-ORCH global non-claims（不複製 Phase%）
- **Dependencies**：
  - 本 Wave 其餘三票 output（建議在 POLICY-DENY · INTAKE-CLI · TRACE 至少 doc 草稿後合併索引）
  - `W5-T5-cross-wave-playbook-index-v1`（並列 SSOT · 非阻塞）
- **Observability**：
  - verify_commands：`rg "p75-upstream-entry|run_intake_gate_cli" docs/p75-upstream-entry-index-v1.md 04_Workflows/WORKFLOW_INDEX.md`
  - evidence_artifacts：index doc · WORKFLOW_INDEX diff
  - trace_fields：`wave_id` · `entry_type`（cli/doc）
  - success_signals：新 Orchestrator 無口述即可列出 P7.5 上游五入口
  - failure_signals：index 含 commands/schema 主施工（應 defer W5）
- **Risks / Edge Cases**：
  - RSK-W1-P75-IDX-01：與 W5-T5 重疊 → mitigation：Non-Goals + AC-2 明示邊界；residual：accept
  - RSK-W1-P75-IDX-02：與原 W1-T3 雙 CP 敘事混淆 → mitigation：本票僅 P7.5 upstream · 雙 CP 見 W5-T5；residual：accept
- **Output Artifact**：`docs/p75-upstream-entry-index-v1.md` · WORKFLOW_INDEX 增量
- **B/C/D/O Landing Plan**：
  - **Build spec**：FRAME 列入口表 outline
  - **Code-Config**：Implementer 寫 index + WORKFLOW_INDEX
  - **Debug-Verify**：Reviewer 模擬「P7.5 上游接戰」traversal
  - **Observe-Trace**：Scribe Progress 末尾 append

| 擴展 meta | 值 |
|-----------|-----|
| wave_id | W1 |
| lifecycle_phase | B |
| phase_targets | P7.5 |
| estimated_cycles | 1 |
| mvp_allowed | true |
| human_only_prereqs | [] |
| infra_only_prereqs | [] |
| security_only_prereqs | [] |
| non_claims | P7.5 upstream only · 非 W5 rollup · 非 lane 自動編排 |

---

### Wave 1 依賴順序（建議開票）

```
W1-P75-POLICY-DENY-MVP-v1  ∥  W1-P75-INTAKE-CLI-MVP-v1
            ↓                           ↓
        W1-P75-TRACE-UPSTREAM-v1（消費 deny + CLI trace 欄位 · evolved W1-T5）
            ↓
W1-P75-UPSTREAM-ENTRY-INDEX-v1（匯總四票 output · 可與 TRACE 尾段並行）
```

### 為何這 4 張 Wave 1 票能優先提升 P7.5 上游完整度

1. **Policy deny 可審計（W1-P75-POLICY-DENY-MVP-v1）**：P75-G3 runtime 已落地，但 Dashboard/MC-SMOKE 的 `phi_demo` deny 探針與 `reason_code` trace 仍分散；本票 doc/MVP 收口 deny 上游，**不**重做 full gate。

2. **Intake CLI 上游鏈（W1-P75-INTAKE-CLI-MVP-v1）**：`W-MVP-W3` 與 P75-G2 gate CLI 之間缺 canonical 敘事；最小 `--run-p75-gate` 級接線讓 MP-SMOKE step 1 與人工接案一致，**不**宣稱 E2E delivery。

3. **上游 trace SSOT（W1-P75-TRACE-UPSTREAM-v1）**：承接 W1-T5 合理部分；把 gate → outbox → MP-SMOKE → metrics 串成 Reviewer 可審計契約；G-1–G-5 **僅列上游觀測欄**，resume runtime 明確 defer Wave 2。

4. **上游可發現性（W1-P75-UPSTREAM-ENTRY-INDEX-v1）**：保留 W1-T3 **合理縮減**（P7.5 入口表），全 Wave rollup 與 commands/schema **defer W5**，解 B-1 去重。

5. **刻意排除**：模板/commands/instruction 主施工（W1-T1/T2/T4）· 全 Wave INDEX rollup（W1-T3 主體）· CI/GA/staging · G-1–G-5 resume runtime · notify transport。

## Wave 2 — Planned Tickets

> **Wave 2 Planner**：Chat 2 · 2026-06-26 · **doc-only 規劃** · 聚焦 P7 Round-2 **解阻 / 治理 / 準備**（非 execute · 非 CI 升格）。  
> **Phase 基線**：P7 **68%**（Dashboard 06-23）· Round-1 local slot **`validated`** · Round-2 execute-v2 **`blocked`**（五顶前置）。  
> **戰術線對齊**：`W-ORCH-wave-next-control-plane-v1` P7 lane · 子票 SSOT 優先於本規劃摘要。

### Wave 2 摘要表

| Ticket ID | 目的（一行） | lifecycle_phase | Phase | estimated_cycles | blocked / human |
|-----------|--------------|-----------------|-------|------------------|-----------------|
| **W2-T1** | governance_dual 真批文 **request / 留痕** runbook（human-only） | B | P7 | 1 | **human-only**（尚書省 / Wave-H） |
| **W2-T2** | Infra 真 staging slot + HTTPS endpoint **provision spec**（infra-only） | B | P7 | 1 | **infra-only**（Infra / Oncall） |
| **W2-T3** | Security 外部 POST **審查 + sign-off** 包（security-only） | B | P7 | 1 | **security-only**（Security） |
| **W2-T4** | 客戶 staging **allowlist 部署** checklist + 變更記錄模板（infra + 客戶 human） | B | P7 | 1 | **human + infra**（Infra / 客戶 Oncall） |
| **W2-T5** | staging slot **receiver 部署驗證** spec + 探針報告模板（infra-only · 非 localhost） | B | P7 | 1 | **infra-only**（Infra / Oncall） |
| **W2-P7-matrix-G1-G5-resume-loop-v1** | G-1〜G-5 resume-loop **MVP spec + test matrix + trace contract**（spec-only · 非 prod gate） | B | P7 · P7.5(ref) | 1 | 无 |
| **W2-P7-advisory-ci-ssot-index-v1** | P7 advisory CI **誠實索引**（STATE / dashboard / INDEX · doc-only） | B | P7 | 1 | 无 |

**執行 ID 建議**（開子票時）：`W2-P7-governance-dual-request-frame-v1` · `W2-P7-infra-staging-slot-spec-v1` · `W2-P7-security-post-signoff-pack-v1` · `W2-P7-staging-allowlist-deploy-checklist-v1` · `W2-P7-receiver-staging-verify-spec-v1` · `W2-P7-matrix-G1-G5-resume-loop-v1` · `W2-P7-advisory-ci-ssot-index-v1`

**本 Wave 明確不開**：P7 CI / GA 功能票 · required CI 升格 · Round-2 S1–S4 **真 POST execute**（留 `WH-P7-NOTIF-staging-integration-execute-v2` · 前置齊備後由 ops 開 execute 循環）· Phase% 上調。

---

### W2-T1 — governance_dual 真批文 request / 留痕 runbook

| 欄位 | 值 |
|------|-----|
| **Ticket ID** | W2-T1（exec: `W2-P7-governance-dual-request-frame-v1`） |
| **Title** | P7 governance · Wave-H **`governance_dual`** 真批文 request / 留痕 runbook |
| **wave_id** | W2 · **lifecycle_phase**: B · **phase_targets**: P7 · **estimated_cycles**: 1 · **mvp_allowed**: true |

**Goal**  
讓 P7 staging Round-2 在尚書省 / Wave-H 核發 **真** `governance_dual` 批文後，有可審計的 request → 核准 → Progress / STATE 留痕路徑；解阻 execute-v2 **P-1** 與 bootstrap **G4**（現 **`open`**）。

**Scope**  
- 起草 **governance_dual 批文 request 表**（申請方 · 範圍 · non-prod 聲明 · rollback 承諾 · 關聯 runbook / execute-v2 票號）。  
- 定義 **核准後留痕欄位**：批文 ID · 核准日期 · 核准人角色 · Progress **末尾 append** 模板句。  
- 更新 `WH-P7-PROD-prod-rollout-governance-bootstrap-v1` **G4** 狀態欄位說明（`open` → `partial` 僅當批文 ID 已回填；**不得**標 `done` 除非 Reviewer 對照真批文）。  
- cross-ref Round-1 `simulated_local_execute_2026-06-24` 與 Round-2 差異（誠實 non-claim 表一行）。  
- 產出 **human dispatch 步驟**（誰提交 · 哪個治理通道 · 預期 SLA 占位 · 阻塞升級路徑）。

**Non-Goals**  
- ❌ AI / Implementer **代為**取得批文或伪造批文 ID。  
- ❌ 跑 staging POST · flip env · 升格 `p7-notification-smoke` required CI。  
- ❌ 修改 `.github/workflows/**` · adapter / tests code。

**Acceptance Criteria**  
- **AC-1**：request 表 + 留痕模板可審計；含 mandatory 欄位（批文 ID · 日期 · 範圍 · non-prod）。  
- **AC-2**：bootstrap G4 與 execute-v2 P-1 有 **同一 SSOT 交叉引用**（雙向連結段落）。  
- **AC-3**：明確 non-claim：「request runbook 就緒 ≠ governance_dual 已核准」。  
- **AC-4**：human 回填批文 ID 後，Reviewer 可僅讀 STATE / Progress 判定 G4 是否可标 `partial`（仍非 Round-2 execute GO）。

**Dependencies**  
- **upstream_tickets**: `WH-P7-PROD-prod-rollout-governance-bootstrap-v1` · `WH-P7-NOTIF-staging-integration-execute-v2` · Round-1 `WH-P7-NOTIF-staging-integration-execute-v1`（`validated`）  
- **downstream_waves**: W3（delivery notify 仍不依赖批文；仅 P7 staging 解阻）  
- **blocks_if_missing**: 尚書省 / Wave-H 治理通道未指定 → 票维持 `blocked` · next_action = 请 Governance 指定 dispatch 入口

**Observability**  
- **verify_commands**:
  - `rg "governance_dual|PENDING_GOV_DUAL_ID|execute_v2_prereq_P1" 04_Workflows/onboarding/p7-governance-dual-request-runbook-v1.md 04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md`
  - `rg "G4|governance_dual" 04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md`
- **evidence_artifacts**: 子票 B_REPORT · bootstrap G4 表行更新 · Progress 末尾（批文 ID 占位符 `PENDING_GOV_DUAL_ID`）  
- **trace_fields**: `governance_dual_approval_id` · `approval_date` · `execute_v2_prereq_P1`  
- **success_signals**: runbook 落盘 · AC-1–AC-3 Reviewer `accepted` · G4 仍为 `open` 直至 human 回填  
- **failure_signals**: AC 含「批文已取得」但 `human_only_prereqs` 仍 open · 无 Progress 留痕位

**Risks / Edge Cases**  
- **RSK-W2-01** 批文 SLA 不可控（L/M）→ mitigation: runbook 含升級路徑與 `blocked` 語意；residual: **accept**  
- **RSK-W2-02** 批文范围过窄不含 staging POST（M/H）→ mitigation: request 表 explicit 列 S1–S4 + 48h 观测；residual: **block** execute until re-approval

**Output Artifact**  
- 新建或更新：`04_Workflows/onboarding/p7-governance-dual-request-runbook-v1.md`（或等價 governance doc · Orchestrator 裁決路径）  
- 更新：`WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md` G4 说明段  
- 可选索引：`04_Workflows/WORKFLOW_INDEX.md` 一句

**B/C/D/O Landing Plan**  
- **B** 建 spec：FRAME + request 表 + 留痕模板 + G4 cross-ref  
- **C** 落文檔/配置：Implementer 写 runbook · bootstrap STATE 文字更新（AllowedPaths 内）  
- **D** 驗證：Reviewer 对照 execute-v2 §解阻步骤 1 · non-claims · 无伪完成  
- **O** trace：Scribe Progress 一句「W2-T1 runbook ready · G4 仍 open pending human 批文」

```yaml
human_only_prereqs:
  - owner: 尚書省 / Wave-H Governance
    deliverable: governance_dual 真批文 ID + 核准日期
    channel: 治理工单 / 批文系统（逻辑名 · 不写具体 URL）
infra_only_prereqs: []
security_only_prereqs: []
non_claims:
  - governance_dual 已核准
  - Round-2 execute 可开始
  - P7 prod-ready / required CI
```

---

### W2-T2 — Infra 真 staging slot + HTTPS endpoint provision spec

| 欄位 | 值 |
|------|-----|
| **Ticket ID** | W2-T2（exec: `W2-P7-infra-staging-slot-spec-v1`） |
| **Title** | P7 infra · 真 staging deployment slot + non-prod HTTPS endpoint provision spec |
| **wave_id** | W2 · **lifecycle_phase**: B · **phase_targets**: P7 · **estimated_cycles**: 1 |

**Goal**  
让 Infra 在 **human governance_dual 并行或之后** 能按 SSOT provision 真 staging slot 与 HTTPS endpoint，使 execute-v2 **P-2** 与 bootstrap **G3** 从 `partial` 可追踪到「endpoint 已 provision · 待 S1–S4」。

**Scope**  
- 基于 `WH-P7-PROD-staging-env-config-v1` env matrix，起草 **Infra provision checklist**（slot 命名 · non-prod host · TLS · secret 注入位 · 与 local slot 差异表）。  
- 定义 **endpoint 就绪物证**：逻辑 host/path · slot ID · env matrix 回填位置（**禁止** secret 原文 · **禁止** prod URL）。  
- 写 **provision → verify 探针** 步骤（HTTPS GET/health · 不含 signed POST execute）。  
- 更新 execute-v2 与 bootstrap **G3** 的「Infra 完成标记」字段说明。  
- cross-ref `WH-P7-PROD-staging-env-bootstrap-v1`（local slot `done_with_gaps`）明确 Round-2 须 **另 provision**。

**Non-Goals**  
- ❌ 本票 **不** 执行 Infra flip / terraform apply / 真机 provision（属 infra-only human/ops）。  
- ❌ 不跑 S1–S4 POST · 不改 CI workflow · 不写磁碟绝对路径。  
- ❌ 不把 local slot localhost 宣称为客户 staging endpoint。

**Acceptance Criteria**  
- **AC-1**：provision checklist 逐步可执行（Infra 人读即可操作）。  
- **AC-2**：endpoint 就绪物证模板含 slot ID · host（逻辑）· 回填至 env-config 交叉引用。  
- **AC-3**：G3 / execute-v2 P-2 状态规则：仅 Infra 回填后 → `partial`（provisioned）；S1–S4 GO 仍属 execute-v2。  
- **AC-4**：non-claim 段：「spec 就绪 ≠ slot 已 provision」。

**Dependencies**  
- **upstream_tickets**: `WH-P7-PROD-staging-env-config-v1`（`validated`）· `WH-P7-PROD-staging-smoke-runbook-v1` · `WH-P7-NOTIF-staging-integration-execute-v2`  
- **downstream_waves**: W2-T4 allowlist · W2-T5 receiver（依赖 endpoint host 已知）  
- **blocks_if_missing**: W2-T1 批文若要求「无 endpoint 不得申请」→ 文档注明并行/顺序由 Governance 裁定

**Observability**  
- **verify_commands**:
  - `rg "staging_slot_id|staging_endpoint_host|provision_completed_at" 04_Workflows/onboarding/p7-infra-staging-slot-provision-spec-v1.md`
  - `rg "G3|execute-v2.*P-2" 04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md 04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md`
- **evidence_artifacts**: Infra 回填的 env matrix 片段（redacted）· bootstrap G3 行 · execute-v2 B_REPORT `run_url` 占位  
- **trace_fields**: `staging_slot_id` · `staging_endpoint_host` · `provision_completed_at`  
- **success_signals**: spec Reviewer accepted · Infra 回填后 G3=`partial(provisioned)`  
- **failure_signals**: spec 标「endpoint ready」但无 slot ID · localhost 混入 allowlist 示例

**Risks / Edge Cases**  
- **RSK-W2-03** Infra 资源排队（M/M）→ runbook 含最小 slot 规格与临时 internal endpoint 选项；residual: accept  
- **RSK-W2-04** host 与 allowlist grammar 不一致（M/H）→ checklist 强制同步 W2-T4 allowlist 步；residual: block POST

**Output Artifact**  
- 新建：`04_Workflows/onboarding/p7-infra-staging-slot-provision-spec-v1.md`  
- 更新：`WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md` G3 说明 · optional `WH-P7-PROD-staging-env-config-v1` 一句 cross-ref

**B/C/D/O Landing Plan**  
- **B** 建 spec：provision checklist + 物证模板 + G3 规则  
- **C** 落文檔：runbook/spec 落盘 · STATE 文字更新  
- **D** 驗證：Reviewer 对照 env-config matrix · execute-v2 P-2 · Rule 6 无硬编路径  
- **O** trace：Progress「W2-T2 spec ready · G3 待 Infra 回填」

```yaml
human_only_prereqs: []
infra_only_prereqs:
  - owner: Infra / Oncall
    deliverable: staging slot provisioned + non-prod HTTPS endpoint + slot ID 回填
security_only_prereqs: []
non_claims:
  - 真 staging endpoint 已就绪
  - Round-2 S1–S4 已执行
```

---

### W2-T3 — Security 外部 POST 審查 + sign-off 包

| 欄位 | 值 |
|------|-----|
| **Ticket ID** | W2-T3（exec: `W2-P7-security-post-signoff-pack-v1`） |
| **Title** | P7 security · 外部 webhook POST 风险审查 + sign-off 包 |
| **wave_id** | W2 · **lifecycle_phase**: B · **phase_targets**: P7 · **estimated_cycles**: 1 |

**Goal**  
为 Security 提供可重复的 **外部 POST 风险审查清单与 sign-off 模板**，解阻 execute-v2 **P-3** 与 bootstrap **G6**（现 **`open`**），且不含任何真实 POST 执行。

**Scope**  
- 起草 **Security review checklist**：allowlist 机制 · secret 管理 · 无 prod URL 混入 · HMAC enforce · DLQ/retry 数据残留 · 日志 redaction。  
- 定义 **sign-off 记录模板**（审查人 · 日期 · 范围 · 条件性批准 · 复审触发条件）。  
- 对齐 `WH-P7-NOTIF-HMAC-receiver-contract-v1` 与 staging env-config §安全隔离段。  
- 更新 bootstrap **G6** 与 execute-v2 P-3 的完成标记（sign-off 文档 ID / 存储位置逻辑名）。  
- 含 **拒绝/附条件批准** 分支与 re-review 路径。

**Non-Goals**  
- ❌ Security sign-off **由 AI 代签**或伪造。  
- ❌ 不执行 penetration test 或真 POST（除非 Security 另开票）。  
- ❌ 不升格 CI · 不 flip prod · 不改 adapter code。

**Acceptance Criteria**  
- **AC-1**：checklist 覆盖 allowlist · secret · prod URL 禁止 · HMAC · DLQ 五类风险。  
- **AC-2**：sign-off 模板可被 Security 填完并归档（逻辑路径 · 无 secret 原文）。  
- **AC-3**：G6 规则：仅 sign-off 归档后 → `partial`；不等于 S1–S4 GO。  
- **AC-4**：non-claim：「pack 就绪 ≠ Security 已批准」。

**Dependencies**  
- **upstream_tickets**: `WH-P7-PROD-staging-env-config-v1` · `WH-P7-NOTIF-HMAC-receiver-contract-v1` · `WH-P7-NOTIF-staging-integration-execute-v2`  
- **downstream_waves**: execute-v2（P-3 齐备后仍须 P-1/P-2/P-4/P-5）  
- **blocks_if_missing**: 若 endpoint host 未知 → checklist 含「待 W2-T2 回填后再审」分支

**Observability**  
- **verify_commands**:
  - `rg "allowlist|HMAC|DLQ|prod URL|security_signoff_id" 04_Workflows/checklists/p7-security-external-post-review-v1.md`
  - `rg "G6|execute-v2.*P-3" 04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md 04_Workflows/tickets/WH-P7-NOTIF-staging-integration-execute-v2_state.md`
- **evidence_artifacts**: sign-off 模板 · bootstrap G6 行 · Security 归档 ID（human 回填）  
- **trace_fields**: `security_signoff_id` · `review_date` · `conditional_approvals[]`  
- **success_signals**: pack Reviewer accepted · G6 仍 open 直至 human sign-off  
- **failure_signals**: AC 写「审查通过」但无 sign-off 物证栏

**Risks / Edge Cases**  
- **RSK-W2-05** Security 要求额外 controls 超出 sandbox impl（M/H）→ mitigation: 附条件批准 + 另开 impl 票（非本 Wave）；residual: block execute  
- **RSK-W2-06** 客户 data class 升级导致 re-review（L/M）→ sign-off 模板含复审触发；residual: accept

**Output Artifact**  
- 新建：`04_Workflows/checklists/p7-security-external-post-review-v1.md`  
- 更新：`WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md` G6 说明

**B/C/D/O Landing Plan**  
- **B** 建 spec：checklist + sign-off 模板 + G6 规则  
- **C** 落文檔：checklist 落盘 · bootstrap cross-ref  
- **D** 驗證：Reviewer 对照 HMAC contract · env-config 安全段 · wave-next non-claims  
- **O** trace：Progress「W2-T3 pack ready · G6 待 Security sign-off」

```yaml
human_only_prereqs: []
infra_only_prereqs: []
security_only_prereqs:
  - owner: Security
    deliverable: 外部 POST 风险书面 sign-off（模板填毕 + 归档 ID）
non_claims:
  - Security 已批准 staging POST
  - 无 residual 风险
```

---

### W2-T4 — 客戶 staging allowlist 部署 checklist

| 欄位 | 值 |
|------|-----|
| **Ticket ID** | W2-T4（exec: `W2-P7-staging-allowlist-deploy-checklist-v1`） |
| **Title** | P7 allowlist · 客户 staging endpoint allowlist 部署 + 变更记录 checklist |
| **wave_id** | W2 · **lifecycle_phase**: B · **phase_targets**: P7 · **estimated_cycles**: 1 |

**Goal**  
让客户 staging **non-prod** allowlist 的部署与变更可被审计，解阻 execute-v2 **P-4**；确保 **禁止 prod endpoint** 有 checklist 级 enforcement 叙述。

**Scope**  
- 基于 env-config allowlist grammar，起草 **allowlist 部署 checklist**（host/path-prefix · 与 `GOV_NOTIFICATION_WEBHOOK_URL` 同步 · negative example 表）。  
- 定义 **变更记录模板**（变更人 · 日期 · 旧/新 host · 审批引用 · rollback 步骤）。  
- 写 **客户协调 human 步骤**（谁提供 endpoint · 谁确认 non-prod · SLA 占位）。  
- 更新 execute-v2 P-4 完成标记与 smoke-runbook S1「allowlist match → 2xx / miss → blocked」cross-ref。  
- 与 W2-T2 endpoint host 字段对齐（依赖说明）。

**Non-Goals**  
- ❌ 不实际部署客户 firewall / DNS / allowlist config（infra + 客户 human）。  
- ❌ 不含 prod allowlist · 不含 CI tier flip。  
- ❌ 不跑 S1 POST 验证（留 execute-v2）。

**Acceptance Criteria**  
- **AC-1**：checklist 含 prod URL 禁止断言与 negative test 叙述。  
- **AC-2**：变更记录模板可独立审计（至少 3 个 mandatory 字段）。  
- **AC-3**：execute-v2 P-4 规则：allowlist 部署记录回填后 → prereq 满足（仍须 P-1–P-3/P-5）。  
- **AC-4**：与 env-config allowlist 示例 grammar **一致**。

**Dependencies**  
- **upstream_tickets**: `WH-P7-PROD-staging-env-config-v1` · `WH-P7-PROD-staging-smoke-runbook-v1` · W2-T2（endpoint host SSOT）  
- **downstream_waves**: execute-v2 S1  
- **blocks_if_missing**: W2-T2 未 provision endpoint → allowlist checklist 标「host TBD」

**Observability**  
- **verify_commands**:
  - `rg "allowlist_version|non_prod_attestation|prod.*禁止|blocked_by_url_tier" 04_Workflows/checklists/p7-staging-allowlist-deploy-v1.md`
  - `rg "GOV_NOTIFICATION_WEBHOOK_CASE_ALLOWLIST|allowlist" 04_Workflows/tickets/WH-P7-PROD-staging-env-config-v1_state.md .github/workflows/p7-notification-smoke.yml`
- **evidence_artifacts**: allowlist 变更记录（redacted host）· execute-v2 checklist P-4 tick · adapter `blocked_by_url_tier_policy` 预期  
- **trace_fields**: `allowlist_version` · `allowlist_change_id` · `non_prod_attestation`  
- **success_signals**: checklist accepted · human 回填变更记录  
- **failure_signals**: prod hostname 出现在示例 · 无变更记录位

**Risks / Edge Cases**  
- **RSK-W2-07** 客户提供 prod URL 误作 staging（H/H）→ checklist mandatory 客户 non-prod attestation；residual: **block**  
- **RSK-W2-08** allowlist 与 URL env 漂移（M/H）→ 变更模板要求同步更新 env matrix；residual: block S1

**Output Artifact**  
- 新建：`04_Workflows/checklists/p7-staging-allowlist-deploy-v1.md`  
- 更新：`WH-P7-NOTIF-staging-integration-execute-v2_state.md` P-4 说明段（若 owner 授权一句 cross-ref）

**B/C/D/O Landing Plan**  
- **B** 建 spec：deploy checklist + 变更记录 + 客户 human 步骤  
- **C** 落文檔/配置索引：checklist 落盘 · execute-v2 cross-ref  
- **D** 驗證：Reviewer 对照 env-config grammar · S1 runbook  
- **O** trace：Progress「W2-T4 checklist ready · P-4 待 Infra/客户回填」

```yaml
human_only_prereqs:
  - owner: 客户 Oncall / 项目经理
    deliverable: non-prod staging endpoint 确认 + 书面 attestation（逻辑模板）
infra_only_prereqs:
  - owner: Infra
    deliverable: allowlist config 部署至 staging slot + 变更记录回填
security_only_prereqs: []
non_claims:
  - allowlist 已部署生效
  - S1 allowlist match 已实测
```

---

### W2-T5 — staging slot receiver 部署驗證 spec

| 欄位 | 值 |
|------|-----|
| **Ticket ID** | W2-T5（exec: `W2-P7-receiver-staging-verify-spec-v1`） |
| **Title** | P7 receiver · staging slot 部署验证 spec（非 localhost · 验签探针） |
| **wave_id** | W2 · **lifecycle_phase**: B · **phase_targets**: P7 · **estimated_cycles**: 1 |

**Goal**  
将 `WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1`（localhost reference · **7/7 tests OK**）与 **真 staging slot 部署验证** 之间的缺口明文化，解阻 execute-v2 **P-5**；提供 Infra 可执行的验签探针报告模板。

**Scope**  
- 起草 **receiver 部署选项表**：reference impl 部署 vs 客户 receiver · 选型条件 · non-prod only。  
- 定义 **staging slot 验签探针步骤**（signed POST 探针 · 期望 2xx · 日志字段 · **不含** S1–S4 全量 execute）。  
- 写 **验证报告模板**（deploy 版本 · endpoint · 探针 run 摘要 · 与 localhost demo 差异）。  
- cross-ref receiver-contract SSOT · smoke-runbook S3 前置。  
- 更新 execute-v2 P-5 与 bootstrap _notes（receiver localhost ≠ staging deployed）。

**Non-Goals**  
- ❌ 本票 **不** 部署 receiver 至 staging（infra-only ops）。  
- ❌ 不修改 receiver reference code · 不新开 CI。  
- ❌ 不把 localhost:8765 demo 宣称为 staging production receiver。

**Acceptance Criteria**  
- **AC-1**：部署选项表 + 探针步骤对 Infra 可读可执行。  
- **AC-2**：验证报告模板含 mandatory 字段（endpoint · 探针结果 · 部署 artifact 版本逻辑名）。  
- **AC-3**：execute-v2 P-5 规则：报告回填 + 探针 2xx 后 → prereq 满足。  
- **AC-4**：non-claim：「spec 就绪 ≠ receiver 已部署至 staging slot」。

**Dependencies**  
- **upstream_tickets**: `WH-P7-NOTIF-HMAC-receiver-contract-v1` · `WH-P7-NOTIF-HMAC-receiver-fixtures-impl-v1`（`done_with_gaps` · localhost）· W2-T2（staging endpoint）· `WH-P7-PROD-staging-smoke-runbook-v1`  
- **downstream_waves**: execute-v2 S3 · W3 不重复 receiver impl  
- **blocks_if_missing**: W2-T2 endpoint 未就绪 → 探针 host TBD

**Observability**  
- **verify_commands**（规划引用 · 执行期由 ops 跑）:
  - `python -m unittest tests.test_*hmac*receiver* -v`（localhost regression · 非 staging 物证）
  - Infra 探针命令（spec 内定义 · 指向 staging slot env）
- **evidence_artifacts**: staging receiver 验证报告 · execute-v2 P-5 tick · B_REPORT phase S3 占位  
- **trace_fields**: `receiver_deploy_version` · `verify_probe_run_id` · `staging_receiver_endpoint`  
- **success_signals**: spec accepted · human 探针报告 2xx 回填  
- **failure_signals**: 仅 localhost 证据却标 P-5 done

**Risks / Edge Cases**  
- **RSK-W2-09** 客户 insist 自有 receiver 不兼容 reference（M/H）→ spec 含 contract conformance checklist；residual: block S3 until attestation  
- **RSK-W2-10** secret 分轨错误（M/H）→ 探针步骤强制 staging-dedicated secret；residual: block

**Output Artifact**  
- 新建：`04_Workflows/onboarding/p7-receiver-staging-verify-spec-v1.md`  
- 更新：`WH-P7-NOTIF-staging-integration-execute-v2_state.md` P-5 说明 · optional smoke-runbook §3 一句 cross-ref

**B/C/D/O Landing Plan**  
- **B** 建 spec：部署选项 + 探针 + 报告模板  
- **C** 落文檔：spec 落盘 · execute-v2 / runbook cross-ref  
- **D** 驗證：Reviewer 对照 receiver-contract · fixtures-impl 边界 · non-claims  
- **O** trace：Progress「W2-T5 spec ready · P-5 待 Infra 探针报告」

```yaml
human_only_prereqs: []
infra_only_prereqs:
  - owner: Infra / Oncall
    deliverable: receiver 部署至 staging slot + 验签探针 2xx + 验证报告回填
security_only_prereqs: []
non_claims:
  - staging receiver 已部署
  - S3 验签已通过
  - 客户 prod receiver 就绪
```

---

### W2-P7-matrix-G1-G5-resume-loop-v1 — G-1〜G-5 resume-loop MVP spec + test matrix + trace contract

| 欄位 | 值 |
|------|-----|
| **Ticket ID** | W2-P7-matrix-G1-G5-resume-loop-v1 |
| **Title** | P7 matrix · G-1〜G-5 resume-loop MVP spec + test matrix + trace contract |
| **wave_id** | W2 · **lifecycle_phase**: B · **phase_targets**: P7 · P7.5(ref) · **estimated_cycles**: 1 · **mvp_allowed**: true |

**Goal**  
將 `standard-case-hitl-resume-notify-matrix.md` §9 **G-1〜G-5** resume-loop 缺口，對齊 **outbox / runner / trace** 觀測契約，產出 MVP 級 spec + test matrix + trace contract；使 Reviewer 與 Wave 3 dispatch 票可不跑 staging 即判斷 resume-loop **行為與觀測點**是否一致，**不做** full prod gate 或 runtime 實作。

**Scope**  
- 新建 `docs/p7-resume-loop-g1-g5-spec-v1.md`（或等價 spec）：逐條定義 G-1〜G-5 **預期行為** · **觸發條件** · **blocked/terminal 語意** · **outbox artifact 路徑邏輯名**。  
- 更新 `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §9：G-1〜G-5 各加 **Observability 列**（trace_fields · verify_command 引用 · 預期 `ok`/`blocked` 語意）。  
- 新建 **test matrix 附錄**（同 doc 或 `04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.md`）：每 gap 至少 1 行 **scenario row**（輸入狀態 · 預期 orchestrator 結論 · 觀測點 · 引用既有 unittest 名或「planned impl」占位）。  
- **Trace contract 段**：cross-ref **W1-T5** `docs/p75-intake-gate-control-plane-trace-v1.md` 欄位命名；resume-loop 專用欄位（`resume_eligibility` · `checkpoint_path` · `stale_checkpoint` · `run.blocked` 等）與 MP-SMOKE **不混用** gate step 1–2。  
- cross-ref W-ORCH P7 lane · `validate_resume_eligibility()` · matrix R-11〜R-15 行 · 既有 P75-G* 票 ID（只讀索引）。

**Non-Goals**  
- ❌ **不**新增 orchestrator/resume **runtime code** 或 dedicated unittest 實作（留後續 impl 票）。  
- ❌ **不**做 full prod gate · **不**跑 staging POST · **不**升格 CI required check。  
- ❌ **不**宣稱 G-1〜G-5 已 closed · **不**宣稱 P7 Round-2 execute 已完成。  
- ❌ **不**覆蓋 G-6〜G-13（本票僅 G-1〜G-5）。

**Acceptance Criteria**  
- **AC-1（G-1）**：spec 列 `stale_checkpoint` 行為（`awaiting_human` + expired `expires_at`）· 觀測點：`validate_resume_eligibility` 回傳 · trace_field `resume_eligibility=stale_checkpoint` · matrix R-11 cross-ref。  
- **AC-2（G-2）**：spec 列 `revise_needed` resume **blocked** 語意 · 觀測點：orchestrator 不進 resume · trace_field `resume_blocked_reason=revise_needed` · matrix R-12。  
- **AC-3（G-3）**：spec 列 `on_hold` resume **blocked** 語意 · 觀測點：CLI/integration 與 orchestrator 邊界 · trace_field `resume_blocked_reason=on_hold` · matrix R-13。  
- **AC-4（G-4）**：spec 列 missing checkpoint file → `blocked` · 觀測點：load error 路徑 · outbox 無 checkpoint artifact · trace_field `checkpoint_load_error` · matrix R-14。  
- **AC-5（G-5）**：spec 列 non-allowlisted case resume early block · 觀測點：`_run_experiment_resume_from_checkpoint` 邊界 · trace_field `case_allowlist_block` · matrix R-15。  
- **AC-6**：trace contract 段 **雙向 cross-ref W1-T5**（gate trace 與 resume trace 分表）· 明確寫「W1-T5 不含 G-1–G-5 runtime」。  
- **AC-7**：test matrix 附錄 ≥5 行（每 G-* 一行）· 每行含 ≥1 條 verify_command（unittest 名或 `rg` 對 spec 關鍵字）。  
- **AC-8**：non-claims 含「spec/matrix 就緒 ≠ G-1–G-5 unittest 已落地 ≠ prod resume 閉環」。

**Dependencies**  
- **upstream_tickets**: **W1-T5**（P7.5 gate trace SSOT · doc-only）· `standard-case-hitl-resume-notify-matrix.md` §9 · `W-ORCH-wave-next-control-plane-v1` P7 lane  
- **downstream_waves**: W3（P8.9 dispatch · G-7 仍獨立）· 後續 resume-loop **impl** 票（非本 Wave 規劃）  
- **blocks_if_missing**: W1-T5 trace doc 未落盘 → 本票 trace contract 段标「pending W1-T5」占位

**Observability**  
- **verify_commands**:
  - `rg "G-1|G-2|G-3|G-4|G-5|stale_checkpoint|resume_eligibility|resume_blocked_reason" docs/p7-resume-loop-g1-g5-spec-v1.md 04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md`
  - `rg "W1-T5|p75-intake-gate-control-plane-trace" docs/p7-resume-loop-g1-g5-spec-v1.md`
  - `python -m unittest tests.test_hitl_checkpoints_v1 -v`（文檔引用的既有 HITL regression · **非** G-1–G-5 閉環物证）
- **evidence_artifacts**: resume-loop spec doc · matrix §9 更新 diff · 子票 B_REPORT `changed_files`  
- **trace_fields**: `resume_eligibility` · `resume_blocked_reason` · `checkpoint_path` · `checkpoint_load_error` · `case_allowlist_block` · `run.blocked`（引用 · 非本票新增 runtime）  
- **success_signals**: AC-1〜AC-8 Reviewer `accepted` · matrix §9 G-1–G-5 均有 Observability 列  
- **failure_signals**: spec 宣稱 gap closed 但 matrix 仍标 no test · 缺 W1-T5 cross-ref · 混入 staging/prod gate 語意

**Risks / Edge Cases**  
- **RSK-W2-11** W1-T5 與 resume trace 欄位命名漂移（M/M）→ mitigation: trace contract 分表 + 引用 W1-T5 為 gate SSOT；residual: accept  
- **RSK-W2-12** 讀者將 spec 當 impl 完成（M/H）→ mitigation: AC-8 non-claims + matrix 保留 `planned impl` 列；residual: accept

**Output Artifact**  
- 新建：`docs/p7-resume-loop-g1-g5-spec-v1.md`  
- 更新：`04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` §9（G-1–G-5 Observability 列）  
- 可選：`04_Workflows/testing/p7-resume-loop-g1-g5-matrix-v1.md`  
- 索引：`04_Workflows/WORKFLOW_INDEX.md` 一句 · `docs/wave1-control-plane-lane-index-v1.md` cross-ref（若 W1-T3 已落盘）

**B/C/D/O Landing Plan**  
- **B** 建 spec：G-1–G-5 行為表 + trace contract + matrix 附錄 outline  
- **C** 落文檔：spec + matrix §9 更新（doc-only）  
- **D** 驗證：Reviewer 紙面 traversal 每 G-* · 對照 W1-T5 · playbook §4.3 observability  
- **O** trace：Scribe Progress「W2-P7-matrix G-1–G-5 spec ready · runtime impl 未開」

```yaml
human_only_prereqs: []
infra_only_prereqs: []
security_only_prereqs: []
non_claims:
  - G-1–G-5 unittest/runtime 已落地
  - P7 Round-2 execute 已完成
  - resume-loop prod gate / required CI
  - MP-SMOKE 七步已覆蓋 resume-loop
```

---

### W2-P7-advisory-ci-ssot-index-v1 — P7 advisory CI 誠實索引（doc-only）

| 欄位 | 值 |
|------|-----|
| **Ticket ID** | W2-P7-advisory-ci-ssot-index-v1 |
| **Title** | P7 · advisory CI SSOT 索引（非 required gate · 非 prod 閉環） |
| **wave_id** | W2 · **lifecycle_phase**: B · **phase_targets**: P7 · **estimated_cycles**: 1 · **mvp_allowed**: true |

**Goal**  
把 P7 線 **advisory CI** 全部集中索引於 STATE / Dashboard 敘事 / WORKFLOW_INDEX，明確標記 **非 required gate** · **非 prod 閉環** · **sandbox-only**，解阻 Master Review **B-3**（P7 advisory 誠實索引缺口）與 playbook §5.3 #6/#7 observability 抽樣。

**Scope**  
- 在 `04_Workflows/WORKFLOW_INDEX.md` 新增 **「P7 · Advisory vs gate」** 小段：至少索引 `p7-notification-smoke.yml` · 相關 unittest 模組 · staging smoke-runbook（人工 env）· bootstrap G8 required-CI 升格模板（**仍 default advisory**）。  
- 每條目標註：`advisory` · `continue-on-error`（若適用）· `127.0.0.1` sandbox · **非 branch protection required** · **≠ staging/prod 閉環**。  
- 更新 `docs/WAVE_PROGRESS_DASHBOARD.md` **敘事** cross-ref 一句（**不改 Phase% 數字**）：P7 CI 邊界 · Round-2 `blocked` 與 advisory 關係。  
- 更新或 cross-ref 相關 P7 STATE：`WH-P7-PROD-prod-rollout-governance-bootstrap-v1` G8 · `WH-P7-NOTIF-PROD-policy-v1` · `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1` B_REPORT §Global #3/#4（只讀對齊 · 不重寫）。  
- 與 Wave 3 `W3-P8-ADV-advisory-ci-ssot-index-v1` **分線**：本票 **僅 P7**；P8/P8.9 advisory 歸 W3。  
- 可選：新建 `docs/internal/p7_advisory_ci_index_v1.md`（若 INDEX 過長）。

**Non-Goals**  
- ❌ 不修改 `.github/workflows/p7-notification-smoke.yml` · 不升格 required check · 不 flip branch protection。  
- ❌ 不跑 GA / 不伪造 run URL · 不宣稱 P7 Round-2 execute 已完成 · 不宣稱 prod-ready。  
- ❌ 不重复 Wave 3 P8/P8.9 advisory 索引正文。  
- ❌ 不上调 Dashboard Phase%。

**Acceptance Criteria**  
- **AC-1**：WORKFLOW_INDEX 含 **≥2** 條 P7 CI/smoke 條目，每條有 **advisory** 或 **human-env-only** 明示標籤。  
- **AC-2**：`p7-notification-smoke.yml` 條目寫清：`continue-on-error: true` · `127.0.0.1:8080` mock · **≠ merge gate** · **≠ staging S1–S4 物证**。  
- **AC-3**：bootstrap **G8** 與 INDEX 敘事一致：required CI 升格 **仍 open/default advisory**（無批文不得标 done）。  
- **AC-4**：Dashboard 敘事 cross-ref 存在且 **不含 Phase% 數字變更**。  
- **AC-5**：Reviewer 對照 `wave-next-code-inspector-v1.md` §3.2 · WH-REV alignment checklist **無反向敘事**（「CI 綠 = prod 可發」）。  
- **AC-6**：non-claim 段：「advisory CI 索引就緒 ≠ Round-2 execute GO ≠ staging 集成完成」。

**Dependencies**  
- **upstream_tickets**: `WH-P7-PROD-prod-rollout-governance-bootstrap-v1` · `WH-P7-NOTIF-PROD-policy-v1` · `WH-P7-NOTIF-staging-integration-execute-v2`（`blocked`）· `.github/workflows/p7-notification-smoke.yml`（只讀）  
- **downstream_waves**: W3-P8-ADV（P8 線分線 · 不重複 P7 正文）· execute-v2（human 物证齊備後另循環）  
- **blocks_if_missing**: 无（纯 doc/index）

**Observability**  
- **verify_commands**:
  - `rg -i "advisory|continue-on-error|non-blocking|required check|127\\.0\\.0\\.1" 04_Workflows/WORKFLOW_INDEX.md docs/WAVE_PROGRESS_DASHBOARD.md`
  - `rg "continue-on-error|127\\.0\\.0\\.1" .github/workflows/p7-notification-smoke.yml`
  - `rg "G8|advisory|required CI" 04_Workflows/tickets/WH-P7-PROD-prod-rollout-governance-bootstrap-v1_state.md`
- **evidence_artifacts**: WORKFLOW_INDEX diff · Dashboard 敘事 diff（无 % 变更）· 子票 B_REPORT `changed_files`  
- **trace_fields**: 无 runtime trace；索引鍵 `ci_class: advisory|human_env` · `p7_round2_execute: blocked`  
- **success_signals**: 三類 P7 smoke/CI 路徑均有 advisory 或 human-env 標籤 · G8 仍 open/advisory  
- **failure_signals**: 任一條目写「merge gate」/「required check」而无批文 · 宣稱 Round-2 execute 完成

**Risks / Edge Cases**  
- **RSK-W2-13** INDEX 与 bootstrap G8 雙 SSOT 衝突（L/M）→ mitigation: bootstrap G8 為升格 SSOT · INDEX 只索引角色；residual: accept  
- **RSK-W2-14** 讀者混淆 P7 与 P8 advisory 索引（M/M）→ mitigation: 首段写分線表 · cross-ref W3-P8-ADV；residual: accept

**Output Artifact**  
- 更新：`04_Workflows/WORKFLOW_INDEX.md` P7 advisory 段 · `docs/WAVE_PROGRESS_DASHBOARD.md` 敘事一句  
- 可選：`docs/internal/p7_advisory_ci_index_v1.md` · 子票 `W2-P7-advisory-ci-ssot-index-v1_state.md` FRAME

**B/C/D/O Landing Plan**  
- **B** 建 spec：INDEX 段 outline + P7/W3 分線表 + non-claims  
- **C** 落文檔：INDEX + Dashboard 敘事 diff（AllowedPaths 内）  
- **D** 驗證：Reviewer rg 抽樣 + 對照 inspector §3.2 + bootstrap G8  
- **O** trace：Scribe Progress「W2-P7-advisory-ci index ready · G8 仍 advisory · Round-2 blocked」

```yaml
human_only_prereqs: []
infra_only_prereqs: []
security_only_prereqs: []
non_claims:
  - p7-notification-smoke 已升格 required check
  - P7 Round-2 execute 已完成
  - advisory CI = prod 閉環 / staging S1–S4 物证
  - Phase% 上调
```

---

### Wave 2 — human-only / infra-only / security-only 汇总说明

| 票 | 类型 | 为何纳入 Master Plan（而非等 human 做完再开票） |
|----|------|--------------------------------------------------|
| **W2-T1** | **human-only** | Round-2 首要阻塞是 **无真 governance_dual 批文**；若无 request/留痕 runbook，Implementer 与 Reviewer 无法一致判定 G4 何时从 `open`→`partial`，易伪称「治理已齐」。开票目的是 **明文化请求路径与物证栏**，不是 AI 代拿批文。 |
| **W2-T2** | **infra-only** | Infra provision 只能由 ops 执行；Master Plan 需 **provision spec + 物证模板** 才能并行准备，且避免 W2-T4/T5 在 host 未知时 over-claim。 |
| **W2-T3** | **security-only** | Security sign-off 不可自动化；checklist 票让 **审查范围与归档格式** 在 execute 前冻结，防止「口头批准」或 Implementer 跳过 G6。 |
| **W2-T4** | **human + infra** | allowlist 涉及 **客户 human attestation + Infra 部署**；无 checklist 则 P-4 在 execute-v2 中不可审计，且 prod URL 混入风险高。 |
| **W2-T5** | **infra-only** | reference receiver 已在 **localhost validated**，但 Round-2 阻塞是 **staging slot 上可验签**；spec 票区分 demo vs deploy 物证，防止用 local slot 冒充 staging receiver ready。 |
| **W2-P7-matrix-G1-G5-resume-loop-v1** | **spec-only** | matrix §9 G-1–G-5 仅有 implementation notes、无统一 trace contract；本票承接 W1-T5 上游 trace，为后续 resume impl 票提供 MVP spec + observability 列，**不**冒充 runtime closed。 |
| **W2-P7-advisory-ci-ssot-index-v1** | **doc-only** | P7 `p7-notification-smoke` 等 advisory CI 分散在 bootstrap/policy/workflow；集中索引防止「CI 绿 = Round-2 GO」误读，对齐 Master Review B-3。 |

**Wave 2 解阻顺序（建议 · 与 execute-v2 §解阻最短路徑 对齐）**  
`W2-T1` 批文 request 并行 `W2-T2` endpoint spec → `W2-T3` Security pack（可 host TBD 分支）→ `W2-T4` allowlist（依赖 T2 host）→ `W2-T5` receiver verify（依赖 T2）→ **全部 human/infra/security 物证回填后** 才开 `WH-P7-NOTIF-staging-integration-execute-v2` execute 循环（**不在 Wave 2 规划内施工**）。

**Wave 2 规划补票（可与解阻 spec 并行 · doc/spec-only）**  
`W2-P7-matrix-G1-G5-resume-loop-v1`（依赖 W1-T5 trace · 可與 W2-T1–T5 並行）· `W2-P7-advisory-ci-ssot-index-v1`（无依赖 · 可最早开）。

**Wave 2 完成后 Dashboard / STATE 预期（仍不上调 Phase%）**  
- bootstrap G4/G6：`open` → 仍 open 或 human 回填后 `partial`  
- G3/G5/G7：维持 `partial` 直至 execute-v2 S1–S4 + 48h  
- P7 68% **不变** · Round-2 仍 **`blocked`** 直至五顶前置物证齐备

## Wave 3 — Planned Tickets

> **Planner**：Chat 3 · Wave 3 · P8 / P8.9 · 2026-06-26  
> **焦點**：bridge / advisory / observability / SSOT 對齊 · **敘事與證據** · 最小觀測閉環 · **不新增功能** · **不上調 Phase%**  
> **對照**：Dashboard P8 **80%** · P8.9 **81%**（06-23 基準）· `bridge-smoke.yml` advisory landing · Scenario1 本機 **14/14·7/7** · Scenario2 GA / closure **human blocked**（Wave 4 域 · 本 Wave 僅 cross-ref）

### 規劃摘要表

| Ticket ID | 目的（一行） | lifecycle_phase | Phase | estimated_cycles | blocked / human |
|-----------|--------------|-----------------|-------|------------------|-----------------|
| W3-P8-ADV-advisory-ci-ssot-index-v1 | P8/P8.9 線 advisory CI 與 prod gate 敘事 SSOT 索引收口 | B | P8 · P8.9 | 1 | 无 |
| W3-P89-OBS-delivery-trace-contract-v1 | P8/P8.9 交付鏈 observability contract（trace 欄位 + artifact 地圖） | B | P8.9 · P8 | 1 | 无 |
| W3-P8-BRG-bridge-advisory-crossref-v1 | minimal bridge 與 P8 交付鏈 cross-ref（advisory · 非 prod gate） | B | P8 · P8.5(ref) | 1 | 无 |
| W3-P89-EVD-scenario1-bridge-evidence-index-v1 | Scenario1 / bridge CI 本機證據納入 index 並標 advisory 性質 | B | P8.9 · P8 | 1 | 无 |
| W3-P89-SSOT-state-dashboard-alignment-v1 | P8/P8.9 子票 STATE · Dashboard · WORKFLOW_INDEX 敘事對齊 | B | P8 · P8.9 | 2 | 无 |

---

### W3-P8-ADV-advisory-ci-ssot-index-v1

**Title**：P8 / P8.9 線 advisory CI 與 prod gate 敘事 SSOT 索引

**Goal**：Reviewer 與 Planner 能從單一索引區分辨 **advisory CI**（`bridge-smoke.yml` · 本機 MP/CI smoke 腳本）與 **非 prod gate / 非 required check** 的交付驗證路徑，消除「CI 綠 = 可發 prod」誤讀。

**Scope**

- 在 `04_Workflows/WORKFLOW_INDEX.md` 新增或收口 **「P8 / P8.9 · Advisory vs gate」** 小段：列 `bridge-smoke.yml` · `run_ci_smoke_check_v1.py` · `run_multi_phase_smoke_v1.py` 各自角色。
- 每條 workflow/腳本標註：`advisory` / `local-only` / `continue-on-error`（若適用）/ **非 branch protection required**。
- 交叉引用 `wave-next-code-inspector-v1.md` §3.2 · `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1` B_REPORT §Global #4。
- 更新 `docs/phase-8-operator-backlog-v1.md` 或 `docs/p8_9-verification-bundle-v1.md` **脚注** 一句 advisory 語意（不重寫正文）。
- 可選：新建 `04_Workflows/tickets/W3-P8-ADV-advisory-ci-ssot-index-v1_state.md` FRAME。

**Non-Goals**

- 不修改 `.github/workflows/**` · 不升格 required check · 不宣稱 prod-ready / INT Tier-A。
- 不跑 GA / 不造 run URL · 不觸 P7 / P8.5 / P9 主敘事區塊重寫。
- 不新增 smoke 步驟或改 `run_multi_phase_smoke_v1.py` 行為。

**Acceptance Criteria**

- [ ] WORKFLOW_INDEX 含 **≥3** 條 P8/P8.9 相關 CI/smoke 條目，每條有 **advisory 或 local-gate** 明示標籤。
- [ ] `bridge-smoke.yml` 條目寫清：**landing `origin/main` ≠ GA pass** · Scenario1/2 **遠端 GA 證據另見 P8.5 ops-run**（cross-ref 票 ID，不宣稱已完成）。
- [ ] `run_ci_smoke_check_v1.py` 標為 **repo local release sanity** · **≠ GitHub required workflow**（若無 yml 掛載則寫「無 workflow 綁定」）。
- [ ] Reviewer 抽樣：對照 inspector checklist §3.2 三項 non-claims **無反向敘事**。

**Dependencies**

- 上游：`WH-P85-CI-LAND-v1` · `MP-SMOKE-std-case-multi-phase-smoke-v1` · `CI-SMOKE-multi-phase-smoke-and-metrics-hook-v1` · `W-ORCH-wave-next-control-plane-v1` §P8.5 快照。
- 下游：W4 P8.5 Scenario2 GA 證據票僅 **引用** 本索引，不重複定義 advisory。
- `blocks_if_missing`：无（纯 doc/index）。

**Observability**

- `verify_commands`：`grep -E "advisory|non-blocking|required" 04_Workflows/WORKFLOW_INDEX.md`（或等價搜尋）· 人工對照 inspector §3.2。
- `evidence_artifacts`：WORKFLOW_INDEX diff · 子票 B_REPORT `changed_files`。
- `trace_fields`：无 runtime trace；索引鍵 `ci_class: advisory|local_gate`。
- `success_signals`：三類 smoke/CI 路徑均有 **advisory 或 local-only** 標籤。
- `failure_signals`：任一條目寫「merge gate」/「required check」而無批文證據。

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W3-ADV-01 | 讀者將 `run_ci_smoke_check_v1` exit 1 誤當 GitHub blocking | M | H | 標「local script · 無 workflow 綁定」 | accept |
| RSK-W3-ADV-02 | bridge 索引與 P8.5 runbook 雙 SSOT 衝突 | L | M | bridge 技術細節 defer 至 runbook · 本票只寫角色/advisory | accept |

**Output Artifact**

- 更新的 WORKFLOW_INDEX advisory 段 · 子票 `W3-P8-ADV-*_state.md` · 可選 `docs/internal/p8_p89_advisory_ci_index_v1.md`（若 INDEX 過長）。

**B/C/D/O Landing Plan**

| 階段 | 動作 |
|------|------|
| **B** | FRAME：Goal/AC · AllowedPaths（INDEX · docs · tickets）· `non_claims` 複製 Global non-goals |
| **C** | 實作 doc diff · B_REPORT `changed_files` + grep 抽樣輸出 |
| **D** | Reviewer 對照 `wave-next-code-inspector-v1` §3.2 · C_REPORT 逐條 AC |
| **O** | Scribe：Progress 末尾一條 · STATE `lifecycle_phase: O` · cross-ref Dashboard §Wave-next 敘事（**不改 %**） |

**Wave Master 擴展**

```yaml
wave_id: W3
lifecycle_phase: B
phase_targets: [P8, P8.9]
estimated_cycles: 1
mvp_allowed: true
human_only_prereqs: []
infra_only_prereqs: []
security_only_prereqs: []
non_claims:
  - advisory CI ≠ prod gate / required check / merge gate
  - CI landing ≠ GA pass
  - 不宣稱 Phase% 上調
```

---

### W3-P89-OBS-delivery-trace-contract-v1

**Title**：P8 / P8.9 交付鏈 observability contract（trace 欄位 + artifact 地圖）

**Goal**：實作者與 Reviewer 能從 **固定 artifact 路徑與 JSON 鍵** 追蹤 gate → notify → consumer → backlog 主鏈，無需翻多份票 STATE。

**Scope**

- 新建 `docs/p8_p89_delivery_observability_contract_v1.md`（或等價路徑）：定義 **trace_fields** · artifact 地圖 · success/failure signals。
- 覆蓋：`multi_phase_smoke_run.json` · `p8.9_verification_run.json` · `operator_backlog` CLI/HTTP 輸出 · `export_std_case_metrics_v1` 關鍵欄（`notifications_failed_ack_count` 等）。
- 在 `docs/p8_9-verification-bundle-v1.md` · `docs/phase-8-operator-backlog-v1.md` 各加 **§Observability cross-ref**（3–5 行）。
- 更新 `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` 一列「trace 契約」指向新 doc。
- 子票 STATE：`W3-P89-OBS-delivery-trace-contract-v1_state.md`。

**Non-Goals**

- 不改 producer/consumer 程式 · 不新增 metrics 欄位 · 不建 Grafana/Local UI。
- 不把 bridge HTTP `POST /api/orchestration/bridge` 納入 **mandatory** MP-SMOKE 步驟（僅 optional cross-ref）。
- 不宣稱 prod SLO / alert。

**Acceptance Criteria**

- [ ] Contract doc 列 **≥6** `trace_fields`（例：`case_ref` · `run_id` · `multi_phase_smoke.ok` · `events_summary.count` · `acks_summary.pending_count` · `notifications_failed_ack_count`）。
- [ ] Artifact 地圖覆蓋 MP-SMOKE step 1–7 與 P8.9 bundle 四檔（見 `p8_9-verification-bundle-v1.md` 表）。
- [ ] 每個 failure_signal 對應 **可執行 CLI**（矩陣或 contract 內列命令，不重跑全鏈亦可單步 inspect）。
- [ ] WORKFLOW_INDEX MP-SMOKE / P8.9 REGRESSION 條目各加一行 observability 連結。

**Dependencies**

- 上游：`MP-SMOKE-*` · `P8.9-REGRESSION-*` · `MP-METRICS-*` STATE · Dashboard §Multi-phase smoke。
- 下游：W5 rollup observability 可引用本 contract，不複製全文。
- `blocks_if_missing`：MP-SMOKE artifact 路徑變更須先更新本 contract（本票 AC 自洽於現行腳本）。

**Observability**

- `verify_commands`：`python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json`（規劃階段可引用既有 MP-SMOKE B_REPORT；施工票須重跑）· `python scripts/run_p8_9_verification_bundle_v1.py --case-ref demo_phase --skip-experiment --format json`。
- `evidence_artifacts`：`outbox/verification/<case_slug>/multi_phase_smoke_run.json` · `p8.9_verification_run.json`。
- `trace_fields`：contract 正文 SSOT。
- `success_signals`：`multi_phase_smoke.ok==true` 且七步 `failed_steps` 空 · bundle `events_summary.count>0`（demo_phase 基線）。
- `failure_signals`：任一步 `ok=false` · `notifications_failed_ack_count>0`（CI-SMOKE 規則 cross-ref）。

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W3-OBS-01 | Contract 與腳本 JSON 形狀漂移 | M | M | AC 要求對照 unittest 現行形狀 · 列 `schema_version` | accept |
| RSK-W3-OBS-02 | 讀者以 contract 存在宣稱 prod observability 完備 | L | H | `non_claims` 明示 local/outbox only | accept |

**Output Artifact**

- `docs/p8_p89_delivery_observability_contract_v1.md` · 矩陣/INDEX cross-ref · 子票 STATE。

**B/C/D/O Landing Plan**

| 階段 | 動作 |
|------|------|
| **B** | 從 MP-SMOKE / REGRESSION B_REPORT 萃取欄位 · 凍結 AC |
| **C** | 寫 contract + cross-ref · 可選 `tests/test_p8_p89_obs_contract_v1.py`（僅 doc 鍵存在性 · **若超 scope 則 defer**） |
| **D** | Reviewer 用 contract 對照一次 demo_phase smoke 產物（本地） |
| **O** | Dashboard §Multi-phase smoke 加 observability 連結（敘事 · **不改 %**） |

**Wave Master 擴展**

```yaml
wave_id: W3
lifecycle_phase: B
phase_targets: [P8, P8.9]
estimated_cycles: 1
mvp_allowed: true
human_only_prereqs: []
non_claims:
  - local outbox trace ≠ prod telemetry
  - contract 存在 ≠ SLO/alert 已落地
```

---

### W3-P8-BRG-bridge-advisory-crossref-v1

**Title**：minimal orchestration bridge 與 P8 交付鏈 cross-ref（advisory · 非 prod gate）

**Goal**：P8 operator / MP-SMOKE 敘事與 P8.5 bridge smoke **邊界清晰**：bridge 為 **optional advisory 側線** · in-memory stub · **不阻塞** P8/P8.9 80% 敘事。

**Scope**

- 更新 `docs/phase-8-operator-backlog-v1.md` §Related / §Release sanity：cross-ref `phase8_5-bridge-smoke-runbook-v1.md` · 明示 **bridge ≠ operator backlog 前置**。
- 更新 `04_Workflows/plans/phase-8-commercial-delivery-to-80-plan.md` **脚注**：batch/webhook deferred 不變 · 加 bridge advisory 一句。
- WORKFLOW_INDEX Phase 8 operator 條目與 Phase 8.5 bridge 條目 **雙向連結**（各一句）。
- 更新 `P8-T2` / `P8-API` STATE（或本票 D_REPORT）`cross_refs` 欄，不改正文 deliverables。

**Non-Goals**

- 不改暗部 `minimal_orchestration_bridge.py` · 不改 `bridge-smoke.yml`。
- 不把 bridge 併入 MP-SMOKE 七步（除非尚書省另開功能票）。
- 不宣稱 Scenario1/2 GA 完成 · 不填 run URL。

**Acceptance Criteria**

- [ ] Phase 8 主 doc 含 **bridge advisory** 脚注：**in-memory stub · advisory CI · ≠ prod browser**。
- [ ] WORKFLOW_INDEX P8 operator 與 P8.5 bridge 條目 **互相可導航**。
- [ ] `WH-REV` alignment B_REPORT §P8.5 與本 cross-ref **無矛盾**（Reviewer spot-check）。
- [ ] 全文無「bridge smoke required for Phase 8 release」類表述。

**Dependencies**

- 上游：`docs/phase8_5-bridge-smoke-runbook-v1.md` · `WH-P85-CI-LAND-v1` · P8-T2/P8-API STATE。
- 下游：W4 P8.5 closure 引用本 cross-ref，不重寫 P8 交付定義。
- Wave 3 內依賴：`W3-P8-ADV-*`（advisory 標籤一致）。

**Observability**

- `verify_commands`：人工導航 WORKFLOW_INDEX 兩條目 · grep `in-memory stub` / `advisory` 於 Phase 8 docs。
- `success_signals`：cross-ref 雙向存在 · non-claims 保留。
- `failure_signals`：Phase 8 doc 暗示 bridge GA 為發版 gate。

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W3-BRG-01 | P8.5 Phase% 敘事污染 P8「已 80%」判斷 | M | M | 分欄寫「P8 80% 不含 bridge prod」 | accept |
| RSK-W3-BRG-02 | cross-ref 被讀成「MP-SMOKE 須跑 bridge」 | L | M | 寫 optional / post-MP 側線 | accept |

**Output Artifact**

- 更新的 Phase 8 plan/doc 脚注 · WORKFLOW_INDEX cross-ref · 子票 STATE。

**B/C/D/O Landing Plan**

| B | 列 AllowedPaths · 對照 W-ORCH §P8.5 快照與 Dashboard P8.5 脚注 |
| C | doc/index diff only |
| D | Reviewer 用 alignment checklist §P8.5 #1–#4 對照 Phase 8 新脚注 |
| O | Progress 末尾 · 可選更新 P8-T2 STATE `notes` |

---

### W3-P89-EVD-scenario1-bridge-evidence-index-v1

**Title**：Scenario1 / bridge CI 本機證據納入 P8/P8.9 證據索引（advisory 性質明示）

**Goal**：**本機 14/14·7/7 validated** 與 **`bridge-smoke.yml` landing** 作為 **Scenario1 證據** 被 P8/P8.9 線索引收錄，且與 **遠端 GA / run URL** 嚴格分離。

**Scope**

- 在 `04_Workflows/testing/standard-case-hitl-resume-notify-matrix.md` 或新建 `04_Workflows/testing/p8_p89_evidence_index_v1.md` 增 **Evidence tier** 表：
  - Tier **L-local**：unittest 計數 · MP-SMOKE · P8.9 bundle（命令 + 預期 ok）。
  - Tier **CI-advisory**：`bridge-smoke.yml` landing · **continue-on-error** · **非 required**。
  - Tier **GA-remote**：Scenario1/2 Actions run · **human dispatch** · 需 run URL（**本 Wave 僅占位 · 不填 URL**）。
- 更新 `P8.9-REGRESSION` · `MP-SMOKE` STATE 的 `evidence_tier` 欄或 B_REPORT 附錄。
- WORKFLOW_INDEX bridge 條目引用 evidence index Tier 表。
- 交叉引用 `WH-P85-SMOKE-B-scenario2-ops-run-v1` **blocked** 狀態（誠實 · 不造 GA）。

**Non-Goals**

- 不 dispatch Actions · 不產生 run URL / run_id。
- 不把 advisory CI 升格 · 不改 workflow yml。
- 不宣稱「Scenario1 GA pass」。

**Acceptance Criteria**

- [ ] Evidence index 含 **≥3 tiers** · Tier CI-advisory 每條標 **non prod gate / non required check**。
- [ ] Scenario1 本機證據列明命令：`test_minimal_orchestration_bridge` **14/14** · `test_app_api_orchestration_bridge` **7/7**（引用 runbook · 施工票須附 unittest 輸出語意）。
- [ ] Tier GA-remote 行寫 **pending human** · 指向 W4 ops-run 票 · **无 URL 占位符造假**。
- [ ] Dashboard §Wave-next 敘事可 cross-ref 本 index（Scribe lane · **不改 Phase%**）。

**Dependencies**

- 上游：`WH-P85-CI-LAND-v1` B_REPORT §5 · `WD-P85-T3` closure · MP-SMOKE / P8.9-REGRESSION verification。
- 下游：W4 Scenario2 GA 完成後 Scribe **仅追加** Tier GA-remote 行，不推翻 advisory 標籤。
- `blocks_if_missing`：无（本機 tier 自洽）。

**Observability**

- `verify_commands`：`python -m unittest tests.test_minimal_orchestration_bridge -v` · `python -m unittest tests.test_app_api_orchestration_bridge -v`（暗部 cwd · 引用 runbook）。
- `evidence_artifacts`：evidence index 表 · unittest 輸出語意入 B_REPORT。
- `trace_fields`：`evidence_tier` · `evidence_kind: local_unittest|ci_advisory_landing|ga_remote`。
- `success_signals`：Tier 表與 W-ORCH / WH-REV D_REPORT「可說/不可說」一致。
- `failure_signals`：index 寫 GA pass 而无 URL · 或 advisory 未標 non-required。

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W3-EVD-01 | Tier 表被當 merge checklist | M | H | 表頭加粗 **advisory ≠ gate** · 鏈 inspector §3.3 | accept |
| RSK-W3-EVD-02 | 本機 14/14 被等同遠端 validated | M | H | 分 Tier · 引用 WH-REV「CI landing ≠ GA pass」 | accept |

**Output Artifact**

- `p8_p89_evidence_index_v1.md`（或矩陣段）· 子票 STATE · 相關票 STATE 附錄。

**B/C/D/O Landing Plan**

| B | 從 WH-REV D_REPORT 萃取 tier 定義 · AC 凍結 |
| C | 寫 index + cross-ref |
| D | Reviewer 對照 alignment「不可說」表逐條 |
| O | `closure-scribe` 可引用 · Progress append |

---

### W3-P89-SSOT-state-dashboard-alignment-v1

**Title**：P8 / P8.9 子票 STATE · Dashboard · WORKFLOW_INDEX 敘事對齊收口

**Goal**：P8-T2 · P8-API · P8.9-T2/T3/REG 的 **overall_status / deferred / observability** 與 Dashboard **80%/81%** 敘事及 WORKFLOW_INDEX **同向**，消除 SSOT lag。

**Scope**

- 盤點並更新（**末尾追加** · 不刪歷史）：
  - `P8-T2-operator-pending-visibility-v1_state.md`
  - `P8-API-operator-backlog-http-endpoint-v1_state.md`
  - `P8.9-T2-feedback-ingest-and-downstream-ack-v1_state.md`
  - `P8.9-T3-downstream-dispatch-handler-registry-v1_state.md`
  - `P8.9-REGRESSION-standard-case-verification-bundle-v1_state.md`
- 每票補 Wave Master schema 最小欄：`overall_status` · `lifecycle_phase` · `deferred_items` · `observability.verify_commands` · `non_claims`。
- Dashboard §Phase 7.5 + P8.9 能力摘要 · §Multi-phase smoke：**敘事對齊**（batch/webhook/T4 deferred 保留 · 加 advisory/observability cross-ref）。
- WORKFLOW_INDEX Phase% 脚注與上列 STATE **交叉引用**一致。
- 可選：對照 `W-DOCSYNC-2026-06-24-phase-refresh-v1` open 項 · 列本票 **closed / still-open** 清單。

**Non-Goals**

- 不上調 Dashboard Phase% 數字 · 不改 `master_status`（除非授權 Governance）。
- 不實作 batch approve / resume-latest / P8.9-T4 webhook。
- 不重跑全鏈 smoke 作為本票唯一 AC（引用既有 B_REPORT 即可 · 施工票可選 spot-check）。

**Acceptance Criteria**

- [ ] 五張 P8/P8.9 子票 STATE 均有 `overall_status` + `non_claims`（含 advisory ≠ prod gate）。
- [ ] Dashboard 敘事與五票 deferred 列表 **零矛盾**（Reviewer checklist 3.1）。
- [ ] WORKFLOW_INDEX Phase% 脚注與 Dashboard P8 **80%** · P8.9 **81%** 一致（**數字不改** · 敘事同向）。
- [ ] 產出 **alignment delta** 表（票 ID · 變更欄 · 證據來源）入本票 C_REPORT。

**Dependencies**

- 上游：W3-P8-ADV · W3-P89-OBS · W3-P89-EVD（建議 **先完成或並行** 索引/contract，本票引用）。
- 下游：W5 rollup · Master Plan Review checklist #6 observability 抽樣。
- `blocks_if_missing`：若 W3-P89-OBS contract 未建，本票 observability 欄可暫引用 MP-SMOKE B_REPORT（標 `pending_contract`）。

**Observability**

- `verify_commands`：人工 diff 五 STATE vs Dashboard · `python 04_Workflows/_four_piece_report.py`（若已存在且涵蓋 tickets · **optional**）。
- `evidence_artifacts`：alignment delta 表 · 各 STATE diff。
- `success_signals`：inspector §3.1 四項全勾 · 无 over-claim。
- `failure_signals`：STATE 写 implemented 但 Dashboard 列 deferred 未列 · 或反之。

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W3-SSOT-01 | 追平敘事時无意 Phase% 上调 | L | H | AC 明示「敘事 only」· diff 禁改 % 列 | block if violated |
| RSK-W3-SSOT-02 | 舊 deliverables 格式與 template 衝突 | M | L | 追加 YAML 欄 · 保留原表 | accept |

**Output Artifact**

- 五子票 STATE 更新 · Dashboard/INDEX 敘事段 · `W3-P89-SSOT-*_state.md` · alignment delta。

**B/C/D/O Landing Plan**

| B | 盤點表 · 依賴 W3 前三票 cross-ref |
| C | **Cycle 1**：三 P8.9 STATE + contract cross-ref |
| C | **Cycle 2**：P8-T2/P8-API + Dashboard/INDEX |
| D | Reviewer 全表對照 WH-REV Global #1 · inspector §3.1 |
| O | Progress rollup · `W-DOCSYNC` 交叉標記 |

**Wave Master 擴展**

```yaml
wave_id: W3
lifecycle_phase: B
phase_targets: [P8, P8.9]
estimated_cycles: 2
mvp_allowed: true
mvp_scope: Cycle 1 三 P8.9 STATE + observability contract cross-ref
stretch: Cycle 2 P8 operator STATE + Dashboard 全對齊
non_claims:
  - 敘事對齊 ≠ 功能新增
  - deferred 仍 deferred
```

---

### 如何避免把 advisory CI 誤當 prod gate

1. **三層標籤（寫入每張 W3 票與 evidence index）**：`advisory` · `continue-on-error`（若為 GitHub workflow）· **explicit non-required** — 三者至少出現其二於任何 CI 條目。
2. **證據分 tier（W3-P89-EVD）**：**L-local**（unittest/MP-SMOKE）與 **CI-advisory landing** 不得寫入 Tier **GA-remote**；無 run URL 不得使用「validated」「GA pass」「遠端 CI 綠」。
3. **角色分離（W3-P8-ADV）**：`run_ci_smoke_check_v1.py` = **repo local sanity**；`bridge-smoke.yml` = **P8.5 advisory workflow**；**branch protection / required checks** 僅在 **尚書省批文 + WC-PRE-06/07** 後另開票，**不在 Wave 3**。
4. **Reviewer 硬門（引用既有 SSOT）**：施工收口必過 `wave-next-code-inspector-v1.md` §3.2–3.3 與 `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1` D_REPORT「不可說」表 — **任一宣稱 required/merge gate 而无批文 → C_REPORT needs_changes**。
5. **Progress / Dashboard 紀律**：Wave 3 仅 **末尾 append** 敘事與索引連結 · **禁止** 将 advisory CI 首跑寫成「P8/P8.9 prod closure」或上调 Phase%。

---

### Wave 3 并行與順序

```
W3-P8-ADV (advisory SSOT index)
    ├─► W3-P8-BRG (bridge cross-ref)
    └─► W3-P89-EVD (evidence tiers)
W3-P89-OBS (trace contract) — 可與 ADV 並行
W3-P89-SSOT — 建議在 OBS + ADV + EVD 至少 MVP 後收口（estimated_cycles: 2）
```

**不改**：P7 / P8.5 / P9 Dashboard 主區塊 · P8.5 Scenario2 human dispatch（归 Wave 4 evidence 票）。

## Wave 4 — Planned Tickets

> **Wave 4 Planner**：Chat 4 · 2026-06-26 · **doc-only 規劃** · 主責 **P8.5 / P9**  
> **狀態依據**：Dashboard §Wave-next 敘事（06-25）· `WH-P85-SMOKE-B-scenario2-ops-run-v1` **`blocked`**（`total_count=0` · 无 run URL）· `WH-P9-CI-payment-sandbox-smoke-v1` **`done_with_gaps`**（B_REPORT `<RUN_URL>` placeholder）· `WH-P85-wave-H2-closure-scribe-v1` **`blocked`** on GA evidence  
> **本 Wave 不做**：GA dispatch · CI workflow_dispatch · Phase% 上調 · required CI 升格

### 摘要表

| Ticket ID | 目的（一行） | lifecycle_phase | Phase | estimated_cycles | blocked / human |
|-----------|--------------|-----------------|-------|------------------|-----------------|
| **W4-P85-S2-GA-RUNBOOK-v1** | Scenario2 GA 證據鏈 runbook / STATE 欄位 / Progress 模板精修 | B | P8.5 | 1 | human: Actions `scenario=scenario2` dispatch |
| **W4-P9-CI-FIRST-RUN-SPEC-v1** | P9 payment sandbox CI 首跑 human dispatch spec + 索引對齊 | B | P9 | 1 | human: `p9-payment-sandbox-smoke` workflow_dispatch |
| **W4-P85-H2-CLOSURE-PREP-v1** | wave-H+2 closure scribe 前置 doc 模板（待 GA 證據後可執行） | B | P8.5 | 1 | blocked on W4-P85-S2 human AC |
| **W4-P9-CI-OBS-TRACE-v1** | P9 CI 首跑 observability / trace 欄位 + Dashboard 敘事對齊 | B | P9 | 1 | human: 首跑 run URL 回填 AC |
| **W4-P85-P9-EVIDENCE-SSOT-v1** | P8.5/P9 跨線 GA/CI 證據 SSOT 索引 + non-claims 對照表 | B | P8.5 · P9 | 2 | human: 兩線 run URL 皆待填 |

---

### W4-P85-S2-GA-RUNBOOK-v1

**Title**：P8.5 Scenario2 GA 證據補齊 — runbook 精修 + STATE / Progress 證據欄位對齊

**Goal**：讓 **Scenario2 GA** 的一次合法 `workflow_dispatch`（`scenario=scenario2`）在被 human 執行後，能依固定 SSOT 完整 trace（run URL · run id · 兩 job notice 摘要）並寫入 Progress / 子票 B_REPORT，Reviewer 可逐條對照 AC 關票。

**Scope（AI · doc / spec / index / state 編輯）**

- 精修 `docs/phase8_5-bridge-smoke-runbook-v1.md` §0.3 Scenario2 表：補 **human dispatch 逐步截圖級 checklist**（UI 路徑 · input 值 · 預期 job id）· cross-ref `WH-P85-SMOKE-B-scenario2-ops-run-v1` FRAME 模板
- 在 `WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md` 追加 **Evidence Schema** 小節（`ga_run.url` · `ga_run.run_id` · `job_results.*` · `progress_append` 占位符格式 · **禁止預填假 URL**）
- 更新 `04_Workflows/WORKFLOW_INDEX.md` §1.4 一句：Scenario2 GA **待 human dispatch** · advisory · 非 required
- 可選：`docs/wave-next-playbook.md` 或 internal runbook 交叉引用 Scenario2 證據鏈（**不改 Phase%**）

**Non-Goals**

- **不** dispatch GitHub Actions · **不**修改 `.github/workflows/bridge-smoke.yml`
- **不**宣稱 Scenario2 GA pass / 已首跑 / workflow landing = GA pass
- **不**以本機 bash 探针結果冒充 GA 證據

**Acceptance Criteria**

- **AC-AI-1**：runbook §0.3 含完整 human dispatch 步驟（branch `main` · input `scenario2` · 預期兩 job id）· 與 ops-run 票 FRAME 一致
- **AC-AI-2**：ops-run STATE 含 Evidence Schema · B_REPORT `ga_run` 欄位仍為 **N/A / placeholder**（本票不填 URL）
- **AC-AI-3**：WORKFLOW_INDEX cross-ref 存在 · 語意 **advisory · non-blocking · 非 required**
- **AC-HUMAN-1（待人類）**：human/ops 於 Actions UI 或 `gh workflow run bridge-smoke.yml --ref main -f scenario=scenario2` 完成 **≥1** completed run · **run URL + run id** 回填 ops-run B_REPORT
- **AC-HUMAN-2（待人類）**：兩 job log 含 design-skip + deps-gate skip notice · step exit **0** · Progress 末尾 append（FRAME 模板）

**Dependencies**

- `WH-P85-CI-LAND-bridge-smoke-push-v1`（workflow landing ✅ · commit `99bf1f590`）
- `WH-P85-SMOKE-B-scenario2-v1`（Scenario2 wiring **`validated`**）
- `WH-P85-SMOKE-B-scenario2-ops-run-v1`（執行票 · 本票為其 doc 前置）
- `docs/phase8_5-bridge-smoke-runbook-v1.md` · `.github/workflows/bridge-smoke.yml`（唯讀對照）

**Observability**（human 跑完後如何捕捉）

```yaml
observability:
  verify_commands:
    - "（human 後）grep -E 'scenario2|run_id=' 04_Workflows/00_Agent_Work_Progress.md | tail -5"
    - "（human 後）python -m unittest tests.test_bridge_smoke_workflow_config -v  # 靜態 wiring 回歸"
  evidence_artifacts:
    - "GitHub Actions workflow run URL（ops-run B_REPORT ga_run.url）"
    - "04_Workflows/00_Agent_Work_Progress.md P8.5 Scenario2 段（末尾 append）"
    - "WH-P85-SMOKE-B-scenario2-ops-run-v1 B_REPORT job_results 表"
  trace_fields:
    - "ga_run.run_id"
    - "ga_run.url"
    - "dispatch_input.scenario=scenario2"
    - "job_a_scenario2.status / notice_summary"
    - "job_b_scenario2.status / notice_summary"
  success_signals:
    - "workflow run completed · 僅兩 Scenario2 job success"
    - "ops-run overall_status → done · C_REPORT accepted_with_gaps"
  failure_signals:
    - "total_count=0 runs 仍為 0"
    - "step exit 1 或 unexpected warning → 勿 append Progress 為 pass"
```

**Risks / Edge Cases**

| id | description | L | I | mitigation | residual |
|----|-------------|---|---|------------|----------|
| RSK-W4-01 | human 無 Actions read/write · dispatch 401 | M | H | AC 明列權限前置 · runbook 含 admin 升權指引 | block |
| RSK-W4-02 | 誤選 `scenario=default` 導致 Scenario1 job 跑 | M | M | runbook 粗體警示 · 驗收表列「Scenario1 jobs 未跑」 | accept |
| RSK-W4-03 | doc 寫「已 GA」但 API total_count=0 | L | H | non-claims · Evidence Schema 占位 N/A · Reviewer 對照 API | block |

**Output Artifact**

- `docs/phase8_5-bridge-smoke-runbook-v1.md`（§0.3 精修）
- `04_Workflows/tickets/WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md`（Evidence Schema）
- `04_Workflows/WORKFLOW_INDEX.md`（§1.4 一句）
- 可選：`04_Workflows/tickets/W4-P85-S2-GA-RUNBOOK-v1_state.md`（FRAME 草稿）

**B/C/D/O Landing Plan**

| 階段 | 內容 |
|------|------|
| **B** | FRAME + Evidence Schema + runbook diff spec |
| **C** | Implementer 提交 doc/state 編輯 · B_REPORT `changed_files` |
| **D** | Reviewer 對照 AC-AI-* · 確認 **無假 URL** · 無 over-claim |
| **O** | Scribe：human 完成 AC-HUMAN-* 後更新 Progress · ops-run 關票 · 本票 `done_with_gaps` |

**Wave Master 擴展**

```yaml
wave_id: W4
lifecycle_phase: B
phase_targets: [P8.5]
estimated_cycles: 1
mvp_allowed: true
human_only_prereqs:
  - owner: ops / oncall
    deliverable: "≥1 GA run URL + run_id for scenario=scenario2"
infra_only_prereqs: []
security_only_prereqs: []
non_claims:
  - "workflow landing ≠ GA pass"
  - "本機 bash 探针 ≠ GA 證據"
  - "advisory ≠ required CI"
```

---

### W4-P9-CI-FIRST-RUN-SPEC-v1

**Title**：P9 payment sandbox CI 首跑證據 spec — human dispatch runbook + 索引 / STATE 對齊

**Goal**：讓 **P9 advisory CI**（`p9-payment-sandbox-smoke.yml`）在被 human 首跑後，run URL · summary artifact · `order_status=PAID` 断言可被完整 trace 並寫入 SSOT；本地 21/21 + e2e 證據與遠端 CI 證據鏈分欄不混寫。

**Scope（AI · doc / spec / index / state 編輯）**

- 補 `WH-P9-CI-payment-sandbox-smoke-v1_state.md`：**First Run Evidence Schema**（`ci_run.url` · `ci_run.run_id` · `summary_artifact.p9_payment_sandbox_smoke_summary.json` · `<RUN_URL>` placeholder 說明）
- 新增或精修 **human dispatch 小節**：push/merge 確認 → Actions **P9 payment sandbox smoke (advisory)** → `workflow_dispatch` → 預期 job 步驟 · env `GOV_PAYMENT_SANDBOX_ENABLED=1`
- Scribe 缺口：`04_Workflows/WORKFLOW_INDEX.md` + `docs/wave_c/overview.md` 各 **一句** advisory CI 索引（non-blocking 語意）
- 對照 `p9-wc-m2-fixture-execute.yml` 模式寫 **並列 advisory 說明**（本票不改 yml）

**Non-Goals**

- **不** push / merge workflow · **不** workflow_dispatch 首跑
- **不**升格 required check / merge gate
- **不**宣稱 sandbox DRAFT→PAID = prod 金流 · INT Tier-A pass

**Acceptance Criteria**

- **AC-AI-1**：STATE 含 First Run Evidence Schema · B_REPORT `GitHub 首跑` 仍為 `<RUN_URL>` placeholder
- **AC-AI-2**：human dispatch checklist 完整（workflow 名 · trigger · 預期 execute 命令 · summary artifact 路徑）
- **AC-AI-3**：WORKFLOW_INDEX + overview 各有一句 · 明示 **advisory · continue-on-error · ≠ required**
- **AC-HUMAN-1（待人類）**：human 於 `main`（或含 yml 之 branch）完成 **≥1** `workflow_dispatch` · run **completed**
- **AC-HUMAN-2（待人類）**：真實 **run URL + run id** 回填 B_REPORT · Progress 末尾 append 首跑條目
- **AC-HUMAN-3（待人類）**：job log 或 summary artifact 顯示 `walkthrough_ok=true` · `order_status=PAID`（或 documented skip/warning 路徑）

**Dependencies**

- `WH-P9-CI-payment-sandbox-smoke-v1`（yml 已建 · 本地 21/21 ✅）
- `WH-P9-PROD-payment-happy-path-execute-v1` · `WH-P9-M2-runner-step6-payment-v1`
- `.github/workflows/p9-payment-sandbox-smoke.yml`（唯讀）
- `WH-P9-PROD-payment-sandbox-adapter-v1`

**Observability**

```yaml
observability:
  verify_commands:
    - "python -m unittest tests.test_run_wc_m2_e2e_walkthrough tests.test_payment_sandbox_adapter -v  # 本地回歸"
    - "（human 後）檢查 Actions job artifact p9_payment_sandbox_smoke_summary.json"
  evidence_artifacts:
    - "WH-P9-CI-payment-sandbox-smoke-v1 B_REPORT ci_run.url"
    - "p9_payment_sandbox_smoke_summary.json（CI artifact）"
    - "04_Workflows/00_Agent_Work_Progress.md P9 首跑段"
  trace_fields:
    - "ci_run.run_id"
    - "ci_run.url"
    - "walkthrough_ok"
    - "order_status"
    - "GOV_PAYMENT_SANDBOX_ENABLED"
  success_signals:
    - "CI job completed · summary walkthrough_ok=true · order_status=PAID"
    - "C_REPORT accepted · Scribe INDEX 完成"
  failure_signals:
    - "B_REPORT 仍含 <RUN_URL> placeholder"
    - "宣稱首跑 pass 但 total_count=0"
```

**Risks / Edge Cases**

| id | description | L | I | mitigation | residual |
|----|-------------|---|---|------------|----------|
| RSK-W4-04 | yml 未 on remote main · dispatch 404 | M | H | AC 前置：確認 remote 含 workflow | block |
| RSK-W4-05 | CI 缺 gov_core / fixture 路徑 → warning 但 exit 0 | M | M | runbook 列 expected warning · 與 local 21/21 對照 | accept |
| RSK-W4-06 | 本地 e2e OK 被寫成「CI 首跑 OK」 | M | H | non-claims 分欄 · Evidence Schema | block |

**Output Artifact**

- `04_Workflows/tickets/WH-P9-CI-payment-sandbox-smoke-v1_state.md`（Evidence Schema + dispatch spec）
- `04_Workflows/WORKFLOW_INDEX.md` · `docs/wave_c/overview.md`（各一句）
- 可選：`04_Workflows/tickets/W4-P9-CI-FIRST-RUN-SPEC-v1_state.md`

**B/C/D/O Landing Plan**

| 階段 | 內容 |
|------|------|
| **B** | FRAME + First Run spec + INDEX 句草案 |
| **C** | doc/state/index 編輯 · B_REPORT verification = 本地 unittest 命令（**非 CI 首跑**） |
| **D** | Reviewer 確認 non-claims · placeholder 未替換為假 URL |
| **O** | human AC 完成後 Scribe 回填 URL · Reviewer C_REPORT · 票 `done_with_gaps` |

**Wave Master 擴展**

```yaml
wave_id: W4
lifecycle_phase: B
phase_targets: [P9]
estimated_cycles: 1
mvp_allowed: true
human_only_prereqs:
  - owner: ops / human with Actions write
    deliverable: "p9-payment-sandbox-smoke workflow_dispatch run URL"
infra_only_prereqs: []
security_only_prereqs: []
non_claims:
  - "sandbox CI ≠ prod 金流"
  - "advisory CI ≠ merge gate"
  - "本地 21/21 ≠ GitHub 首跑"
```

---

### W4-P85-H2-CLOSURE-PREP-v1

**Title**：P8.5 wave-H+2 closure scribe 前置 — doc 模板 + entry STATE 收口欄位（blocked until GA evidence）

**Goal**：預置 **closure-scribe** 可執行模板，使 human 完成 Scenario2 GA 後 Scribe 能在 **一輪 doc 施工** 內完成 entry → `done_with_gaps` · Progress rollup · INDEX cross-ref，無需臨時發明欄位。

**Scope（AI · doc / spec / state 編輯）**

- 精修 `WH-P85-wave-H2-closure-scribe-v1_state.md`：**Closure Rollup Template**（GA evidence 段 · bridge stub non-claims · optional follow-up 清單占位）
- 更新 `WH-P85-wave-H2-entry-v1_state.md` notes：**post-GA 收口欄位**（`done_with_gaps` 條件 checklist · 仍 **不** 升 status）
- Progress **rollup 模板**（末尾 append · 不改寫 Wave-H+1 歷史段）
- WORKFLOW_INDEX §1.4 **post-closure 一句**（draft · 標 `pending GA evidence`）

**Non-Goals**

- **不**在 GA 證據缺失時將 closure-scribe / entry 標 `done` / `done_with_gaps`
- **不**修改 `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 數字
- **不**實作 bridge 程式 · **不**升格 required CI

**Acceptance Criteria**

- **AC-AI-1**：closure-scribe 票含可複製 Rollup Template · Hard blocking 表與 ops-run 票一致
- **AC-AI-2**：entry 票 notes 含 post-GA checklist · **overall_status 仍 `design_accepted`**
- **AC-AI-3**：closure-scribe **overall_status 仍 `blocked`**（本票不解除）
- **AC-HUMAN-1（待人類）**：`WH-P85-SMOKE-B-scenario2-ops-run-v1` AC-1–AC-4 全 ✅ · run URL 存在
- **AC-HUMAN-2（待人類，下游）**：Scribe 執行 closure 模板 · entry → `done_with_gaps` · closure-scribe → `done_with_gaps`

**Dependencies**

- `WH-P85-SMOKE-B-scenario2-ops-run-v1`（**blocking** · GA 未跑）
- `WH-P85-wave-H2-closure-scribe-v1` · `WH-P85-wave-H2-entry-v1`
- `W4-P85-S2-GA-RUNBOOK-v1`（建議先完成 runbook 對齊）

**Observability**

```yaml
observability:
  verify_commands:
    - "grep 'WH-P85-wave-H2-closure' 04_Workflows/tickets/WH-P85-wave-H2-closure-scribe-v1_state.md"
  evidence_artifacts:
    - "closure-scribe Rollup Template 段"
    - "（human 後）entry overall_status=done_with_gaps"
  trace_fields:
    - "ops_run.ga_run.url"
    - "entry.overall_status"
    - "closure_scribe.overall_status"
  success_signals:
    - "GA evidence 索引於 closure B_REPORT"
    - "Progress rollup 已 append · 無歷史段改寫"
  failure_signals:
    - "closure 標 done 但 ops-run 仍 blocked"
    - "虛構 run URL 出現在 rollup"
```

**Risks / Edge Cases**

| id | description | L | I | mitigation | residual |
|----|-------------|---|---|------------|----------|
| RSK-W4-07 | Scribe 提前收口 · over-claim wave-H+2 closed | M | H | AC-AI-3 維持 blocked · Hard blocking 表 | block |
| RSK-W4-08 | bridge jsonl/dom 票未 Reviewer 仍寫 closed | L | M | optional follow-up 清單 · 非 ops-run blocking | accept |

**Output Artifact**

- `WH-P85-wave-H2-closure-scribe-v1_state.md`（Rollup Template）
- `WH-P85-wave-H2-entry-v1_state.md`（post-GA notes）
- 可選：`04_Workflows/tickets/W4-P85-H2-CLOSURE-PREP-v1_state.md`

**B/C/D/O Landing Plan**

| 階段 | 內容 |
|------|------|
| **B** | 模板 + blocking 對照表 |
| **C** | Scribe/Implementer doc-only diff |
| **D** | Reviewer 確認 **closure 仍 blocked** · 無假 GA |
| **O** | 待 human GA 後由 Scribe 執行 rollup · 本票 `done` |

---

### W4-P9-CI-OBS-TRACE-v1

**Title**：P9 CI 首跑 observability 接線 — Dashboard 敘事 / Progress trace 欄位 / 失敗信號 spec

**Goal**：定義 P9 CI 首跑完成後 **observability 最小集**（trace 欄位 · failure_signals · Dashboard 敘事增量），使 Reviewer 不跑 code 也能判定「首跑證據是否誠實回填」。

**Scope（AI · doc / dashboard 敘事 / state 編輯）**

- 在 `docs/WAVE_PROGRESS_DASHBOARD.md` **§Wave-next 敘事** 追加 P9 首跑 trace 欄位說明（**不改 Phase% 數字** · 只增「待首跑 URL」/「證據欄位」註腳）
- 撰寫 `docs/internal/p9-payment-sandbox-ci-first-run-trace-v1.md`（或等價 internal runbook 段）：success/failure 對照 · artifact 路徑 · non-claims
- 更新 `WH-P9-CI-payment-sandbox-smoke-v1` observability YAML 塊（對齊 playbook §4.3）
- Progress append **模板**（首跑條目 · 最小欄位：date · ticket · run_id · URL · walkthrough_ok · order_status · advisory 註明）

**Non-Goals**

- **不**執行 CI · **不**填 run URL
- **不**新增 metrics HTTP / Prometheus 接線（非本票）
- **不**宣稱 CI 首跑 = prod payment closure

**Acceptance Criteria**

- **AC-AI-1**：internal trace doc 存在 · 含 verify_commands · evidence_artifacts · trace_fields · success/failure_signals
- **AC-AI-2**：Dashboard 敘事增量已寫 · Phase% **未改**
- **AC-AI-3**：P9 CI 票 observability 塊與 trace doc 一致
- **AC-HUMAN-1（待人類）**：首跑 run URL 依 trace doc 回填 B_REPORT + Progress
- **AC-HUMAN-2（待人類）**：Reviewer 依 failure_signals 判定 honest pass / blocked

**Dependencies**

- `W4-P9-CI-FIRST-RUN-SPEC-v1`（建議同 Wave 並行或緊接）
- `WH-P9-CI-payment-sandbox-smoke-v1`
- `docs/WAVE_PROGRESS_DASHBOARD.md`（敘事 only）
- `04_Workflows/review_checklists/wave-next-code-inspector-v1.md`（non-claims 對照）

**Observability**

```yaml
observability:
  verify_commands:
    - "test -f docs/internal/p9-payment-sandbox-ci-first-run-trace-v1.md"
    - "grep -c 'Phase%' docs/WAVE_PROGRESS_DASHBOARD.md  # 確認未改 % 列"
  evidence_artifacts:
    - "docs/internal/p9-payment-sandbox-ci-first-run-trace-v1.md"
    - "Dashboard §Wave-next P9 敘事增量"
  trace_fields:
    - "ci_run.url"
    - "ci_run.run_id"
    - "p9_payment_sandbox_smoke_summary.json"
    - "notifications_failed_ack_count  # 若 smoke 串 MP 時"
  success_signals:
    - "trace doc + Dashboard 敘事一致"
    - "human 回填後 C_REPORT 引用 trace_fields"
  failure_signals:
    - "Dashboard Phase% 被 Planner 改動"
    - "trace doc 宣稱首跑已完成"
```

**Risks / Edge Cases**

| id | description | L | I | mitigation | residual |
|----|-------------|---|---|------------|----------|
| RSK-W4-09 | Dashboard Phase% 誤改 | L | H | AllowedPaths 限敘事段 · Reviewer grep 基线 | block |
| RSK-W4-10 | W-ORCH 與子票 STATE 不同步 | M | M | 本票 cross-ref WH-REV alignment · 以子票 B_REPORT 為準 | accept |

**Output Artifact**

- `docs/internal/p9-payment-sandbox-ci-first-run-trace-v1.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md`（§Wave-next 敘事增量 only）
- `WH-P9-CI-payment-sandbox-smoke-v1_state.md`（observability 塊）

**B/C/D/O Landing Plan**

| 階段 | 內容 |
|------|------|
| **B** | trace spec + Dashboard 敘事 diff 草案 |
| **C** | doc 施工 |
| **D** | Reviewer + code-inspector non-claims 對照 |
| **O** | human 首跑後 Scribe 依模板 append · 更新敘事「URL 已回填」|

---

### W4-P85-P9-EVIDENCE-SSOT-v1

**Title**：P8.5 / P9 跨線 GA·CI 證據 SSOT — 對照索引 + W-ORCH non-claims 同步 + alignment checklist 更新

**Goal**：提供 **單一 doc SSOT**，匯總 P8.5 Scenario2 GA 與 P9 sandbox CI 首跑的證據欄位 · human dispatch 入口 · 禁止宣稱表，消除 W-ORCH 快照與子票 STATE 不同步造成的 over-claim 風險。

**Scope（AI · doc / index / state 交叉引用）**

- 新增 `docs/wave4-p85-p9-evidence-ssot-v1.md`：兩線對照表（workflow 名 · yml 路徑 · 子票 ID · Evidence Schema 連結 · human AC 摘要 · **URL 占位 `<PENDING>`**）
- 更新 `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1_state.md` notes：**Wave 4 evidence 段**（P85/P9 run URL 狀態 · 仍 partial）
- 更新 `W-ORCH-wave-next-control-plane-v1_state.md` **notes only**：指向 evidence SSOT · 標明「子票 B_REPORT 優先於 control plane 假設」（**不改** lane 施工 scope）
- `04_Workflows/WORKFLOW_INDEX.md` 增 Wave 4 evidence 索引一句

**Non-Goals**

- **不**代替 human 跑 GA/CI
- **不**在 SSOT 中写入真实或虚构 run URL（统一 `<PENDING>` / N/A）
- **不**修改 Wave 1–3 / Wave 5 區塊 · **不**改 workflow yml

**Acceptance Criteria**

- **AC-AI-1**：evidence SSOT 存在 · 含 P85 + P9 兩線完整對照 · 所有 URL 欄為 `<PENDING>` 或 N/A
- **AC-AI-2**：alignment checklist + W-ORCH notes cross-ref SSOT · 無「已 GA / 已首跑」語句
- **AC-AI-3**：code-inspector non-claims 表與 SSOT 一致（workflow landing ≠ GA pass 等）
- **AC-HUMAN-1（待人類）**：P85 ops-run B_REPORT `ga_run.url` 由 `<PENDING>` → 真实 URL
- **AC-HUMAN-2（待人類）**：P9 CI B_REPORT `ci_run.url` 由 `<PENDING>` → 真实 URL
- **AC-HUMAN-3（待人類）**：SSOT 狀態列更新為 `partial`（一線）或 `complete`（兩線皆有 URL）— **仅 human/Scribe 在证据到位后**

**Dependencies**

- `W4-P85-S2-GA-RUNBOOK-v1` · `W4-P9-CI-FIRST-RUN-SPEC-v1`（Evidence Schema 來源）
- `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1`
- `W-ORCH-wave-next-control-plane-v1_state.md`
- 子票：`WH-P85-SMOKE-B-scenario2-ops-run-v1` · `WH-P9-CI-payment-sandbox-smoke-v1`

**Observability**

```yaml
observability:
  verify_commands:
    - "grep -E '<PENDING>|N/A' docs/wave4-p85-p9-evidence-ssot-v1.md  # 规划阶段应有占位"
    - "grep -c '已 GA\\|已首跑\\|GA pass' docs/wave4-p85-p9-evidence-ssot-v1.md  # 应为 0"
  evidence_artifacts:
    - "docs/wave4-p85-p9-evidence-ssot-v1.md"
    - "WH-REV alignment checklist Wave 4 段"
  trace_fields:
    - "p85.ga_run.url"
    - "p9.ci_run.url"
    - "ssot.evidence_status  # none|partial|complete"
  success_signals:
    - "SSOT 兩線 URL 皆真实 · evidence_status=complete"
    - "Reviewer PARTIAL_READY → CLOSURE_WITH_GAPS 可升级讨论"
  failure_signals:
    - "SSOT 含虚构 URL"
    - "control plane 與 SSOT 矛盾未标注"
```

**Risks / Edge Cases**

| id | description | L | I | mitigation | residual |
|----|-------------|---|---|------------|----------|
| RSK-W4-11 | W-ORCH 歷史段写「Human 已完成」误导 | H | H | notes 同步 + SSOT 权威声明 | accept |
| RSK-W4-12 | 仅一线有 URL · SSOT 标 complete | M | H | evidence_status=partial 规则 | block |

**Output Artifact**

- `docs/wave4-p85-p9-evidence-ssot-v1.md`
- `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1_state.md`（notes）
- `W-ORCH-wave-next-control-plane-v1_state.md`（notes only）
- `04_Workflows/WORKFLOW_INDEX.md`（一句）

**B/C/D/O Landing Plan**

| 階段 | 內容 |
|------|------|
| **B** | SSOT 框架 + 占位符规则 |
| **C** | doc + state notes 施工 |
| **D** | Master Reviewer / code-inspector 对照 W-MASTER global non-claims |
| **O** | human 两线证据齐后 Scribe 更新 SSOT status · Progress rollup |

**Wave Master 擴展**

```yaml
wave_id: W4
lifecycle_phase: B
phase_targets: [P8.5, P9]
estimated_cycles: 2
mvp_allowed: true
human_only_prereqs:
  - owner: ops
    deliverable: "P85 Scenario2 GA run URL"
  - owner: ops
    deliverable: "P9 payment sandbox CI first run URL"
dependencies_detail:
  upstream_tickets:
    - WH-P85-SMOKE-B-scenario2-ops-run-v1_state.md
    - WH-P9-CI-payment-sandbox-smoke-v1_state.md
  downstream_waves:
    - W5  # observability rollup 可引用 SSOT
  blocks_if_missing:
    - item: "P85 GA run URL"
      owner: "human/ops"
      if_missing: "SSOT evidence_status 最高 partial"
non_claims:
  - "SSOT 存在 ≠ GA/CI 已执行"
  - "alignment checklist 更新 ≠ Phase% 上调"
```

---

### Wave 4 · Human dispatch vs AI 分工说明

| 类别 | AI（Wave 4 doc-only 票）可完成 | 必须 human dispatch（仅以 AC 描述） |
|------|-------------------------------|-------------------------------------|
| **Runbook / spec** | runbook §0.3 精修 · First Run / Evidence Schema · internal trace doc | — |
| **STATE / 模板** | B_REPORT 占位符 · Rollup Template · Hard blocking 表 | 回填 **真实 run URL / run id** · job log 摘要 |
| **Index / Dashboard** | WORKFLOW_INDEX · overview · Dashboard **敘事**（不改 Phase%） | — |
| **GA / CI 执行** | — | P85：`workflow_dispatch` + `scenario=scenario2` · P9：`p9-payment-sandbox-smoke` workflow_dispatch |
| **Progress / 关票** | append **模板** · observability 字段定义 | Progress **实际 append** · ops-run / closure-scribe **overall_status → done** |
| **Verification** | 本地 unittest 命令（静态 wiring / 21/21） | Actions completed run · artifact `p9_payment_sandbox_smoke_summary.json` |

**明确需要 human dispatch 的 AC（AI 仅支援 doc / observability 层）**

1. **W4-P85-S2-GA-RUNBOOK-v1 · AC-HUMAN-1/2** — GitHub Actions 手动跑 Scenario2 · 验证两 job log · append Progress  
2. **W4-P9-CI-FIRST-RUN-SPEC-v1 · AC-HUMAN-1/2/3** — payment sandbox CI 首跑 · URL 回填 · summary 断言  
3. **W4-P85-H2-CLOSURE-PREP-v1 · AC-HUMAN-1/2** — 依赖 #1 完成后 Scribe 执行 closure（human 触发链）  
4. **W4-P9-CI-OBS-TRACE-v1 · AC-HUMAN-1/2** — 首跑 trace 字段实际回填与 Reviewer 判定  
5. **W4-P85-P9-EVIDENCE-SSOT-v1 · AC-HUMAN-1/2/3** — 两线 URL 从 `<PENDING>` 更新为真实值 · evidence_status 升级  

**Wave 4 执行顺序建议**：`W4-P85-S2` ∥ `W4-P9-CI-FIRST-RUN-SPEC` → `W4-P9-CI-OBS-TRACE` → `W4-P85-P9-EVIDENCE-SSOT`；`W4-P85-H2-CLOSURE-PREP` 可与前两票并行（维持 blocked 直到 human GA）。

## Wave 5 — Planned Tickets

> **规划焦点**：cross-wave **tooling / observer CLI / reviewer checklist / evidence ingestion** + **WC-PRE-06/07 治理设计/批文准备**（doc-only · human-only）；**不**做 Wave 1 Master CP 骨架主施工；**不**做纯文案微调；**不**拉升 Phase%；**不**改 Wave 1–4 行为或 `.github/workflows` required 升格。  
> **phase_targets**：Cross-wave observability · P10/P10.5 **编排/观测/治理叙事锚点**（doc/tooling 层 · **非** runtime 自动化闭环）。  
> **规划日期**：2026-06-26 · Wave 5 Planner 第二輪修正（Chat 5 · B-1/B-8）

### Wave 5 最终定位（Master CP SSOT · tooling / governance / observer）· 与 Wave 1 分工

| 维度 | **Wave 1（Chat 1）** | **Wave 5（Chat 5）** |
|------|----------------------|----------------------|
| **主责** | P7.5 上游功能缺口（policy deny · intake CLI · trace · entry index） | **Master CP 骨架 SSOT** · cross-wave 观测 · Review 工具链 · WC-PRE 治理设计 |
| **施工 SSOT** | **W1-P75-*** 四票 · **只消費** Wave 5 schema/commands/index | **W5-T1** commands · **W5-T2** schema/instruction · **W5-T5** lane/playbook index · **W5-T3** observer · **W5-T4** Review checklist · **W5-WC-PRE-06/07** |
| **明确不做** | Master CP 模板/commands/lane/instruction **主维护** · G-1–G-5 runtime · P7 notify 接線 | P7.5 功能缺口主施工 · P10 **runtime**（S15 notify · intake API · prod 闭环）· required CI 升格 |
| **并行规则** | W1-P75-* 可与 W5-T3/T4/WC-PRE **并行** | **禁止** Wave 1 双份落地 schema/commands；W1 票引用 W5-T1/T2 路径 |

**P10 / P10.5 诚实边界（对齐 Dashboard · Phase% 不变）**

- **P10（48%）**：实验线 auto ≈86.7%（15 步）为**实验/沙盒叙事**；**S15 notify · intake API · prod 闭环仍 gap** — 本 Wave **不**排完整 S1–S15 runtime 施工，**不**宣稱 P10 prod-ready。
- **P10.5（32%）**：`distill_control_plane_skills_lite` 等为 **skeleton** · 无 prod 蒸馏闭环 — 本 Wave 仅可在 INDEX/observer 层**索引**既有 registry/skills 路径，**不**交付 prod 蒸馏管线。
- **WC-PRE-06/07**：Wave 5 负责 **design_ready + 批文 template**；**尚未**获尚書省 `approval_status=approved` — **不得**改 branch protection / PR required。

### 摘要表

| Ticket ID | 目的（一行） | lifecycle_phase | Phase | estimated_cycles | blocked / human |
|-----------|--------------|-----------------|-------|------------------|-----------------|
| **W5-T3-evidence-ingestion-observer-v1** | 定义 smoke/B_REPORT/run URL 证据汇入 spec + 只读 observer CLI 骨架 | B | P10 · P10.5 | 2 | 无 |
| **W5-T4-wave-plan-reviewer-checklist-v1** | Master Plan Review + 跨 Wave rollup 专用 Reviewer checklist + ticket reviewer 附页模板 | B | P10 | 1 | 无 |
| **W5-T5-cross-wave-playbook-index-v1** | Wave Master / Wave-next / Multi-Chat skill 索引汇整 + Dashboard 叙事锚点（P10 非-runtime 边界） | B | P10 | 1 | 无 |
| **W5-WC-PRE-06-governance-spec-v1** | P10 相关 CI governance 升格设计稿对齐 + 批文 template（toolchain health L0→L2） | B | P10 | 1 | **human** 尚書省批文（design 票本身 AI 可交付） |
| **W5-WC-PRE-07-approval-workflow-v1** | mandatory smoke CI 设计稿 + human 批文流程 SSOT（谁批 · 何种证据 · rollback） | B | P10 · P10.5 | 1 | **human** 尚書省批文（design 票本身 AI 可交付） |

### 已去重 · Master CP SSOT 归 Wave 5（RB-1 · 方案 A · active 票）

| 原 Wave 1 票 | 处置 | Wave 5 SSOT 承接 |
|--------------|------|------------------|
| ~~W1-T1~~ | **删除** | **W5-T2-wave-master-ticket-template-v1**（schema 模板 + instruction 扩展栏） |
| ~~W1-T2~~ | **删除** | **W5-T1-multi-chat-commands-v1**（`.cursor/commands` 四角色 + Wave Master slash） |
| ~~W1-T3~~ | **删除** | **W5-T5-cross-wave-playbook-index-v1**（lane / playbook / skill 汇整） |
| ~~W1-T4~~ | **删除** | **W5-T2** + **W5-T4**（instruction 扩展 · reviewer 附页模板） |
| ~~W1-T5~~ | **合并/evolve** | **W1-P75-TRACE-UPSTREAM-v1**（Wave 1 · trace 契约 · 非 Master CP） |

> Wave 1 **不再**维护 schema/commands/lane/instruction；Implementer 开 Master CP 施工票请开 **Chat 5 · W5-T1/T2/T5**。

---

### W5-T3-evidence-ingestion-observer-v1

**Title**：Cross-Wave 证据汇入 Observer Spec + 只读 CLI 骨架

**Goal**：Wave 1–4 施工产生的 smoke JSON · B_REPORT verification · run URL 可被**统一只读查询**，Master Reviewer / Orchestrator 不必手工翻多个目录；完成後**观测层**可回答「本 Wave 有哪些可重跑证据、缺哪些 human 占位符」。

**Scope**

- 新建 `docs/wave-evidence-ingestion-spec-v1.md`：
  - 证据类型表（`multi_phase_smoke_run.json` · `multi_case_smoke_run.json` · B_REPORT.verification · GA run URL 占位符 · Progress 末尾条目）
  - 逻辑路径约定（`outbox/verification/**` · `*_state.md` B_REPORT · Progress append-only）
  - `trace_fields` 标准键（`run_id` · `ticket_id` · `ga_run.url` · `notifications_failed_ack_count`）
  - success/failure_signals 与 playbook §4.3 对齐
- 新建 `scripts/observe_wave_evidence_v1.py`（**只读** skeleton）：
  - 输入：`--wave W1|…|W5` 或 `--ticket-id` · `--format json|text`
  - 输出：`{ ok, wave, tickets[], evidence_summary[], gaps[], message }`
  - 扫描：对应 `04_Workflows/tickets/W*-*.md` STATE/B_REPORT + 已知 smoke 产物路径
  - **不**写 DB · **不**改 smoke runner 行为
- 更新 `docs/WAVE_PROGRESS_DASHBOARD.md` §Multi-phase smoke — 增加「证据 observer」索引句（**不改 Phase% 数字**）
- 可选 unittest：`tests/test_observe_wave_evidence_v1.py`（fixture 用 ephemeral tmp · 3–5 cases）

**Non-Goals**

- 不实现 full metrics pipeline / Grafana
- 不改 `run_multi_phase_smoke_v1.py` 等现有 runner
- 不 ingest prod/staging 真 POST 或 secret
- 不宣稱「系统已完全自动化观测」
- **不**闭合 P10 runtime gap（S15 notify · intake API · prod 闭环）— observer 仅只读汇总既有证据
- **不**将 P10.5 skill 蒸馏 skeleton 宣稱为 prod 闭环

**Acceptance Criteria**

- AC-1：`wave-evidence-ingestion-spec-v1.md` 覆盖 ≥4 种证据类型 + trace_fields 表
- AC-2：`observe_wave_evidence_v1.py --wave W1 --format json` 返回稳定 `dict`（含 `ok` · `gaps`）
- AC-3：对已知 demo 路径（如 MP-SMOKE 产物逻辑名）可列出 `evidence_summary` 或 honest `gaps`（无文件时不 crash）
- AC-4：spec 明确 **human-only** 证据（run URL 占位符）与 AI 可验证证据的分界

**Dependencies**

- Wave 1–4 planned tickets（消费其 ticket ID 命名 · 非阻塞施工）
- `docs/wave-master-ticketing-playbook.md` §4.3 observability
- `scripts/run_multi_phase_smoke_v1.py` · `scripts/run_multi_case_smoke_v1.py`（产物格式参考 · 不改）
- Dashboard §Multi-phase smoke & metrics

**Observability**

```yaml
observability:
  verify_commands:
    - "python scripts/observe_wave_evidence_v1.py --wave W5 --format json"
    - "python -m unittest tests.test_observe_wave_evidence_v1 -v  # 若 unittest 交付"
  evidence_artifacts:
    - "docs/wave-evidence-ingestion-spec-v1.md"
    - "observe_wave_evidence_v1.py stdout JSON"
  trace_fields:
    - "run_id"
    - "ticket_id"
    - "evidence_type"
    - "gap_reason"
  success_signals:
    - "CLI ok=true 且 gaps 对缺失证据 honest 标注"
  failure_signals:
    - "静默忽略 B_REPORT 空 verification"
    - "伪造 run URL 为已验证"
```

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W5-T3-01 | Wave 1–4 票 ID 未定时 observer 误报 gaps | M | L | `--wave` 过滤 + spec 注明 planning 阶段 gaps 预期 | accept |
| RSK-W5-T3-02 | 路径硬编码违反 Rule 6 | M | H | 用 `gov_paths` / Master_Map 逻辑名 · 禁磁盘绝对路径 | block→mitigate |
| RSK-W5-T3-03 | skeleton 被误标为 production observability | M | M | spec + CLI docstring 标 skeleton · non_claims | accept |

**Output Artifact**

- `docs/wave-evidence-ingestion-spec-v1.md`
- `scripts/observe_wave_evidence_v1.py`
- `tests/test_observe_wave_evidence_v1.py`（可选 MVP）

**B/C/D/O Landing Plan**

| 阶段 | 动作 |
|------|------|
| **B** | Spec 冻结证据类型与 trace_fields |
| **C** | Implementer 交付 CLI skeleton + spec · cycle 1；unittest cycle 2 若拆 |
| **D** | Reviewer 跑 CLI + 对照 spec 逐条 AC |
| **O** | Scribe Dashboard 索引句 + Progress 末尾；Orchestrator 关票 |

**wave_id**: W5 · **lifecycle_phase**: B · **estimated_cycles**: 2 · **mvp_allowed**: true（MVP=spec+CLI text/json；stretch=unittest） · **human_only_prereqs**: []

**non_claims**

- 非 production metrics backend
- 非自动关闭 human-blocked 票
- 不替代 Reviewer 人工 over-claim 判定

---

### W5-T4-wave-plan-reviewer-checklist-v1

**Title**：Wave Master Plan Review Checklist + 跨 Wave Rollup Inspector

**Goal**：Master Reviewer 验收 Chat 1–5 规划质量时有专用 SSOT（对照 playbook §5.3），并可 spot-check 跨 Wave 依赖与 observability 字段；完成後**规划层 Reviewer 工具链**与执行层 `wave-next-code-inspector-v1.md` 并列、不混用。

**Scope**

- 新建 `04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md`：
  - playbook §5.3 Master Plan Review Checklist 展开为可勾选表
  - 扩展：observability 字段抽样规则（§4.1–4.3）
  - 扩展：Cross-wave dependency 对照 W-MASTER §Cross-Wave Dependencies
  - Verdict 输出模板（`PLAN_READY` / `PLAN_WITH_GAPS` / `PLAN_REJECT`）
- 新建 `04_Workflows/review_checklists/wave-cross-rollup-inspector-v1.md`：
  - 只读：Wave 1–4 施工完成后的 smoke/metrics/Progress 汇总检查项
  - 引用 W5-T3 spec trace_fields · **不**重复定义
- 新建 `04_Workflows/tickets/_templates/ticket_reviewer_checklist.template.md`（逐条 AC 勾选 · skeleton/placeholder 分栏 · 字段名对齐 **W1-T1** `ticket_state.template.md`）
- 更新 `wave-next-code-inspector-v1.md` — 文首 cross-ref 区分「战术 lane Reviewer」vs「Master Plan Reviewer」（各 1–2 句 · 非全文重复）

**Non-Goals**

- 不跑 prod/staging · 不改 workflow yml
- 不替代 Master Reviewer 人工 verdict
- 不修改 W-MASTER 他 Wave 區塊
- **不**扩展 `ticket_state.template.md` 主 schema（属 **W1-T1** · defer W5-T2）

**Acceptance Criteria**

- AC-1：`wave-master-plan-reviewer-v1.md` 含 playbook §5.3 全部 9 项（blocking 标注一致）
- AC-2：含 observability 抽样合格/不合格示例各 ≥1（YAML 块）
- AC-3：`wave-cross-rollup-inspector-v1.md` 引用 W5-T3 trace_fields · 无重复定义
- AC-4：Reviewer 仅读 checklist 即可对 W-MASTER 填 `C_REPORT` Master Plan Verdict 段
- AC-5：`ticket_reviewer_checklist.template.md` 存在 · 含 AC 逐条 · verification 占位 · over-claim 拦截项 · cross-ref W1-T1 模板字段名

**Dependencies**

- `docs/wave-master-ticketing-playbook.md` §4 · §5
- `04_Workflows/review_checklists/wave-next-code-inspector-v1.md`
- **W1-T1**（ticket state 字段 SSOT · checklist 附页对齐 · 可并行）
- W5-T3（rollup inspector cross-ref · 可并行开工 · T3 未就绪时标 gap）

**Observability**

```yaml
observability:
  verify_commands:
    - "rg 'PLAN_READY|PLAN_REJECT' 04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md"
    - "rg 'observability' 04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md"
  evidence_artifacts:
    - "04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md"
    - "04_Workflows/review_checklists/wave-cross-rollup-inspector-v1.md"
    - "W-MASTER-wave-plan C_REPORT（Master Plan Review 时使用）"
  trace_fields:
    - "reviewer_verdict"
    - "blocking_issues"
    - "per_wave_notes"
  success_signals:
    - "Master Reviewer C_REPORT verdict 与 checklist 一致"
  failure_signals:
    - "checklist 缺 blocking 标注"
    - "与 playbook §5.3 项数不一致"
```

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W5-T4-01 | 与 wave-next-code-inspector 职责重叠 | M | M | 文首职责分表 · 不同文件名 | accept |
| RSK-W5-T4-02 | Wave 1–4 规划未完成时 rollup 无内容 | H | L | rollup checklist 标注「执行阶段启用」 | accept |

**Output Artifact**

- `04_Workflows/review_checklists/wave-master-plan-reviewer-v1.md`
- `04_Workflows/review_checklists/wave-cross-rollup-inspector-v1.md`
- `04_Workflows/tickets/_templates/ticket_reviewer_checklist.template.md`
- `wave-next-code-inspector-v1.md`（cross-ref 增量）

**B/C/D/O Landing Plan**

| 阶段 | 动作 |
|------|------|
| **B** | 对照 playbook §5.3 列检查项 |
| **C** | Scribe 撰写两份 checklist + inspector cross-ref |
| **D** | Master Reviewer dry-run：用 checklist 审 W-MASTER Wave 5 區塊 |
| **O** | W-MASTER `C_REPORT` Master Plan Verdict 首次使用本 checklist |

**wave_id**: W5 · **lifecycle_phase**: B · **estimated_cycles**: 1 · **mvp_allowed**: false · **human_only_prereqs**: []

---

### W5-T5-cross-wave-playbook-index-v1

**Title**：Wave Master / Wave-next / Multi-Chat Playbook 汇整索引

**Goal**：Planner / Orchestrator / 新 chat 接战时可从单一索引找到「该读哪份 playbook、哪条 traversal、哪张票是 SSOT」，减少 W-MASTER · W-ORCH · wave-next · SKILL 四套文档来回跳；完成後**下一輪 Wave 编排**起手成本降低。

**Scope**

- 更新 `04_Workflows/WORKFLOW_INDEX.md` — 新节「Wave Master · Wave-next · Multi-Chat」：
  - SSOT 位阶表（Dashboard Phase% · W-MASTER · W-ORCH · 子票 STATE）
  - Traversal 图（规划阶段 vs 执行阶段 vs Reviewer 收口）
  - 链接：`wave-master-ticketing-playbook.md` · `wave-next-playbook.md` · `multi-chat-ticket-workflow/SKILL.md` · `multi_chat_roles.mdc`
- 更新 `docs/WAVE_PROGRESS_DASHBOARD.md` — **新增** §Wave Master 编排叙事（3–8 条要点 · **不改 Phase% 数字**）：
  - 必须含 P10/P10.5 **非-runtime 边界**（S15 notify · intake API · prod 闭环仍 gap · 蒸馏 skeleton）
  - 必须 cross-ref WC-PRE-06/07 为 **design / pending_approval** · 非已升格
- 可选：`docs/wave-master-ticketing-playbook.md` §7 索引表补 W5 产出路径占位

**Non-Goals**

- 不重写 playbook 正文
- 不合并 W-MASTER 与 W-ORCH state 文件
- 不做 lint/format 全库
- **不**在 INDEX/Dashboard 叙事中排 P10 S1–S15 完整 runtime 施工或宣稱 prod-ready
- **不**假设 WC-PRE-06/07 已获 human `approval_status=approved`

**Acceptance Criteria**

- AC-1：`WORKFLOW_INDEX.md` 含 SSOT 位阶 + traversal + ≥6 条有效相对路径链接
- AC-2：Dashboard 新节明确「规划 vs 执行 vs Reviewer」三阶段 · Phase% 仍指向 06-23 基准 · **且**含 P10 gap 诚实句（对齐 Phase 表 S15/intake/prod）
- AC-3：索引与 `W-ORCH-wave-next-control-plane-v1` lane 表无 hard conflict（冲突以子票 STATE 为准）
- AC-4：Orchestrator 接战读索引即可决定开 Wave Master 还是 Wave-next chat
- AC-5：commands 路径引用 **W1-T2**（非 W5-T1）；未交付时标 `TBD: W1-T2`

**Dependencies**

- **W1-T2**（commands 路径 SSOT · 可并行 · 未就绪时索引标 `TBD: W1-T2`）
- W5-WC-PRE-06/07（Dashboard 叙事 cross-ref · 可 TBD 占位）
- `W-MASTER-wave-plan_state.md` · `W-ORCH-wave-next-control-plane-v1_state.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md` §Wave-next 敘事刷新 · Phase 表 P10/P10.5 行

**Observability**

```yaml
observability:
  verify_commands:
    - "rg 'Wave Master' 04_Workflows/WORKFLOW_INDEX.md"
    - "rg 'Wave Master' docs/WAVE_PROGRESS_DASHBOARD.md"
  evidence_artifacts:
    - "04_Workflows/WORKFLOW_INDEX.md"
    - "docs/WAVE_PROGRESS_DASHBOARD.md（叙事节 diff）"
  trace_fields:
    - "index_section"
    - "ssot_tier"
  success_signals:
    - "WORKFLOW_INDEX 链接可达 · 无死链（相对路径）"
  failure_signals:
    - "索引声称 Phase% 变更"
    - "与 W-ORCH lane 表矛盾且无注明"
```

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W5-T5-01 | Dashboard 叙事与 Phase% 表混淆 | M | H | 新节标题含「叙事 · Phase% 不变」· Scribe 禁止改数字 | accept |
| RSK-W5-T5-02 | W1-T2 commands 未交付时索引过时 | M | L | 占位符 `TBD: W1-T2` + O 阶段刷新 | accept |
| RSK-W5-T5-03 | P10 叙事被误读为 runtime 已排期 | M | H | Dashboard 节显式列 S15/intake/prod gap · non_claims | accept |

**Output Artifact**

- `04_Workflows/WORKFLOW_INDEX.md`（Wave Master 节）
- `docs/WAVE_PROGRESS_DASHBOARD.md`（§Wave Master 编排叙事）

**B/C/D/O Landing Plan**

| 阶段 | 动作 |
|------|------|
| **B** | 列 SSOT 位阶与链接清单 |
| **C** | Scribe 更新 INDEX + Dashboard 叙事 |
| **D** | Reviewer 对照 W-ORCH · W-MASTER 无 conflict |
| **O** | Progress 末尾 · **W1-T2** 完成后可选二次 append 补 commands 链接 |

**wave_id**: W5 · **lifecycle_phase**: B · **estimated_cycles**: 1 · **mvp_allowed**: true · **human_only_prereqs**: []

**non_claims**

- 非 Wave 1–4 功能交付
- 非 P10/P10.5 runtime 施工排期
- 非 CI governance required 升格（见 W5-WC-PRE-06/07 · 仅索引提及批文门槛）

---

### W5-WC-PRE-06-governance-spec-v1

**Title**：P10 CI Governance 升格设计对齐 + 尚書省批文 Template（WC-PRE-06 · doc-only · human-only 批文）

**Goal**：将 toolchain health L0→L1→L2 升格路径与 Wave Master P10 **治理/观测**叙事对齐，产出可被 Reviewer 验收为 **`design_ready`** 的 governance spec + 空白批文 template；**不**实施 CI 变更 · **不**宣稱已获 human 批准。

**Scope**

- 对齐/增量 `docs/toolchain-observability-governance-upgrade-v1.md`（WC-PRE-06 既有设计稿）：
  - 新增 §Wave Master cross-ref：本 Wave 5 与 P10 Phase%（48%）关系 · **explicit non-runtime** 边界
  - L0/L1/L2 定义 · `OG-TOOLCHAIN-HEALTH` 提案行 · rollback playbook 草案
- 新建 `docs/governance/WC_PRE_06_approval_template.md`：
  - **批准方**：尚書省 / 治理委員会（字段：`approver` · `approval_date` · `approval_scope`）
  - **证据形式**：signed `approval_status.L1/L2` · Progress **末尾** append 条目 · 可选 meeting ref（**非** run URL）
  - **前置条件**：L1 advisory 观察期 · L2 须 G1–G8 checklist + rollback 演练（引用 rollout plan）
- 新建 `04_Workflows/tickets/W5-WC-PRE-06-governance-spec-v1_state.md`（FRAME · doc-only）
- `docs/governance/WC_PRE_06_07_rollout_plan.md` — 追加 Wave 5 票 cross-ref 段（**不改** D1–D5 决策正文）

**Non-Goals**

- 不改 `.github/workflows/**` · branch protection · PR required checks
- 不改 `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 数字
- 不实施 `WC-IMPL-L2` · 不跑 mandatory health gate
- **不**填写 `approval_status=approved`（仅 template 占位）

**Acceptance Criteria**

- AC-1：存在 governance spec（`toolchain-observability-governance-upgrade-v1.md` 含 Wave Master + P10 non-runtime 边界段）
- AC-2：存在 `WC_PRE_06_approval_template.md` · 含批准方 · 证据形式 · L1/L2 门槛 · rollback 引用
- AC-3：`approval_status` 区段为 **未批准** 占位 · Reviewer 可判定 **`design_ready`**（**非** `approved`）
- AC-4：spec 与 Dashboard Lane B 表 WC-PRE-06 `pending_approval` 叙事一致 · 无 over-claim
- AC-5：零 workflow yml diff · 零 Phase% 变更

**Dependencies**

- `docs/toolchain-observability-governance-upgrade-v1.md` · `docs/governance/WC_PRE_06_07_rollout_plan.md`
- `docs/WAVE_PROGRESS_DASHBOARD.md` §Lane B · WC-PRE-06 行
- `docs/phase3-5-cost-model-governance-contract-v1.md` §2（gate 分类 · 引用不改正文）

**Observability**

```yaml
observability:
  verify_commands:
    - "rg 'approval_status|design_ready|non-runtime' docs/toolchain-observability-governance-upgrade-v1.md docs/governance/WC_PRE_06_approval_template.md"
    - "rg 'approved' docs/governance/WC_PRE_06_approval_template.md  # 应为占位/未批准语境"
  evidence_artifacts:
    - "docs/toolchain-observability-governance-upgrade-v1.md"
    - "docs/governance/WC_PRE_06_approval_template.md"
    - "04_Workflows/tickets/W5-WC-PRE-06-governance-spec-v1_state.md"
  trace_fields:
    - "approval_status.L1"
    - "approval_status.L2"
    - "design_ready"
  success_signals:
    - "Reviewer C_REPORT: design_ready · approval pending"
  failure_signals:
    - "文档含 approved 已填值"
    - "声称 PR required 已开启"
```

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W5-PRE06-01 | 与 Monitoring Graph L0/L1/L2 命名混淆 | M | M | spec 文首 axis 对照表 | accept |
| RSK-W5-PRE06-02 | 设计稿被误当 implementation 票 | M | H | ticket_id + non_claims · human_only_prereqs | accept |

**Output Artifact**

- `docs/governance/WC_PRE_06_approval_template.md`
- `04_Workflows/tickets/W5-WC-PRE-06-governance-spec-v1_state.md`
- `docs/toolchain-observability-governance-upgrade-v1.md`（Wave Master 增量段）

**B/C/D/O Landing Plan**

| 阶段 | 动作 |
|------|------|
| **B** | FRAME 冻结 · AllowedPaths=docs/governance/** + spec + 本票 STATE |
| **C** | Scribe 撰写 template + spec 增量 · B_REPORT |
| **D** | Reviewer 对照 Dashboard · 判定 design_ready · **不得**标 approved |
| **O** | Progress 末尾 · INDEX cross-ref · 等待尚書省 human 批文 |

**wave_id**: W5 · **lifecycle_phase**: B · **estimated_cycles**: 1 · **mvp_allowed**: true · **human_only_prereqs**: [{ owner: "尚書省/治理委員会", deliverable: "WC-PRE-06 L1/L2 approval_status signed" }]

**non_claims**

- 非 CI implementation · 非 branch protection 变更
- 非 WC-PRE-06 已 human 批准

---

### W5-WC-PRE-07-approval-workflow-v1

**Title**：Mandatory Smoke CI 设计稿 + Human 批文流程 SSOT（WC-PRE-07 · doc-only）

**Goal**：补齐 WC-PRE-07 smoke matrix mandatory CI 的**设计稿 + 批文 workflow**，明确谁批准、何种证据、rollback 条件；Reviewer 可验收 **`design_ready`** · **不**宣稱 PR required 已开启。

**Scope**

- 新建或对齐 `docs/toolchain-smoke-mandatory-ci-runner-v1.md`（WC-PRE-07 设计 SSOT）：
  - optional_ci vs mandatory 边界 · L1 advisory vs L2 required 白名单（对齐 rollout D3）
  - 挂载点：`eval-gate-ci.yml` job 增量（**设计 only** · 无 yml diff）
  - explicit：**≠** INT Tier-A · **≠** P10 S15/intake runtime
- 新建 `docs/governance/WC_PRE_07_approval_template.md`：
  - **批准方**：尚書省（L1 optional_ci advisory）· 尚書省 + 治理委員会（L2 mandatory 子集）
  - **证据形式**：`approval_status.L1/L2` · Progress append · CH 编号引用（rollout plan）· implementation 票号（`WC-IMPL-SMOKE-CI-L1` 等）**另开**
  - **rollback**：关闭 workflow step · 恢复 advisory-only · Progress 留痕
- 新建 `04_Workflows/tickets/W5-WC-PRE-07-approval-workflow-v1_state.md`
- 更新 `docs/WAVE_PROGRESS_DASHBOARD.md` §Lane B WC-PRE-07 行 cross-ref（**不改 Phase%**）

**Non-Goals**

- 不新建/改 `.github/workflows/**`
- 不实施 `WC-IMPL-SMOKE-CI-L1/L2`
- 不把 smoke CI 与 P10 95% 自动化闭环混写
- **不**填写 human 批文

**Acceptance Criteria**

- AC-1：存在 `toolchain-smoke-mandatory-ci-runner-v1.md` · 含 tier 表 · workflow 挂载设计 · rollback 段
- AC-2：存在 `WC_PRE_07_approval_template.md` · 含批准方 · L1/L2 证据形式 · 下游 implementation 票映射
- AC-3：Reviewer 可判定 **`design_ready`** · `approval_status` 仍为 pending/blocked · **非** approved
- AC-4：文档 explicit：mandatory smoke CI **不**闭合 S15 notify / intake API / prod gap
- AC-5：与 `WC_PRE_06_07_rollout_plan.md` D5 一致 · 无 workflow diff

**Dependencies**

- `docs/governance/WC_PRE_06_07_rollout_plan.md` §7 D5 · CH-01 映射
- `routing/toolchain_smoke_matrix_v1.yaml` · `scripts/run_toolchain_smoke_matrix.py`（格式参考 · 不改）
- W5-WC-PRE-06（治理叙事一致 · 可并行）

**Observability**

```yaml
observability:
  verify_commands:
    - "test -f docs/toolchain-smoke-mandatory-ci-runner-v1.md || echo design_draft_expected"
    - "rg 'blocked_on_approval|design_ready' docs/governance/WC_PRE_07_approval_template.md"
  evidence_artifacts:
    - "docs/toolchain-smoke-mandatory-ci-runner-v1.md"
    - "docs/governance/WC_PRE_07_approval_template.md"
    - "04_Workflows/tickets/W5-WC-PRE-07-approval-workflow-v1_state.md"
  trace_fields:
    - "approval_status.L1"
    - "approval_status.L2"
    - "mandatory_ci_scope"
  success_signals:
    - "design_ready · pending_approval"
  failure_signals:
    - "PR required 已开启 over-claim"
    - "P10 prod-ready 暗示"
```

**Risks / Edge Cases**

| id | description | likelihood | impact | mitigation | residual |
|----|-------------|------------|--------|------------|----------|
| RSK-W5-PRE07-01 | WC-PRE-07 与 eval-gate 重复跑 | M | M | D3 白名单 · rollout 已裁定 | accept |
| RSK-W5-PRE07-02 | 设计稿缺失导致 impl 票漂移 | H | M | 本票 AC-1 强制 spec 存在 | accept |

**Output Artifact**

- `docs/toolchain-smoke-mandatory-ci-runner-v1.md`
- `docs/governance/WC_PRE_07_approval_template.md`
- `04_Workflows/tickets/W5-WC-PRE-07-approval-workflow-v1_state.md`

**B/C/D/O Landing Plan**

| 阶段 | 动作 |
|------|------|
| **B** | 对照 rollout D3/D5 · FRAME 冻结 |
| **C** | Scribe 设计稿 + approval template |
| **D** | Reviewer design_ready 判定 · cross-ref Dashboard |
| **O** | human 批文后 **另开** WC-IMPL-SMOKE-CI-* · 本票不关 approved |

**wave_id**: W5 · **lifecycle_phase**: B · **estimated_cycles**: 1 · **mvp_allowed**: true · **human_only_prereqs**: [{ owner: "尚書省", deliverable: "WC-PRE-07 L1/L2 approval + implementation 票授权" }]

**non_claims**

- 非 mandatory CI 已上线
- 非 P10 runtime 交付

---

### Wave 5 Cross-Wave 依赖（本 Wave 内 · RB-2 同步）

```
W5-T2 (schema) ──► W5-T4 (reviewer checklist 附页字段对齐)
W5-T1 (commands) ──► W5-T5 (INDEX 链接 commands 路径 SSOT)
W5-T3 (evidence spec) ──► W5-T4 (rollup inspector cross-ref)
W5-WC-PRE-06 ──► W5-WC-PRE-07 (治理叙事一致 · 可并行)
W5-WC-PRE-06/07 ──► W5-T5 (Dashboard 叙事 cross-ref · 可 TBD)
W1-P75-* (P7.5 trace) ──► W5-T3 (observer 消费 trace_fields · 只读)
W1–W4 planned tickets ──► W5-T3 (observer 扫描目标 · planning 阶段 gaps 预期)
```

| 依赖 | Planner 动作 |
|------|--------------|
| W5-T2 → W5-T4 | checklist 附页字段名对齐 **W5-T2** `ticket_state.template.md` · **不**重复 schema 主施工 |
| W5-T1 → W5-T5 | commands 路径 SSOT = **W5-T1** · INDEX 直接链接 |
| W5-T3 → W5-T4 | rollup checklist 不重复 trace_fields |
| W5-PRE-06 → W5-PRE-07 | smoke CI 批文流程与 health gate 叙事一致 |
| W1-P75-TRACE → W5-T3 | observer 只读消费 `intake.gate_decision` trace 栏 · Wave 1 不维护 CP 模板 |
| W1–W4 → W5-T3 | observer 对未施工票 honest gaps |

---

### 下一波 Multi-Chat 起手模板投资建议

| 优先级 | 票号 | 理由 |
|--------|------|------|
| **P0 · 并行** | **W5-T1** ∥ **W5-T2** | Master CP SSOT 主施工 · schema/commands 须先于 W1-P75 票引用 |
| **P0 · 并行** | **W5-T4** | Master Plan 第三輪 Review 截止前必须就绪；含 reviewer checklist 附页 |
| **P0 · 并行** | **W5-WC-PRE-06** ∥ **W5-WC-PRE-07** | 闭合 B-8 · doc-only · Scribe 可并行 · 不依赖 runtime |
| **P1 · 紧随其后** | **W5-T3** | Wave 1–4 进入 C/D 后价值最大；规划阶段可先交付 spec MVP |
| **P1 · 执行波次** | **W5-T5** | 依赖 W5-T1 commands 路径 + WC-PRE 叙事；适合 W5 末轮 Scribe |

**推荐 Multi-Chat 起手组合（第一轮并行）**

1. **Orchestrator chat** → 待 **W5-T1** 完成后用 Multi-Chat commands
2. **Implementer chat A** → **W5-T2** ticket schema 模板 + instruction 扩展栏
3. **Implementer chat B** → **W5-T1** Multi-Chat commands
4. **Scribe chat A** → W5-WC-PRE-06 governance spec + approval template
5. **Scribe chat B** → W5-WC-PRE-07 smoke CI design + approval template
6. **Reviewer chat** → W5-T4 Master Plan checklist dry-run（第三輪 Review）
7. **Implementer chat C** → W5-T3 observer CLI（与 Scribe 并行 · 不同 AllowedPaths）

**不宜作为起手模板的票**：W5-T5（索引型 · 末轮）· W5-T3（若 Wave 1–4 票 ID 未稳定 · 可先 spec-only）

**Wave 1 起手提醒（与 Wave 5 分工）**：P7.5 上游四票请开 **Chat 1 · W1-P75-*** — Master CP schema/commands 请开 **Chat 5 · W5-T1/T2/T5** · **勿**在 Wave 1 重复维护 CP 骨架。

---

### Global Non-Goals

- ❌ **不**在本輪建立 Wave 1–5 **具體施工** diff（僅框架 + 規範 + 預留區）。
- ❌ **不**微優化已 accepted 模組 · **不**全庫 format/lint。
- ❌ **不**重做 Phase ≥80% 且無 blocking gap 的 Phase（P1/P2/P4/P6/P8.6–8.8 等）。
- ❌ **不**單方面上調 `docs/WAVE_PROGRESS_DASHBOARD.md` Phase%。
- ❌ **不**改 `.github/workflows/**` required / branch protection（無批文）。
- ❌ **不**跑 prod/staging 真 POST · 不 flip env · 不輸出 secret。
- ❌ **不**把 advisory CI / local slot / sandbox 宣稱為 prod-ready · INT Tier-A · required check。
- ❌ **不**伪造 run URL / run_id / human 批文。
- ❌ Wave Planner **不得**更改其他 Wave 區塊或 ticket ID。

---

### Cross-Wave Dependencies

```
Wave 1 (P7.5 上游 · W1-P75-* 四票 · 只消費 Wave 5 CP)
    │ W1-P75-TRACE-UPSTREAM-v1: intake.gate_decision trace 欄位 SSOT（觀測 · 非 runtime）
    │ schema/commands/lane/instruction → 單向消費 Wave 5（W5-T1/T2/T5）
    ▼
Wave 2 (P7 staging 解阻 spec) ──blocked──► human Infra/Security（W2-T1–T5 · 非 execute · 非 notify 接線）
    │ 規劃承接（Chat 2 第二輪已補）: W2-P7-matrix-G1-G5-resume-loop-v1 · W2-P7-advisory-ci-ssot-index-v1
    │ notify transport 接線：本 Master Plan 範圍外 defer
    ▼
Wave 3 (P8/P8.9 delivery/outbox) ◄── 既有 P75-G2/G4 gateway+outbox · dispatch registry · operator backlog
    │ （W2 不處理 notify 接線；W3 不重複 notify transport）
    ├──► Wave 4 (P8.5 bridge · P9 payment) ◄── human GA/CI 證據
    │
    ▼
Wave 5 (Master CP SSOT · cross-wave observer · Master Review checklist · WC-PRE 設計 doc-only)
    │ W5-T1/T2/T5 = schema · commands · lane index 權威
    │ W5-T3/T4 消費 W1–W4 施工證據 · 不 duplicate P7.5 功能施工
    └──► W5-T3/T4 rollup（execution 階段啟用）
```

| 依賴 | 說明 | Planner / Implementer 動作 |
|------|------|---------------------------|
| W1 → W2 | **W1-P75-TRACE-UPSTREAM-v1** 定義 `intake.gate_decision` **trace 契約**（doc-only）；G-1–G-5 **runtime** 歸 Wave 2 新票 | W2 補票須 cross-ref W1-P75-TRACE trace 欄位 + P75-G* 票 ID；**不得**在 W1 做 resume-loop runtime |
| W1 → W5 | **單向消費**：Wave 1 **只消費** Wave 5 Master CP（W5-T1/T2/T5）；Wave 1 **不維護** schema/commands/lane/instruction | W1-P75-* 票 FRAME 引用 W5 模板路徑 · **禁止** Wave 1 開 CP 主施工票 |
| W5 → W1 | Master CP 骨架（schema · commands · lane index · instruction） | **Wave 5 權威**（W5-T1 · W5-T2 · W5-T5）；W5-T4 附页对齐 W5-T2 字段名 |
| W2 → W3 | **W2 本 Master Plan 不處理 notify 接線**；W3 依 **既有** P75 gateway/outbox（P75-G2 · P75-G4）與 dispatch registry | W3 **不**重複 notify transport；staging execute-v2 待 W2 human 解阻齊備後 **另循環**（非本規劃票） |
| W2 → W3 | G-1–G-5 resume-loop | **`W2-P7-matrix-G1-G5-resume-loop-v1`**（Chat 2 第二輪已補 FRAME · **spec-only**）；W1-P75-TRACE 僅觀測 |
| W2 → W3 | P7 advisory CI 索引 | **`W2-P7-advisory-ci-ssot-index-v1`**（Chat 2 第二輪已補 · 與 W3-P8-ADV 分線） |
| W3 → W4 | bundle_ready handler 与 P8.9-T3 | W4 不另开重复 registry |
| W4 human → W4 | Scenario2/P9 首跑 | 仅 `evidence` / `runbook` 票 · 不含假执行 |
| W1–W4 → W5 | smoke/metrics/B_REPORT 證據 | W5-T3 observer **只读** 匯總 · W5-T4 Review checklist · **不改** W1–W4 行为 |
| W5 → governance | WC-PRE-06/07 | W5 **W5-WC-PRE-06/07** doc-only 批文/设计 · **不** required CI 升格 · **不** claim approved |

**notify 線邊界（B-4 裁定）**：本 Master Plan **不含** P7 notify transport 接線施工票。W2 現有 W2-T1–T5 僅 human/infra/security **解阻 spec**；W3 假設 P75-G2/G4 已落地之 gateway/outbox 路徑，**不**等待 W2 notify 接線票。若尚書省要求補 notify 接線，須 **另開 Wave 2 執行票** 並更新本表 — 非本輪 Orchestrator 修訂範圍。

**并行規則**：Chat 1/3/5 可在 **doc+planning** 层并行；Chat 2/4 遇 **human blocked** 时仅产出解阻清单票，不与「执行完成」混写。**W5-T1/T2**（Master CP SSOT）与 **W1-P75-***（P7.5 上游）可並行，但 W1 票 **只引用** W5 模板路径、**禁止** Wave 1 维护 CP 主版本；Wave 5 observer/checklist（W5-T3/T4）可与 W1-P75 并行。

---

### Review Protocol

#### A. Master Plan Review（Wave 规划层 · 本票完成后）

| 步驟 | 角色 | 動作 |
|------|------|------|
| 1 | Wave Planner Chat 1–5 | 填各自 `## Wave N — Planned Tickets` · 子票 FRAME 草稿（可另建 `*_state.md`） |
| 2 | **Master Reviewer** | 只读：本票 + 五 Wave 區塊 + 抽样子票 FRAME |
| 3 | Master Reviewer | 写 **C_REPORT**（本票）· verdict 见下 |
| 4 | Wave Master Orchestrator | 更新 STATE · `planning_status: ready_for_execution` 或 `needs_revision` |

**Master Plan Verdict**

| Verdict | 條件 |
|---------|------|
| `PLAN_READY` | 五 Wave 均有 ≥1 票 · 无 over-claim · 依赖/ human 标注完整 · 无跨 Wave ID 冲突 |
| `PLAN_WITH_GAPS` | 有可并行票 · 但某 Wave 仅 blocked/解阻票 · 须列 next wave |
| `PLAN_REJECT` | 伪完成 · 跨 Wave 改 ID · Phase>80% 重开大工程 · 缺 B/C/D/O 路径 |

#### B. 子票 Review（执行层 · 沿用既有）

- 逐票走 **B→C→D→O** · `04_Workflows/tickets/README.md` · `multi_chat_roles.mdc`。
- 涉及 P7/P8.5/P9 战术线时，额外对照 `wave-next-code-inspector-v1.md` non-claims 表。

---

### Progress Update Protocol

| 事件 | 写入位置 | 写入者 |
|------|----------|--------|
| Master plan 框架完成 | 本票 STATE + `docs/wave-master-ticketing-playbook.md` | Wave Master Orchestrator |
| Wave N 规划完成 | 本票 `## Wave N` 區塊 + 可选子票 STATE | Wave N Planner |
| 子票施工完成 | 子票 B/C/D_REPORT + Progress **末尾** | Implementer / Reviewer / Scribe |
| Phase% 变更 | **仅** Dashboard + 授权 Governance | Governance 票 |
| 阻塞 | 子票 STATE `blocked` + Progress 末尾一条 | 任何角色发现即报 Orchestrator |

**格式**：Progress 条目须含 `ticket_id` · 命令/URL 证据 · non-claims 一句 · **不**改写历史段。

---

### Ready-for-Parallelization Checklist

Master Orchestrator 宣告可开 Chat 1–5 前，下列 **须全勾**：

- [x] 本票 FRAME 含 Objective / Baseline / Planning rules / B/C/D/O / Priority / >80% rule / Schema / Ownership / Non-goals / Dependencies / Review / Progress protocol
- [x] `docs/wave-master-ticketing-playbook.md` 已建并与本票 cross-ref
- [x] **五 Wave 區塊已填**（Wave 1–5 Planned Tickets · 2026-06-26 第二輪 Planner 修正完成）
- [x] **Master CP SSOT 裁定**：**方案 A** · 權威 = **Wave 5**（W5-T1 commands · W5-T2 schema/instruction · W5-T5 lane index）· Wave 1 只消費不維護
- [x] **execution_ready**: `true` — 本 Master Plan 可支援後續 Implementer 多 chat 分拆與執行
- [ ] Chat 1–5 起手模板 / playbook §Chat 读取协议 已读（各 Implementer 开工时勾选）
- [ ] 各 Implementer 确认 **只写本 Wave 區塊 · 遵守 Wave 内依赖**
- [ ] 与 `W-ORCH-wave-next-control-plane-v1` 战术线无冲突（P7/P8.5/P9 以子票 STATE 为准）

**当前**：五 Wave 區塊已填 · Master CP SSOT 方案 A 已裁定 · 第三輪 Reviewer verdict = `PLAN_READY` · **execution_ready**。

---

### AllowedPaths（本票 · Wave Master Orchestrator）

- `04_Workflows/tickets/W-MASTER-wave-plan_state.md`
- `docs/wave-master-ticketing-playbook.md`
- `04_Workflows/tickets/README.md`（可选一句索引）
- `04_Workflows/WORKFLOW_INDEX.md`（可选一句索引）

### BlockedPaths（本票 + 全 Wave Planner 共通）

- `core/**` · 暗部 `core/**` · `tests/**`（除非子票 FRAME 明示）
- `.github/workflows/**`（无批文）
- `docs/WAVE_PROGRESS_DASHBOARD.md` Phase% 数字（Planner 不可改）
- `04_Workflows/project_status/master_status.md`（Governance 独占）
- 其他 Wave 的 `## Wave N` 區塊 · 他人 ticket ID

---

## STATE

- **overall_status**: `frame_ready`
- **planning_status**: `ready_for_execution` — Master Plan 規劃／修訂／Review 已完成 · 可開 Wave 子任務 Implementer 并行
- **lifecycle_phase**: O
- **current_owner**: wave_master_orchestrator（Master Plan 收口完成 · execution-ready）
- **next_action**: 依 Wave 1–5 Planned Tickets 開 Implementer 多 chat 分拆 · 遵守 Wave 内依赖与 human blocked 表 · **當次優先序見** `04_Workflows/command_queue/QUEUE.yaml`（`priority_next` · 2026-07-08 Command Queue v1）
- **last_updated**: 2026-06-26 · Wave Master Orchestrator 收口（第三輪 Review 後）
- **wave**: Wave Master · planning v1
- **reviewer_verdict**: `PLAN_READY`
- **review_rounds**: 3
- **reviewer_verdict_notes**: 第一輪 + 第二輪 `PLAN_WITH_GAPS`（B-1〜B-8 · RB-1〜RB-3）；第三輪 Orchestrator 修 RB-1（方案 A）/ RB-2 / RB-3 後 · **第三輪 Reviewer 轻量复验** → **`PLAN_READY`** · 詳細 SSOT 见 `docs/WAVE_MASTER_PLAN_REVIEW_2026-06-26.md`
- **reviewer_report_ssot**: `docs/WAVE_MASTER_PLAN_REVIEW_2026-06-26.md`
- **reviewer_report_sources**:
  - round_1: `docs/WAVE_MASTER_PLAN_REVIEW_2026-06-26.md` §Round 1 · transcript [Wave Master Plan Review](7d630001-ec4e-4561-bbef-2f7e4dcf49d9) · B-1〜B-8
  - round_2: `docs/WAVE_MASTER_PLAN_REVIEW_2026-06-26.md` §Round 2 · transcript [Wave Master Plan Review Round 2](26967be7-cc5c-4cf8-a7d4-9c8f11f805d7) · RB-1〜RB-3
  - round_3: 第三輪 Master Reviewer 轻量复验 · verdict **`PLAN_READY`** · 对照 SSOT §何时可以宣告 PLAN_READY · RB-1/RB-2/RB-3 闭合确认
- **status_by_role**:
  - orchestrator: done — Master Plan 規劃／修訂完成（第三輪 RB-1 方案 A · RB-2 高階表 · RB-3 元資料 · execution-ready 收口）
  - implementer: n/a — 本票非施工 · Wave 子票 Implementer 可据 `planning_status: ready_for_execution` 并行开工
  - reviewer: done_round3 — 第三輪 Master Plan Review 2026-06-26 · verdict **`PLAN_READY`**
  - scribe: done — Review SSOT 已落盘 `docs/WAVE_MASTER_PLAN_REVIEW_2026-06-26.md` · 五张解阻票 Progress 已 append
- **notes**:
  - Wave 1–5 區塊已填；**RB-1 裁定（方案 A）**：Master CP SSOT = **Wave 5**（W5-T1/T2/T5）· Wave 1 = P7.5 四票 `W1-P75-*` 只消費不維護
  - 第二輪 Review 已闭合：Wave 2 G-1–G-5 / P7 advisory（B-2/B-3）· notify 边界（B-4）· Wave 5 WC-PRE（B-8）· Wave 2 observability（B-7）
  - 第一輪 residual B-1/B-5/B-6 → 第三輪 Orchestrator 以 RB-1/RB-2/RB-3 修訂；**individual ticket FRAME 未改**
  - **Known gaps（deferred · 不阻塞本輪执行）**：P10 runtime（S15 notify · intake API · prod 闭环）· Wave 2 notify transport 接線 · Human GA / CI workflow_dispatch · WC-PRE 尚書省批文 — 见 SSOT §仍不在 PLAN_READY 范围
  - 战术线 `W-ORCH-wave-next-control-plane-v1` 仍有效；冲突以**子票 STATE** + Dashboard §Wave-next 为准
  - Phase% 仍以 Dashboard 06-23 为 SSOT · Planner 不可上调

---

## B_REPORT

（本票无 Implementer 施工 · n/a）

---

## C_REPORT

### Master Plan 收口结论

Wave Master Plan 历经 **3 轮** Reviewer / Orchestrator 修訂：Round 1–2 判定 `PLAN_WITH_GAPS` 并闭合 B-1〜B-8；Round 3 Orchestrator 以**方案 A**裁定 Master CP SSOT（权威 = Wave 5）并同步 §Wave Ownership / §Cross-Wave；第三輪 Reviewer 轻量复验确认 RB-1/RB-2/RB-3 闭合、高阶表与 active 票一致。

**当前 verdict = `PLAN_READY`** · `planning_status: ready_for_execution` · **individual ticket FRAME 未改**。

尚存 **known gaps** 类型（runtime / human approval / prod flip）已在 Master Plan 与 SSOT 中**明确标为 deferred**，**不阻塞**本輪 Wave 子任务 Implementer 并行：P10 runtime（S15 notify · intake API · prod 闭环）· Wave 2 notify transport 接線（须另开执行票）· Human GA / CI workflow_dispatch（Wave 4 AC-HUMAN）· WC-PRE-06/07 尚書省批文（design 票可交付 · approval 仍 human）。

详细 Round 1/2/3 摘要、RB 沿革与 `PLAN_READY` gate 条件 → **`docs/WAVE_MASTER_PLAN_REVIEW_2026-06-26.md`**（Review SSOT）。

---

### Master Plan Review Verdict

> **SSOT**：`docs/WAVE_MASTER_PLAN_REVIEW_2026-06-26.md`（Round 1+2+3 摘要 · RB-1〜RB-3 沿革 · `PLAN_READY` gate）

- **reviewer_date**: 2026-06-26
- **verdict**: `PLAN_READY`
- **waves_reviewed**: W1–W5
- **review_rounds_completed**: 3（Round 1+2 Reviewer · Round 3 Orchestrator 修訂 + Reviewer 轻量复验）
- **summary**: Round 1–2 `PLAN_WITH_GAPS` 闭合 Wave 2/5 缺口与 observability；Round 3 Orchestrator 方案 A 闭合 RB-1/RB-2/RB-3；第三輪 Reviewer 确认无 open P0 blocking → **`PLAN_READY`**。
- **blocking_issues**: 无 open P0 · RB-1/RB-2/RB-3 已闭合 · deferred gaps 见 SSOT §仍不在 PLAN_READY 范围
- **over_claims_found**: 无新增
- **per_wave_notes**: 见 SSOT §Master Plan Review Verdict
- **next_action**: 依 Wave 1–5 Planned Tickets 开 Implementer 多 chat 并行 · 遵守 Wave 内依赖与 human blocked 表

**Transcript 归档**（非 SSOT）:

- Round 1: [Wave Master Plan Review](7d630001-ec4e-4561-bbef-2f7e4dcf49d9)
- Round 2: [Wave Master Plan Review Round 2](26967be7-cc5c-4cf8-a7d4-9c8f11f805d7)

---

## D_REPORT

（Scribe 可选：WORKFLOW_INDEX / playbook cross-ref 完成后填写）

---

## 上游 SSOT 交叉引用

| 类型 | 路径 |
|------|------|
| 接战 | `AGENTS.md` §初始化校準 |
| 工程合約 | `04_Workflows/ENGINEERING_CONTRACT.md` · `.cursor/rules/engineering-contract.mdc` |
| Multi-Chat 角色 | `.cursor/rules/multi_chat_roles.mdc` |
| Phase 4 contract | `docs/phase4-multi-agent-collaboration-contract-v1.md` |
| Phase% | `docs/WAVE_PROGRESS_DASHBOARD.md` |
| Wave-next 战术 | `04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md` |
| Playbook | `docs/wave-master-ticketing-playbook.md` |
| Ticket 模板 | `04_Workflows/tickets/_templates/ticket_state.template.md` |
