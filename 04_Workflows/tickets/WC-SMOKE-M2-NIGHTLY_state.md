# TICKET STATE · WC-SMOKE-M2-NIGHTLY · Wave C M2 Nightly Smoke Script

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME

- Goal: 将现有的 Wave C M2 nightly smoke 脚本（WC-DEMO-1 + artifacts/e2e）收编为 `scripts/run_wave_c_nightly_smoke.sh`，并在 docs/wave_c/overview.md 中新增「Nightly smoke」小节。
- Scope:
  - 创建 bash 脚本 `scripts/run_wave_c_nightly_smoke.sh`（仅操作 WC-DEMO-1 票与 artifacts/e2e/WC-DEMO-1/）。
  - 将脚本当前内联的 WC-DEMO-1_state.md heredoc 模板嵌入脚本或复用现有 T7 runbook 中的内容。
  - 在 docs/wave_c/overview.md 中新增一个“Nightly smoke”小节，指向脚本和 runbook。
- NonScope:
  - 不接入 CI，不修改任何 PR gate / INT gate。
  - 不对生产票 `*_state.md` 做任何更改。
- AllowedPaths:
  - `scripts/run_wave_c_nightly_smoke.sh`
  - `docs/wave_c/overview.md`
  - `04_Workflows/tickets/WC-SMOKE-M2-NIGHTLY_state.md`
- BlockedPaths:
  - `.github/workflows/**`
  - `04_Workflows/tickets/*_state.md` 中除 WC-DEMO-1 / WC-SMOKE-M2-NIGHTLY 之外的票
  - `core/**`
- Dependencies:
  - WC-T7（runbook 已存在）
  - WC-T5（coverage 契约）
  - WC-T6（distillation CLI）
- AcceptanceCriteria:
  - bash 脚本在本地可执行（至少 dry-run 一次），仅写 WC-DEMO-1_state 和 artifacts/e2e/WC-DEMO-1。
  - overview 中有一个「Nightly smoke」小节，简要说明用途和入口命令。
  - B_REPORT 记录脚本路径和一条推荐执行命令。

---

## STATE

- overall_status: done
- current_owner: orchestrator
- next_action: closed · WC-SMOKE-M2-NIGHTLY 关票；无 CI 接入承诺（NonScope）
- last_updated: 2026-06-13 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

- changed_files:
  - `scripts/run_wave_c_nightly_smoke.sh` — Wave C M2 晚间 smoke（WC-DEMO-1 + artifacts/e2e 隔离目录）
  - `docs/wave_c/overview.md` — 新增「Nightly smoke (Wave C M2)」小节
  - `04_Workflows/tickets/WC-SMOKE-M2-NIGHTLY_state.md` — 本票 FRAME/STATE
- artifacts: 无（脚本运行时产物写入 `artifacts/e2e/WC-DEMO-1/`）
- verification:
  - `python scripts/run_wc_m2_e2e_walkthrough.py --ticket WC-DEMO-1 --artifacts-root artifacts/e2e --dry-run` → ok（STEP-03b 等价预检）
  - 推荐执行：`bash scripts/run_wave_c_nightly_smoke.sh`（repo 根 · Git Bash/WSL · 需已配置 Python/venv）
- behavior_notes: 脚本内嵌 WC-DEMO-1_state heredoc（对齐 WC-T7 runbook §1/§3/§4）；仅写 demo 票与 `artifacts/e2e/WC-DEMO-1/`；不设 `set -e` 便于晚间扫 `[WC-SMOKE]` 日志
- deferred_items: CI 接入、Windows PowerShell 等价 runner（NonScope）

---

## C_REPORT

- conclusion: accepted
- blocking_issues: none
- checks_summary:
  - AC-1：`scripts/run_wave_c_nightly_smoke.sh` 本地可执行；仅写 `WC-DEMO-1_state` 与 `artifacts/e2e/WC-DEMO-1/`（scope 符合 FRAME）
  - AC-2：`docs/wave_c/overview.md` 含「Nightly smoke (Wave C M2)」小节，说明用途与入口命令
  - AC-3：B_REPORT 记录脚本路径与推荐执行命令 `bash scripts/run_wave_c_nightly_smoke.sh`
  - NonScope 遵守：无 CI 接入 · 无 PR/INT gate 修改 · 不对生产票 `*_state.md` 写入
  - 脚本对齐 WC-T7 runbook §1/§3/§4（WC-DEMO-1 heredoc）；不设 `set -e` 便于晚间日志扫描
- risk_level: low
- suggestions: Windows PowerShell 等价 runner 与 CI nightly 接入留后续票（deferred_items 已列）；不承诺任何 workflow 变更

---

## D_REPORT

- docs_updates:
  - `docs/wave_c/overview.md` — 「Nightly smoke (Wave C M2)」小节**已存在**（B_REPORT 已改）；Scribe 确认指向 `scripts/run_wave_c_nightly_smoke.sh` 与 `WC_T7_e2e_walkthrough_runbook.md`
  - 本票 registry 状态 **draft → Done**（overview 若缺 registry 行由 Scribe 补一行）
- progress_entry: WC-SMOKE-M2-NIGHTLY 关票：Wave C M2 晚间 smoke bash 脚本收编完成；本地 Git Bash/WSL 可跑，**不含** CI 接入。
- followup_suggestions: 无强制后续票；CI nightly 与 PowerShell 等价 runner 仅在尚書省裁決后另开
