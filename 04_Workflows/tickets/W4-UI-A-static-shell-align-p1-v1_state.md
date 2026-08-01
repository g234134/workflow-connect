# TICKET STATE · W4-UI-A-static-shell-align-p1-v1 · Wave4-A 靜態殼對齊 PNG

> Wave 4 UI 首票 · build · FRAME 凍結後可施工  
> 上游凍結：`W4-UI-FREEZE-unified-p1-p5-v1` · SSOT：`docs/wave4-ui-visual-freeze-v1.md`

---

## FRAME

- Goal: 交付戰車根獨立靜態／輕量指揮中心殼，視覺對齊 `unified_P1.png`，以 mock JSON 掛載 operator fields 草案鍵；宿主可本地開啟，預留接 `app/local_ui`。
- Scope:
  - MUST：共用 sidebar／header／設計 token（炭黑＋青／金＋綠黃紅狀態），左導五項固定、品牌「三省六部指揮中心」
  - MUST：P1 頁面靜態結構對齊 `docs/ui-templates/unified_P1.png`（KPI 列 · 主流程 · 狀態點 · 活動日誌）
  - MUST：以 `page01.html`（及必要共用 CSS／JS）為起點升級視覺；**不以**降級 HTML 當最終美觀標準
  - MUST：接入 **operator fields mock**（至少對齊計劃 §2.1–2.4／`p89_operator_fields_v1` 五鍵之可顯示子集；可用靜態 `mock/*.json`）
  - MUST：宿主＝**獨立靜態殼**（戰車根相對路徑，例如 `docs/ui-templates/` 或約定 `ui/command_center/`）；文件註明後續可掛 `app/local_ui`
  - MUST：金鑰相關 UI **僅遮罩**占位（即使 P1 無金鑰區，共用元件也不得渲染明文）
  - MUST：unittest 或 CLI smoke 證明 mock JSON 可載入且頂層 `ok`／schema 鍵穩定
  - MAY：最小 README／runbook 一頁（如何開殼、對照 PNG）
- NonScope:
  - Wave4-B–E（P5／P4／P3／P2 完整頁）— 另票
  - 真 API／prod／暗部 `dashboard.html` 大翻修／Grafana
  - 改暗部 `core`、DarkOps 解禁、寫 runtime checkpoints
  - 展示金鑰原文；改 `.env`；Dashboard Phase% authorize
  - React 全站重寫（本票允許純靜態＋輕量 JS）
- AllowedPaths:
  - `docs/ui-templates/**`（page／css／js／mock；**不**刪 `unified_P*.png`）
  - `ui/command_center/**`（若新建獨立殼目錄）
  - `docs/wave4-ui-a-static-shell-runbook-v1.md`（MAY）
  - `tests/test_w4_ui_a_static_shell_v1.py`（或等價）
  - `scripts/` 下本票專用 smoke（若需要）
  - `04_Workflows/tickets/W4-UI-A-static-shell-align-p1-v1_state.md`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
  - `04_Workflows/WORKFLOW_INDEX.md`（MAY 一句）
- BlockedPaths:
  - 憲法 §7 類型（Z-ENV／Z-VENV-TREE／Z-RUNTIME-CP／Z-DARK-OPS／Z-HQ-LIQUIDATION／Z-HQ-ENV-EDIT）
  - 暗部根／`dashboard.html` 大翻修（除非另授權）
  - `docs/WAVE_PROGRESS_DASHBOARD.md` 數字格
  - `.github/workflows/**`（本票不開 required CI）
- Dependencies:
  - `W4-UI-FREEZE-unified-p1-p5-v1`（視覺凍結 **done**）
  - `docs/p89-operator-fields-projection-v1.md`（mock 鍵參考）
  - 計劃 §2.1–2.4 UI 必讀欄位草案
