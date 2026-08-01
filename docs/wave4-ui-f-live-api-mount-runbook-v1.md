# Wave4-UI-F · command_center live API／CLI 只讀掛載 runbook v1

> **票**：`W4-UI-F-command-center-live-api-mount-v1`  
> **宿主**：`ui/command_center/`  
> **性質**：mock → 本地只讀 live 投影 · **≠** Operator prod · **≠** Grafana · **≠** PG soak  
> **apply_phase_pct**：`false`（票面亦寫 `apply_phase_pct=false`）

---

## 1. 開關

| 模式 | 觸發 | 行為 |
|------|------|------|
| **mock（預設）** | 無 query，或 `?source=mock` | 載入 `mock/*.json`（A–E 回歸不變） |
| **live** | `?source=live` 或 `?data=live` | 載入 `live/*.json`；失敗 → **fallback mock**（banner 標 `mock_fallback`） |

共用 API：`CommandCenterShell.resolveDataSource()` · `CommandCenterShell.loadPageData({mockUrl, liveUrl})`（`ui/command_center/js/shell.js`）。

**本輪掛載頁**：P1／P5（F 票）+ P2／P3／P4（**G 票** `W4-UI-G-p2-p4-live-source-v1`）。五頁均可 `?source=live`。

---

## 2. 開啟方式

```powershell
# 於戰車根
python scripts/project_command_center_live_v1.py --write
python -m http.server 8765
# 瀏覽器：
#   http://127.0.0.1:8765/ui/command_center/p1.html
#   http://127.0.0.1:8765/ui/command_center/p1.html?source=live
#   http://127.0.0.1:8765/ui/command_center/p5.html?source=live
```

CLI 投影（不寫檔）：

```powershell
python scripts/project_command_center_live_v1.py --page p1 --format json
python scripts/inspect_p89_operator_fields_v1.py --case-ref demo_phase --format json
```

---

## 3. 契約對齊

| 域 | 來源 | 掛載位置 |
|----|------|----------|
| P8.9 五鍵 | `delivery.p89_operator_fields_v1`／`scripts/inspect_p89_operator_fields_v1.py` | `operator_fields`（P1 live；P5 live_overlays） |
| P7.5 gate／alerts／sink | 計劃 §2.1 敘事 | `live_overlays.gate_note`（≠ prod alert） |
| P5 metrics | toolchain／`/metrics` stub 語意 | `live_overlays.metrics_note`（≠ Grafana／PG soak） |
| P4 佇列 | `command_queue/QUEUE.yaml` 只讀計數 | KPI 輕量 overlay + `live_overlays.command_queue` |

---

## 4. 驗證

```powershell
python -m unittest tests.test_w4_ui_f_live_api_mount_v1 -v
python -m unittest tests.test_w4_ui_a_static_shell_v1 tests.test_w4_ui_b_p5_swimlane_v1 tests.test_w4_ui_c_p4_command_desk_v1 tests.test_w4_ui_d_p3_dark_loop_v1 tests.test_w4_ui_e_p2_skills_resources_v1 tests.test_w4_ui_f_live_api_mount_v1 -v
```

期望：F 票契約測 PASS；A–E 仍 **40/40**；合計 **48/48**。

---

## 5. non_claims

- ≠ Grafana
- ≠ PG soak
- ≠ DarkOps 解禁／改暗部根
- ≠ 金鑰明文（僅遮罩；驗收語意 `_smoke_test_keys.py`）
- ≠ Operator prod 全量
- ≠ Phase% authorize／Dashboard 數字格
- ≠ Round-2 GO／execute-v2
- ≠ war_status 升檔（須尚書省）

---

## 6. 回退

- 預設即 mock；關閉 live 只需去掉 `?source=live`。
- 刪除或忽略 `ui/command_center/live/*.json` 時，live 模式會 fallback mock（若 mock 仍在）。
- `GOV_*`／`.env`：**本票不改**。
