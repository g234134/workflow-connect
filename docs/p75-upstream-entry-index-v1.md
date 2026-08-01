# P7.5 Upstream Entry Index v1

> **Ticket**: `W1-P75-UPSTREAM-ENTRY-INDEX-v1` · **Wave 1** · P7.5 upstream  
> **Scope**: single-page discoverability for P7.5 **upstream** docs/CLIs  
> **Not**: full Wave 1–5 rollup · Master CP commands/schema · Phase% refresh

## Boundary (read first)

| This index | Deferred elsewhere |
|------------|-------------------|
| **P7.5 upstream only** — gate CLI · policy · intake CLI · deny · trace · MP-SMOKE step 1 | **全 Wave playbook rollup → `W5-T5-cross-wave-playbook-index-v1`** |
| Entry table for Planner / Orchestrator 接戰 | W-MASTER 全 Wave 規劃正文 · W-ORCH lane 編排 |
| Cross-ref `W1-P75-*` + `P75-G*` 票 ID | Multi-Chat commands / ticket schema 主施工（**W5-T1 / W5-T2**） |

**一句話**：全 Wave playbook rollup → **W5-T5**；本 index **僅 P7.5 上游**。

## Entry table (≥5 rows)

| # | entry_type | Path / command | Ticket / SSOT | When to open |
|---|------------|----------------|---------------|--------------|
| 1 | cli | `python scripts/run_intake_gate_cli.py --task-type tabular.cleaning.mvp --case-dir <case> --mode preview\|run --format json` | `P75-G2` · contract `docs/intake-gate-contract-v1.md` | Gate preview / run + outbox |
| 2 | cli | `python scripts/new_cleaning_case.py … --run-p75-gate` | `W1-P75-INTAKE-CLI-MVP-v1` · `docs/p75-intake-cli-upstream-mvp-v1.md` | Human case create → P75 preview（無 outbox） |
| 3 | doc | `docs/p75-policy-deny-path-mvp-v1.md` | `W1-P75-POLICY-DENY-MVP-v1` · policy YAML `routing/intake_gate_policy_v1.yaml` | Deny `reason_code` / golden / MC-SMOKE `phi_demo` |
| 4 | doc | `docs/p75-intake-gate-control-plane-trace-v1.md` | `W1-P75-TRACE-UPSTREAM-v1` | gate→outbox→MP-SMOKE→metrics **trace 欄位 SSOT** |
| 5 | doc | `docs/p75-intake-cli-upstream-mvp-v1.md` | `W1-P75-INTAKE-CLI-MVP-v1` | Canonical ≥3-step case→gate 敘事 |
| 6 | cli | `python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json`（step 1 = gate） | `MP-SMOKE` · consumes TRACE SSOT | Upstream smoke 觀測（≠ staging/prod） |
| 7 | doc | `docs/WAVE_PROGRESS_DASHBOARD.md`（P7.5 列 · **只讀**） | Dashboard Phase% SSOT | 看完成度敘事；**本票不改 %** |
| 8 | cli／http | `python scripts/run_intake_gate_http_stub_v1.py --once …` · loopback `POST /api/intake/gate` | `P75-G7` · `docs/p75-intake-gate-http-stub-v1.md` | Wave 2 本地 HTTP stub（≠ prod app_api） |

## Ticket → artifact map

| Ticket | Status (as of open) | Primary artifact |
|--------|---------------------|------------------|
| `W1-P75-POLICY-DENY-MVP-v1` | done | `docs/p75-policy-deny-path-mvp-v1.md` |
| `W1-P75-INTAKE-CLI-MVP-v1` | done | `docs/p75-intake-cli-upstream-mvp-v1.md` + `--run-p75-gate` |
| `W1-P75-TRACE-UPSTREAM-v1` | done | `docs/p75-intake-gate-control-plane-trace-v1.md` |
| `W1-P75-UPSTREAM-ENTRY-INDEX-v1` | this doc | `docs/p75-upstream-entry-index-v1.md` |

Related capability tickets（只讀索引）：`P75-G2` · `P75-G3` · `P75-G4` · `P75-G5` · `P75-G6` · `P75-G7` · `P75-REGRESSION` · `MP-SMOKE`.

## Suggested read order (P7.5 upstream 接戰)

```
1. 本 index（定位邊界）
2. docs/p75-intake-cli-upstream-mvp-v1.md          # 人類接案 CLI
3. docs/p75-policy-deny-path-mvp-v1.md             # deny 路徑
4. docs/p75-intake-gate-control-plane-trace-v1.md  # trace SSOT（禁止自創欄位）
5. scripts/run_intake_gate_cli.py --mode preview   # 本地 spot-check
6. （可選）MP-SMOKE step 1 · Dashboard P7.5 列
```

## Non-claims

引用 `W-ORCH-wave-next-control-plane-v1_state.md` **§全局 non-claims**（不在此複製 Phase% 表）：

- 不調高 Phase%／不宣稱某 Phase 100%
- advisory CI ≠ required check／merge gate
- local slot／sandbox／smoke ok ≠ prod-ready
- CI workflow landing ≠ GA pass（無 run URL 不算）
- 本 index **≠** W5-T5 全 Wave rollup · **≠** notify transport 完成 · **≠** G-1–G-5 resume runtime（Wave 2）

## Index maintenance

- 新 P7.5 **上游**入口：在本表增量一行，並在對應 `W1-P75-*`／`P75-G*` 票留 cross-ref。
- 全 Wave／commands／schema／lane index：**不要**寫進本檔 → 開或更新 **W5-T5**／**W5-T1**／**W5-T2**。
