# G7-3 — IMP-* Exit 条件与合法迁移

> **票号**：G7-3  
> **范围**：每个 **IMP-*** 状态的 **exit 条件**、**合法下一状态**、**禁止跳转**、**IMP-REWORK** 触发与回退、**角色门槛**（checker / owner / release owner）。  
> **不含**：entry 条件（→ G7-2）；代码实现；完整 release gate（→ G8-5）；queue `TODO`/`DOING` 等施工票态。  
> **上游**：`10_workflow_states.md`（G7-1，状态名冻结）  
> **下游引用**：G10 rulebook、G4 管线、G8 artifact contract（ART-* 名对齐）

---

## 1. 文档约定

### 1.1 迁移记法

| 符号 | 含义 |
|------|------|
| `A → B` | **合法**正向迁移；须满足 A 的 exit 条件 |
| `A ⇢ B` | **须审批**迁移（见 §3 角色门槛）；缺审批视为非法 |
| `A ↛ B` | **禁止**迁移（含跳关） |
| `A → IMP-REWORK → B` | 关口失败后进入返工，再**回退**至 B（非跳关前进） |

**禁止**用 queue `Status`、battle_report `status`、route `assignable` 的值**代替** IMP 迁移依据（命名空间见 G7-1 §1）。

### 1.2 角色简称

| 角色 | 说明 |
|------|------|
| **artifact owner** | 对该 AI 导入 artifact 负责的范围／交付 owner（PM 轨 **ART-PM-***，见 G8-1 `10_pm.md` §4） |
| **engineering owner** | 施工产出 owner；通常即 worker 或 Eng 轨责任人 |
| **checker** | `checker-reviewer` 或等价 QA 角色；产出 `ART-QA-REV` |
| **release owner** | 发布裁决责任人（Release 轨 **ART-REL-***，见 G8-5 `50_release_owner.md` §4） |
| **guard** | `governance-guard` 或 G10 等价裁決；**不**写入 `imp_state`，但可 **block 迁移** |

### 1.3 与 G8 占位 IMP 的对账（v0.1）

G8 Eng/QA 轨（`30_engineering.md` §2、`40_qa.md` §2）仍使用 **施工票级占位别名**。本档 **G7-1 正式名** 为 artifact 主线唯一机读态；占位仅作 **并行维度** 索引，**不得**覆盖 `imp_state`。

| G8 占位 | G7 正式态（建议映射） | 说明 |
|---------|----------------------|------|
| `IMP-OPEN` | （非 G7 态）→ 触发进入 `IMP-SCOPE-DRAFT` | 接战／票受理；G8-1 PM 轨 v0.1 已交付（见 `10_pm.md`） |
| `IMP-ACTIVE` | 并行：`IMP-AI-READY` … `IMP-REVIEW-READY` 施工窗口 | 单票 Context→Incremental；≠ 主线单态 |
| `IMP-VERIFY` | `IMP-QA-READY` | Eng 证据齐、**待 checker**；≠ `IMP-REVIEW-READY` |
| `IMP-ARCHIVE-PENDING` | 并行：`IMP-RELEASE-DECISION` 前后 | QA verdict 已 accepted；封存 append **不**等于 `IMP-RELEASED` |
| `IMP-ARCHIVED` | 并行：ops `cycle_states.archived` | battle report 已 append；**不**映射 `IMP-OBSERVING` |

> **CHK-W1 风险 R1**：exit 引用的 ART-* 以 G8 已交付轨为准；**ART-GOV-RISK** 仍 defer（W2-3）；G8-RECON-IMP（W2-1）已更新 PM/Design/Release 交叉引用。

---

## 2. 全局规则

### 2.1 不可跳过的主线关口

下列状态 **不得** 从更早态直接跳入更晚态（须逐关 exit）：

```text
IMP-SCOPE-DRAFT → IMP-SPEC-CLARIFY → IMP-AI-READY → IMP-REVIEW-READY
    → IMP-RISK-VALIDATION → IMP-QA-READY → IMP-RELEASE-DECISION
    → IMP-RELEASED → IMP-OBSERVING
```

**硬性禁止跳关示例**（完整表见 §4）：

