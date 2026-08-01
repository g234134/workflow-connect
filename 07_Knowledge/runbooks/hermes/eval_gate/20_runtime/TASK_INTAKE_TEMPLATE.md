# TASK_INTAKE_TEMPLATE.md — Infra Hygiene 任務 intake 模板

> 每個 hygiene 任務都應使用此模板紀錄。

---

```yaml
task_id: H-<YYYYMMDD>-<NNN>
created_at: <ISO 8601>
trigger: <routine | pr_scan | incident | debt_tracking | scheduled_audit>
module: eval_gate
reporter: <name / agent>
```

## 任務描述

<!-- 簡述此次 hygiene 任務的目的。 -->

## 範圍

- [ ] 合約檢查（Contract）
- [ ] 錯誤處理（Error Handling）
- [ ] 型別與介面（Type & Interface）
- [ ] 日誌與可觀測性（Logging & Observability）
- [ ] 測試穩定性（Test Hygiene）
- [ ] 技術債（Debt Tracking）

## 發現摘要

| # | 檔案 | 類型 | 嚴重度 | 說明 |
|---|------|------|--------|------|
| 1 | — | — | — | — |

## 行動項目

| # | 動作 | 責任人 | 預計完成 | 狀態 |
|---|------|--------|----------|------|
| 1 | — | — | — | open |

## 阻斷項

<!-- 如果有無法進行的項目，列出原因。 -->

## 參考

- ARCH.md（架構）
- STYLE.md（風格）
- DEBT_LOG.md（技術債）
- PLAYBOOK.md（常見問題）
- SKILL_INFRA_HYGIENE_OWNER.md（角色 skill）

## 結束檢查

- [ ] 所有發現已記錄至 DEBT_LOG.md
- [ ] 嚴重度 Low / Medium 項目已排程
- [ ] 嚴重度 High / Critical 項目已通知對應 owner
- [ ] Playbook 是否需要更新？
- [ ] ARCH / STYLE 是否需要更新？
- [ ] run note 已寫入 `90_runs/`
