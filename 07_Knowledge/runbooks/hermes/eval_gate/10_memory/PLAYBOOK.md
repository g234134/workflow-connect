# PLAYBOOK.md — eval_gate 常見問題處理步驟

> 狀態：bootstrap | 2026-05-30
> 本 playbook 記錄 Infra Hygiene Owner 可能遇到的常見情境與處理步驟。
> ⚠ 大部分條目目前為占位內容，待實際運作後補充。

---

## P-001: 發現測試 flaky

**症狀**：同一測試在不同執行中時而通過時而失敗。

**步驟**：
1. 確定 flaky 測試的檔案與測試名稱。
2. 在 DEBT_LOG.md 建立條目，類型 `FLAKY`。
3. 檢查是否依賴外部資源（網路、檔案、時間、亂數）而未 mock。
4. 檢查是否有競賽條件（race condition）或共享可變狀態。
5. 如果無法立即修復，建議 `pytest.mark.flaky` 或 retry。
6. 設定追踪到期日。

---

## P-002: 發現裸 except

**症狀**：程式碼中有 `except:` 或 `except Exception` 未指定具體例外。

**步驟**：
1. 確認該 except 是否真的有捕捉一切例外的理由。
2. 若是上層錯誤處理邊界（如 main entry point），補上 logging。
3. 若在中間層，改為具體例外類型。
4. 記錄至 DEBT_LOG.md，類型 `FIXME`。

---

## P-003: docstring 缺失

**症狀**：公開函數或類別缺少 docstring。

**步驟**：
1. 確認函數是否真的是公開介面（public API）。
2. 根據 STYLE.md 規定格式補上 docstring。
3. 包含 Args、Returns、Raises 三段。
4. 若屬 serialization / private helper 等內部函數，可簡化但不可省略。

**實例參考**：`20_runtime/eval_gate.suggested.v1.py` 中的規則函數 docstring（觸發條件 + 依賴欄位 + 意圖三段模板）是建議的規則級 docstring 格式。而 `_int_field` 等工具函數則檢討為過長（見 2026-05-30_review_v1 §1.3），建議未來比照精简：3–5 行即可（功能描述 + 1 個 Args + 1 個 Returns）。

---

## P-004: 型別不一致

**症狀**：type hint 與實際回傳值不一致，或使用 `Any` 但可更具體。

**步驟**：
1. 確認函數的實際回傳值型別。
2. 更新 type hint 以符合實際行為。
3. 如果無法確定確切型別，使用 `Union` 或 `Optional` 而非 `Any`。
4. 若涉及 Protocol / ABC，檢查實作是否符合介面契約。

---

## P-005: 第三方套件版本鎖定過鬆

**症狀**：`requirements.txt` 或 `pyproject.toml` 中版本範圍過寬（如 `>=1.0`）。

**步驟**：
1. 確認專案是否使用 lock file（`poetry.lock`、`Pipfile.lock`、`requirements.txt` with pins）。
2. 如果沒有 lock file，建議建立。
3. 將主要依賴鎖定至 minor version（如 `pydantic>=2.5,<3`）。
4. 記錄變更至 DEBT_LOG.md（若涉及 breaking change 風險）。

---

## P-006: 日誌欄位不一致

**症狀**：不同模組或函數紀錄的結構化日誌欄位命名不同。

**步驟**：
1. 確認專案有無統一的 logging schema。
2. 若無，建議建立 minimal logging convention（例如 `event`、`module`、`duration_ms` 等）。
3. 統一欄位命名為 snake_case。
4. 在 STYLE.md 中記錄 logging convention。

**完成信標（2026-05-30）**：STYLE.md §9 已定義 eval_gate 模組的 logging convention（等级分配、訊息格式、不打 log 情境）。此條目視為已完成 eval_gate 範圍的 logging 慣例基礎。若有新模組加入，比照 §9 實作。

---

## P-007: 規則引擎欄位耦合 — 規則直接存取上游嵌套欄位

**症狀**：規則函數內出現 `record["nested"]["field"]` 或 `record.get("deep", {}).get("path")` 等深層路徑存取，且無任何 schema contract 文件或警告。

**步驟**：
1. 在規則函數的 docstring 中記錄預期的 record schema（欄位路徑、型別、是否可選）。
2. 若上游 schema 不穩定（例如來自第三方 adapter），考慮加入輕量 schema layer：
   - 定義 `_extract_*` helper 並在其中檢查型別 + 記錄 warning。
   - 或使用 `TypedDict` / `dataclass` 做一次解析後傳給規則。
