# DEBT_LOG.md — eval_gate 技術債追蹤

> 狀態：active | 首次掃描：2026-05-30
> 追蹤所有 TODO / FIXME / HACK / deprecated 程式碼條目。

---

## 格式說明

```
| ID | 位置 | 類型 | 摘要 | 發現日期 | 預計修復 | 狀態 |
|----|------|------|------|----------|----------|------|
| D-001 | path/to/file.py:42 | FIXME | 摘要說明 | 2026-05-30 | 2026-Q3 | open |
```

類型：`TODO`、`FIXME`、`HACK`、`DEPRECATED`、`FLAKY`、`WORKAROUND`、`DESIGN`
狀態：`open`、`in_progress`、`resolved`、`wontfix`、`superseded`

---

## 現有條目

| ID | 位置 | 類型 | 嚴重度 | 摘要 | 發現日期 | 預計修復 | 狀態 |
|----|------|------|:--:|------|----------|----------|:--:|
| D-001 | `observability/eval_gate.py:1–199` | DESIGN | **P1** | **零日誌**：eval_gate 為 Observability 模組，但 `evaluate_task_record` 及 5 條規則函數完全無 logging。規則觸發、schema 失敗（invalid/malformed_record）皆無可觀測紀錄。建議加入 `logging.getLogger(__name__)` 並在關鍵路徑記錄 info/warning。 | 2026-05-30 | 2026-Q2 | **fixed_in_repo**（已依 apply_plan_v1 套用至 observability/eval_gate.py，24 項 unittest 全數通過） |
| D-002 | `observability/eval_gate.py:142–199` | DESIGN | P2 | **回傳型別過寬**：`evaluate_task_record` 回傳 `dict[str, Any]`，但回傳結構（`pass`/`tags`/`reasons`/`eval_gate_version`）已知且穩定。可用 `typing.TypedDict` 定義 `GateVerdict` 型別，提升下游消費者的型別安全。 | 2026-05-30 | 2026-Q3 | open |
| D-003 | `observability/eval_gate.py:83–139` | TODO | P2 | **規則與 helper 函數無 docstring**：5 條 `_rule_*` 函數及 `_int_field`、`_float_field`、`_total_context_tokens`、`_error_type`、`_collect_schema_issues` 全部缺少 docstring。建議每條規則至少記錄觸發條件與回傳格式。 | 2026-05-30 | 2026-Q2 | **fixed_in_repo**（已依 apply_plan_v1 套用至 observability/eval_gate.py，24 項 unittest 全數通過） |
| D-004 | `observability/eval_gate.py:93–103` | FIXME | P2 | **比較運算子不一致**：`_rule_context_heavy` 使用 `>`（strict），而 `_rule_high_retry` 和 `_rule_many_handoffs` 使用 `>=`（non-strict）。對 boundary value（102,400 剛好等於 80% of 128K）的行為差異雖小，但違反 uniformity 原則。 | 2026-05-30 | 2026-Q2 | open |
| D-005 | `observability/eval_gate.py:62–70`、`observability/eval_exporter.py:35–43` | WORKAROUND | P2 | **`_total_context_tokens` 重複實作**：`eval_gate.py` 的 `_total_context_tokens` 與 `eval_exporter.py` 的 `_context_tokens_total` 邏輯幾乎相同。應抽取共用版本或由 exporter import eval_gate 版本。 | 2026-05-30 | 2026-Q2 | open |
| D-006 | `observability/eval_gate.py:93–130` | DESIGN | **P1** | **嵌套欄位路徑隱性耦合**：`_rule_context_heavy` 直接存取 `record["context_token_usage"]["total_tokens"]`，`_rule_observability_gap` 直接存取 `record["trace_completeness"]["score"]`。若上游 ibridge record 格式變更（重新命名或扁平化），規則會靜默回退至 default 值而不報錯。建議補 schema contract 文件，或加入 `logging.warning` 在結構不符預期時通報。 | 2026-05-30 | 2026-Q2 | open |
| D-007 | `observability/eval_gate.py:183–192` | FIXME | P2 | **規則迴圈無例外邊界**：`for rule in _RULES` 迴圈內若任一規則函數拋出非預期例外（例如因上游 record 結構破壞導致 `TypeError`），例外會穿透 `evaluate_task_record` 向上傳播，而非回傳結構化錯誤。建議在迴圈外包一層 try/except 並回傳 `malformed_record` tag。 | 2026-05-30 | 2026-Q3 | open |
| D-008 | `observability/eval_stats.py:24–32` | WORKAROUND | P2 | **`KNOWN_GATE_TAGS` 硬編碼**：`eval_stats.py` 中 `KNOWN_GATE_TAGS` 手動列出 5 個已知 tag（`high_retry`、`context_heavy`、`many_handoffs`、`infra_risk`、`observability_gap`）。若 eval_gate 新增規則，需手動同步此集合。建議改為從 `eval_gate._RULES` 動態提取。 | 2026-05-30 | 2026-Q3 | open |
| D-009 | `observability/eval_gate.py:142–199` | TODO | P2 | **`disabled_tags` 參數無測試覆蓋**：公開 API 提供 `disabled_tags` 參數（可選擇性跳過特定規則），但無任何測試驗證其行為。所有已知的呼叫點（k2_langgraph_flow、eval_exporter、eval_ci_check）均未傳入此參數。需至少一個單元測試確認 tag 跳過邏輯。 | 2026-05-30 | 2026-Q3 | open |
| D-010 | `observability/eval_gate.py:133–139` | TODO | P3 | **`_RULES` 註冊表無 docstring**：`_RULES` tuple 是規則引擎的註冊點（新增規則需加至此處），但無任何註解說明註冊慣例、執行順序是否有語意、或 tag 去重邏輯。 | 2026-05-30 | — | **fixed_in_repo**（已依 apply_plan_v1 套用至 observability/eval_gate.py，24 項 unittest 全數通過） |

