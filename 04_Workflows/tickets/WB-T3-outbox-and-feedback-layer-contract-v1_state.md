# TICKET STATE · WB-T3 · outbox-and-feedback-layer-contract-v1

> handoff 摘要檔；跨 chat 交棒以本檔為準，不是完整工作日誌。

---

## FRAME
<!-- Orchestrator 填：票的邊界與驗收標準；開票時寫，施工前凍結 -->

- Goal: 把 Tabular MVP outbox、Agent experiment/CI outbox、Non-Tabular sandbox、sandbox delivery、agent metrics 統一 schema 索引；產出 contract SSOT；與 Phase 8.8 orchestration_bridge_outbox 永久分軌。
- Scope:
  - 新增 `docs/outbox-and-feedback-layer-contract-v1.md`
  - 新增 `docs/schemas/outbox_layer_v1.json`
  - 新增 `tests/test_outbox_and_feedback_layer_contract_v1.py`
  - 降級 `docs/tabular-tool-outbox-spec.md` · `docs/tabular-outbox-consumer-spec.md` 為實作附錄 + 指針
  - 更新 `docs/WAVE_PROGRESS_DASHBOARD.md` · `04_Workflows/WORKFLOW_INDEX.md`
- NonScope:
  - 不改 outbox writer/consumer 行為或檔名規則
  - 不實作 replay / DLQ / 新 consumer
  - 不讀寫 orchestration_bridge_outbox
  - 不改 inspect_tabular_outbox CLI
- AllowedPaths:
  - `docs/outbox-and-feedback-layer-contract-v1.md`
  - `docs/schemas/outbox_layer_v1.json`
  - `docs/tabular-tool-outbox-spec.md`
  - `docs/tabular-outbox-consumer-spec.md`
  - `tests/test_outbox_and_feedback_layer_contract_v1.py`
  - `04_Workflows/tickets/WB-T3-outbox-and-feedback-layer-contract-v1_state.md`
  - `docs/WAVE_PROGRESS_DASHBOARD.md`
  - `04_Workflows/WORKFLOW_INDEX.md`
- BlockedPaths:
  - `tools/tabular_outbox_writer.py`
  - `tools/tabular_outbox_consumer.py`
  - `tools/inspect_tabular_outbox.py`
  - 暗部 `core/orchestration_bridge_outbox.py`
- Dependencies: W3-TL-T3/T4 · W6-T5/T6/T8 · W9-T4 · W10-T1 · W12-T1 · WB-T1 · WB-T2 · WA-T1 P2（index_status 側車）
- AcceptanceCriteria:
  - [AC-1] contract §2 六命名空間表
  - [AC-2] 每命名空間 schema_id / producer / consumer / retention
  - [AC-3] feedback 子物件語意（HITL / delivery approval / controlled notify）
  - [AC-4] join_with_case_history 對齊 cases/index.json
  - [AC-5] unittest 全綠；fixture 掃描驗證 schema_id
  - [AC-6] inspect_tabular_outbox 最小範例符合 contract §3
  - [AC-7] Dashboard Phase 8.9 40%→80%
  - [AC-8] 無 schema_version 退化規則
  - [AC-9] 引用 WA-T4 §5 STATE 寫入凍結
  - [AC-10] 禁止合併路徑 unittest 斷言

---

## STATE
<!-- Orchestrator 維護：當前進度與下一棒；每次角色交棒後更新 -->

- overall_status: done
- current_owner: orchestrator
- next_action: 無（票面已收口；Toolchain Wave B closure complete）
- last_updated: 2026-06-11 · orchestrator
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT
<!-- Implementer 填：施工結果；只寫本區塊，不改 FRAME / STATE -->