- `IMP-SCOPE-DRAFT` ↛ `IMP-AI-READY` 及之后任一态  
- `IMP-AI-READY` ↛ `IMP-RISK-VALIDATION` / `IMP-QA-READY` / `IMP-RELEASE-*`  
- `IMP-REVIEW-READY` ↛ `IMP-QA-READY` / `IMP-RELEASE-*`（须经 `IMP-RISK-VALIDATION`）  
- `IMP-RISK-VALIDATION` ↛ `IMP-RELEASE-DECISION` / `IMP-RELEASED`  
- `IMP-QA-READY` ↛ `IMP-RELEASED`（须经 `IMP-RELEASE-DECISION`）  
- `IMP-RELEASED` ↛ 终局冻结（须经 `IMP-OBSERVING` 或 `IMP-REWORK`）

### 2.2 全局禁止迁移

| 禁止 | 原因 |
|------|------|
| 任意态 → 写入 queue `DOING`/`DONE` 到 `imp_state` | 命名空间混用（G7-1 §1.2） |
| 任意态 → 仅因 battle_report `done` 前进 | 战报封口 ≠ artifact 关口通过 |
| 任意态 → 仅因 route `assignable:true` 前进 | 路由可派工 ≠ artifact 阶段完成 |
| `IMP-OBSERVING` → 任意「前进」态（除 `IMP-REWORK`） | 观测期不承载新 scope 前进施工 |
| `IMP-REWORK` → `IMP-RELEASED` / `IMP-OBSERVING` | 返工须先回到修复目标态再重走关口 |
| 无 `rework_target` 记录离开 `IMP-REWORK` | 返工无回退锚点 |

### 2.3 角色门槛总表

| 迁移 | 必须角色 | 说明 |
|------|----------|------|
| `IMP-SCOPE-DRAFT` → `IMP-SPEC-CLARIFY` | artifact owner | 范围意图已识别 |
| `IMP-SPEC-CLARIFY` → `IMP-AI-READY` | artifact owner | 澄清闭环 |
| `IMP-AI-READY` → `IMP-REVIEW-READY` | engineering owner | AI/混合产出齐套 |
| `IMP-REVIEW-READY` → `IMP-RISK-VALIDATION` | peer reviewer 或 design owner（见 G8-2 `20_design.md` §4.2–§4.3 **ART-DES-REV**） | 人审结论非 reject |
| `IMP-RISK-VALIDATION` → `IMP-QA-READY` | guard **allow** 或等效风险 sign-off | 触 `stop_work` 则不得 exit |
| `IMP-QA-READY` → `IMP-RELEASE-DECISION` | **checker**（`ART-QA-REV`） | `accepted` / `accepted_with_gaps` |
| `IMP-RELEASE-DECISION` → `IMP-RELEASED` | **release owner** | 发布裁决 affirmative |
| `IMP-RELEASED` → `IMP-OBSERVING` | **release owner** | 发布执行确认 |
| `IMP-OBSERVING` → 终局／冻结 | **release owner** | 观测窗口结束（载体 **ART-REL-OBS**，见 G8-5 `50_release_owner.md` §4.3） |
| 任意 → `IMP-REWORK` | 失败关口 owner + 记录 | 见 §5 |
| `IMP-REWORK` → 回退目标态 | 失败关口 owner；自 QA 失败须 **checker** 确认 rework plan | 见 §5 |

---

## 3. 分状态 Exit 与迁移

### IMP-SCOPE-DRAFT

| 项 | 内容 |
|----|------|
| **Exit 条件** | ① 导入目标 artifact 类型可识别；② 粗粒度 in/out scope 已写；③ 关联票号或 intake 引用已登记；④ `primary_change_class`（CHG-*）草案或 TBD 已显式标注 |
| **合法下一状态** | `IMP-SPEC-CLARIFY` |
| **禁止** | ↛ `IMP-AI-READY` 及之后（缺澄清闭环） |
| **→ IMP-REWORK** | 一般不触发；若 intake 后 scope 被 governance 判定无效 → `IMP-REWORK` → 废弃或重开 artifact（**非** queue `BLOCKED`） |
| **角色** | exit：`artifact owner` |

---

### IMP-SPEC-CLARIFY

