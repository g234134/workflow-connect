# Phase Progress Impact Protocol（v1）

> **Ticket**: `FP-PHASE-IMPACT-protocol-v1` · Governance doc · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-13  
> **對齊**：`docs/progress-dashboard-append-protocol-v1.md` · `docs/lane-progress-append-template-v1.md` · `docs/WAVE_PROGRESS_DASHBOARD.md` · playbook `phase_targets`

---

## non_claims（置頂 · 必讀）

| 本協議 **不是** | 說明 |
|-----------------|------|
| ≠ **授權普通票改 Dashboard Phase% 數字格** | 普通票只提案 Δ；寫入 % 僅 W-PROG／Governance |
| ≠ **自動 uplift** | `apply_phase_pct: false` 為預設；不得默認 true |
| ≠ **Phase closure** | 提案／寫入 % ≠ 任一 Phase 結案 |
| ≠ **prod／required CI／Round-2 GO** | 影響敘事不得越級宣稱 |

**位階**

| 文件 | 角色 |
|------|------|
| **本檔** | Phase 影響提案欄位與報告小節 **SSOT** |
| [`docs/progress-dashboard-append-protocol-v1.md`](./progress-dashboard-append-protocol-v1.md) | 誰可寫 Progress／Dashboard／master_status；**提案 Δ vs 寫入 %** |
| [`docs/lane-progress-append-template-v1.md`](./lane-progress-append-template-v1.md) | Progress 末尾條目形狀（含 Phase 影響欄） |
| [`docs/WAVE_PROGRESS_DASHBOARD.md`](./WAVE_PROGRESS_DASHBOARD.md) | Phase% **唯一數字 SSOT** |
| playbook `phase_targets` | FRAME 只列 Phase 名 · **不寫 %** |

---

## 1. Purpose

統一 Multi-Chat 票對 Phase 完成度的**影響聲明**：普通票提案 Δ；僅授權 W-PROG 刷新票可寫入 Dashboard 數字格。

---

## 2. FRAME 必填（Phase 影響）

開票時 Orchestrator **MUST** 在 FRAME（或 Wave Master 擴展旁）填下列欄位；缺任一 → Reviewer `needs_changes`。

| 欄位 | 類型 | 規則 |
|------|------|------|
| `phase_targets` | list[str] | Dashboard Phase 名（如 `P8.5`）；**不寫 %**（與 playbook 一致） |
| `baseline_pct` | str | 提案時引用之 SSOT 基線（如 `06-27 SSOT · P8.5=10%`）；無影響寫 `n/a` |
| `proposed_delta_pct` | str／number | 建議 Δ（如 `+8` 或 `0`）；**僅提案** |
| `evidence_gate` | str | 證據門檻（`L-local`／`CI-advisory`／`GA-remote`／`blocked`） |
| `apply_phase_pct` | bool | **預設 `false`**；僅 W-PROG／Governance 授權票可 `true` |

```yaml
# FRAME 片段示例（普通票）
phase_targets: [P8.5]
baseline_pct: "06-27 SSOT · P8.5=10%"
proposed_delta_pct: "+8"
evidence_gate: L-local
apply_phase_pct: false   # MUST default
```

```yaml
# FRAME 片段示例（W-PROG 刷新票 · 尚書省授權後）
phase_targets: [P8.5, P9]
baseline_pct: "06-27 SSOT"
proposed_delta_pct: "P8.5 +8 · P9 +2（保守端）"
evidence_gate: L-local+CI-advisory
apply_phase_pct: true    # 僅本類票
```

---

## 3. 報告小節「Phase 影響」（B／C／D／Progress）

下列區塊 **MUST** 含小節 `### Phase 影響`（或等價標題）：

| 區塊 | 誰寫 | 必填語義 |
|------|------|----------|
| **B_REPORT** | Implementer | 影響 Phase · baseline · proposed_delta · 實際上調 · non_claims |
| **C_REPORT** | Reviewer | 核對提案是否越權寫 %；`apply_phase_pct` 是否違規 |
| **D_REPORT** | Scribe | 複述結論；Progress 條目是否已含 Phase 影響 |
| **Progress 末尾** | Scribe | 同欄位；見 lane 模板 |

