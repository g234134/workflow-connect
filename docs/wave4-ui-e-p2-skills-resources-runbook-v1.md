# Wave4-E · P2 Skills & Resources Runbook v1

> **Ticket**：`W4-UI-E-p2-skills-resources-v1`  
> **宿主**：戰車根獨立靜態殼 `ui/command_center/`（可後接 `app/local_ui`）  
> **視覺 SSOT**：`docs/ui-templates/unified_P2.png`  
> **上游**：`W4-UI-D`（accepted_with_gaps）· 共用 CSS／JS  
> **≠** Grafana · **≠** 暗部 `dashboard.html` 大翻修 · **≠** live API · **≠** DarkOps · **≠** 金鑰明文 · **≠** Dashboard Phase% authorize（`apply_phase_pct=false`）

---

## 開啟 P2 殼

於戰車根目錄：

```powershell
python -m http.server 8765
```

瀏覽器開啟：

- 權威：`http://127.0.0.1:8765/ui/command_center/p2.html`
- 導覽入口：`http://127.0.0.1:8765/ui/command_center/index.html`（P1／P2／P3／P4／P5／settings stub）
- P1：`…/p1.html` · P3：`…/p3.html` · P4：`…/p4.html` · P5：`…/p5.html`
- 設定 stub：`http://127.0.0.1:8765/ui/command_center/settings.html`

對照：`docs/ui-templates/unified_P2.png`（允許像素差；記於票 B_REPORT）。

---

## Mock

| 路徑 | 說明 |
|------|------|
| `ui/command_center/mock/p2_skills_resources_v1.json` | 六部技能卡／映射表／本機雲／API·Token／金鑰庫 + P8.9 subset |

頂層穩定鍵：`ok` · `schema_version=w4_ui_e_p2_skills_resources_v1` · `demo` · `read_only` · `skill_ministries` · `skill_module_map` · `resource_governance` · `operator_fields`。

金鑰：`secrets.api_key_display` 與 `key_vault.rows[].name_masked` 僅遮罩（`*********`／`••••••••`）；JS `maskSecrets`；禁止明文。

導覽：P1／P2／P3／P4／P5 **全部可互點**；settings 為極簡 stub。

---

## 驗證

```powershell
python -m unittest tests.test_w4_ui_e_p2_skills_resources_v1 -v
```

五頁合計：

```powershell
python -m unittest tests.test_w4_ui_a_static_shell_v1 tests.test_w4_ui_b_p5_swimlane_v1 tests.test_w4_ui_c_p4_command_desk_v1 tests.test_w4_ui_d_p3_dark_loop_v1 tests.test_w4_ui_e_p2_skills_resources_v1 -v
```

期望：**40/40 OK**（A8+B8+C8+D8+E8）。

---

## Non-claims

- ≠ Operator UI 全量交付 / Round-2 GO / Operator 全量 prod  
- ≠ Dashboard Phase% authorize（`apply_phase_pct=false`）  
- ≠ DarkOps / 暗部 core 改寫  
- ≠ live API / Grafana / PG soak  
- ≠ 金鑰原文  
- ≠ 像素完美重畫五頁  

下一階：真 API 掛載另票。

---

## 交叉

- A：`docs/wave4-ui-a-static-shell-runbook-v1.md`  
- B：`docs/wave4-ui-b-p5-swimlane-runbook-v1.md`  
- C：`docs/wave4-ui-c-p4-command-desk-runbook-v1.md`  
- D：`docs/wave4-ui-d-p3-dark-loop-runbook-v1.md`  
- Freeze：`docs/wave4-ui-visual-freeze-v1.md`（A–E 靜態殼完成）
