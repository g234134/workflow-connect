# Milestone A Closure Pack

> 建立日期：2026-05-30
> 用途：確保里程碑 A 的「stable single-line operation closure」可被正式判定為 DONE，且可被下一個模組復用。

## 這是什麼

本目錄收納里程碑 A 的判定標準、封存證據、可復用 SOP，以及下一個模組的 bootstrap 模板。

## 目錄

| # | 檔案 | 用途 |
|---|------|------|
| 1 | `MILESTONE_A_DONE_CRITERIA.md` | 里程碑 A 的定義、已滿足項、未完全滿足但不阻擋的項 |
| 2 | `SINGLE_LINE_OWNER_SOP.md` | 從 zero 到 applied fix 的完整 7 步 SOP（可復用至下一模組） |
| 3 | `SINGLE_LINE_REPLAY_CHECKLIST.md` | 可回放、可複製的關閉前自檢清單（含檢查點） |
| 4 | `NEXT_MODULE_BOOTSTRAP_TEMPLATE.md` | 複製到第二模組時最小需要準備的文件/目錄/記錄 |
| 5 | `2026-05-30_A_closure_report.md` | 封存報告：證據鏈、結論、下一步 |

## 引用起點

單線樣板的實際檔案位於：

```
/mnt/d/hermes-workspace/infra_owner/eval_gate/
├── 00_skill/
├── 10_memory/
├── 20_runtime/
└── 90_runs/
```

本 closure pack 不建立新的 skill / memory / runtime，只做封裝與標準化。
所有「需人工確認」的建議會明確標註，不直接寫入下游客戶 config 或 SKILL.md。
