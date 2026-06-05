# 导入案卷标准模板（`_TEMPLATE_case`）

> **用途**：Wave 2+ 每条新导入 case 复制本目录为 `20_pilot/<CASE>_case/`，再按票面填写。  
> **字段权威**：`../W2-2_imp_state_schema.md`（v0.1）；IMP-* 状态名与迁移语义 → `../../10_governance/G7_state_machine/`（G7-1／G7-3）。  
> **试点参考**：`../W2-1_case/W2-1_case.md`（已对齐本模板）。

---

## 1. 如何开新案

1. 复制 `_TEMPLATE_case/` → `20_pilot/<CASE>_case/`（例如 `W2-4_case/`）。
2. 将 `_TEMPLATE_case.md` 重命名为 `<CASE>_case.md`。
3. 填写 front matter 与 §1 任务描述；建案时 **§2** 设为 `IMP-SCOPE-DRAFT`（或接战已明确的更高态须注明依据）。
4. 在 `90_run_queue.md` 登记施工票；**禁止**在 queue `Status` 栏写入 `imp_state` 取值。

---

## 2. 必填 IMP 区块（每个案卷 **必须** 有）

| 案卷节 | 逻辑名 | 内容 |
|--------|--------|------|
| **§2** | `imp_state_current` | 当前 `imp_state` 单值 + `entry_owner_role` + `entry_evidence_refs` + 更新时间／票号 |
| **§3** | `imp_state_transitions`（迁移日志） | 每次合法 **IMP-*** 前进或进入 `IMP-REWORK` **追加一行**；不删历史行 |

案卷骨架见 [`_TEMPLATE_case.md`](_TEMPLATE_case.md)。

### §2 表头（`imp_state_current`）

| 字段 | 说明 |
|------|------|
| **`imp_state`** | 当前 G7-1 正式 **IMP-*** 名（**禁止** queue 四态别名） |
| **entry_owner_role** | 本态 entry owner：`pm` / `engineering` / `qa` / `release` / … |
| **entry_evidence_refs** | 本态 ART 路径或案卷内文件名 |
| **rework_target** | 仅 `IMP-REWORK` 时必填 |
| **imp_state_updated_at** | ISO 日期（`YYYY-MM-DD`） |
| **imp_state_updated_by_ticket** | 最近一次更新对应的 queue 票号 |

### §3 表头（`imp_state_transitions`）

| 列 | 说明 |
|----|------|
| **at** | 迁移日期 |
| **from** | 上一态；建案首行可用 `—` |
| **to** | 新态（单步前进；REWORK 时 `to`=`IMP-REWORK`） |
| **by** | 票号 + 角色（如 `W2-x-ENG` / `engineering`） |
| **reason / artifact_refs** | 事件摘要；指向 ART／EVD 路径 |

---

## 3. 谁负责更新、何时更新

| 动作 | 负责角色 | 何时 | 写入 |
|------|----------|------|------|
| 建案 | PM / orchestrator | 案卷目录创建当日 | §2 → `IMP-SCOPE-DRAFT`；§3 首行 |
| 关口 exit 后前进 | 该态 **entry owner**（G7-2／G7-3）或指派 worker（artifact owner 监督） | 本态 **ART-***／EVD 落盘后 **同日** | 更新 §2；§3 **追加**一行 |
| 进入 REWORK | 失败关口 owner | 判定返工当日 | §2 + §3；填 `rework_target` |
| 施工票 DONE | worker | 票收口时 | **仅** `90_run_queue.md` Notes 写「IMP exit → …」；**须同步** §2／§3，不得以 queue `DONE` 代替 |
| guard `stop_work` | — | — | **不** 写 `imp_state`；记 guard JSON／Progress 阻塞 |

---

## 4. 可选载体（不替代 §2／§3）

| 优先级 | 载体 | 说明 |
|:------:|------|------|
| P2 | `*_art_qa_rev.json` 等 | 可选键 `imp_state_at_review`（快照） |
| P3 | `90_run_queue.md` Notes | 索引 only |
| P4 | `99_latest_status.md` | 波次摘要；非单案 lifecycle 源 |

---

## 5. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | W2-2-IMP-FIELD：标准案卷模板初版 |
