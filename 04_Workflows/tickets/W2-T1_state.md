# TICKET STATE · W2-T1 · Core Agent Smoke PR 門禁（Phase 6 收口）

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。  
> Wave：Wave 2 - Multi-agent & Testing

---

## FRAME

- Title: Core Agent Smoke PR 門禁（Phase 6 收口）
- Goal: 每次 PR 自動跑 H-line／routing／eval-gate 子集，防止企業化補強層回歸。
- Scope:
  - 新增或擴充 .github/workflows/core-agent-smoke.yml
  - 整合 04_Workflows/_core_agent_smoke.py --tier PR
  - 文檔對齊 docs/testing.md：標明 PR tier 模組清單
  - 失敗時輸出結構化摘要
- NonScope:
  - 不全庫 unittest
  - 不預設跑 DARK_FULL
  - 不改暗部 135+ 測試全量矩陣
- AllowedPaths:
  - .github/workflows/core-agent-smoke.yml
  - 04_Workflows/_core_agent_smoke.py
  - docs/testing.md
- BlockedPaths:
  - core/*（非 smoke 腳本本身）
  - AGENTS.md
- Dependencies:
  - W1-T1（testing 文檔索引）
  - 04_Workflows/_core_agent_smoke.py
  - docs/testing.md
- Risks:
  - 暗部 venv 不可用時 PR tier 不應依賴暗部路徑
  - tests/ package clash → 沿用 subprocess 隔離
- Observability:
  - logs: smoke tier 每模組 pass/fail
  - metrics: CI duration、fail rate（GitHub Actions）
  - traces: N/A
- OutputArtifacts:
  - .github/workflows/core-agent-smoke.yml
  - 更新 docs/testing.md
  - CI 首次綠色 run URL（戰報引用）
- AcceptanceCriteria:
  - PR 觸發 workflow 綠（戰車根）
  - --tier PR 本地與 CI 結果一致
  - docs/testing.md 與 workflow 步驟一致
  - 至少覆蓋 test_context_entry、test_eval_gate、test_hq_task_routing_smoke
- VerificationCommands:
  - `python 04_Workflows/_core_agent_smoke.py --tier PR`
    - 預期：exit 0
  - `GitHub Actions core-agent-smoke`
    - 預期：PR 觸發綠

---

## STATE

- overall_status: done
- implementation_status: done
- current_owner: scribe
- next_action: 無（票面已收口；首次 CI 綠 run URL / branch protection 見 D_REPORT follow-up）
- last_updated: 2026-06-07 · reviewer（post-implementation · accepted_with_gaps）
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

> **C 區（Orchestrator 預填）**：Implementer 施工時更新下方欄位，保留 Implementation Plan 歷史。

### 本輪施工變更摘要（2026-06-07 · implementer · 施工輪）

1. **`.github/workflows/core-agent-smoke.yml`**
   - PR job 更名為 `Agent workflow smoke (PR tier)`；核心命令 `python 04_Workflows/_core_agent_smoke.py --tier PR -v`。
   - smoke step 內嵌 inline Python：解析 CLI JSON → 產 `smoke_ci_summary.json`（含 `workflow_name`、`failed_modules[]`、`duration_ms` 等 §D 欄位）。
   - 新增 `Emit structured failure summary`（`if: failure()`）與 `Upload smoke CI summary`（`if: always()`，artifact 保留 14 天）。
   - `agent-smoke-dark` / `agent-smoke-all` 維持 `workflow_dispatch` only，PR 路徑不觸發。

2. **`docs/testing.md`**
   - 新增 **§5 PR Smoke Tier (W2-T1)**：目的、執行命令、7 模組覆蓋表、exit code 表。
   - 新增 **§5.1 PR smoke vs Release Tier-A (W2-T4)** 對照表。
   - 新增 **Excluded / Not covered by PR smoke** 全表（§F 原樣落地）。
   - **§6 CI acceptance** 同步：pass criteria 含 `smoke_ci_summary.json` schema 摘要。

3. **未改動**：`04_Workflows/_core_agent_smoke.py`、`core/*`、治理憲法檔。

---

### Implementation Plan (initial)

- [x] 新增 core-agent-smoke.yml workflow
- [x] 整合 _core_agent_smoke.py --tier PR
- [x] 更新 docs/testing.md PR tier 清單
- [x] 確認覆蓋三個核心測試模組

### Implementation Plan (detailed · 2026-06-07 · implementer)

> **本輪定位**：規劃與草稿；**不**聲稱 workflow／docs 已驗收。  
> **現況盤點**：`.github/workflows/core-agent-smoke.yml` 與 `docs/testing.md` §5–§6 已有初稿；本票收口需對齊 AcceptanceCriteria、補結構化失敗摘要、明確 PR vs Release 分工。

#### A. CI workflow 設計（`.github/workflows/core-agent-smoke.yml`）

| 項 | 設計決策 |
|----|----------|
| **Workflow name** | `Core agent smoke` |
| **觸發** | `pull_request` + `push`（主線）；`workflow_dispatch`（可選 DARK / ALL，**非** PR 預設） |
| **paths-ignore** | `02_Agents_Core/repos/**`、`05_Temp_Cache/**`、`**/*.md`、`workflow_v2/**` — 純文檔 PR 不跑 smoke |
| **concurrency** | `core-agent-smoke-${{ github.workflow }}-${{ github.ref }}-${{ github.event_name }}`，`cancel-in-progress: true` |
| **Job（PR 路徑）** | 單 job `agent-smoke-pr`；**不** install dark deps；**不** 跑 `DARK` / `DARK_FULL` |
| **Python** | `3.12`（`actions/setup-python@v5`） |
| **核心命令** | `python 04_Workflows/_core_agent_smoke.py --tier PR -v` |
| **失敗摘要** | 腳本 stdout 為 JSON；CI 步驟在 exit ≠ 0 時 `echo` JSON + stderr 首行 hint（`format_first_failure_line`） |
| **與 eval-gate 關係** | 並行 required check；eval 側重 P+ `eval_ci_check` + 更廣 eval unittest；本 workflow 側重 agent workflow 子集（見下方模組表） |

**待施工 diff（相對現有 yml）**

1. PR job 增加 `set -euo pipefail` shell 與失敗時結構化 log step（見 YAML 草稿 §Failure handling）。
2. 確認 branch protection 將 `agent-smoke-pr` 列為 required（ops 手動，非本票改碼）。
3. `workflow_dispatch` dark/all jobs 維持現狀；**禁止** PR 路徑預設觸發 DARK。

#### B. 本地 `--tier PR` 對應

**命令（repo 根、無 venv 依賴）**

```powershell
python 04_Workflows/_core_agent_smoke.py --tier PR
python 04_Workflows/_core_agent_smoke.py --tier PR -v          # 等同 CI verbosity
python 04_Workflows/_core_agent_smoke.py --tier PR --pretty    # 可讀 JSON
```

**預期 exit code**

| 結果 | exit | 說明 |
|------|------|------|
| 全綠 | `0` | JSON `"ok": true` |
| 測試失敗 | `1` | JSON `"ok": false`，stderr 含 `test_id=…` hint |
| 配置／載入錯誤 | `2` | JSON `"message"` 說明 tier／Master_Map 等問題 |

**預期 JSON 形狀（成功範例，欄位語意）**

```json
{
  "ok": true,
  "suite": "agent_workflow_smoke",
  "tier": "PR",
  "modules": [
    "tests.test_context_entry",
    "tests.test_context_subagent_routing",
    "tests.test_monitoring_executor",
    "tests.test_langgraph_flow_k2",
    "tests.test_hq_task_routing_smoke",
    "tests.test_eval_gate",
    "tests.test_eval_ci_check"
  ],
  "passed": "<N>",
  "failed": 0,
  "errors": 0,
  "tests_run": "<N>",
  "failed_tests": []
}
```

**PR tier 模組來源**：`core/agent_workflow_smoke.py` → `TIER_ROOT_MODULES`（`PR` ≡ `ROOT`；**不**觸暗部 subprocess）。

**AcceptanceCriteria 三項必達模組（含於上表）**

| 模組 | 對應 workflow |
|------|----------------|
| `tests.test_context_entry` | H-line context entry |
| `tests.test_eval_gate` | P+ eval gate contract |
| `tests.test_hq_task_routing_smoke` | HQ `route_task` smoke |

**Non-Goals 再確認**

- 不跑 `python -m unittest discover -s tests`
- PR job 不設 `--tier DARK_FULL` / 不 install `requirements-ci-minimal.txt`
- 不擴暗部 135+ 全量矩陣

#### C. `docs/testing.md` 新增／調整大綱

在現有 §5–§6 基礎上，**新增獨立小節**「PR Smoke Tier」（建議 §5.1 或重編號 §5a），內容大綱：

1. **PR Smoke Tier 介紹**  
   - 定位：每次 PR 的 fast gate（目標 &lt; ~2 min on GHA）。  
   - 入口：`python 04_Workflows/_core_agent_smoke.py --tier PR` + CI `core-agent-smoke.yml` → `agent-smoke-pr`。  
   - 與 `eval-gate-ci.yml` 互補：eval 跑 fixture `eval_ci_check` + 廣 eval unittest；PR smoke 跑 agent workflow 契約子集。

2. **覆蓋測試項（模組級清單）**  
   - **必列三項（AcceptanceCriteria）**：`test_context_entry`、`test_eval_gate`、`test_hq_task_routing_smoke`。  
   - **同 tier 一併執行**：`test_context_subagent_routing`、`test_monitoring_executor`、`test_langgraph_flow_k2`、`test_eval_ci_check`。  
   - **表格**：模組 → 權威檔 → happy / edge 代表測試名（可引用現 §2 表）。

3. **與 Release regression gate（W2-T4）分工**  

   | 層級 | 票號 | 命令 | 觸發 | 範圍 |
   |------|------|------|------|------|
   | **PR fast** | W2-T1 | `_core_agent_smoke.py --tier PR` | 每 PR（GHA required） | ROOT agent smoke；無 PG/LLM；無 Wave7 Tier-A |
   | **P+ eval** | existing | `eval-gate-ci.yml` | 每 PR | eval unittest + `eval_ci_check` fixture |
   | **Pre-release** | W2-T4 | `_wave7_regression_gate.py --tier A` | Release checklist / manual | CLEAN orchestrator Tier-A；產 `artifacts/regression/wave7_tier_a.latest.json` |
   | **Dark optional** | — | `--tier DARK` / `workflow_dispatch` | 手動 / pre-release | gov_core 子集；**非** PR 預設 |

4. **Excluded（PR tier）** — 見下方「Excluded 初版清單」；寫入 docs 時用表格式，避免錯誤期待。

5. **Pass criteria 與 CI 步驟一字對齊** — workflow 命令、exit 0、JSON 鍵與 §6 表同步。

6. **Exit code 表** — 施工時原樣寫入 docs/testing.md「PR Smoke Tier」小節（見 §B 表格）。

---

### Implementation Plan (review gaps · 2026-06-07 · implementer)

> Reviewer `accepted_with_gaps` 後補；仍屬規劃，**未**改 workflow／未跑 CI。

#### D. CI 失敗時結構化 JSON 摘要（schema）

**設計**：CLI stdout 維持 `run_agent_workflow_smoke()` 原生 JSON；CI job 在失敗（或 `always()`）時**另產** `smoke_ci_summary.json`，供 log 解析與 artifact 上傳。  
**`failed_modules[]`** 由 `failed_tests[].test_id` 推導模組前綴（`tests.test_foo.bar` → `tests.test_foo`）。

| 欄位 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `workflow_name` | string | ✓ | 固定 `"Core agent smoke"`（對應 `name:`） |
| `job_name` | string | ✓ | 例 `"agent-smoke-pr"` |
| `tier` | string | ✓ | `"PR"` |
| `ok` | boolean | ✓ | smoke CLI exit 0 → true |
| `duration_ms` | integer | ✓ | job smoke step 牆鐘時間（ms） |
| `github_run_id` | string | ○ | `${{ github.run_id }}` |
| `github_sha` | string | ○ | `${{ github.sha }}` |
| `smoke_result` | object | ✓ | CLI stdout 解析後的完整 dict（含 `modules`、`failed_tests`） |
| `failed_modules` | array | ✓ | 失敗模組摘要；成功時 `[]` |

**`failed_modules[]` 元素**

| 欄位 | 型別 | 說明 |
|------|------|------|
| `module` | string | unittest 模組名，例 `tests.test_context_entry` |
| `test_id` | string | 完整 `test.id()` |
| `kind` | string | `"failure"` \| `"error"` |
| `message` | string | 末行或短訊息 |

**失敗 sample payload**

```json
{
  "workflow_name": "Core agent smoke",
  "job_name": "agent-smoke-pr",
  "tier": "PR",
  "ok": false,
  "duration_ms": 42150,
  "github_run_id": "1234567890",
  "github_sha": "abc123def456",
  "smoke_result": {
    "ok": false,
    "suite": "agent_workflow_smoke",
    "tier": "PR",
    "modules": [
      "tests.test_context_entry",
      "tests.test_context_subagent_routing",
      "tests.test_monitoring_executor",
      "tests.test_langgraph_flow_k2",
      "tests.test_hq_task_routing_smoke",
      "tests.test_eval_gate",
      "tests.test_eval_ci_check"
    ],
    "passed": 41,
    "failed": 1,
    "errors": 0,
    "tests_run": 42,
    "failed_tests": [
      {
        "test_id": "tests.test_hq_task_routing_smoke.TestHqTaskRoutingSmoke.test_dark_infra_blocked",
        "kind": "failure",
        "message": "AssertionError: expected blocked"
      }
    ]
  },
  "failed_modules": [
    {
      "module": "tests.test_hq_task_routing_smoke",
      "test_id": "tests.test_hq_task_routing_smoke.TestHqTaskRoutingSmoke.test_dark_infra_blocked",
      "kind": "failure",
      "message": "AssertionError: expected blocked"
    }
  ]
}
```

**Log 輸出（機器／人讀）**

- `echo '::group::core-agent-smoke summary'` → `cat smoke_ci_summary.json` → `echo '::endgroup::'`
- 可選：`jq -c '.failed_modules[]' smoke_ci_summary.json` 逐行 print（方便 log grep）

#### E. CI YAML：摘要產生 + artifact 上傳（片段）

```yaml
      - name: Core agent smoke (tier PR)
        id: smoke
        shell: bash
        run: |
          set -euo pipefail
          START_MS=$(python -c "import time; print(int(time.time()*1000))")
          set +e
          python 04_Workflows/_core_agent_smoke.py --tier PR -v | tee smoke_result_raw.json
          SMOKE_EXIT=$?
          set -e
          END_MS=$(python -c "import time; print(int(time.time()*1000))")
          export SMOKE_EXIT START_MS END_MS
          python - <<'PY'
          import json, os, sys
          from pathlib import Path
          raw = Path("smoke_result_raw.json").read_text(encoding="utf-8").strip()
          smoke = json.loads(raw) if raw else {"ok": False, "message": "empty stdout"}
          failed_tests = smoke.get("failed_tests") or []
          seen = set()
          failed_modules = []
          for rec in failed_tests:
              tid = str(rec.get("test_id") or "")
              mod = tid.rsplit(".", 1)[0] if "." in tid else tid
              key = (mod, tid)
              if key in seen:
                  continue
              seen.add(key)
              failed_modules.append({
                  "module": mod,
                  "test_id": tid,
                  "kind": rec.get("kind"),
                  "message": rec.get("message"),
              })
          summary = {
              "workflow_name": "Core agent smoke",
              "job_name": "agent-smoke-pr",
              "tier": "PR",
              "ok": SMOKE_EXIT == 0 and smoke.get("ok") is True,
              "duration_ms": int(os.environ["END_MS"]) - int(os.environ["START_MS"]),
              "github_run_id": os.environ.get("GITHUB_RUN_ID", ""),
              "github_sha": os.environ.get("GITHUB_SHA", ""),
              "smoke_result": smoke,
              "failed_modules": failed_modules,
          }
          Path("smoke_ci_summary.json").write_text(
              json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
          )
          print(json.dumps(summary, ensure_ascii=False))
          sys.exit(int(os.environ["SMOKE_EXIT"]))
          PY

      - name: Emit structured failure summary
        if: failure()
        shell: bash
        run: |
          echo "::group::core-agent-smoke summary"
          cat smoke_ci_summary.json 2>/dev/null || cat smoke_result_raw.json 2>/dev/null || true
          echo "::endgroup::"

      - name: Upload smoke CI summary
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: core-agent-smoke-pr-${{ github.run_id }}
          path: |
            smoke_ci_summary.json
            smoke_result_raw.json
          if-no-files-found: warn
          retention-days: 14
```

> **施工備註**：summary 組裝可留在 workflow inline Python（如上）或日後抽到 `04_Workflows/_core_agent_smoke.py --emit-ci-summary`；本票優先 workflow 內完成，避免動 `core/*`。

#### F. docs/testing.md — Excluded / Not covered by PR smoke（初版清單）

施工時寫入「PR Smoke Tier」小節末尾；與 FRAME Non-Goals 對齊。

| 類別 | 不在 PR smoke 的項目 | 替代 gate／備註 |
|------|----------------------|-----------------|
| **全量 unit** | `python -m unittest discover -s tests` | 本地／專票；PR 僅 ROOT 7 模組 |
| **Dark tier** | `--tier DARK`、`DARK_FULL`、gov_core 135+ 全矩陣 | `workflow_dispatch` 或本地 venv |
| **Wave7 regression** | `_wave7_regression_gate.py` Tier-A/B/C | **W2-T4** Release checklist（Tier-A） |
| **Live I/O** | PostgreSQL、Qdrant、OpenAI 實連 | mock／fixture only |
| **Ask e2e** | `tests.test_ask_selector_and_answer` | 需 gov_core `langgraph`；eval-gate-ci 部分覆蓋 |
| **Keys／runbook** | `_smoke_test_keys.py`、Telegram listener | 手動 runbook；禁 CI 印 secret |
| **Eval nightly** | prod shadow spool、`eval-shadow-nightly` cron | `eval-gate-ci.yml` schedule job |
| **workflow_v2** | `gov-gate-metrics.yml` 路徑 gate | 觸 `workflow_v2/**` 時另跑 |
| **純文檔 PR** | 僅 `**/*.md` 等 paths-ignore 變更 | workflow 不觸發（by design） |

**一句話邊界（docs 首段可引用）**：PR smoke 驗證 **7 個 ROOT agent workflow 模組**；**不**代表發版就緒——Release 前仍須 W2-T4 Tier-A 與可選 DARK／ALL。

---

### CI workflow skeleton（YAML 草稿 · 施工參考）

> 以下為 **目標形狀**；現倉已有 `.github/workflows/core-agent-smoke.yml`，施工時 diff 對照合併。

```yaml
# Phase 6 (P6): core agent workflow smoke — PR fast path + optional dark tier.
# Complements eval-gate-ci.yml (P+ eval) and gov-gate-metrics.yml (workflow_v2).