### 必填欄（小節內）

| 欄 | 說明 |
|----|------|
| **影響 Phase** | 與 `phase_targets` 一致 |
| **baseline** | 引用 Dashboard 刷新日／列（如 06-27） |
| **proposed_delta** | 本票建議 Δ |
| **實際上調** | `否`／`待 W-PROG`／`是（W-PROG · YYYY-MM-DD）` |
| **non_claims** | 至少一句誠實邊界 |

```markdown
### Phase 影響

- **影響 Phase**：P8.5
- **baseline**：06-27 SSOT · 10%
- **proposed_delta**：+8（保守端；區間授權 +8～+15）
- **實際上調**：待 W-PROG（`apply_phase_pct: false`）
- **non_claims**：≠ prod browser · ≠ required CI · ≠ Phase closure
```

---

## 4. 寫入規則（提案 Δ vs 寫入 %）

| 角色／票類 | 可做 | 禁止 |
|------------|------|------|
| **普通票**（build／doc／lane） | 提案 `proposed_delta_pct`；敘事腳注（若授權） | 改 Dashboard **數字格**；`apply_phase_pct: true` |
| **Scribe／lane chat** | Progress 末尾記 Phase 影響 | 改 Phase% |
| **W-PROG／Governance 授權刷新票** | 在 STATE 標「已授權寫入」後改數字格 | 回到已廢棄虛高基線（如 06-23 全盤 78%／多數≥80%）而無證據 |
| **Reviewer** | 發現普通票改 % → `needs_changes` | 代替 W-PROG 寫 % |

**唯一可寫數字格** = Governance／尚書省授權的 **W-PROG** 刷新票（且 `apply_phase_pct: true` + 留痕）。

---

## 5. 與既有協議互鏈

| 協議／模板 | 分工 |
|------------|------|
| **本檔** | Phase 影響欄位 · 報告小節 · 提案／寫入分權 |
| **progress-dashboard-append-protocol** | 誰可寫哪類檔；**提案 Δ vs 寫入 %** 分欄 |
| **lane-progress-append-template** | Progress 末尾形狀（含 Phase 影響欄） |

---

## 6. Mini checklist

- [ ] FRAME 五欄齊（含 `apply_phase_pct: false` 預設）
- [ ] B／C／D／Progress 含「Phase 影響」
- [ ] 普通票未改 Dashboard 數字格
- [ ] W-PROG 寫入前有授權句 + 證據 + 保守端選取說明

---

## 7. Verification（本票 AC · `rg`）

```bash
rg "apply_phase_pct|proposed_delta_pct|Phase 影響|non_claims" docs/phase-progress-impact-protocol-v1.md
```

期望命中：`apply_phase_pct`、`proposed_delta_pct`、Phase 影響、`non_claims`、W-PROG 唯一寫入句。

---

## 8. Apply runner（完成時更新對應 P 趴數）

> **缺口補齊（2026-07-13）**：既往 W-PROG 手算寫入 Dashboard；現提供可重跑 CLI。  
> **≠** 普通票默認自動 uplift（仍須 `estimate` → `verify` → `apply_phase_pct: true` + 已授權寫入 + `--authorize`）。

| 命令 | 用途 |
|------|------|
| `python 04_Workflows/_phase_pct_apply.py estimate --ticket-id <TICKET> --pretty` | **開工前**自動估 `proposed_delta`（不寫 Dashboard） |
| `python 04_Workflows/_phase_pct_apply.py estimate --ticket-id <TICKET> --write-back --pretty` | 估 Δ 並寫回票 state（lifecycle=`estimated`） |
| `python 04_Workflows/_phase_pct_apply.py verify --ticket-id <TICKET> --checks-ok --write-back --pretty` | **檢查通過後**升格 lifecycle=`verified`（仍不寫 Dashboard） |
| `python 04_Workflows/_phase_pct_apply.py read --pretty` | 讀 Gauge 現況 |
| `python 04_Workflows/_phase_pct_apply.py plan --delta P8.5=+2 --pretty` | 僅計畫（dry-run） |
| `python 04_Workflows/_phase_pct_apply.py from-ticket --ticket-id <TICKET> --pretty` | 自票 FRAME 提案 Δ |
| `python 04_Workflows/_phase_pct_apply.py apply --ticket-id <W-PROG> --authorize --pretty` | **寫入** Dashboard 數字格（須已 `verified`） |
| `python 04_Workflows/_phase_pct_apply.py self-test --pretty` | 非破壞自檢 |