| 项 | 内容 |
|----|------|
| **Exit 条件** | ① open questions **已关闭**或转入显式 `defer` 清单（带 owner）；② G8 五轨必填字段缺口已列清单（PM/Design 项见 G8-1 `10_pm.md` §4.3 **ART-PM-GAPS**、G8-2 `20_design.md` §4.1）；③ 验收口径／acceptance 引用已对齐（可指向 runbook 或票内 runner）；④ 依赖票状态已检查（阻塞则不得 exit，写 artifact 阻塞而非 queue 混写） |
| **合法下一状态** | `IMP-AI-READY` |
| **禁止** | ↛ `IMP-REVIEW-READY` 及之后；↛ 在 open questions 未关闭时标 AI-ready |
| **→ IMP-REWORK** | 澄清评审 reject；scope 重大变更需重起草案 → `IMP-REWORK` → `IMP-SCOPE-DRAFT` 或 `IMP-SPEC-CLARIFY`（rework 级 **minor** / **major** 见 §5.2） |
| **角色** | exit：`artifact owner`；major rework 建议 guard 抽检 |

---

### IMP-AI-READY

| 项 | 内容 |
|----|------|
| **Exit 条件** | ① `ART-ENG-CTX` 就绪（G8-3 §4.1）；② G6 `allowed_actions` 对当前 CHG-* 可满足（G6-2）；③ AI/混合施工产出已齐套，可进入人审队列；④ 若票触 guard 门槛：`verdict=allow`（G6-2 §7） |
| **合法下一状态** | `IMP-REVIEW-READY` |
| **禁止** | ↛ `IMP-RISK-VALIDATION` / `IMP-QA-READY` / `IMP-RELEASE-*`（缺 review 与 risk 关口） |
| **→ IMP-REWORK** | guard `stop_work`；施工 scope 越界；产出不可审 → `IMP-REWORK` → `IMP-SPEC-CLARIFY`（scope）或 `IMP-AI-READY`（仅重施工） |
| **角色** | exit：`engineering owner`；guard 为 **条件必须** |

**G8 对账**：施工窗口并行对应占位 `IMP-ACTIVE`；exit 至 `IMP-REVIEW-READY` **不**等同 `IMP-VERIFY`。

---

### IMP-REVIEW-READY

| 项 | 内容 |
|----|------|
| **Exit 条件** | ① 产出物齐套（Eng：`ART-ENG-WR` 草案；Design：**ART-DES-SPEC**／**ART-DES-REV**，见 G8-2 `20_design.md` §4.1–§4.3）；② peer / design review 结论为 **通过** 或 **通过带 gaps**（gaps 已写入 WR §3）；③ 无未关闭 P0 review blocker |
| **合法下一状态** | `IMP-RISK-VALIDATION` |
| **禁止** | ↛ `IMP-QA-READY` / `IMP-RELEASE-*`（缺风险校验）；↛ 仅因 checker `accepted` 跳 risk（checker 属 QA 子域，G7-1 §3） |
| **→ IMP-REWORK** | review **reject** → `IMP-REWORK` → `IMP-SPEC-CLARIFY`（设计/范围问题）或 `IMP-AI-READY`（实现问题） |
| **角色** | exit：peer reviewer 或 design owner |

---

### IMP-RISK-VALIDATION

| 项 | 内容 |
|----|------|
| **Exit 条件** | ① G6 change class 边界未越界或 override 已留痕（WR §7）；② G10 禁止盲信情境已对照（见 G10-2 `20_no_blind_trust.md` §5.3 **IMP-RISK-VALIDATION** 对照）；③ 憲法 §7 禁区类型无未授权触达；④ 风险清单 **closed** 或 **accepted** 并带 owner |
| **合法下一状态** | `IMP-QA-READY` |
| **禁止** | ↛ `IMP-RELEASE-DECISION` / `IMP-RELEASED`；↛ 在 guard `stop_work` 等价结论下 exit |
| **→ IMP-REWORK** | 风险/治理未通过 → `IMP-REWORK` → 通常 `IMP-SPEC-CLARIFY`（scope/制度）；纯实现风险可 → `IMP-AI-READY` |
| **角色** | exit：**guard allow** 或 artifact owner + guard 记录；**禁止** worker 单方 exit |

---

### IMP-QA-READY