name: Core agent smoke

on:
  push:
    paths-ignore:
      - "02_Agents_Core/repos/**"
      - "05_Temp_Cache/**"
      - "**/*.md"
      - "workflow_v2/**"
  pull_request:
    paths-ignore:
      - "02_Agents_Core/repos/**"
      - "05_Temp_Cache/**"
      - "**/*.md"
      - "workflow_v2/**"
  workflow_dispatch:
    inputs:
      tier:
        description: Smoke tier (PR, ROOT, DARK, ALL)
        type: choice
        options: [PR, ROOT, DARK, ALL]
        default: PR

concurrency:
  group: core-agent-smoke-${{ github.workflow }}-${{ github.ref }}-${{ github.event_name }}
  cancel-in-progress: true

jobs:
  agent-smoke-pr:
    name: Agent workflow smoke (PR tier)
    if: >-
      github.event_name != 'workflow_dispatch'
      || (github.event_name == 'workflow_dispatch' && (inputs.tier == 'PR' || inputs.tier == 'ROOT'))
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Core agent smoke (tier PR)
        id: smoke
        shell: bash
        run: |
          set -euo pipefail
          python 04_Workflows/_core_agent_smoke.py --tier PR -v | tee smoke_result.json

      # Failure handling（僅 exit ≠ 0 時執行；施工時用 if: failure()）
      - name: Emit structured failure summary
        if: failure()
        shell: bash
        run: |
          echo "::group::Smoke JSON"
          cat smoke_result.json 2>/dev/null || true
          echo "::endgroup::"
          exit 1

  # agent-smoke-dark / agent-smoke-all: workflow_dispatch only — 見現有 yml；PR 不觸發
