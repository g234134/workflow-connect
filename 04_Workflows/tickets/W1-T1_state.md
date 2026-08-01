# TICKET STATE · W1-T1 · 治理入口收口與 OPS 一鍵自檢

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 1 - Governance & Observability

---

## FRAME

- Title: 治理入口收口與 OPS 一鍵自檢
- Goal: 新 Agent／新 chat 僅需閱讀 3 份關鍵文件即可完成初始化對齊；checklist --mode full 可機器化驗證接戰就緒。
- Scope:
  - 新增或更新戰車根 README.md（僅索引：AGENTS / Refresher / W0 / Master_Map）
  - 對齊 04_Workflows/WORKFLOW_INDEX.md 與 runbooks/*.md（消除 TODO 假陰性）
  - 擴充 04_Workflows/_ops_cycle.py checklist --mode full：三鑰 smoke、eval-gate 子集、routing_policy validate
  - 撰寫 docs/GOVERNANCE_ONBOARDING_v1.md（接戰 10 步精簡對照表）
- NonScope:
  - 不改憲法／工程合約正文
  - 不實作 master_status／handoff 自動寫回（留 Wave 2）
  - 不接 prod selector
- AllowedPaths:
  - README.md
  - 04_Workflows/WORKFLOW_INDEX.md
  - 04_Workflows/_ops_cycle.py
  - docs/GOVERNANCE_ONBOARDING_v1.md
  - artifacts/ops/**
- BlockedPaths:
  - .cursor/rules/engineering-contract.mdc
  - 04_Workflows/HARNESS_CONSTITUTION.md
  - 04_Workflows/ENGINEERING_CONTRACT.md
  - core/*
  - 04_Workflows/00_Agent_Work_Progress.md
- Dependencies:
  - AGENTS.md §初始化校準
  - 04_Workflows/_ops_cycle.py
  - 04_Workflows/_smoke_test_keys.py
  - 04_Workflows/WORKFLOW_INDEX.md
- Risks:
  - DarkOps blocked 時 checklist 不能靜默通過
  - 雙路徑 runbook（總部 vs 暗部）連結錯誤導致假綠
  - README 過冗長難辨識最重要的三檔
- Observability:
  - logs: checklist 每步 [OK]/[FAILED] 結構化輸出；DarkOps blocked 標 assignable: false
  - metrics: N/A（本票文檔／自檢為主）
  - traces: N/A
- OutputArtifacts:
  - README.md
  - docs/GOVERNANCE_ONBOARDING_v1.md
  - 更新 WORKFLOW_INDEX.md
  - artifacts/ops/checklist_full.sample.json
- AcceptanceCriteria:
  - README.md 四鏈可點、無硬編磁碟路徑
  - WORKFLOW_INDEX 所列 runbook 檔案均存在
  - python 04_Workflows/_ops_cycle.py checklist --mode full → exit 0
  - Reviewer conclusion ∈ {accepted, accepted_with_gaps}（僅文檔缺口）
- VerificationCommands:
  - `python 04_Workflows/_ops_cycle.py checklist --mode full`
    - 預期：exit 0；含 Wave 1 最小項狀態
  - `手動檢查 README.md 四鏈`
    - 預期：連結有效、無硬編磁碟路徑
  - `手動檢查 WORKFLOW_INDEX runbook 存在性`
    - 預期：列表中 runbooks/*.md 均存在

---

## STATE

- overall_status: done
- implementation_status: done
- current_owner: scribe
- next_action: 無（票面已收口；archive hygiene 見 D_REPORT follow-up）
- last_updated: 2026-06-07 · reviewer
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

> **B 區（Implementer）**：IP-1～IP-8 已施工；待 Reviewer 第二輪驗收。

### Implementation Plan（勾選式 · 8 項）

- [x] **IP-1 · README.md Start Here 四鏈索引**  
  - **檔案**：`README.md`  
  - **動作**：頂部新增 `## Start Here`（≤15 行）；四鏈指向 `AGENTS.md`、`README_Refresher.md`、`04_Workflows/_PORTABLE_CORE_INDEX.md`（W0）、`04_Workflows/Master_Map.json`；既有長文下移為「延伸閱讀」；全文移除硬編磁碟路徑（含 `D:\...`、`cd D:\`）。  
  - **驗證**：`rg -n 'D:\\\\' README.md` → 零匹配；手動點四鏈可開檔。

- [x] **IP-2 · WORKFLOW_INDEX runbook 路徑對齊**  
  - **檔案**：`04_Workflows/WORKFLOW_INDEX.md`  
  - **動作**：§1.1／§1.2 將 `Runbooks/`（大寫）改為實際存在的 `runbooks/`；移除「Runbook（TODO）」假陰性，改為已存在檔案連結；§3 範例同步。  
  - **驗證**：`python -c "import os; paths=['04_Workflows/runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md','04_Workflows/runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md','04_Workflows/runbooks/GOV_CORE_OPERATING_MAP_v0.1.md']; assert all(os.path.isfile(p) for p in paths)"`

- [x] **IP-3 · WORKFLOW_INDEX 新增治理入口條目**  
  - **檔案**：`04_Workflows/WORKFLOW_INDEX.md`  
  - **動作**：新增 §1.5「Governance Onboarding & OPS Cycle」：連結 `docs/GOVERNANCE_ONBOARDING_v1.md`、`04_Workflows/OPS_CYCLE.md`、runner `runners.ops_cycle_py`（見 Master_Map）；標註 HQ 總部路徑 vs 暗部 `gov_core_system` 分工。  
  - **驗證**：`rg 'GOVERNANCE_ONBOARDING_v1' 04_Workflows/WORKFLOW_INDEX.md` 有匹配；所列檔案 `os.path.isfile` 全 True。

- [x] **IP-4 · _ops_cycle.py Wave 1 就緒檢查（子程序）**  
  - **檔案**：`04_Workflows/_ops_cycle.py`（AllowedPaths 內；以 subprocess 呼叫既有 runner，**不**改 `02_Agents_Core/ops_cycle.py`）  
  - **動作**：新增 `run_wave1_readiness_checks(repo_root) -> dict`（見下方草稿）；含四檢查：  
    1. 三鑰 smoke — `python 04_Workflows/_smoke_test_keys.py`（解析 stdout `[OK]`/`[FAILED]`，禁印金鑰）  
    2. routing policy — `python -m core.routing_policy_loader validate --format json`  
    3. eval-gate 子集 — `python -m observability.eval_ci_check tests/fixtures/eval/ibridge_records.jsonl --limit 50 --format json`  
    4. DarkOps 路由 — `python 04_Workflows/_route_task.py --type dark.infra`（`assignable: false` 或 `blocked` 時本步 **pass** 並標 `darkops_blocked_expected: true`；若錯誤回傳 `assignable: true` 則 **fail**）  
  - **驗證**：單獨執行各子命令 exit 語意符合預期；函式回傳 `{"ok": bool, "checks": [...]}`。

- [x] **IP-5 · checklist --mode full 合併輸出**  
  - **檔案**：`04_Workflows/_ops_cycle.py`  
  - **動作**：`checklist` 分支在 `get_archive_checklist("full")` 之後合併 `wave1_readiness` 區塊；頂層 `ok` = archive 自動步驟無 fail **且** wave1 全 pass；每步輸出 `status` ∈ `{pass, fail, manual, skip}` + `message`；新增 `--save-json` 可選寫入 `artifacts/ops/checklist_full.<UTC>.json`。  
  - **驗證**：`python 04_Workflows/_ops_cycle.py checklist --mode full --pretty` → exit 0；JSON 含 `wave1_readiness.checks` 陣列。

- [x] **IP-6 · GOVERNANCE_ONBOARDING_v1.md**  
  - **檔案**：`docs/GOVERNANCE_ONBOARDING_v1.md`  
  - **動作**：撰寫 10 步接戰清單（對齊 AGENTS §初始化校準 1–9 + OPS 自檢第 10 步）；每步含「讀什麼／跑什麼命令／預期結果」。  
  - **驗證**：`rg '^### Step' docs/GOVERNANCE_ONBOARDING_v1.md | wc -l` = 10；無硬編磁碟路徑。

- [x] **IP-7 · checklist 樣本 JSON**  
  - **檔案**：`artifacts/ops/checklist_full.sample.json`  
  - **動作**：依 IP-5 輸出 schema 撰寫樣本（含 `archive_checklist` + `wave1_readiness`）；DarkOps blocked 範例步驟標 `darkops_blocked_expected: true`。  
  - **驗證**：`python -c "import json; json.load(open('artifacts/ops/checklist_full.sample.json'))"`；欄位與實跑 `--save-json` 一致。

- [x] **IP-8 · 整票驗收自檢**  
  - **檔案**：全部 OutputArtifacts  
  - **動作**：依 FRAME VerificationCommands 跑一輪；記錄 exit code 與關鍵 `ok` 於本區 `verification`。  
  - **驗證**：`python 04_Workflows/_ops_cycle.py checklist --mode full` exit 0（施工完成後）。

### Files To Touch

- README.md
- 04_Workflows/WORKFLOW_INDEX.md
- 04_Workflows/_ops_cycle.py
- docs/GOVERNANCE_ONBOARDING_v1.md
- artifacts/ops/checklist_full.sample.json

### 本輪施工變更摘要（草稿 · 未落地）

> 以下為下一輪 Implementer 可直接貼上的初稿；**本輪僅寫入 state，尚未改動目標檔**。

#### 草稿 A · README.md（Start Here 置頂 · 最小索引）

```markdown
# 大唐三省六部 — AI Workflow 治理基线

> **新接戰副官**：先讀下方 **Start Here** 四鏈，再執行 OPS 一鍵自檢。

## Start Here

| 優先 | 文件 | 用途 |
|:----:|------|------|
| 1 | [`AGENTS.md`](./AGENTS.md) | 接戰／封存口令與 §初始化校準（權威入口） |
| 2 | [`README_Refresher.md`](./README_Refresher.md) | 日常 SOP 與點火指令速查 |
| 3 | [`04_Workflows/_PORTABLE_CORE_INDEX.md`](./04_Workflows/_PORTABLE_CORE_INDEX.md) | W0 可移植核心 vs 實例錨點分流 |
| 4 | [`04_Workflows/Master_Map.json`](./04_Workflows/Master_Map.json) | 路徑、runners、cabins 權威索引 |

**一鍵自檢**：`python 04_Workflows/_ops_cycle.py checklist --mode full`  
**接戰對照表**：[`docs/GOVERNANCE_ONBOARDING_v1.md`](./docs/GOVERNANCE_ONBOARDING_v1.md)

---

## 延伸閱讀

（保留既有 §1–§9 架構／模組說明，但移除所有 `D:\...` 硬編路徑，改為相對路徑或「見 Master_Map.json」。）
```

#### 草稿 B · WORKFLOW_INDEX.md 變更摘要

| 動作 | 位置 | 內容 |
|------|------|------|
| **修正** | §1.1 | `Runbook` → `04_Workflows/runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md`（刪 TODO） |
| **修正** | §1.2 | `Runbook` → `04_Workflows/runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md`（刪 TODO） |
| **保留** | §1.3–§1.4 | Phase 5 probe、Phase 8.6 bridge（路徑已存在，不動） |
| **新增** | §1.5 | Governance Onboarding & OPS Cycle（見下） |
| **修正** | §3 步驟 2 | 範例路徑改 `runbooks/` 小寫 |

**§1.5 新增條目草稿**：

```markdown
### 1.5 Governance Onboarding & OPS Cycle（Wave 1）

- Onboarding：
  - `docs/GOVERNANCE_ONBOARDING_v1.md` — 接戰 10 步精簡對照表
- OPS 制度：
  - `04_Workflows/OPS_CYCLE.md` — 戰報／封存／回顧
- CLI：
  - `python 04_Workflows/_ops_cycle.py checklist --mode full` — 接戰就緒一鍵自檢
- 操作地圖：
  - `04_Workflows/runbooks/GOV_CORE_OPERATING_MAP_v0.1.md` — 總部 vs 暗部路徑
- 注意：暗部實作 CLI 工作目錄為 `gov_core_system` 根；本索引列 HQ 總部相對路徑。
```

**移除／不列**：§2 預留項維持 TODO／Blocked 標記（非假陰性 runbook）。

#### 草稿 C · _ops_cycle.py checklist 擴充（pseudo-code）

```python
# 新增於 04_Workflows/_ops_cycle.py（AllowedPaths 內）

def run_wave1_readiness_checks(repo_root: str) -> dict:
    """Wave 1 接戰就緒檢查；回傳結構化 dict，不修改 02_Agents_Core。"""
    checks: list[dict] = []

    # 1) 三鑰 smoke
    checks.append(_run_subprocess_check(
        id="smoke_keys",
        title="三鑰盲測",
        cmd=[sys.executable, "04_Workflows/_smoke_test_keys.py"],
        cwd=repo_root,
        pass_if=lambda rc, out: rc == 0 and "[FAILED]" not in out,
    ))

    # 2) routing policy validate
    checks.append(_run_subprocess_check(
        id="routing_policy_validate",
        title="routing_policy validate",
        cmd=[sys.executable, "-m", "core.routing_policy_loader", "validate", "--format", "json"],
        cwd=repo_root,
        pass_if=lambda rc, out: rc == 0 and '"ok": true' in out.replace(" ", ""),
    ))

    # 3) eval-gate CI 子集（fixture）
    checks.append(_run_subprocess_check(
        id="eval_gate_ci_subset",
        title="eval-gate CI check (fixture)",
        cmd=[
            sys.executable, "-m", "observability.eval_ci_check",
            "tests/fixtures/eval/ibridge_records.jsonl",
            "--limit", "50",
        ],
        cwd=repo_root,
        pass_if=lambda rc, out: rc == 0,
    ))

    # 4) DarkOps 路由預期 blocked
    dark = _run_subprocess_json(
        cmd=[sys.executable, "04_Workflows/_route_task.py", "--type", "dark.infra"],
        cwd=repo_root,
    )
    assignable = dark.get("assignable")
    blocked = dark.get("blocked")
    dark_ok = (not assignable) or blocked
    checks.append({
        "id": "darkops_route_gate",
        "title": "DarkOps route gate",
        "status": "pass" if dark_ok else "fail",
        "message": f"assignable={assignable} blocked={blocked}",
        "darkops_blocked_expected": True,
    })

    ok = all(c.get("status") == "pass" for c in checks)
    return {"ok": ok, "checks": checks}


# checklist 分支（mode == "full" 時）：
#   archive = get_archive_checklist("full")
#   wave1 = run_wave1_readiness_checks(repo_root)
#   result = {
#       "ok": archive["ok"] and wave1["ok"],
#       "mode": "full",
#       "archive_checklist": archive,
#       "wave1_readiness": wave1,
#   }
#   if args.save_json: write artifacts/ops/checklist_full.<ts>.json
```

**輔助函式簽名**：

```python
def _run_subprocess_check(*, id: str, title: str, cmd: list[str], cwd: str, pass_if) -> dict: ...
def _run_subprocess_json(*, cmd: list[str], cwd: str) -> dict: ...
def _repo_root() -> str: ...  # 沿用 _tang_paths / gov_paths 既有解析
```

#### 草稿 D · docs/GOVERNANCE_ONBOARDING_v1.md 骨架

```markdown
# Governance Onboarding v1 — 接戰 10 步對照表

> 對齊 `AGENTS.md` §初始化校準；路徑見 `Master_Map.json`，禁區類型見憲法 §7。

| Step | 做什麼 | 讀／跑 | 預期 |
|:----:|--------|--------|------|
| 1 | 憲法校準 | 讀 `04_Workflows/HARNESS_CONSTITUTION.md` | 知禁區類型與四域 |
| 2 | 合約校準 | 讀 `04_Workflows/ENGINEERING_CONTRACT.md` | 四流派 + 12-rule |
| 3 | 條件校準 | 讀 `04_Workflows/00_Agent_Work_Conditions.md` | 知當期 Smoke 標準 |
| 4 | 地圖校準 | 讀 `04_Workflows/WORKFLOW_INDEX.md` | 知 runbook 入口 |
| 5 | 路線校準 | 讀 `04_Workflows/runbooks/GOV_CORE_OPERATING_MAP_v0.1.md` | 總部 vs 暗部路徑 |
| 6 | 工作流校準 | 讀任務對應 runbook（見 WORKFLOW_INDEX §1） | CLI 步驟清晰 |
| 7 | 戰史校準 | 讀 `04_Workflows/00_Agent_Work_Progress.md` 末段 | 知最近風險 |
| 8 | 任務路由 | `python 04_Workflows/_route_task.py --type hq.governance` | `ok: true` |
| 9 | 營運週期 | 讀 `04_Workflows/OPS_CYCLE.md` | 知戰報／封存流程 |
| 10 | **一鍵自檢** | `python 04_Workflows/_ops_cycle.py checklist --mode full` | exit 0；wave1 全 pass |

### Step 10 細項（OPS 一鍵自檢）

- 三鑰：`python 04_Workflows/_smoke_test_keys.py` → 僅 `[OK]`/`[FAILED]`
- 路由策略：`python -m core.routing_policy_loader validate`
- Eval 子集：`python -m observability.eval_ci_check tests/fixtures/eval/ibridge_records.jsonl --limit 50`
- DarkOps：`python 04_Workflows/_route_task.py --type dark.infra` → 預期 `assignable: false`

### 快速入口（README Start Here）

- [`README.md`](../README.md) · [`AGENTS.md`](../AGENTS.md) · [`README_Refresher.md`](../README_Refresher.md) · W0 · Master_Map
```

#### 草稿 E · artifacts/ops/checklist_full.sample.json（結構樣本）

```json
{
  "ok": true,
  "mode": "full",
  "generated_at": "2026-06-07T12:00:00Z",
  "archive_checklist": {
    "ok": true,
    "steps": [
      {"id": "milestone", "title": "里程碑封存", "status": "pass"},
      {"id": "battle_report", "title": "戰報封存", "status": "pass"}
    ]
  },
  "wave1_readiness": {
    "ok": true,
    "checks": [
      {"id": "smoke_keys", "title": "三鑰盲測", "status": "pass", "message": "[OK] OpenAI [OK] Groq [OK] Telegram"},
      {"id": "routing_policy_validate", "title": "routing_policy validate", "status": "pass", "message": "ok=true"},
      {"id": "eval_gate_ci_subset", "title": "eval-gate CI check (fixture)", "status": "pass", "message": "sampled_count=50"},
      {
        "id": "darkops_route_gate",
        "title": "DarkOps route gate",
        "status": "pass",
        "message": "assignable=false blocked=true",
        "darkops_blocked_expected": true
      }
    ]
  }
}
```

### 交付狀態

- changed_files:
  - `README.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
  - `04_Workflows/_ops_cycle.py`
  - `docs/GOVERNANCE_ONBOARDING_v1.md`
  - `artifacts/ops/checklist_full.sample.json`
  - `04_Workflows/tickets/W1-T1_state.md`
- artifacts: `artifacts/ops/checklist_full.sample.json`
- verification:
  - `python 04_Workflows/_ops_cycle.py checklist --mode full --pretty` → **exit 0**；`ok: true`；`wave1_readiness.ok: true`；`archive_checklist.ok: true`
  - README 硬編路徑：`rg 'D:\\' README.md` → **零匹配**
  - runbook 存在性：`04_Workflows/runbooks/*.md` 三檔 + `docs/GOVERNANCE_ONBOARDING_v1.md` → **全存在**
  - wave1 四檢：`smoke_keys`/`routing_policy_validate`/`eval_gate_ci_subset`/`darkops_route_gate` 皆 **pass**
- behavior_notes:
  - `eval_gate_ci_subset` 使用 fixture + `--max-needs-review-ratio 0.9`（對齊 `tests/test_eval_ci_check.py`）；stdout 含 ENF 前綴，以 `_parse_json_stdout` 抽取 JSON。
  - `darkops_route_gate`：`_route_task.py` 在 blocked 時 exit 1 屬預期；以 `assignable=false` + `blocked=true` 判 pass，不假綠。
  - Wave 1 檢查仍集中於 `_ops_cycle.py` subprocess 層，未改 `02_Agents_Core/ops_cycle.py`。
- deferred_items:
  - `02_Agents_Core/ops_cycle.py` 合併 wave1 至 schema（非 AllowedPaths；Reviewer 若要求再開子票）
  - `master_status`／`handoff` 自動寫回（FRAME NonScope · Wave 2）
  - prod selector 接線（FRAME NonScope）

---

## C_REPORT

### 第一輪（Implementation Plan 審查 · 2026-06-07）

- conclusion: **accepted_with_gaps**
- blocking_issues: 無
- checks_summary:
  - Goal／Scope／Non-Goals 對齊；8 項 IP 均有檔案 + 驗證命令。
  - gaps：GOVERNANCE_ONBOARDING 10 步需實作輪寫成明確清單；sample JSON schema 需正式 key 列表 → **已由 Implementer 施工輪補齊**。
- risk_level: low
- suggestions:
  - 施工順序：IP-1/2/3 → IP-4/5 → IP-6/7 → IP-8。
  - 完成後 `implementation_status` → `in_review` 交第二輪驗收。

### 第二輪（實作驗收 · 2026-06-07）

- verdict: accepted
- conclusion: accepted
- blocking_issues: 無
- checks_summary: |
    - README Start Here 四鏈可點、無硬編磁碟路徑（`rg 'D:\\' README.md` 零匹配）。
    - WORKFLOW_INDEX 所列 runbooks/*.md 均存在；§1.5 治理入口條目已對齊。
    - `python 04_Workflows/_ops_cycle.py checklist --mode full` → exit 0；`ok: true`；archive + wave1 全 pass。
    - Wave 1 四檢均 pass：smoke_keys、routing_policy_validate、eval_gate_ci_subset、darkops_route_gate（blocked 預期 pass）。
    - GOVERNANCE_ONBOARDING_v1.md 10 步齊全；checklist_full.sample.json schema 可解析。
- risk_level: low
- suggestions: |
    - Scribe 填 D_REPORT + Progress 末尾摘要。
    - archive_checklist 絕對路徑 hygiene 可另開小票（非阻塞）。

---

## D_REPORT

- docs_updates:
  - `README.md` — Start Here 四鏈（AGENTS / Refresher / W0 / Master_Map）；移除硬編磁碟路徑
  - `04_Workflows/WORKFLOW_INDEX.md` — §1.5 治理入口；runbooks 路徑對齊 `runbooks/`
  - `docs/GOVERNANCE_ONBOARDING_v1.md` — 接戰 10 步對照表（對齊 AGENTS §初始化校準）
  - `artifacts/ops/checklist_full.sample.json` — `archive_checklist` + `wave1_readiness` schema 樣本
- verification:
  - `python 04_Workflows/_ops_cycle.py checklist --mode full --pretty` → **exit 0**；`ok: true`；archive + wave1 全 pass
  - `rg 'D:\\' README.md` → **零匹配**（無硬編磁碟路徑）
  - runbook 存在性：`04_Workflows/runbooks/*.md` 三檔 + `docs/GOVERNANCE_ONBOARDING_v1.md` → **全存在**
  - Wave 1 四檢：`smoke_keys` / `routing_policy_validate` / `eval_gate_ci_subset` / `darkops_route_gate` → **皆 pass**
  - `python -c "import json; json.load(open('artifacts/ops/checklist_full.sample.json'))"` → schema 可解析
- behavior_notes:
  - `eval_gate_ci_subset` 使用 fixture + `--max-needs-review-ratio 0.9`；stdout 含 ENF 前綴，以 `_parse_json_stdout` 抽取 JSON
  - `darkops_route_gate`：`_route_task.py` blocked 時 exit 1 屬預期；以 `assignable=false` + `blocked=true` 判 pass，不假綠
  - Wave 1 檢查集中於 `04_Workflows/_ops_cycle.py` subprocess 層，**未**改 `02_Agents_Core/ops_cycle.py`
  - `master_status`／`handoff` 自動寫回、prod selector 接線 — **FRAME NonScope**（留 Wave 2）
- progress_entry: |
    W1-T1 收口：新 Agent 可依 README Start Here + `docs/GOVERNANCE_ONBOARDING_v1.md` 完成接戰對齊；`python 04_Workflows/_ops_cycle.py checklist --mode full` 一鍵驗證三鑰 smoke、routing policy、eval-gate 子集、DarkOps gate（blocked 預期 pass）。下游票可引用 checklist JSON schema 與 wave1 四檢語意。
- followup_suggestions:
  - **archive_checklist 絕對路徑 hygiene**（Reviewer 非阻塞 gap）：統一 `get_archive_checklist` 輸出為 repo 相對路徑
  - **Wave 2**：`master_status`／`handoff` 自動寫回（FRAME NonScope 已列）
  - **可選**：`02_Agents_Core/ops_cycle.py` 合併 wave1 schema（非本票 AllowedPaths）

---

## O_NOTES

> **O 區**：Orchestrator 維護 run log 與戰報連結；Observe / Operate 計畫。

### Observability Plan

- checklist 每次執行保留 JSON 於 `artifacts/ops/checklist_full.<timestamp>.json`（`--save-json` 落地後）

### Rollout / Ops Notes

- 合併後 Orchestrator 手動跑一次 checklist 確認無假綠
- 新成員僅依 README Start Here + `GOVERNANCE_ONBOARDING_v1.md` 完成首次接戰

### 預填驗收命令清單（施工完成後貼結果）

```powershell
# 0) 工作目錄：戰車根（相對路徑自洽即可）

# 1) OPS 一鍵自檢（主驗收）
python 04_Workflows/_ops_cycle.py checklist --mode full --pretty

# 2) 可選：寫出 JSON 樣本比對
python 04_Workflows/_ops_cycle.py checklist --mode full --save-json --pretty

# 3) README 四鏈 + 無硬編路徑
rg -n 'D:\\\\' README.md
# 預期：無匹配

# 4) WORKFLOW_INDEX runbook 存在性
python -c "import os; paths=['04_Workflows/runbooks/GOV_CORE_SMOKE_TEST_RUNBOOK_v0.1.md','04_Workflows/runbooks/RAG_SMOKE_TEST_RUNBOOK_v0.1.md','04_Workflows/runbooks/GOV_CORE_OPERATING_MAP_v0.1.md','docs/GOVERNANCE_ONBOARDING_v1.md']; missing=[p for p in paths if not os.path.isfile(p)]; assert not missing, missing"

# 5) Wave 1 子檢查（除錯用）
python 04_Workflows/_smoke_test_keys.py
python -m core.routing_policy_loader validate --format json
python -m observability.eval_ci_check tests/fixtures/eval/ibridge_records.jsonl --limit 50
python 04_Workflows/_route_task.py --type dark.infra --pretty

# 6) 樣本 JSON 可解析
python -c "import json; json.load(open('artifacts/ops/checklist_full.sample.json', encoding='utf-8')); print('sample ok')"
```

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
| 2026-06-07 | implementer | B_REPORT 勾選式計畫 + 五份檔案草稿；STATE→in_progress | 本檔 |
| 2026-06-07 | reviewer | 第一輪 Plan 審查 accepted_with_gaps | 本檔 C_REPORT §第一輪 |
| 2026-06-07 | implementer | IP-1～IP-8 落地；checklist exit 0；STATE→in_review | 本檔 B_REPORT verification |
