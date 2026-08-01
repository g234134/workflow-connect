# Wave4-A · Static Shell Runbook v1

> **Ticket**：`W4-UI-A-static-shell-align-p1-v1`  
> **宿主**：戰車根獨立靜態殼 `ui/command_center/`（可後接 `app/local_ui`）  
> **視覺 SSOT**：`docs/ui-templates/unified_P1.png`  
> **≠** Grafana · **≠** 暗部 `dashboard.html` 大翻修 · **≠** live API · **≠** 金鑰明文

---

## 開啟 P1 殼

於戰車根目錄：

```powershell
python -m http.server 8765
```

瀏覽器開啟：

- 權威：`http://127.0.0.1:8765/ui/command_center/p1.html`
- 別名：`http://127.0.0.1:8765/docs/ui-templates/page01.html`（共用同一 mock／CSS／JS）
- 導覽：`http://127.0.0.1:8765/ui/command_center/index.html` · P2–P5 見 Wave4-B／C／D／E runbook（五頁靜態殼已閉環）

對照：`docs/ui-templates/unified_P1.png`（允許像素差；記於票 B_REPORT）。

---

## Mock

| 路徑 | 說明 |
|------|------|
| `ui/command_center/mock/p1_overview_v1.json` | P1 KPI／流程／狀態／活動 + `operator_fields` |

頂層穩定鍵：`ok` · `schema_version=w4_ui_a_p1_overview_v1` · `demo` · `read_only` · `operator_fields`。

`operator_fields` 對齊 P8.9 五鍵：`event_id` · `ack_status` · `handler_id` · `dispatch_registry_hit` · `dlq_flag`（mock subset · ≠ live projection 宣稱）。

金鑰：`secrets.api_key_display` 僅 `••••••••`；JS `maskSecrets` 額外過濾常見明文樣式。

---

## 驗證

```powershell
python -m unittest tests.test_w4_ui_a_static_shell_v1 -v
```

可選鍵名對照（live）：

```powershell
python scripts/inspect_p89_operator_fields_v1.py --case-ref demo_phase --format json
```

---

## Non-claims

- ≠ Operator UI 全量交付 / Round-2 GO  
- ≠ Dashboard Phase% authorize（`apply_phase_pct=false`）  
- ≠ DarkOps / 暗部 core 改寫  
- 交叉：Wave4-E P2 → `docs/wave4-ui-e-p2-skills-resources-runbook-v1.md` 
