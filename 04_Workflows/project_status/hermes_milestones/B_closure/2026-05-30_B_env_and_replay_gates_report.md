# 2026-05-30 B Env and Replay Gates Report

> 建立：2026-05-30
> 類型：milestone B closure report（B-2/B-3 批次）
> 上層：`/mnt/d/hermes-workspace/milestones/B_closure/`

---

## 1. 本次新建/更新了哪些檔案

### 新建（3 份）

| # | 檔案 | 大小 | 用途 |
|---|------|:----:|------|
| 1 | `ENV_FREEZE_AND_REPLAY_GATES.md` | 11,287 B | 環境凍結條件（5 欄位）、CI/CD 識別 decision tree、重播記錄標準（run ID/config snapshot/依賴/outcome）、人工 vs 自動化分配表、7 個開線閘門 |
| 2 | `CROSS_FILE_DEBT_HANDLING_SOP.md` | 10,955 B | 跨檔案 debt 四步處理流程（識別→拆票→ lane 對齊→ 驗收合併）、freeze 條件（3 條強制）、DEBT_LOG 狀態機對接、D-005 完整演練、常見陷阱表 |
| 3 | `2026-05-30_B_env_and_replay_gates_report.md` | **本檔** | 摘要報告 |

### 更新（1 份）

| # | 檔案 | 變更 |
|---|------|------|
| 4 | `B_MINIMAL_GAP_LIST.md` | 新增 §2（環境凍結與重播 gate 缺口）、更新 §3（總缺口摘要，7 項） |

---

## 2. 「多線調度前的環境與重播 gate」最低標準（摘要）

**5 行總結**：

1. **開新線前**，該線的 PIPELINE.md 必須填入 venv 路徑、Python 版本、可執行的測試指令，且密鑰存在性已驗證（§1）。任一項 missing → 不得進入 scan 階段。
2. **CI/CD 不要求知道**，但必須分類（GitHub / GitLab / Jenkins / custom / unknown）。unknown 不是 blocker，但需標記對應的影響範圍（§2）。
3. **每條線的 run note** 必須包含 config snapshot（venv/python/pytest/version）、依賴清單、outcome block（PASS/FAIL/BLOCKED）。檔名按 `YYYY-MM-DD_<module>_<step>` 規則，同一步同一天不得重複（§3）。
4. **七個閘門**（G-ENV-1~4 + G-REPLAY-1~3）必須在 step 推進前逐項檢核。目前全為人工確認（§5）。
5. **跨檔案 debt** 需拆成 3+ 張小票（prep/apply/cleanup），每張票獨立走 runtime → review → doc-sync → gate 階梯，任一張票失敗不影響其他票。危險度 ★★★ 的債務必須先 freeze 再開分支處理。

**與 control plane 用語的對齊**：
- `lane` = runtime / review / doc-sync / gate（已被 SOP 採用）
- `Ticket Memory` 模板中的 location/severity/status 結構與 DEBT_LOG 的 8 種狀態一致
- gate lane 使用 G-ENV / G-REPLAY 編號，與 control plane 的 gate 概念一致

---

## 3. 人工確認 vs 未來自動化檢查點

### 可預期未來實作成自動化檢查工具的項目

| 檢查點 | 自動化方法 | 優先級 |
|--------|-----------|:------:|
| G-ENV-1：venv 路徑存在檢查 | `ls $(venv_path)/bin/python` | P1 |
| G-ENV-2：測試指令 --dry-run | `python -m pytest --collect-only` | P1 |
| CI/CD decision tree 識別 | Python 腳本檢查 `.github/`、`.gitlab-ci.yml`、`Jenkinsfile` 是否存在 | P2 |
| Run ID 唯一性 | `find 90_runs/ -name "*<module>*" \| sort \| uniq -d` | P2 |
| Config snapshot 自動生成 | `python --version && pip list --json && git rev-parse HEAD` 包成 helper script | P2 |
| Import 依賴樹生成 | `pipdeptree --json` 或 `modulefinder` script | P3 |
| Outcome block 完整性 | 檢查每份 run note 末端是否包含 `## Outcome` 及 5 個欄位 | P3 |
| G-REPLAY 閘門 batch 檢核 | shell script 遍歷 90_runs/ 並對照 ENV_FREEZE 閘門表 | P3 |

### 永遠需要人工確認的項目

| 檢查點 | 原因 |
|--------|------|
| Python 版本與 venv 路徑在跨 session 的有效性 | WSL 路徑可能因 mount/restart 變化；agent 無法保證路徑仍有效 |
| CI 平台為 unknown 的後續處理 | 需要人類知悉團隊使用的 CI 工具（或決定不使用 CI）|
| PASS/FAIL/BLOCKED 的 outcome 判斷 | agent 可能工具執行成功但邏輯錯誤，「通過測試」也需要人類看結果是否合理 |
| 密鑰存在性驗證 | 基於安全紅線，agent 不得直接讀取/列印 .env 或金鑰內容 |
| freeze 決策 | 人類需要判斷該 debt 是否值得用 freeze/branch 成本來處理 |
| 跨線 DEBT_LOG 同步（更新兩份 DEBT_LOG）| agent 可能只更新了自己所在線的 DEBT_LOG，漏了另一條線 |

---

## 4. 對里程碑 B 的評估

### 已完成的部分（B 判定更接近 DONE）

| 面向 | 狀態 | 備註 |
|------|:----:|------|
| 第二模組（eval_exporter）bootstrap 完成 | ✅ | 16 份檔案就緒（B-1 報告）|
| 環境 freeze gate 定義完成 | ✅ | ENV_FREEZE_AND_REPLAY_GATES.md 全 5 節 + 7 閘門 |
| 跨檔案 debt SOP 定義完成 | ✅ | CROSS_FILE_DEBT_HANDLING_SOP.md 全 7 節 + D-005 完整演練 |
| 缺口清單更新 | ✅ | B_MINIMAL_GAP_LIST.md 新增 §2 + §3 摘要 |

### 仍為缺口的部分（❌ 尚未閉環）

| 缺口 | 類型 | 阻擋 B 判定？ |
|------|:----:|:--------------:|
| eval_exporter discovery 未真實執行 | execution | **YES** — 無 discovery 則無法填入 PIPELINE.md，無法驗證 G-ENV 閘門 |
| D-005 三張 ticket 未真實執行 | execution | **YES** — SOP 雖完成定義，但未跑一次完整回路 |
| DEBT_LOG 跨線同步（D-005 關聯欄位）| documentation | NO — 但 P1 |
| CI/CD 平台仍 unknown | discovery | NO — unknown 是合法狀態，不阻擋 |
| G-ENV 閘門自動化 | automation | NO — 屬於 milestone C/D scope |
| B-TKT 票據系統整合 | integration | NO — 屬於 control plane 整合範圍 |

### 總結

里程碑 B 在**定義層面**已大幅推進（環境凍結 gate + 跨檔案 debt SOP 已定義，缺口清單已完成）。但**執行層面**的兩個缺口（eval_exporter discovery 未執行、D-005 ticket 未真實跑）使得 B 尚不能判定 DONE。下一步應優先執行 eval_exporter discovery，然後依 SOP 跑三張 D-005 ticket。

**這不是提前宣判 YES。** 缺口清單中有 2 項 P0（缺 execution），需在下一次對話中補上，B 才有可能達到 DONE 的 threshold。
