# Wave-next Code Inspector v1 — Reviewer 只讀驗收清單

> **用途**：Wave-next Multi-Chat 收口 · **Reviewer 專用** · doc-only SSOT。  
> **編排入口**：`04_Workflows/tickets/W-ORCH-wave-next-control-plane-v1_state.md`  
> **對照 pre-flight**：`04_Workflows/tickets/WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1_state.md`

> **職責分界（W5-T4）**：**本檔** = 戰術 lane Reviewer（P7 / P8.5 / P9 施工與 advisory CI）。  
> **Master Plan Reviewer** → `wave-master-plan-reviewer-v1.md`；**跨 Wave 證據 rollup** → `wave-cross-rollup-inspector-v1.md`（消費 W5-T3）。三者**勿混用**。

---

## 1. Reviewer 只讀原則

| 規則 | 說明 |
|------|------|
| **只讀施工** | Reviewer **不**改 workflow yml · **不**跑 prod/staging 真執行 · **不** flip env · **不**調 Phase% |
| **可寫範圍** | 子票 **C_REPORT** · 本 control plane 票 **STATE notes**（經 Orchestrator 合併）· 本 checklist 的 verdict 紀錄（可貼 C_REPORT） |
| **禁止** | 改 FRAME（子票）· 改 B_REPORT · 末尾以外改 Progress · 改 Dashboard / master_status |
| **證據優先** | 宣稱須有 **命令輸出 / run URL / unittest 計數 / 子票 B_REPORT**；無證據 → **Blocked** 或 **Reject-over-claim** |
| **SSOT 位階** | 子票 STATE ＞ control plane 快照 ＞ chat 口述；Phase% 以 Dashboard 06-23 為準 |

---

## 2. 檢查範圍

Reviewer 依各 lane **至少 spot-check** 下列類型（不必全庫 diff）：

| 類型 | 典型路徑 | 檢查重點 |
|------|----------|----------|
| **Workflow yml** | `.github/workflows/p9-payment-sandbox-smoke.yml` · `.github/workflows/bridge-smoke.yml` · `.github/workflows/p7-notification-smoke.yml` | `continue-on-error` · advisory 命名 · 無 secret 明文 · paths/trigger 與子票 FRAME 一致 |
| **子票 `*_state.md`** | 各 lane Primary ticket（見 control plane B_REPORT） | `overall_status` 誠實 · B_REPORT 證據欄已填 · non-goals 未違反 · gaps 未隱藏 |
| **Progress append** | `04_Workflows/00_Agent_Work_Progress.md` **末尾** | 新條目與子票 AC 對齊 · 含 run_id/URL（若宣稱 GA/CI 首跑）· 未改寫歷史段 |
| **Runbook / summary / index** | `docs/phase8_5-bridge-smoke-runbook-v1.md` · `docs/wave_c/overview.md` · `04_Workflows/WORKFLOW_INDEX.md` | 索引與子票一致 · advisory 語意保留 · landing ≠ GA pass 分開寫 |
| **Control plane** | `W-ORCH-wave-next-control-plane-v1_state.md` | 快照與子票 STATE 無衝突 · lane status 已更新 |

---

## 3. 一致性檢查清單

逐項打勾；任一 **blocking** 與對外宣稱衝突 → 不得給 **OK**。

### 3.1 Code / ticket / summary 一致

- [ ] workflow yml 行為與子票 FRAME Goal / Non-goals 一致
- [ ] 子票 `overall_status` 與 B_REPORT 證據一致（例如 `done_with_gaps` 時 gaps 有列）
- [ ] WORKFLOW_INDEX / overview / runbook 未寫與子票相反的狀態
- [ ] Progress 末尾增量與子票 ticket_id / run_id 交叉引用正確

### 3.2 Non-claims 保留

- [ ] CI 仍標 **advisory / non-blocking**（若未獲 required 升格批文）
- [ ] P7 local slot 未寫成客戶 staging SLA / prod-ready
- [ ] P8.5 bridge 仍標 in-memory stub / 非 prod browser（若適用）
- [ ] P9 sandbox 未寫成 real provider / INT Tier-A / prod closure

### 3.3 Over-claim 攔截

