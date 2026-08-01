# Wave4-D · P3 Dark Execution Loop Runbook v1

> **Ticket**：`W4-UI-D-p3-dark-execution-loop-v1`  
> **宿主**：戰車根獨立靜態殼 `ui/command_center/`（可後接 `app/local_ui`）  
> **視覺 SSOT**：`docs/ui-templates/unified_P3.png`  
> **上游**：`W4-UI-C`（accepted_with_gaps）· 共用 CSS／JS  
> **≠** Grafana · **≠** 暗部 `dashboard.html` 大翻修 · **≠** live API · **≠** DarkOps · **≠** 金鑰明文

---

## 開啟 P3 殼

於戰車根目錄：

```powershell
python -m http.server 8765
```

瀏覽器開啟：

- 權威：`http://127.0.0.1:8765/ui/command_center/p3.html`
- 導覽入口：`http://127.0.0.1:8765/ui/command_center/index.html`（P1／P2／P3／P4／P5）
- P1：`http://127.0.0.1:8765/ui/command_center/p1.html`
- P2：`http://127.0.0.1:8765/ui/command_center/p2.html`（見 Wave4-E runbook）
- P5：`http://127.0.0.1:8765/ui/command_center/p5.html`
- P4：`http://127.0.0.1:8765/ui/command_center/p4.html`

對照：`docs/ui-templates/unified_P3.png`（允許像素差；記於票 B_REPORT）。

---

## Mock

| 路徑 | 說明 |
|------|------|
| `ui/command_center/mock/p3_dark_loop_v1.json` | 七模組／閉環四階／右側監控 + P8.9 subset |

頂層穩定鍵：`ok` · `schema_version=w4_ui_d_p3_dark_loop_v1` · `demo` · `read_only` · `modules` · `loop_flow` · `side_monitor` · `operator_fields`。

金鑰：`secrets.api_key_display` 僅 `••••••••`；JS `maskSecrets`。

導覽：P1／P2／P3／P4／P5 可互點；settings stub。交叉：Wave4-E → `docs/wave4-ui-e-p2-skills-resources-runbook-v1.md`。

---

## 驗證

```powershell
python -m unittest tests.test_w4_ui_d_p3_dark_loop_v1 -v
python -m unittest tests.test_w4_ui_a_static_shell_v1 tests.test_w4_ui_b_p5_swimlane_v1 tests.test_w4_ui_c_p4_command_desk_v1 -v
```

建議合計：

```powershell
python -m unittest tests.test_w4_ui_a_static_shell_v1 tests.test_w4_ui_b_p5_swimlane_v1 tests.test_w4_ui_c_p4_command_desk_v1 tests.test_w4_ui_d_p3_dark_loop_v1 -v
```

---

## Non-claims

- ≠ Operator UI 全量交付 / Round-2 GO  
- ≠ Dashboard Phase% authorize（`apply_phase_pct=false`）  
- ≠ DarkOps / 暗部 core 改寫  
- ≠ live API / Grafana  