```

---

### docs/testing.md 段落大綱（施工清單）

```markdown
## PR Smoke Tier（W2-T1 · Phase 6 收口）

### 目的
…（fast PR gate；H-line / routing / eval-gate 子集）

### 執行方式
| 環境 | 命令 |
| 本地 | `python 04_Workflows/_core_agent_smoke.py --tier PR` |
| CI | `.github/workflows/core-agent-smoke.yml` → job `agent-smoke-pr` |

### 覆蓋模組
| 模組 | 領域 | 備註 |
| tests.test_context_entry | H-line | **AC 必達** |
| tests.test_hq_task_routing_smoke | HQ routing | **AC 必達** |
| tests.test_eval_gate | P+ eval | **AC 必達** |
| …（其餘 ROOT 模組）

### 與其他 gate 分工
| Gate | 票 | 何時跑 |
| PR smoke | W2-T1 | 每 PR |
| Eval gate CI | P+ | 每 PR（並行） |
| Wave7 Tier-A | W2-T4 | Release checklist |

### Exit codes
| exit | 語意 |
| 0 | 全綠 |
| 1 | 測試失敗 |
| 2 | tier／載入／配置錯誤 |

### Excluded / Not covered by PR smoke
（見 B_REPORT §F 表格 — 全量列舉，勿省略）