- relay_mode: same_chat
- AcceptanceCriteria:
  - AC-1：瀏覽器可開 P1 殼；左導／品牌／KPI／流程／日誌區塊存在，對照 `unified_P1.png` 資訊架構一致（允許像素級差異記於 B_REPORT）
  - AC-2：mock JSON 含 `ok` 與至少 P8.9 五鍵之一組 rows／fields（或明確標 skeleton 的缺鍵）
  - AC-3：`python -m unittest tests.test_w4_ui_a_static_shell_v1 -v`（或票內约定 CLI）PASS
  - AC-4：文件聲明宿主＝獨立靜態殼；≠ Grafana；≠ 暗部大翻修；金鑰無明文
  - AC-5：Progress 末尾有驗證命令與 `ok` 語意；`apply_phase_pct=false`
  - AC-6：未改禁區；未宣稱 Wave4-B–E 完成

### Wave Master 擴展

- wave_id: W4
- group_id: null
- lifecycle_phase: B
- phase_targets: [P7.5, P8.9, P5]
- estimated_cycles: 1
- mvp_allowed: true
- human_only_prereqs: []
- infra_only_prereqs: []
- security_only_prereqs: []
- dependencies_detail:
  - upstream_tickets: [W4-UI-FREEZE-unified-p1-p5-v1, P89-W2-narrative-t4-obs-projection-v1]
  - downstream_waves: [W4]
  - blocks_if_missing:
    - item: visual_freeze
      owner: W4-UI-FREEZE
      if_missing: stop_work
- risks:
  - id: html_visual_downgrade
    description: 沿用簡化 page01 導致與 PNG 落差大
    likelihood: medium
    impact: medium
    mitigation: B_REPORT 對照清單；必要時拆「視覺對齊」子增量
    residual: 像素完美可留 Wave4-A.1
  - id: fake_kpi_as_acceptance
    description: mock 100% 被當成真契約
    likelihood: medium
    impact: high
    mitigation: mock 標 `demo`／`read_only`；non_claims 寫明 ≠ live SLO
    residual: Reviewer 抽查
- observability:
  - verify_commands:
    - `python -m unittest tests.test_w4_ui_a_static_shell_v1 -v`
    - `python scripts/inspect_p89_operator_fields_v1.py --case-ref demo_phase --format json`（對照鍵名；本票可用 mock 而非 live）
  - evidence_artifacts:
    - P1 HTML／CSS 路徑（B_REPORT 填）
    - mock JSON 路徑
    - 可選截圖 vs `unified_P1.png`
  - trace_fields: [event_id, ack_status, handler_id, dispatch_registry_hit, dlq_flag]
  - success_signals: [unittest PASS, shell opens, mock ok true]
  - failure_signals: [missing mock keys without skeleton label, secrets rendered]
- non_claims:
  - ≠ Wave4-B–E 完成
  - ≠ live API／prod
  - ≠ 金鑰原文
  - ≠ DarkOps／暗部 core 改寫
  - ≠ Grafana
  - ≠ Dashboard Phase% authorize
  - ≠ Phase closure
- ticket_class: build
- evidence_tier: L-local
- parallel_ok: false

---

## STATE

- overall_status: accepted_with_gaps
- lifecycle_phase: B
- current_owner: scribe
- next_action: Wave4-B（P5 泳道）施工；A.1 視覺薄補可併本輪；Wave4-C–E 另票
- last_updated: 2026-07-27 · reviewer/orchestrator
- ops_checklist: 無
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done
- gaps_summary: 像素／插畫節點／字距未完美對齊 unified_P1.png；flow 為 CSS 圓＋首字 icon（非原圖向量）；KPI 缺細緻圖示可留 A.1

---

## B_REPORT

- changed_files:
  - `ui/command_center/index.html`
  - `ui/command_center/p1.html`
  - `ui/command_center/css/shell.css`
  - `ui/command_center/js/shell.js`
  - `ui/command_center/mock/p1_overview_v1.json`
  - `docs/ui-templates/page01.html`（升級對齊；共用 command_center 資產）
  - `docs/wave4-ui-a-static-shell-runbook-v1.md`
  - `tests/test_w4_ui_a_static_shell_v1.py`
  - `04_Workflows/00_Agent_Work_Progress.md`（末尾 append）