| 项 | 内容 |
|----|------|
| **Exit 条件** | ① `ART-ENG-WR` + `ART-ENG-EVD` 定稿（G8-3）；② `ART-ENG-DOD` 自检为是；③ **`ART-QA-REV.verdict`** ∈ {`accepted`, `accepted_with_gaps`}；④ gaps 已诚实写入 WR §3，**不得**隐瞒 skeleton/placeholder |
| **合法下一状态** | `IMP-RELEASE-DECISION` |
| **禁止** | ↛ `IMP-RELEASED` / `IMP-OBSERVING`；↛ worker 无 checker 单方标 QA 通过 |
| **→ IMP-REWORK** | `ART-QA-REV.verdict` ∈ {`rejected`, `blocked`} → `IMP-REWORK` → 见 §5.3 |
| **角色** | exit：**checker** 必须；`blocked` 时 **不得** exit 至 release，仅可 rework 或保持 |

**G8 对账**：入口对齐占位 `IMP-VERIFY`；exit **不**等同 `IMP-ARCHIVE-PENDING`（后者含 QA verdict 后封存并行维）。

---

### IMP-RELEASE-DECISION

| 项 | 内容 |
|----|------|
| **Exit 条件（批准发布）** | ① **`ART-REL-DEC`** 或等价发布裁决 artifact 已记录（见 G8-5 `50_release_owner.md` §4.1）；② 发布范围、受众、回退策略已写；③ 无未解决 P0 blocker |
| **Exit 条件（拒绝发布）** | 裁决 **deny** → **不得** exit 至 `IMP-RELEASED`；须 `IMP-REWORK` |
| **合法下一状态** | 批准 → `IMP-RELEASED`；拒绝 → `IMP-REWORK` |
| **禁止** | ↛ `IMP-OBSERVING`；↛ 无 release owner 标 released |
| **→ IMP-REWORK** | 发布 deny；范围/环境未就绪 → `IMP-REWORK` → `IMP-QA-READY` 或 `IMP-RISK-VALIDATION`（按根因） |
| **角色** | exit：**release owner** 必须 |

> 本档 **不写** 完整 release gate 细则；字段与闸机见 G8-5。

---

### IMP-RELEASED

| 项 | 内容 |
|----|------|
| **Exit 条件** | ① 发布执行已完成（目标受众／环境切换有证据，载体 **ART-REL-EXEC**，见 G8-5 `50_release_owner.md` §4.2）；② 与裁决记录一致；③ 回退路径仍有效 |
| **合法下一状态** | `IMP-OBSERVING` |
| **禁止** | ↛ 直接终局冻结；↛ 在观测期外宣称「完成导入」 |
| **→ IMP-REWORK** | 发布后发现 P0 缺陷需撤回 → `IMP-REWORK` → `IMP-RELEASE-DECISION` 或 `IMP-QA-READY`（按严重度） |
| **角色** | exit：**release owner** |

---

### IMP-OBSERVING

| 项 | 内容 |
|----|------|
| **Exit 条件（正常）** | ① 观测窗口结束（时长/指标见 G8-5 `50_release_owner.md` §4.3 **ART-REL-OBS** 与 G8-1 §4.4 **ART-PM-OBS-PLAN**）；② 无未关闭 P0 incident；③ 反馈已归档或转入 follow-up 票 |
| **Exit 条件（异常）** | SLO  breach / P0 incident → `IMP-REWORK`（非「前进」） |
| **合法下一状态** | 终局／冻结（见 G8-5 §4.3 **ART-REL-OBS**；废弃策略见 G10 rulebook）；异常 → `IMP-REWORK` |
| **禁止** | ↛ `IMP-AI-READY` 等「新 scope 前进」（应 **新开 artifact** 或经 rework）；↛ 新 scope 施工在本态进行 |
| **→ IMP-REWORK** | 见 §5.4 |
| **角色** | 正常 exit：**release owner**；incident rework：**release owner** + ops 记录 |

---

### IMP-REWORK

| 项 | 内容 |
|----|------|
| **Exit 条件** | ① **`rework_record`** 已写：失败关口、根因、`rework_target`（合法回退态）、owner；② 针对根因的修复计划或 scope 修正已就绪；③ 若自 `IMP-QA-READY` 进入：checker 已确认 rework plan 或新 acceptance 引用 |
| **合法下一状态** | 仅 **回退** 至 §5.2 表中的 `rework_target`（重走该态之后关口） |
| **禁止** | ↛ 任意「向前跳关」；↛ 无 record 离开本态 |
| **角色** | exit：失败关口 owner；QA 来源须 **checker** |

---

## 4. 禁止迁移矩阵（摘要）

