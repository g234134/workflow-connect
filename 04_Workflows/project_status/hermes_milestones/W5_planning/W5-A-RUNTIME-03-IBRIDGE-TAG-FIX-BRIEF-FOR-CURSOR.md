# W5-A-RUNTIME-03-IBRIDGE-TAG-FIX — tags 傳遞驗證 BRIEF（更新版）

> **票號**：W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01
> **指派對象**：Cursor Agent（驗證確認）
> **先讀**：W5-A-RUNTIME-03-POLICY-MINING-03.md → **W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01.md（已更新）**

---

## 一句話任務

驗證 `observability/ibridge_exporter.py` 的 k2_summary → ibridge → dryrun → enf_preview tags 傳遞鏈已完整。**注意：程式碼已正確處理 tags，不需要任何修補。** 任務目標從「修補」調整為「驗證確認＋文件化」。

---

## 背景

W5-POLICY-MINING-03 的根因分析（「_k2_summary_to_ibridge() 沒有保留 tags」）在實際程式碼審查後發現**不成立**：

- `_k2_summary_to_ibridge()` L247: `tags = _coerce_tags(summary.get("tags") or [])` ✅
- `_k2_summary_to_ibridge()` L257: `"tags": tags` ✅
- `EXPORT_FIELD_NAMES` L50: `"tags",` ✅
- 對應 unittest: `test_k2_summary_tags_preserved_in_ibridge_record` (L140) ✅
- 下游 dryrun (L245): `tags = list(record.get("tags") or [])` ✅
- 下游 enf_preview (L86): `tags = list(row.get("tags") or [])` ✅

**所有節點均已正確處理 tags。**

### 那麼真正的根因在哪裡？

MINING-03 觀察到「2 條帶有 infra_risk 訊號的真實 shadow 記錄最終被分類為 allow/allow」。這可能另有原因：

1. **K-2 flow (`eval_gate.tags`) 未產出 `infra_risk`** — 問題在 LangGraph 流程而非 ibridge 管線
2. **tags 在 k2_summary 層面正確但 k2_merge.k2_eval_tags 未同步**
3. **MINING-03 分析時程式碼版本不同**

---

## 終止條件（本票完成時應達成的狀態）

本票不修改程式碼。終止條件為：

| 項目 | 狀態 |
|------|------|
| 完整 tags 流向圖已文件化（k2_ask_shadow → ibridge → dryrun → enf_preview） | ✅ 於設計檔 §2 |
| 各節點型別安全確認 | ✅ 於設計檔 §2.2 |
| 既有 unittest 驗證通過 | ✅ |
| 完整端到端 `export_ibridge_jsonl(source="shadow")` tags 測試 | ⏳ 可選補上 |
| 文件化 MINING-03 根因勘誤 | ✅ 於設計檔 §1.1 |
| 提出下一階段建議（檢查 K-2 eval_gate.tags 填充） | ✅ 於設計檔 §4.2 |

---

## 相關檔案（不需修改任何程式碼）

| 檔案 | 角色 |
|------|------|
| `observability/ibridge_exporter.py` | tags 傳遞核心模組。已確認正確。 |
| `core/k2_ask_shadow.py` | k2_summary tags 來源 (`summarize_k2_output` L224-265) |
| `core/k2_prod_shadow_worker.py` | spool line 建構 (`_build_spool_line` L36-75) |
| `tests/test_ibridge_exporter.py` | tags 相關測試 (L140-169) |
| `tools/dryrun/core.py` | tags 消費 (L245, L294) |
| `tools/enf_preview_wrapper.py` | tags 消費 (L86) |
| `tests/fixtures/eval/shadow_raw_records.jsonl` | tags fixture (line 3-4) |

## 禁止的變更

- ❌ 不修改 `ibridge_exporter.py`（已正確處理 tags）
- ❌ 不修改 `k2_ask_shadow.py`（summarize_k2_output 已正確產出 tags）
- ❌ 不修改 `k2_prod_shadow_worker.py`（spool 已正確保留 k2_summary）
- ❌ 不修改 `dryrun/core.py` 或 `enf_preview_wrapper.py`（已正確讀取 tags）
- ❌ 不新增治理規則、不調 ENF-RULE-1/2、不改 scoring/verdict

如要在本票範圍內補統一 `_k2_summary_to_ibridge(k2_summary, raw)` 的 type annotation 或空值防禦，屬於低風險可選項。

---

## 驗收條件

### AC-1：既有 unittest 全部 PASS

```bash
python -m pytest tests/test_ibridge_exporter.py -v --tb=short
```

### AC-2：端到端 tags 流向驗證（可選）

```bash
python -m tools.dryrun --input-dir artifacts/eval/ --output-dir observability/dryrun/ --verbose
python -c "
import json
from pathlib import Path
for f in sorted(Path('observability/dryrun').glob('*_per_record.jsonl')):
    with open(f) as fh:
        for line in fh:
            r = json.loads(line.strip())
            tags = r.get('tags', 'MISSING')
            if tags and tags != [] and tags != 'MISSING':
                print(f'{r[\"task_id\"]}: tags={tags}')
"
```

預期：所有 prod-shadow 記錄的 `tags` 如原始 `k2_summary.tags` 中有值，應正確顯示。

### AC-3：設計檔揭示的根因勘誤已被文件化

確認 `W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01.md` §1.1 包含前後對照與勘誤說明。

---

## 實作步驟（文檔化步驟，非程式修改）

1. 閱讀 `observability/ibridge_exporter.py` L232-264（_k2_summary_to_ibridge）和 L39-57（EXPORT_FIELD_NAMES）
2. 確認 tags 處理邏輯正確
3. 閱讀 `tests/test_ibridge_exporter.py` L140-169（tags 測試）
4. 確認 fixture `tests/fixtures/eval/shadow_raw_records.jsonl` 含 tags
5. 閱讀 `tools/dryrun/core.py` L245, L294（消費端）
6. 閱讀 `tools/enf_preview_wrapper.py` L86（消費端）
7. 確認所有消費端使用 `list(record.get("tags") or [])` 或等價處理
8. 執行 `python -m pytest tests/test_ibridge_exporter.py -v` 確認全部 PASS
9. 更新設計檔 §2 流向圖（若發現缺失）

---

## Before/After 對照

本票為驗證確認，無程式碼 before/after。

**文件 before/after**：

| 文件 | Before（v0.1） | After（v0.2） |
|------|---------------|--------------|
| `W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01.md` | 假設 tags 在 `_k2_summary_to_ibridge` 和 `EXPORT_FIELD_NAMES` 兩層遺失，需修補程式碼 | 基於實際審查，確認程式碼已正確，任務調整為驗證確認＋文件化 |
| `W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-BRIEF-FOR-CURSOR.md` | 含程式碼修改步驟和單位測試建議 | 不含程式碼修改，僅驗證確認與文件化步驟 |

---

## 引用

- W5-A-RUNTIME-03-POLICY-MINING-03.md（前提分析。**注意**：ibridge_exporter 根因結論需 revisiting。）
- W5-A-RUNTIME-03-IBRIDGE-TAG-FIX-01.md（完整設計 — v0.2 已更新）
- `observability/ibridge_exporter.py` L39-57, L223-229, L232-264
- `tests/test_ibridge_exporter.py` L140-169
- `tests/fixtures/eval/shadow_raw_records.jsonl`