- changed_files:
  - `docs/outbox-and-feedback-layer-contract-v1.md`（新增 SSOT）
  - `docs/schemas/outbox_layer_v1.json`（新增機器索引）
  - `tests/test_outbox_and_feedback_layer_contract_v1.py`（新增 contract unittest）
  - `docs/tabular-tool-outbox-spec.md`（WB-T3 指針 + contract SSOT 降級附錄）
  - `docs/tabular-outbox-consumer-spec.md`（WB-T3 指針 + contract SSOT 降級附錄）
  - `docs/WAVE_PROGRESS_DASHBOARD.md`（Phase 8.9 40%→80% · WB-T3 條目）
  - `04_Workflows/WORKFLOW_INDEX.md`（WB-T3 索引）
  - `04_Workflows/tickets/WB-T3-outbox-and-feedback-layer-contract-v1_state.md`（本檔 B_REPORT）
- artifacts:
  - `docs/outbox-and-feedback-layer-contract-v1.md`
  - `docs/schemas/outbox_layer_v1.json`
- verification:
  - `python -m unittest tests.test_outbox_and_feedback_layer_contract_v1 -v` → **16/16 OK**
  - `python -m tools.inspect_tabular_outbox --case-ref demo_phase --json --outbox-root tests/fixtures/outbox` → exit 0；`ok: true`, `count: 2`, runs[] 含 §3 必填欄位
- behavior_notes:
  - 對齊 WB-T1（`tool-catalog-and-selector-contract-v1.md`）與 WB-T2（`tool-executor-and-sandbox-safety-contract-v1.md`）之 `execution_mode` / outbox 落盤矩陣；未改任何 writer/consumer。
  - AC-6 票面寫 `--format json`；實作 CLI 凍結為 `--json`（Non-Goals）；contract §3 與 unittest 使用實際旗標。
  - `orchestration_bridge_outbox` 僅出現在禁止合併表與 unittest 斷言；未讀寫暗部模組。
- deferred_items:
  - WB-T4：`outbox_write_count` / `outbox_read_count` 即時聚合 hook（contract 僅預留欄位）
  - `events.jsonl` streaming consumer（仍為 Non-Goals）

---

## C_REPORT
<!-- Reviewer 填：審查結論；只寫本區塊，不改 code -->

- conclusion: **accepted_with_gaps**
- blocking_issues: **无**
- checks_summary:
  - **FRAME**：未被 Implementer 改动；六命名空间、feedback、join、分轨禁令与 AC 一致。
  - **B_REPORT 证据**：`tests.test_outbox_and_feedback_layer_contract_v1` **16/16 OK**；`inspect_tabular_outbox --case-ref demo_phase --json --outbox-root tests/fixtures/outbox` → exit 0，`ok: true`, `count: 2`。
  - **AC 对照**：§2 六命名空间表；§3 inspect 输出形状；§4 feedback 子对象；§5 `join_with_case_history`；§6/§8 退化规则；`outbox_layer_v1.json` 机器索引；旧 spec 降级附录；`orchestration_bridge_outbox` 永久分轨 unittest 断言；Dashboard P8.9 40%→80%。
  - **Rule 3**：未改 writer/consumer/暗部 bridge。
- risk_level: **low**
- suggestions:
  - **缺但可接受**：票面 AC-6 写 `--format json`，CLI 冻结为 `--json`（B_REPORT 已留痕；contract/unittest 用实际旗标）。
  - **缺但可接受**：`outbox_write_count`/`outbox_read_count` 实时聚合留 WB-T4 deferred。
  - 无 blocking；可交 Scribe。

---

## D_REPORT

- docs_updates:
  - `docs/schemas/outbox_layer_v1.json` 机器索引与 readme / 执行计划 §5 交叉引用一致
  - Dashboard Toolchain 分栏 P8.9 状态列已对齐（WC-PRE-01）
- progress_entry: WB-T3 交付 outbox+feedback contract SSOT（六命名空间 · `orchestration_bridge_outbox` 永久分轨）；`tests.test_outbox_and_feedback_layer_contract_v1` 16/16 OK。
- followup_suggestions:
  - **WB-T4 deferred**：`outbox_write_count` / `outbox_read_count` 实时聚合
  - CLI 旗标：`--json`（非 `--format json`）已在 C_REPORT 留痕