行 = 当前态，列 = 目标态。`✓` = 合法（满足 exit）；`R` = 经 `IMP-REWORK` 回退后再到达；`—` = 禁止。

| 从 \ 到 | SPEC | AI | REV | RISK | QA | REL-D | REL | OBS | REWORK |
|---------|:----:|:--:|:---:|:----:|:--:|:-----:|:---:|:---:|:------:|
| **SCOPE-DRAFT** | ✓ | — | — | — | — | — | — | — | R |
| **SPEC-CLARIFY** | — | ✓ | — | — | — | — | — | — | ✓ |
| **AI-READY** | R | — | ✓ | — | — | — | — | — | ✓ |
| **REVIEW-READY** | R | R | — | ✓ | — | — | — | — | ✓ |
| **RISK-VALIDATION** | R | R | — | — | ✓ | — | — | — | ✓ |
| **QA-READY** | R | R | R | R | — | ✓ | — | — | ✓ |
| **RELEASE-DECISION** | — | — | — | — | R | — | ✓ | — | ✓ |
| **RELEASED** | — | — | — | — | — | — | — | ✓ | ✓ |
| **OBSERVING** | — | — | — | — | — | — | — | — | ✓ |
| **REWORK** | R | R | R | R | R | R | — | — | — |

表内缩写：`SCOPE`= `IMP-SCOPE-DRAFT`，`SPEC`= `IMP-SPEC-CLARIFY`，`AI`= `IMP-AI-READY`，`REV`= `IMP-REVIEW-READY`，`RISK`= `IMP-RISK-VALIDATION`，`QA`= `IMP-QA-READY`，`REL-D`= `IMP-RELEASE-DECISION`，`REL`= `IMP-RELEASED`，`OBS`= `IMP-OBSERVING`。

---

## 5. IMP-REWORK 规则

### 5.1 触发（必须进入 `IMP-REWORK`）

| 来源态 | 触发条件 | 典型 `rework_target` |
|--------|----------|----------------------|
| `IMP-SPEC-CLARIFY` | 澄清 reject；scope 无效 | `IMP-SCOPE-DRAFT` / `IMP-SPEC-CLARIFY` |
| `IMP-AI-READY` | guard `stop_work`；越界施工 | `IMP-SPEC-CLARIFY` / `IMP-AI-READY` |
| `IMP-REVIEW-READY` | review **reject** | `IMP-SPEC-CLARIFY` / `IMP-AI-READY` |
| `IMP-RISK-VALIDATION` | 风险/治理未通过 | `IMP-SPEC-CLARIFY` / `IMP-AI-READY` |
| `IMP-QA-READY` | `ART-QA-REV`: `rejected` / `blocked` | `IMP-AI-READY` / `IMP-SPEC-CLARIFY` / `IMP-RISK-VALIDATION` |
| `IMP-RELEASE-DECISION` | 发布 **deny** | `IMP-QA-READY` / `IMP-RISK-VALIDATION` |
| `IMP-RELEASED` | 发布后 P0 撤回 | `IMP-RELEASE-DECISION` / `IMP-QA-READY` |
| `IMP-OBSERVING` | P0 incident / SLO breach | `IMP-QA-READY` / `IMP-RELEASE-DECISION` |

**不触发 REWORK 的情况**（并行维度，改 queue/战报，**不改** `imp_state` 或仅保持当前 IMP 态）：

- 施工票 queue `BLOCKED`（依赖未满足）  
- battle_report `blocked`（验证不可跑）  
- route `assignable:false`（Phase 门闸）  
- intake `reject`（入站拒绝；artifact 可能永不进入主线）

### 5.2 回退级别

| 级别 | 条件 | 允许 `rework_target` |
|------|------|----------------------|
| **L1 · 重施工** | 仅实现/证据问题；scope 不变 | `IMP-AI-READY` |
| **L2 · 重澄清** | 验收口径/依赖/设计 gaps | `IMP-SPEC-CLARIFY` |
| **L3 · 重范围** | scope 或 CHG-* 变更 | `IMP-SCOPE-DRAFT` |
| **L4 · 重风险/QA** | 治理或 QA 程序性失败 | `IMP-RISK-VALIDATION` / `IMP-QA-READY` |

自 `IMP-REWORK` exit 后，须 **重走** `rework_target` 之后的每一关（不可跳关）。

### 5.3 QA 失败回退（与 G8-4 对齐）