- [ ] 無「CI landing = GA pass」— 須有 **run URL** 才可口述 GA
- [ ] 無「unittest 本地 pass = 遠端 validated」
- [ ] 無「Phase% 自行上調」於 ticket / Progress / chat 摘要
- [ ] 無「required check / merge gate」除非 G8 證據 + 批文

### 3.4 Blocked 狀態誠實

- [ ] P7 Round-2 仍 blocked 時，未宣稱真 staging execute 完成
- [ ] P8.5 ops-run 仍 blocked 時，未宣稱 Scenario2 GA pass
- [ ] P9 無 run URL 時，未宣稱 CI 首跑 pass
- [ ] blocked 票有 **next_action** 與負責方（human Infra / ops / Security）

### 3.5 Lane 專項（spot-check）

| Lane | 額外檢查 |
|------|----------|
| **P9** | `p9-payment-sandbox-smoke.yml` 存在 · job 內 `GOV_PAYMENT_SANDBOX_ENABLED=1` 僅 job scope · 子票 gaps（INDEX / run URL）已列 |
| **P7** | execute-v2 STATE = blocked · bootstrap G3–G6 與 narrative 一致 · 無 prod URL flip |
| **P8.5** | ops-run 無 run URL → AC-1/AC-2 ❌ 須誠實 · Scenario2 skip notice 語意未改為 happy path pass |
| **Global** | 對照 `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1` D_REPORT 可說/不可說表 |

---

## 4. 驗收輸出模板

Reviewer 完成 traversal 後，在 **子票 C_REPORT** 或 **control plane C_REPORT** 使用下列模板（擇一或兩者）。

```markdown
## Wave-next Code Inspector Verdict

- **reviewer_date**: YYYY-MM-DD
- **checklist**: `04_Workflows/review_checklists/wave-next-code-inspector-v1.md`
- **lanes_reviewed**: P9 · P7 · P8.5 · Global（刪去未審者）
- **verdict**: OK | Partial | Blocked | Reject-over-claim
- **summary**（2–4 句）:
- **evidence_spot_checks**:
  - P9: …
  - P7: …
  - P8.5: …
- **over_claims_found**: 無 | （列項）
- **blocked_items**:
- **next_action**:
```

### Verdict 定義

| Verdict | 條件 | 典型 next_action |
|---------|------|------------------|
| **OK** | 已審 lane 證據齊 · 敘事誠實 · 無 blocking over-claim | Orchestrator 更新 control plane STATE · 可關子票或標 accepted |
| **Partial** | 部分 lane 完成 · gaps 已誠實列 · 無 false pass | 繼續 pending lane · Scribe 補索引 |
| **Blocked** | 前置未齊 · 無法驗收 · 或關鍵證據缺失 | 維持 blocked · 寫 Progress 阻塞項 · 不關票 |
| **Reject-over-claim** | 發現 landing/local/sandbox 被說成 prod/GA/required | 要求 Implementer/Scribe 修正敘事 · **不得**标 done |

---

## 5. 建議 traversal 順序（Reviewer chat 起手）

1. 讀 `W-ORCH-wave-next-control-plane-v1_state.md`（STATE + 快照 + B_REPORT）。
2. 讀本檔 §1–§3。
3. 讀 `WH-REV-2026-06-P7-P8_5-P9-alignment-checklist-v1` D_REPORT（可說/不可說）。
4. 逐 lane 讀子票 STATE + B_REPORT。
5. 讀 `00_Agent_Work_Progress.md` **末尾 1–3 條**增量。
6. Spot-check 對應 workflow yml + index 一句（若有改）。
7. 填 §4 模板 · 寫 C_REPORT。

---

## 6. 與 Multi-Chat 角色對齊

- 角色邊界：`.cursor/rules/multi_chat_roles.mdc` §Reviewer
- Contract： `docs/phase4-multi-agent-collaboration-contract-v1.md` — Reviewer **must_not** 改 FRAME/STATE/B_REPORT
- 收口後由 **Orchestrator** 更新 control plane `overall_status`（例如 `frame_ready` → `reviewer_partial` / `done`）

---

*版本：v1 · 2026-06-24 · Wave-next control plane 配套*
