# W5 TICKET TEMPLATES — Wave 5 常用票模板

> **設計者**：WAVE5-PLANNING 專線（2026-05-31）
> **用途**：提供 Wave 5 三種最常用的子票模板，讓 runtime 施工可以快速複用已驗證的格式。
> **對齊**：`30_control_plane/W4-X_control_plane_mvp.md`（§3 Ticket Memory 約定）、
>           `40_ticket_memory/_TEMPLATE_ticket_memory.md`（欄位規範）。
> **使用方式**：開工 runtime 切片時，複製模板，填充 `read_set` / `write_set` / `done_definition` 等必要欄位。

---

## 模板 1：Runtime-only Rollout 小票（W5-A 型）

適用情境：為一個新 repo/service 或新 prod CI 流水線嵌入 K-2 rollout 階段（shadow→canary→promote）。

### 模板內容

```
# Ticket Memory — <TICKET-ID>

> **用途**：<一句話說明本票的 runtime 目標>
> **父票**：`workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md`
> **控制面**：`workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`（`lane=runtime` · Reviewer §1.4.1）
> **模板**：`workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`

---

## ticket

- id: **<TICKET-ID>**
- title: **<一句話標題>**

## lane

- lane: **runtime**

## priority

- priority: **P0**（[P0/P1/P2]，視是否接觸 prod 流水線）

## mode

- mode: **runtime-only**（Executor 在 `write_set` 內做 CI / rollout 配置增量）

## goal

在 <目標 workflow 路徑> 的 <目標 job 名／step> 中嵌入 K-2 rollout 階段（shadow → canary → promote），且滿足：

1. **階段完整**：至少包含 shadow、canary、promote 三階段，每階段有 documented 進入/退出條件。
2. **漸進交付**：禁止一次性全量 K-2 主答案；cohort 至少分 2 階。
3. **保護機制**：rollback（觸發即 cohort→0）、pause、override（allowlist + reason）。
4. **Gate 對齊**：canary/promote 決策點須引用 W4-B index gate（`kb_index_*` 非 `missing`）與 W4-C gov metrics。
5. **範圍隔離**：僅改票面 `write_set` 鎖定的 1 條 workflow 與對應 config。

## read_set

| 路徑 | 用途 |
|------|------|
| `workflow_v2/40_ticket_memory/W5-A-K2-ROLLOUT-EXPANSION.memory.md` | 父票 goal / frozen_constraints |
| `<目標 workflow 路徑>`（佔位） | 首條/下一條 prod CI 目標（Planning 續卡填實） |
| `workflow_v2/20_pilot/W3-A/W4-A_rollout_runbook.md` | W4-A 試點流 runbook（參考 shadow/canary/rollback 行為） |
| `workflow_v2/20_pilot/W3-A_case/W4-A_gate_checklist.md` | Gate 勾選範式 |
| `workflow_v2/tools/wf_k2_rollout_run.ps1` | 現有 helper 參考 |

## write_set

| 路徑 | 允許操作 |
|------|----------|
| `<目標 workflow 路徑>`（佔位） | 僅該檔案的指定 job/step 內插入 rollout 步驟 |
| `rollout_pipeline_config.json` | 新增 prod 流配置段（新 `stream_id`，不刪 v0.1 試點流） |
| `workflow_v2/20_pilot/W3-A_case/run_records/**` | 新增 run id 目錄（**禁止**篡改 W4-A 歷史 run） |
| 本票 Memory | 本文 |

## frozen_constraints

1. 漸進交付：禁止一次性全量。
2. 每階段保護：可觀測、停止條件、rollback、override。
3. 治理對齊：G7/G8、W4-B index gate、W4-C gov metrics。
4. 範圍隔離：僅一條 workflow。
5. W4-A 邊界保護：不 retro 改 W4-A DONE。
6. 憲法 §7 禁區：不觸暗部/venv/金鑰。

## done_definition

- [ ] CI workflow 已嵌入 shadow→canary→promote 階段
- [ ] 至少 1 次成功 rollout 可索引（workflow run id / run_records 路徑）
- [ ] rollout 證據含 trace、rollback 記錄、gate 引用
- [ ] 未改 W4-A 試點流或歷史 run_records
- [ ] 未改 `00`/`90`/`99` 全局語義（屬 DOCSYNC 票）
```

---

## 模板 2：Knowledge / Index 擴面小票（W5-B 型）

適用情境：將 index 回填與 gate 從一個 case 擴展到另一個 case／modify `wf_kb_index_*` 支援多 case。

### 模板內容

```
# Ticket Memory — <TICKET-ID>

> **用途**：將 W4-B index 回填與 gate 能力擴展到<目標 case 或新情境>
> **父票**：`workflow_v2/40_ticket_memory/<軸父票>.memory.md`
> **控制面**：`workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`（`lane=runtime`）
> **模板**：`workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`

---

## ticket

- id: **<TICKET-ID>**
- title: **<目標 case / index 擴面> · runtime-only**

## lane

- lane: **runtime**

## priority

- priority: **P1**（通常為 P1，除非觸及 production block 路徑 → P0）

## mode

- mode: **runtime-only**

## goal

將 W4-B 已實現的 `kb_index_*` 回填 + index gate 擴展到<目標 case 或目標範圍>，且滿足：

1. **真實資料**：擴展後的 case 的 `kb_index_*` 為真實 index 結果（非 file_count=0 樣本）。
2. **Gate 對齊**：`wf_kb_index_gate` 在目標 case 上可正確回傳 allow/deny（missing→block, stale→degrade）。
3. **不破壞既有**：W2-1_case 的 index 回填不受影響；既有的 `index_status_*.json` 未被 retro 改寫。
4. **參數化**（若適用）：helper script 支援 `--case-id` 或等價參數，不硬編碼 case path。

## read_set

| 路徑 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-B/W4-B_orch_integration.md` | 既有 index integration 設計 |
| `workflow_v2/tools/wf_kb_index_sync.ps1` | 現有 sync helper（擴展時參考） |
| `workflow_v2/tools/wf_kb_index_gate.ps1` | 現有 gate helper（擴展時參考） |
| `<目標 case 目錄>/W2-1_case.md`（或等價） | 目標 case 的主文檔 |

## write_set

| 路徑 | 允許操作 |
|------|----------|
| `workflow_v2/tools/wf_kb_index_sync.ps1` | 參數化支援（若需要） |
| `workflow_v2/tools/wf_kb_index_gate.ps1` | 參數化支援（若需要） |
| `<目標 case 目錄>/<case>.md` | 追加 `kb_index_*` 段 |
| `workflow_v2/20_pilot/W3-B/index_status_*.json` | 新增目標 case 的 index status |
| 本票 Memory | 本文 |

## frozen_constraints

1. 不破壞 W2-1_case 既有的 index 回填與 gate 行為。
2. 不改 W4-B DONE 口徑。
3. 不觸暗部/venv/金鑰。
4. 不修改 `00`/`90`/`99`（屬 DOCSYNC 票）。

## done_definition

- [ ] 目標 case 的 `kb_index_*` 已真實回填（file_count>0）
- [ ] `wf_kb_index_gate` 在目標 case 上可正確回傳 allow/deny
- [ ] W2-1_case 未受影響（對照前後 diff）
- [ ] 未改 `00`/`90`/`99` 全局語義
```

---

## 模板 3：Observability / Metrics 強化小票（W5-C 型）

適用情境：擴展 gov metrics schema、新增 dashboard 佔位、設計 fail-on-deny 方案、驗證 nightly auto-run。

### 模板內容

```
# Ticket Memory — <TICKET-ID>

> **用途**：<強化 gov metrics / 驗證 nightly / 設計 fail-on-deny 等>
> **父票**：`workflow_v2/40_ticket_memory/<軸父票>.memory.md`（若獨立則無）
> **控制面**：`workflow_v2/30_control_plane/W4-X_control_plane_mvp.md`（`lane=runtime`）
> **模板**：`workflow_v2/40_ticket_memory/_TEMPLATE_ticket_memory.md`

---

## ticket

- id: **<TICKET-ID>**
- title: **<一句話：metrics schema v0.2 / nightly 驗證 / fail-on-deny 設計>**

## lane

- lane: **runtime**（純文檔票可為 planning→review→doc-sync）

## priority

- priority: **P1**（P0 若阻塞其他 W5 軸）

## mode

- mode: **runtime-only**（若 CI 配置變更）或 **planning→review→doc-sync**（若純文檔）

## goal

在不改 G7/G8 治理核心語義的前提下，達成：

1. **Metrics 擴展（若適用）**：擴展現有 `gov-metrics-0.1` schema 至 v0.2，新增 field（如 blocking rate、gate pass/fail trend）。
2. **Nightly 驗證（若適用）**：確認 `gov-gate-metrics.yml` 的 nightly cron job 已自動執行 ≥3 次，且 artifact `gov-gate-metrics` 可下載查閱。
3. **Fail-on-deny 設計（若適用）**：產出治理設計稿，包含可行方案、風險評估（對 prod CI 的影響）、分階段 rollout 建議；**不**含 production 啟用。
4. **Dashboard（若適用）**：產出 dashboard 佔位（Grafana 或等價 config 草稿），**不**上線 production。

## read_set

| 路徑 | 用途 |
|------|------|
| `workflow_v2/20_pilot/W3-C_metrics_schema.md` | 既有 metrics schema |
| `workflow_v2/observability/gov_gate_metrics/*.jsonl` | 既有 metrics 時間序列 |
| `.github/workflows/gov-gate-metrics.yml` | 現有 CI workflow |
| `workflow_v2/20_pilot/W3-C/ci_gate_wire.md` | 既有 PR/nightly/manual 接線設計 |

## write_set

| 路徑 | 允許操作 |
|------|----------|
| `workflow_v2/20_pilot/W3-C_metrics_schema.md` | 新增 v0.2 節（若適用） |
| `workflow_v2/observability/` | 新增 dashboard 配置佔位（若適用） |
| `workflow_v2/20_pilot/W3-C/fail_on_deny_design.md` | 設計稿（若適用） |
| 本票 Memory | 本文 |

## frozen_constraints

1. 不修改 G7/G8/G10 治理核心語義。
2. 不 production 啟用 fail-on-deny。
3. 不修改 `merge_ask_and_k2` / K-2 adapter。
4. 不觸暗部/venv/金鑰。
5. 不修改 `00`/`90`/`99`（屬 DOCSYNC 票）。

## done_definition

- [ ] 擴展/設計已產出可索引文件
- [ ] （若 CI 變更）已有驗證證據（workflow run id）
- [ ] 未違反 frozen_constraints
- [ ] 未改 `00`/`90`/`99` 全局語義
```

---

## 模板使用指引

1. **選模板**：根據票的類型選用對應模板（rollout / index / metrics）。
2. **填空**：將 `<...>` 標記替換為實際值（ticket id、目標路徑、case 名等）。
3. **調整 priority**：預設值可根據實際影響範圍調整（P0 若觸 production 路徑）。
4. **擴充 read_set/write_set**：若任務需要讀/寫額外檔案，在模板基礎上追加。
5. **提交 review**：使用 W4-X 控制面的四 lane 流程：planning → runtime → review → doc-sync。
6. **不破壞既有的 frozen_constraints**：若需要 override，須尚書省書面批准 + 票面留痕。