| `ART-QA-REV.verdict` | 进入 REWORK | 默认 `rework_target` |
|----------------------|-------------|------------------------|
| `rejected` | ✓ | `IMP-AI-READY`（实现）；scope 越界 → `IMP-SPEC-CLARIFY` |
| `blocked` | ✓（保持 QA 或 REWORK） | 保持 `IMP-QA-READY` 直至阻塞解除，或 REWORK → `IMP-AI-READY` |
| `accepted_with_gaps` | ✗（合法 exit QA） | — |
| `accepted` | ✗ | — |

G8 占位「`rejected` → `IMP-ACTIVE`」**映射**为：`IMP-REWORK` → `IMP-AI-READY`（L1），**非**写入占位名。

### 5.4 观测期回退

| 事件 | 动作 |
|------|------|
| 非 P0 反馈 | 保持 `IMP-OBSERVING`；开 follow-up 票，**不**强制 REWORK |
| P0 / 安全 / 数据损坏 | `IMP-REWORK` → `IMP-RELEASE-DECISION`（撤回）或 `IMP-QA-READY`（热修） |
| 新 scope 需求 | **新开 artifact** @ `IMP-SCOPE-DRAFT`；**禁止**从 `IMP-OBSERVING` 直接 → `IMP-AI-READY` |

---

## 6. Exit 与 ART-* 索引（G8 五轨 v0.1）

| IMP 态 | Exit 引用的主要 ART-* | 待补（未交付／defer） |
|--------|-------------------------|----------------------|
| `IMP-SCOPE-DRAFT` | **ART-PM-SCOPE**（G8-1 `10_pm.md` §4.1） | — |
| `IMP-SPEC-CLARIFY` | **ART-PM-CLARIFY**、**ART-DES-SPEC**（G8-1 §4.2、G8-2 §4.1） | — |
| `IMP-AI-READY` | **ART-ENG-CTX**（G8-3 §4.1） | — |
| `IMP-REVIEW-READY` | **ART-ENG-WR**（草案）；**ART-DES-REV**（G8-2 §4.3，条件触发） | — |
| `IMP-RISK-VALIDATION` | **ART-ENG-WR** §7；G10-2 §5.3 对照 | **ART-GOV-RISK**（W2-3 defer） |
| `IMP-QA-READY` | **ART-ENG-WR**, **ART-ENG-EVD**, **ART-ENG-DOD**, **ART-QA-REV**, **ART-QA-EVD** | — |
| `IMP-RELEASE-DECISION` | **ART-QA-REV**；**ART-REL-DEC**（G8-5 §4.1） | — |
| `IMP-RELEASED` | **ART-REL-EXEC**（G8-5 §4.2） | — |
| `IMP-OBSERVING` | **ART-REL-OBS**（G8-5 §4.3）；**ART-PM-OBS-PLAN**（G8-1 §4.4） | — |

---

## 7. 文档边界与 TODO

| 本档（G7-3） | 其他票 |
|--------------|--------|
| exit + 合法/禁止迁移 + REWORK | G7-2：entry 条件 |
| 角色门槛（checker / owner / release owner） | G8-1/2/5：ART-* 字段 |
| G8 占位 ↔ 正式态映射表 | G8-5：release gate 与终局冻结 |
| — | G10：盲信情境清单正文 |
| — | Wave 2+：`imp_state` 机读 enforcement |

**待对账 TODO**

1. G7-2 entry 与本文 exit 成对合并时，checker 跑 CHK-W1（R1）。  
2. ~~G8-5 定稿后补全 `ART-REL-*` 与 `IMP-RELEASE-*` / 终局冻结 exit~~ → **已解**（G8-5 v0.1 + W2-1-ENG 交叉引用）。  
3. ~~G8-1/2 定稿后补 PM/Design review exit 字段~~ → **已解**（G8-1/2 v0.1 + W2-1-ENG）。  
4. ~~G10-2 NBT 占位句~~ → **已解**（W2-1-ENG → G10-2 §5.3）；**ART-GOV-RISK** 仍 defer W2-3。

---

## 8. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-05-27 | G7-3 初版：10 态 exit、迁移矩阵、REWORK 规则、G8 占位对账、角色门槛 |
| 2026-05-27 | G8-RECON-IMP（W2-1-ENG）：G8-1/2/5、G10-2 §5.3 交叉引用；§6 ART 索引更新 |