- artifacts:
  - 宿主：`ui/command_center/p1.html`（獨立靜態殼）
  - mock：`ui/command_center/mock/p1_overview_v1.json`（`ok` + P8.9 五鍵 rows）
  - runbook：`docs/wave4-ui-a-static-shell-runbook-v1.md`
  - 視覺 SSOT：`docs/ui-templates/unified_P1.png`（未刪）
- verification:
  - `python -m unittest tests.test_w4_ui_a_static_shell_v1 -v` → PASS（8 tests）
  - 開啟方式：repo 根 `python -m http.server 8765` → `/ui/command_center/p1.html`
- behavior_notes:
  - 資訊架構對齊 PNG：sidebar 五項＋品牌、8 KPI、主流程圓節點、六部／暗部狀態點、活動日誌；另加 P8.9 operator fields 表（票 MUST，PNG 無此區）
  - 視覺 gap（允許）：PNG 細緻插畫／精確字距未像素級還原；flow 節點為 CSS 圓＋首字 icon，非原圖向量插畫；header 時鐘為 mock 字串
  - 金鑰：sidebar／mock 僅 `••••••••`；JS `maskSecrets`；KPI「額度剩餘」無 key 明文
  - mock 標 `demo`／`read_only`；`phase_field_drafts` 標 skeleton（§2.1／2.3／2.4）
  - ≠ live SLO／Grafana／暗部大翻修／Wave4-B–E／Phase% authorize
- deferred_items: Wave4-B–E；像素完美可留 A.1；真 API 掛載另票

---

## C_REPORT

- conclusion: accepted_with_gaps
- blocking_issues: 無（AC-1–6 資訊架構／mock／unittest／紅線均過；殘差為視覺 polish）
- checks_summary: |
  - AC-1：P1 殼 landmarks（sidebar／KPI／flow／六部／暗部／活動）存在；對照 unified_P1.png 資訊架構一致（像素差見 gaps）
  - AC-2：mock `ok` + P8.9 五鍵 rows；phase_field_drafts 標 skeleton
  - AC-3：`python -m unittest tests.test_w4_ui_a_static_shell_v1 -v` → **8/8 OK**（2026-07-27 重跑）
  - AC-4：runbook 聲明獨立宿主／≠ Grafana／金鑰遮罩
  - AC-5：Progress 有驗證語意；`apply_phase_pct=false`
  - AC-6：未改禁區；未宣稱 Wave4-B–E 完成
  - 瀏覽：金鑰僅 `••••••••`；JS `maskSecrets`；mock `demo`/`read_only`
- gaps:
  - 像素級間距／字距未對齊 PNG
  - flow 節點為 CSS 圓＋首字，非原圖插畫向量
  - KPI 卡缺 PNG 級圖示／環形微圖
  - header 時鐘為 mock 字串
- risk_level: low
- suggestions:
  - A.1 視覺薄補（token／KPI icon／flow 節點／狀態點）— 本輪可併
  - 開 Wave4-B（P5 泳道作業台）
  - 勿把 mock KPI 當 live SLO

---

## D_REPORT

- docs_updates:
  - 本票 STATE／C／D 對齊磁碟交付
  - Progress 末尾 append 收票摘要
  - 開票 `W4-UI-B-p5-swimlane-workbench-v1`；A.1 併本輪薄補（不另開長票）
- progress_entry: 2026-07-27 · W4-UI-A Reviewer `accepted_with_gaps` · 8/8 OK · next=Wave4-B／A.1
- followup_suggestions: Wave4-B P5 泳道；A.1 視覺；Wave4-C–E 另票；`apply_phase_pct=false`
- a1_note: A.1 視覺薄補於 Wave4-B 同輪完成（token／KPI icon／flow 點／status chip）；殘差像素仍允許
