# Wave4-UI-G · P2–P4 live 換源薄補 runbook v1

> **票**：`W4-UI-G-p2-p4-live-source-v1`  
> **上游**：`W4-UI-F-command-center-live-api-mount-v1`（共用 `loadPageData`／`?source=`）  
> **宿主**：`ui/command_center/`  
> **性質**：P2／P3／P4 mock → 本地只讀 live 投影 · **≠** Operator prod · **≠** Grafana · **≠** PG soak  
> **apply_phase_pct**：`false`（票面亦寫 `apply_phase_pct=false`）

---

## 1. 範圍

| 頁 | mock | live |
|----|-------|------|
| P2 技能與資源 | `mock/p2_skills_resources_v1.json` | `live/p2_skills_resources_v1.json` |
| P3 暗部閉環 | `mock/p3_dark_loop_v1.json` | `live/p3_dark_loop_v1.json` |
| P4 三省指揮台 | `mock/p4_command_desk_v1.json` | `live/p4_command_desk_v1.json` |

開關與 fallback 與 F 票相同：預設 mock；`?source=live` 讀 live，失敗 → `mock_fallback`。

---

## 2. 開啟方式

```powershell
python scripts/project_command_center_live_v1.py --write
python -m http.server 8765
# http://127.0.0.1:8765/ui/command_center/p2.html?source=live
# http://127.0.0.1:8765/ui/command_center/p3.html?source=live
# http://127.0.0.1:8765/ui/command_center/p4.html?source=live
```

---

## 3. 驗證

```powershell
python -m unittest tests.test_w4_ui_g_p2_p4_live_source_v1 -v
python -m unittest tests.test_w4_ui_a_static_shell_v1 tests.test_w4_ui_b_p5_swimlane_v1 tests.test_w4_ui_c_p4_command_desk_v1 tests.test_w4_ui_d_p3_dark_loop_v1 tests.test_w4_ui_e_p2_skills_resources_v1 tests.test_w4_ui_f_live_api_mount_v1 tests.test_w4_ui_g_p2_p4_live_source_v1 -v
```

期望：G 契約測 PASS；A–G 合計綠（既有 A–F + G）。

---

## 4. non_claims

- ≠ Grafana · ≠ PG soak · ≠ DarkOps · ≠ 金鑰明文
- ≠ Operator prod · ≠ Phase% authorize · ≠ Round-2 GO
- ≠ 代替 H1–H5 Human 閘門

---

## 5. 回退

去掉 `?source=live`（或改 `?source=mock`）即回靜態殼行為；刪／忽略 `live/p2|p3|p4_*.json` 不影響預設 mock。