### 與其他 gate 分工
| Gate | 票 | 何時跑 | 覆蓋 |
| PR smoke | W2-T1 | 每 PR | 7 ROOT 模組 |
| Eval gate CI | P+ | 每 PR | eval unittest + eval_ci_check |
| Wave7 Tier-A | W2-T4 | Release | orchestrator integration |
| Dark smoke | — | manual | gov_core 子集 |
```

---

### Files To Touch

- .github/workflows/core-agent-smoke.yml
- 04_Workflows/_core_agent_smoke.py（僅當需補 JSON 欄位；預設不改）
- docs/testing.md

- changed_files:
  - `.github/workflows/core-agent-smoke.yml`
  - `docs/testing.md`
  - `04_Workflows/tickets/W2-T1_state.md`
- artifacts:
  - CI artifact `core-agent-smoke-pr-<run_id>`（含 `smoke_ci_summary.json`、`smoke_result_raw.json`）— 待首次 PR 觸發後確認
- verification:
  - 本地：`python 04_Workflows/_core_agent_smoke.py --tier PR` → exit 0；78 tests，7 模組，`"ok": true`
  - CI：待人工 PR 觸發（O_NOTES 占位 URL）
- behavior_notes: |
  - 2026-06-07 implementer：完成 Implementation Plan 與 YAML/docs 草稿；未改 workflow 檔、未跑 CI。
  - 2026-06-07 implementer（post-review）：補 §D CI 失敗 JSON schema、§E artifact YAML 片段、§F Excluded 初版清單；Reviewer accepted_with_gaps → gaps closed in Plan。
  - 2026-06-07 implementer（施工輪）：workflow + docs 已落地；本地 PR tier 全綠；CI URL 占位待填。
- deferred_items: |
  - Branch protection required check 設定（ops）
  - 首次 PR 觸發綠色 run URL（O_NOTES 占位；不阻塞票面關閉）
  - W2-T4 Release checklist 正文（W2-T4 票；本票 docs 已 cross-ref + Excluded 表）
  - 可選：將 CI summary 組裝抽到 smoke CLI（非本票必須）

---

## C_REPORT

> Post-Implementation Review · 2026-06-07

- verdict: accepted_with_gaps
- conclusion: accepted_with_gaps
- blocking_issues: 無
- risk_level: low
- checks_summary: |
  - **core-agent-smoke (PR tier)**：job `Agent workflow smoke (PR tier)`（`agent-smoke-pr`）；命令 `python 04_Workflows/_core_agent_smoke.py --tier PR -v`；7 ROOT 模組（context_entry / subagent_routing / monitoring_executor / langgraph_k2 / hq_task_routing / eval_gate / eval_ci_check）；dark/all 僅 `workflow_dispatch`。
  - **本地驗證**：`--tier PR` exit 0；78 tests；`ok: true`。
  - **失敗摘要**：CI inline Python 產 `smoke_ci_summary.json`（含 `workflow_name`、`failed_modules[]`、`duration_ms`）；`if: failure()` 結構化 log；`always()` artifact 14 天。
  - **docs/testing.md**：§5 PR Smoke Tier + §5.1 W2-T4 對照 + Excluded 表 + §6 schema — 對齊 workflow。
  - **Gaps（非阻塞）**：尚缺首次 CI 綠 run URL（O_NOTES 占位）；branch protection required check 尚未啟用（ops follow-up）。
- gap: |
  缺少第一次綠色 CI run 實戰佐證（O_NOTES URL 仍占位）。不影響票面完整度；首次 PR 綠燈後填 URL，若有問題開 follow-up 小票，不回滾 W2-T1。
- suggestions: |
  1. Ops：將 `Agent workflow smoke (PR tier)` 設為主要分支 required check。
  2. W2-T4：施工時引用 docs/testing.md §5.1，保持 gate 定義一致。
  3. 首次 CI 綠 run 後更新 O_NOTES 占位 URL；確認 `smoke_ci_summary.json` artifact 可 JSON parse。

---

## D_REPORT

- docs_updates:
  - `.github/workflows/core-agent-smoke.yml` — PR job `Agent workflow smoke (PR tier)`；`smoke_ci_summary.json` 產生 + artifact 上傳（14 天）
  - `docs/testing.md` §5 PR Smoke Tier + §5.1 W2-T4 對照 + Excluded 表 + §6 CI acceptance schema
- verification:
  - 本地：`python 04_Workflows/_core_agent_smoke.py --tier PR` → **exit 0**；78 tests；`ok: true`；7 ROOT 模組全在 `modules[]`
  - 本地（CI 等價）：`python 04_Workflows/_core_agent_smoke.py --tier PR -v` → **exit 0**
  - AC 必達模組：`test_context_entry`、`test_eval_gate`、`test_hq_task_routing_smoke` — 含於 PR tier
  - **CI 實戰**：尚無含本版 workflow 的首次 PR 綠色 run URL（Reviewer gap，**不阻塞票面**）
- behavior_notes:
  - PR／push 觸發；`paths-ignore` 含 `**/*.md` — 純文檔 PR **不**跑 smoke（by design）
  - `agent-smoke-dark` / `agent-smoke-all` 僅 `workflow_dispatch`；PR 路徑**不**觸發 DARK / DARK_FULL
  - 失敗時 inline Python 產 `smoke_ci_summary.json`（`workflow_name`、`failed_modules[]`、`duration_ms`）；`if: failure()` 結構化 log
  - PR smoke 驗證 7 個 ROOT agent workflow 模組；**不代表** Release 就緒（發版前仍須 W2-T4 Tier-A）
  - **branch protection required check 尚未啟用** — 勿宣稱已設 required check
- progress_entry: |
    W2-T1 收口：`.github/workflows/core-agent-smoke.yml` 已落地；PR tier 覆蓋 7 個 ROOT 模組（含 context_entry / eval_gate / hq_task_routing）；本地 `--tier PR` exit 0。契約見 `docs/testing.md` §5–§6。首次 CI 綠 run 與 branch protection 為 ops follow-up，非重開條件。
- followup_suggestions:
  - **ops**：merge 含 workflow 的 PR 後，將首次 Actions 綠 run URL 填入 O_NOTES `_TBD_` 列
  - **ops**：Settings → Branch protection → required check **`Agent workflow smoke (PR tier)`**（與 eval-gate-ci 並行）
  - **W2-T4**：Release checklist 引用 `docs/testing.md` §5.1，保持 gate 定義一致
  - **可選**：將 CI summary 組裝抽到 `_core_agent_smoke.py --emit-ci-summary`（非本票必須）

---

## O_NOTES

> **O 區**：Orchestrator 維護 run log 與戰報連結；Observe / Operate 計畫。

### Observability Plan

- 記錄首次 CI 綠色 run URL 至 O_NOTES Run Log
- 失敗時 artifact `core-agent-smoke-pr-<run_id>` 含 `smoke_ci_summary.json`（`workflow_name`、`failed_modules[]`、`duration_ms`）

### VerificationCommands

**本地（repo 根、無 venv）**

```powershell
python 04_Workflows/_core_agent_smoke.py --tier PR
python 04_Workflows/_core_agent_smoke.py --tier PR -v
python 04_Workflows/_core_agent_smoke.py --tier PR --pretty
```

預期：exit `0`；JSON `"ok": true`；7 模組全在 `modules[]`。

**CI**

- Workflow：`Core agent smoke`（`.github/workflows/core-agent-smoke.yml`）
- Job：`Agent workflow smoke (PR tier)`（`agent-smoke-pr`）
- 觸發：PR / push（paths-ignore 純文檔 PR 除外）
- 手動驗收：`workflow_dispatch` → tier `PR`
- 預期：job 綠；artifact 含 `smoke_ci_summary.json`

**Actions run URL（占位，待人工跑完後替換）**

`https://github.com/<ORG>/<REPO>/actions/runs/<RUN_ID>`

> **票面關閉說明**：首次 CI 綠 run URL 待填；**不阻塞 W2-T1 關票**。merge 含本 workflow 的 PR 後，由 ops／implementer 將實際 run URL 填入上列占位與 Run Log `_TBD_` 列。

### Rollout / Ops Notes

- 記錄首次 CI 綠色 run URL 至 O_NOTES Run Log
- Merge 前確認 repo Settings → Branch protection → required checks 含 `Agent workflow smoke (PR tier)` 或等價 job 名

### Run Log

| date | role | action | link |
|------|------|--------|------|
| 2026-06-07 | orchestrator | 開票 FRAME/STATE/B_REPORT 預填 | 本檔 |
| 2026-06-07 | implementer | B_REPORT Implementation Plan 詳細草稿；STATE → in_progress | 本檔 |
| 2026-06-07 | reviewer | C_REPORT accepted_with_gaps（缺 JSON schema + Excluded 列舉） | 本檔 |
| 2026-06-07 | implementer | B_REPORT §D–§F 補 gap；Plan 可進施工 | 本檔 |
| 2026-06-07 | implementer | 施工 workflow + docs；STATE → in_review；本地 PR smoke 全綠 | 本檔 |
| 2026-06-07 | reviewer | Post-implementation C_REPORT accepted_with_gaps；STATE → done | 本檔 |
| _TBD_ | ops / implementer | 首次 PR 觸發 core-agent-smoke 全綠（不阻塞關票） | `https://github.com/<ORG>/<REPO>/actions/runs/<RUN_ID>` <!-- 占位：首次 PR 綠燈後替換 --> |