---

## 統計摘要（2026-05-30 apply_result_v1 後 — 3 條已進 repo）

- 總技術債：10
- P1（高優先）：2
- P2（中優先）：7
- P3（低優先）：1
- 已解決（fixed_in_repo）：**3**（D-001、D-003、D-010）
- 已產出建議修正（fixed_suggested）：**0**
- 開放中：**7**（D-002、D-004、D-005、D-006、D-007、D-008、D-009）
- 逾期未修：0

> 歷程：10 open（掃描）→ 3 fixed_suggested + 7 open（fix_round1）→ 3 fixed_in_repo + 7 open（apply_result_v1）

---

## 注意事項

- 每次掃描後更新本表
- 超過預計修復日期 30 天未處理的條目應標記為 `overdue`（在備註欄標註）
- `wontfix` 需說明理由
- `superseded` 需引用取代的條目 ID
- P1 條目建議在下個 sprint 處理；P2 條目建議在兩 sprint 內處理

---

## 狀態流轉規則（2026-05-30 建立）

### 定義

| 狀態 | 說明 | 誰可設定至此 |
|------|------|-------------|
| `open` | 首次發現，尚未處理 | Hermes（掃描時） |
| `planned` | 有計畫但尚未產出程式碼 | Hermes / Human |
| `fixed_suggested` | 已產出建議修正版（suggested.vN.py），等待人工審核與 repo 套用 | Hermes（fix_round 後） |
| `fixed_in_repo` | 已成功套入 repo，測試通過 | Human（套用後）→ Hermes（更新狀態） |
| `rejected` | 人工審查或套用後否決，確定不採納 | Human（review 或 apply 時） |
| `deferred` | 目前不處理，但保留追蹤 | Human（社群決策或排程調整） |
| `superseded` | 被另一條 debt 取代 | Hermes / Human（需引用取代 ID） |
| `wontfix` | 確認不修，有充分理由 | Human（architect 決定） |

### 流轉圖

```
                    ┌─────────────────┐
                    │      open       │
                    └───────┬─────────┘
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ planned  │  │ fixed_   │  │ deferred │
        └─────┬────┘  │suggested │  └──────────┘
              │       └─────┬────┘
              │             │
              └──────┬──────┘
                     ▼
              ┌───────────┐         ┌──────────┐
              │ fixed_in_ │ ◄────── │ rejected │
              │   repo    │         └──────────┘
              └───────────┘
```

### 關鍵轉換閘門

#### `open` → `fixed_suggested`

- 觸發：Hermes 完成 fix_round，產出 `<module>.suggested.v<N>.py`
- 閘門：
  - [ ] suggested 檔已通過靜態比對（簽名 / keys / if 條件 / 常數一致）
  - [ ] patch 類型在 APPLY_PLAYBOOK 適用範圍內
  - [ ] 風險評估為零或低

#### `fixed_suggested` → `fixed_in_repo`

- 觸發：收到人類或 Cursor 回報（使用 APPLY_CONFIRM_TEMPLATE.md）
- 閘門：
  - [ ] 人工審查結論為 `approved`
  - [ ] 已套入 repo 對應檔案
  - [ ] 靜態驗證全部 PASS
  - [ ] 測試驗證 PASS（或明確標記 N/A 但有理由）

#### `fixed_suggested` → `rejected`

- 觸發：人工審查結論為 `rejected`，或建議版內容因上遊變更而不再適用
- 閘門：
  - [ ] 有明確 rejection 理由記錄在 `apply_plan` 或 `review` 文件
  - [ ] 理由可能是：風格不一致、行為變更風險、上遊 schema 已改

#### `fixed_suggested` → `deferred`

- 觸發：暫不套用，但建議版保留
- 閘門：有排程或環境限制（例如等待上游 PR 合併、等待春季大翻新）

#### `fixed_suggested` → `open`（回退）

- 觸發：Hermes 判斷建議版有誤，或上遊變更使建議版過期
- 閘門：須在 DEBT_LOG 備註欄寫明回退原因

### 狀態轉換記錄慣例

每次狀態變更時，在 DEBT_LOG 的備註欄（或獨立紀錄）留下：

```
狀態變更: open → fixed_suggested
日期: 2026-05-30
原因: 完成 fix_round1，產出 suggested.v1.py
參考: 90_runs/2026-05-30_fix_round1.md
```

狀態變更欄位格式：`<舊狀態> → <新狀態>（日期：YYYY-MM-DD，原因：簡述，參考：文件路徑）`