**完成時建議流程（先估 → 後驗 → 再寫）**

1. **接戰／開工**：`estimate`（可 `--write-back`）→ 票面留下 `proposed_delta`；`apply_phase_pct: false`；**干活 ≠ 漲 %**。  
2. **驗收／Review 通過**：`verify --checks-ok [--write-back]` → lifecycle=`verified`（可 apply **候選**）。  
3. **W-PROG／Governance**：票標 `apply_phase_pct: true` +「已授權寫入」→ `apply --authorize` 寫入 `docs/WAVE_PROGRESS_DASHBOARD.md`。  
4. Progress **末尾** append「實際上調=是／否」；**勿**默認改 `Master_Map.war_status`（另授權）。

Runner 回傳結構化 `dict`（`ok`／`message`／`updates`／`dry_run`／`lifecycle` 等）。SSOT 仍為 Dashboard；本 runner **不**另起帳本。

---

## 9. 自動估 Δ（heuristic v0.1）與狀態機

> **性質**：`heuristic v0.1` · **approved／定稿**（尚書省 **2026-07-13** 確認採納）。可重跑、可 dry-run；升級權重須另開票，不得 silently 改表。

### 9.1 狀態機

```text
none ──estimate──► estimated ──verify──► verified ──apply──► applied
                      │                      │
                      │   （未 verified）      │  仍須 apply_phase_pct=true
                      └──────► apply 拒絕 ◄───┘  + 已授權寫入 + --authorize
```

| lifecycle | 允許 | 禁止 |
|-----------|------|------|
| `estimated` | 提案、寫票 state | 寫 Dashboard % |
| `verified` | 標為 apply 候選 | 仍不可無授權寫 % |
| `applied` | 已寫 Dashboard（W-PROG） | — |

### 9.2 啟發式權重表（v0.1 · 定稿）

> **權威**：尚書省 **2026-07-13** 確認採納（用戶回覆「可以.確定」）。版本號仍為 **v0.1**；`heuristic_status=approved`。

**優先**：票面已有可解析 `proposed_delta_pct` → **explicit**（不覆蓋，除非 `--force-heuristic`）。

**否則**依 `impact_size`／`ticket_size`／關鍵字推 size，再取 base Δ，並以 `evidence_gate` **封頂**：

| impact_size | base Δ | 典型 |
|-------------|--------|------|
| `micro` | **0** | 工具／協議／runner／docs-only |
| `small` | **+1** | 小索引／checklist／cross-ref |
| `medium` | **+2** | 常規貢獻（歷史 W-PROG-B 慣例） |
| `large` | **+5** | 較大證據包 |
| `xl` | **+8** | 罕見里程碑（歷史 P8.5 保守端） |

| evidence_gate | cap |
|---------------|-----|
| `blocked` | **0** |
| `L-local` | **2** |
| `CI-advisory`／`L-local+CI-advisory` | **5** |
| `GA-remote` | **8** |

可選 FRAME 欄：`impact_size: medium`（或 `ticket_size`／`impact_class` 別名）。未填則關鍵字推斷；有 `phase_targets` 預設 `medium`。

### 9.3 與「干活 ≠ 漲 %」對齊

- 普通票：`apply_phase_pct: false`；`estimate`／`verify` **只**動票 state／提案。  
- 寫入 Dashboard：**唯一**路徑仍是 W-PROG／Governance + `verified` + `--authorize`。  
- 權重表：v0.1 **已定稿**（尚書省 2026-07-13）；升級權重須另開票，不得 silently 改歷史慣例敘事。