3. 避免靜默 fallback 到 default 值而無任何 signal — 至少記錄 `logging.debug`。
4. 將 schema contract 記錄至 ARCH.md 的公開介面章節。
5. 若欄位路徑在多處重複（例如 eval_gate + eval_exporter 都讀 `context_token_usage`），抽取共用存取函數。

**輕量方案（經 v1 review 確認，2026-05-30）**：若因 scope 或風險考量無法加入 runtime warning，至少：
  - 在規則函數 docstring 中記錄預期的 record schema（欄位路徑、型別、是否可選）。
  - 在 docstring 中標記「若結構不符預期則靜默 fallback 至 default 值」的語意。
  - 參見 `eval_gate.suggested.v1.py` 中 `_rule_context_heavy` 與 `_rule_observability_gap` 的 docstring 實作。此為「docstring 優先」的第一線防禦。

---

## P-008: 規則門檻調整 — 確保比較運算子一致性

**症狀**：同一規則引擎中，不同規則使用不一致的比較運算子（`>` vs `>=`），雖不一定是 bug，但降低可讀性與 predictability。

**步驟**：
1. 審查所有規則的比較運算子 — 列出每個規則的 `>` / `>=` / `<` / `<=`。
2. 選定專案慣例（建議：numeric threshold 一律用 `>=` / `<=`，讓 boundary value 觸發規則；或一律 `>` / `<`，讓 boundary 不觸發）。
3. 若切換運算子會改變 boundary behavior，確認 boundary value 在實務中的語意（例如：80% of budget 是否該在剛好等於時觸發）。
4. 統一全部規則的運算子。
5. 更新對應的 unit test assertion（測試中的 boundary fixture 可能需要調整一行）。
6. 在常數定義旁加一行註解解釋為什麼選這個門檻值（例如 `# 80% of MAX_TOTAL_TOKEN_BUDGET`）。

---

## P-009: 規則引擎新增規則 — SOP

**症狀**：需要在現有規則引擎（如 eval_gate）中新增一條規則。

**步驟**：
1. **命名**：選定 snake_case tag 名稱（函數用 `_rule_<name>`，tag 字串用 `<name>`）。確認不與現有 tag 衝突。
2. **門檻**：把門檻值定義為模組層級常數（`UPPER_SNAKE_CASE`），附一行註解說明選擇依據。
3. **實作**：寫 `_rule_<name>(record) -> tuple[str, str] | None`，保持與其他規則相同的簽章與回傳格式。
4. **docstring**：記錄觸發條件、預期的 record 欄位、回傳格式。
5. **註冊**：在 `_RULES` tuple 中加入新規則函數（注意順序是否有語意 — 若無則按字母或優先級排列）。
6. **同步**：檢查並更新所有硬編碼的 tag 集合：
   - `eval_stats.py` 的 `KNOWN_GATE_TAGS`
   - 任何 hardcoded `fail_on_tags` 範例或文件
   - DEBT_LOG 中任何引用「5 條規則」的描述
7. **測試**：至少新增一條 unit test，覆蓋：
   - 規則觸發的 boundary case
   - 規則不觸發的 normal case
   - 上游欄位缺失時的 fallback 行為

---

## P-010: 低風險純加法 patch 完成後標記 fixed_in_repo

**症狀**：一個僅含 docstring + logging + 區塊註解（無語意變更）的 patch 已通過整個流程。

**標記條件**：當以下四關全部通過時，可將相關 debt 的狀態從 `fixed_suggested` 或 `planned` 標記為 `fixed_in_repo`：

1. **技術審查（fix_round）**
   - [ ] 建議版已產出（`suggested.v<N>.py`）
   - [ ] 靜態比對通過（簽名 / keys / 常數 / if 條件 / _RULES 順序一致）

2. **人工審查（review_vN）**
   - [ ] 審查結論為 `approved`（記錄在 `90_runs/YYYY-MM-DD_review_vN.md`）

3. **實際套用（apply）**
   - [ ] 已依 apply_plan 套入 repo 對應檔案
   - [ ] 靜態驗證 5 項全部 PASS（importable / 簽名 / keys / logging / 依賴）
   - [ ] 套用方式記錄在 `90_runs/YYYY-MM-DD_apply_result_vN.md`

4. **測試驗證**
   - [ ] 對應 unittest 全部 PASS（或明確標記 N/A 且有理由）

**範例**：`eval_gate.suggested.v1.py` 的 docstring + logging + 註解 patch 已完整走完以上四關，D-001 / D-003 / D-010 已標為 `fixed_in_repo`。

**注意**：此準則僅適用於「零風險 / 低風險」patch（APPLY_PLAYBOOK.md §2 定義的適用範圍）。若 patch 含有語意變更、跨檔案重構或新增測試，仍需走完整 PR review 流程。