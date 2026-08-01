# TICKET STATE · W-MVP-W5-LOCAL-UI · Wave 5 · 最小本机 Web UI（CLI 包装层）

> handoff 摘要档；跨 chat 交棒以本档为准，不是完整工作日志。  
> **定位句**：本 UI 票是把**已验收的 CLI 主链**包装成一个**本机浏览器工作台**，**不是**新建第二套业务逻辑。

---

## FRAME

### Goal（一句话）

在 repo 根新增**本机单用户 Web UI**，通过浏览器触发既有 MVP 主链 CLI（lookup / 建案+gate / E2E），展示结构化 JSON 与产物路径；**不改** core pipeline、**不上云**、**不重做**产品架构。

### 票定位（冻结）

| 声明 | 说明 |
|------|------|
| **包装层** | UI = CLI wrapper / process runner；业务规则、gate、清洗、bundle、E2E **全部**留在现有 `scripts/` 与 `notebooks/csv_cleaning/`。 |
| **NOT 第二套逻辑** | 禁止在 UI 后端或前端复刻 eligibility、schema 探针、output_guard 判定；只透传 CLI `--json` 输出。 |
| **local MVP / not prod** | 页面与启动日志须明示 **INTERNAL · LOCAL MVP · NOT PROD**（无 SLA、无多用户）。 |
| **演示锚点** | 验收以 `cases/demo_phase` 与 `cases/sampleco/2026-0001` 为主；操作顺序对齐 `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`。 |

---

### Step 1 — In Scope（UI 第一版只做）

#### 1. Intake / New Run

| 能力 | 字段 / 行为 |
|------|-------------|
| 选择或填写 source CSV 路径 | `--source-file`（repo 相对或绝对路径；Implementer 可附「浏览」为文本框，**不必**文件 picker 组件库） |
| `client_ref` | 必填；传给 `new_cleaning_case.py` |
| `product_sku` | 必填；默认建议 `CLEAN-BASIC` |
| 可选解析参数 | `encoding`（默认 `utf-8`）· `delimiter`（默认 `,`）· `file_format`（可选覆盖） |
| 建案后 gate | 勾选或默认开启 `--run-gate` |

#### 2. Lookup

| 能力 | 说明 |
|------|------|
| 建案前可执行 lookup | 调用 `lookup_case_history.py`（至少支持 `--client-ref`；可选 `--product-sku` · `--schema-headers` · `--list-all`） |
| 展示 `matches[]` | 每条至少：`case_dir` · `client_ref` · `case_id` · `product_sku` · `gate_status` |
| 展示 `known_limits` | 索引层限制列表（如 demo_phase 的 `legacy_demo_path` · `rows<100`） |
| 索引刷新（可选加分） | 按钮触发 `build_cases_index.py`（非 AC 硬要求，但 demo 走查 Step 0 有此项） |

#### 3. Run Actions

| 动作 | 底层命令 | UI 须展示的关键信号 |
|------|----------|---------------------|
| 建案 + gate | `new_cleaning_case.py ... --run-gate` | `case_dir` / `case_dir_rel` · `gate_status`（= eligibility）· `dimensions.schema.notes` · `dimensions.schema.warnings` |
| 已有 case E2E | `run_case_e2e_validation.py --case-dir <path> --json` | `ok` · `eligibility` · `steps.gate` / `steps.cleaning` / `steps.bundle` · `output_guard.status` · `output_guard.ratio` · `artifacts` |
| 单步 gate（可选加分） | `check_case_eligibility.py --case-dir ... --json` | 供已有案复查；非 AC 硬要求 |

**Wave 4 护栏展示字段（冻结）**

| 来源 | 字段 | demo_phase 预期 | sampleco 预期 |
|------|------|-----------------|---------------|
| gate JSON | `eligibility` / `gate_status` | `review_needed` | `accepted` |
| `dimensions.schema` | `notes[]` | `phase_like` · `phase_demo` | `phase_like` · `multi_row_export` · `schema_ambiguous` |
| `dimensions.schema` | `warnings[]` | `[]` 或空 | 可有 warning token |
| bundle / E2E / report | `output_guard.status` | `ok` | `warning` |
| bundle / E2E / report | `output_guard.ratio` | ≈ 0.71（5/7） | ≈ 0.07（8/115） |
| bundle / E2E / report | `output_guard.notes[]` | 空或信息性 | 含 below-threshold 说明 |

#### 4. Results

| 能力 | 说明 |
|------|------|
| 结构化 JSON 摘要 | 最近一次动作的完整 `--json` 或解析后的 dict；可折叠 raw JSON |
| 产物路径 | 至少列出（若存在）：`reports/report.json` · `reports/report.md` · `reports/eligibility_result.json` · `delivery_signoff.md` · `cleaned/*.csv` |
| 运行日志 | subprocess stdout/stderr 摘要（C 区块）；错误时显示 `message` |

---

### Step 2 — Out of Scope（第一版明确不做）

- 不做云端部署 / 远程服务 / 多用户 / 反向代理生产配置
- 不做登录 / 权限 / RBAC / 数据库存储 / 会话持久化（除浏览器内存态）
- 不重写 gate / cleaning / bundle / E2E 逻辑；**不修改**既有 `scripts/*.py` 与 `notebooks/csv_cleaning/*.py` 业务实现（仅 subprocess 调用）
- 不做拖拽式复杂前端、组件库大工程、WebSocket 实时流（轮询或单次响应即可）
- 不做自然语言 agent / RAG / 推荐最优 cleaner / SKU 路由
- 不保证生产级容错 / SLA / 并发隔离 / 请求队列
- 不在本票写 runbook / README 大段用户文档（留给 Scribe 后续票）
- 不接入 `core/*`、暗部 `app_api`、Telegram、dispatch executor

---

### Step 3 — 技术形态（冻结建议）

| 项 | 决策 |
|----|------|
| 部署形态 | **本机单用户**；`127.0.0.1` 绑定；手动启动，无守护进程 |
| 后端 | Python（repo 根 venv / 系统 Python 3.10+）；**仅** CLI wrapper / `subprocess.run` |
| 前端 | **单页** HTML + 少量原生 JS + CSS；无 React/Vue 脚手架 |
| 业务规则位置 | **零**前端业务规则；后端不 import `case_eligibility` 做裁决，只调 CLI |
| HTTP 库 | 优先 **stdlib**（`http.server` 或等效轻量路由）；若用 FastAPI 须注明仅 dev 本机且不加新 CI 重依赖 |
| 启动方式 | 单一入口，例如：`python app/local_ui.py`（可选 `--port 8765`） |

**建议目录结构（草案）**

```
app/
  __init__.py              # 空或包标记
  local_ui.py              # HTTP 服务 + subprocess 调度 + JSON API
  templates/
    local-ui.html          # 单页四区块
  static/
    local-ui.css           # 最小样式
tests/
  test_local_ui.py         # 可选：smoke（启动/路由/ mock subprocess）
```

**建议 API 面（Implementer 可微调路径，语义须保留）**

| Method | Path | 行为 |
|--------|------|------|
| GET | `/` | 返回 `local-ui.html` |
| GET | `/static/*` | 静态资源 |
| POST | `/api/lookup` | body: `{client_ref?, product_sku?, schema_headers?, list_all?}` → 调 `lookup_case_history.py` |
| POST | `/api/new-case` | body: intake 字段 + `run_gate: true` → 调 `new_cleaning_case.py` |
| POST | `/api/e2e` | body: `{case_dir}` → 调 `run_case_e2e_validation.py --json` |
| POST | `/api/reindex` | （可选）调 `build_cases_index.py` |

所有 API 响应建议统一：`{ok, action, data, stderr?, message?}`，其中 `data` 为 CLI 解析后的 JSON。

---

### Step 4 — 最小页面结构（单页四区块）

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: "Local MVP Workbench" + NOT PROD 警示条              │
├─────────────────────────────────────────────────────────────┤
│  A. New case form                                           │
│  B. Lookup results                                          │
│  C. Run results / logs                                      │
│  D. Artifact links / paths                                  │
└─────────────────────────────────────────────────────────────┘
```

#### A. New case form — 最少字段

| UI 控件 | 对应 |
|---------|------|
| Source CSV path | `--source-file` |
| client_ref | 文本 |
| product_sku | 文本（placeholder: CLEAN-BASIC） |
| encoding / delimiter / file_format | 可选，有默认值 |
| Run gate after create | checkbox，默认 on |
| 按钮 | 「Lookup first」·「Create case + gate」 |
| 已有 case E2E | `case_dir` 文本 + 按钮「Run E2E」；快捷填入 demo_phase / sampleco |

#### B. Lookup results — 最少字段

| 显示项 | 来源 |
|--------|------|
| `ok` | lookup JSON |
| `match_count` | lookup JSON |
| 表格或列表：`case_dir` · `client_ref` · `gate_status` · `known_limits` | `matches[]` 每项 |
| `disclaimer` / `note` | index 元数据（若有） |

#### C. Run results / logs — 最少字段

| 显示项 | 来源 |
|--------|------|
| `action` 标签 | new-case / e2e / lookup |
| `ok` | 包装层 + CLI |
| `case_dir` | 创建或 E2E 结果 |
| `gate_status` / `eligibility` | gate 或 E2E 顶层 |
| `schema.notes` · `schema.warnings` | `dimensions.schema`（gate JSON） |
| `output_guard.status` · `ratio` | E2E / bundle 结果 |
| `steps.*.ok` | E2E `steps` 摘要 |
| Raw JSON | 可折叠 `<pre>` |
| stderr 摘要 | 失败时 |

#### D. Artifact links / paths — 最少字段

| 显示项 | 说明 |
|--------|------|
| `reports/report.json` | 相对 case_dir 路径 |
| `reports/report.md` | 同上 |
| `reports/eligibility_result.json` | 建案+gate 后 |
| `delivery_signoff.md` | case 根 |
| `cleaned/*` | 清洗后 CSV（E2E 成功后） |
| 存在性 | 文件不存在时灰显或标注 missing（不伪造链接） |

---

### AllowedPaths

- `app/**`（新建本票 UI 包）
- `tests/test_local_ui.py`（可选 smoke）
- `04_Workflows/tickets/W-MVP-W5-LOCAL-UI_state.md`

### BlockedPaths

- `core/*`、暗部 `core/*`、`subagents/*`
- `notebooks/csv_cleaning/*`（gate / cleaning / bundle 实现）
- **既有** `scripts/lookup_case_history.py` · `new_cleaning_case.py` · `check_case_eligibility.py` · `build_case_delivery_bundle.py` · `run_case_e2e_validation.py` · `build_cases_index.py` · `cases_index_lib.py`（**禁止改逻辑**；若必须修 CLI bug 须另开票）
- `cases/**` 案例数据（验收只读，不修改 demo 案）
- `AGENTS.md` · `ENGINEERING_CONTRACT.md` · `HARNESS_CONSTITUTION.md` · `.cursor/rules/*`
- `04_Workflows/00_Agent_Work_Progress.md`（Scribe 票）
- `docs/**`（本票不写 runbook；Scribe 后续）
- `.github/workflows/*`

### Dependencies

| 依赖 | 状态 |
|------|------|
| W-MVP-W3（intake CLI · E2E driver） | 已验收 |
| W-MVP-W4A（lookup · `cases/index.json`） | 已验收 |
| W-MVP-W4B（schema guard · output_guard） | 已验收 |
| W-MVP-W4C（`docs/MVP_DEMO_WALKTHROUGH_v0.1.md`） | 已验收 |
| `cases/demo_phase` · `cases/sampleco/2026-0001` | 磁盘锚点须存在 |

### AcceptanceCriteria（AC）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC1** | 能在本机启动并通过浏览器访问 | `python app/local_ui.py` → 打开 `http://127.0.0.1:<port>/` 见四区块页面 |
| **AC2** | 对 sampleco / demo_phase 显示 lookup、gate、schema、output_guard 等关键信号 | UI 走查两案：lookup 见 `known_limits` / `gate_status`；E2E 见 `schema.notes` 与 `output_guard.status` 符合 walkthrough 预期表 |
| **AC3** | 至少触发一条主链动作 | **必须**：(a) new case + gate（可用 `_experiment_samples` 源文件）；(b) 对已有 `cases/demo_phase` 或 `cases/sampleco/2026-0001` 跑 E2E |
| **AC4** | 底层复用现有 scripts，不复制核心逻辑 | 代码审查：`app/local_ui.py` 无 `case_eligibility` / `output_guard` 判定逻辑；仅 subprocess 调既有 CLI；`scripts/` diff 为空 |
| **AC5** | UI 文案明确标注 "local MVP / not prod" | 页面 header 或 banner 含 **LOCAL MVP · NOT PROD · INTERNAL DEMO ONLY** 等价文案 |

---

### Implementer 施工要点（摘自 demo walkthrough 操作顺序）

1. （推荐）`build_cases_index.py` → lookup by `client_ref` / `schema-headers`
2. 新案：`new_cleaning_case.py --run-gate`（demo 走查常用跳过，UI AC 仍须演示一次）
3. 已有案：`run_case_e2e_validation.py --case-dir cases/demo_phase --json`
4. 对照 `docs/MVP_DEMO_WALKTHROUGH_v0.1.md` §1.1 / §1.2 信号表做 UI 展示

---

## STATE

- overall_status: reviewer_zh_hant_done
- current_owner: orchestrator
- next_action: Orchestrator 可将 W-MVP-W5-LOCAL-UI 总 verdict 收口为 **accepted**（含 zh-Hant 层）；于 `00_Agent_Work_Progress.md` 末尾补一句「Local MVP UI 已支援繁體中文介面」
- last_updated: 2026-06-08 · reviewer (zh-Hant)
- status_by_role:
  - orchestrator: done
  - implementer: done
  - reviewer: done
  - scribe: done

---

## B_REPORT

### Step 0 — Module Reuse Check（Orchestrator 冻结 · Implementer 施工时须确认）

**定位句（必填复述）**：这张 UI 票的定位是「**把已验收的 CLI 主链包装成一个本机浏览器工作台**」，**不是**新建第二套业务逻辑。

| 必须复用资产 | 用途 | UI 集成方式 |
|--------------|------|-------------|
| `scripts/lookup_case_history.py` | 只读历史案查询 | subprocess；透传 `--client-ref` / `--product-sku` / `--schema-headers` / `--list-all`；解析 stdout JSON 的 `matches[]` · `known_limits` |
| `scripts/new_cleaning_case.py` | 建案 + 可选 gate | subprocess；`--run-gate`；展示 `case_dir` 与 gate JSON |
| `scripts/check_case_eligibility.py` | 单案 gate（可选） | subprocess `--json`；展示 `dimensions.schema` |
| `scripts/build_case_delivery_bundle.py` | 由 E2E 间接调用 | **不**单独暴露除非 Implementer 加可选按钮；AC 不要求 |
| `scripts/run_case_e2e_validation.py` | gate → clean → bundle 一键 | subprocess `--case-dir` `--json`；展示 `output_guard` · `artifacts` · `steps` |
| `scripts/build_cases_index.py` | 刷新 `cases/index.json` | 可选 API；lookup 前置 |
| `cases/index.json` | lookup SSOT | 只读；由 build_cases_index 刷新 |
| `cases/**` | 案例落盘 | 读路径展示产物；不写案例内容 |
| `docs/MVP_DEMO_WALKTHROUGH_v0.1.md` | 已验证操作顺序与预期信号 | UI 走查与 Reviewer 验收对照表 |
| Wave 4 `dimensions.schema.notes` / `warnings` | schema guard 展示 | 从 gate JSON 原样显示，不在 UI 重算 |
| Wave 4 `output_guard` | ratio guard 展示 | 从 E2E/bundle/report JSON 原样显示 |

- changed_files:
  - `app/__init__.py`
  - `app/local_ui.py`
  - `app/templates/local-ui.html`
  - `app/static/local-ui.css`
  - `app/static/local-ui.js`
  - `04_Workflows/tickets/W-MVP-W5-LOCAL-UI_state.md`
- artifacts:
  - 本机 UI 入口：`app/local_ui.py`
  - 单页：`app/templates/local-ui.html`
  - 样式/脚本：`app/static/local-ui.css` · `app/static/local-ui.js`
- run_instructions:
  - 启动：`python app/local_ui.py`（可选 `--port 8765`）
  - 浏览器打开：`http://127.0.0.1:8765/`
  - 绑定默认 `127.0.0.1`；控制台会打印 **INTERNAL · LOCAL MVP · NOT PROD** 警示
- reused_scripts:
  - `scripts/lookup_case_history.py` — POST `/api/lookup`
  - `scripts/new_cleaning_case.py --run-gate` — POST `/api/new-case`
  - `scripts/run_case_e2e_validation.py --case-dir … --json` — POST `/api/e2e`
  - `scripts/check_case_eligibility.py --json` — E2E 结果区补充 `schema.notes`（只读展示，无裁决逻辑）
  - `scripts/build_cases_index.py` — POST `/api/reindex`（可选）
- supported_flows:
  - lookup — client_ref / product_sku / schema_headers / list_all
  - create case + gate — source path + intake 字段 + `--run-gate`
  - existing case E2E — case_dir → gate → clean → bundle 一键
- limitations:
  - local only（`127.0.0.1` 绑定）
  - no auth / no multi-user
  - no async queue（同步 subprocess，长 E2E 会阻塞请求）
  - relies on local file paths（source-file、case_dir 须本机可读）
  - stdlib `http.server` only；无 Flask/FastAPI 新依赖
- demo_notes:
  - **demo_phase**：E2E 面板点 `demo_phase` 预设 → Run E2E；预期 `gate_status=review_needed`、`output_guard.status=ok`、`output_guard.ratio≈0.71`
  - **sampleco**：Lookup 填 `client_ref=sampleco` → Run Lookup；E2E 点 `sampleco/2026-0001` → Run E2E；预期 `gate_status=accepted`、`schema.notes` 含 `phase_like`/`multi_row_export`/`schema_ambiguous`、`output_guard.status=warning`、`ratio≈0.07`
  - 新建案（AC3 可选）：`cases/_experiment_samples/sampleco_milestone_export.csv` + 新 client_ref
- verification:
  - 启动 UI：`python app/local_ui.py --port 8765` → GET `/` 200，页面含 **NOT PRODUCTION** banner
  - sampleco lookup：POST `/api/lookup` `{"client_ref":"sampleco"}` → `ok=true`，`matches` 长度 1
  - demo_phase E2E：POST `/api/e2e` `{"case_dir":"cases/demo_phase"}` → `ok=true`，`output_guard.status=ok`
  - sampleco E2E：POST `/api/e2e` `{"case_dir":"cases/sampleco/2026-0001"}` → `ok=true`，`output_guard.status=warning`，`ratio≈0.0696`
  - `scripts/` diff 为空（未改 core pipeline CLI）
- behavior_notes:
  - 后端零 import `case_eligibility` / `output_guard`；仅 `subprocess.run` 调既有 scripts
  - E2E 展示 `schema.notes` 时额外 subprocess 调 `check_case_eligibility.py --json`（透传 gate JSON，不重算）
  - 结果区：gate_status / output_guard 颜色区分；关键字段高亮 + 可折叠 Raw JSON
- deferred_items:
  - 单步 gate 按钮（FRAME 可选加分）
  - 文件 picker / 拖拽上传
  - runbook / README 用户文档（Scribe 票）
  - `tests/test_local_ui.py` smoke（可选）
- scope_out（Implementer 确认）:
  - 不改 core pipeline 逻辑（`scripts/` · `notebooks/csv_cleaning/` 无 diff）
  - 不引入数据库
  - 不做云端部署 / prod hardening
  - 不包装全部脚本，仅 lookup / new-case+gate / E2E / 可选 reindex

### Handoff（Implementer · 2026-06-08）

- **next_reviewer**：
  1. `python app/local_ui.py` → 打开 `http://127.0.0.1:8765/`
  2. 确认 header 含 **NOT PRODUCTION · Single-user · Local only**
  3. Lookup：`client_ref=sampleco` → 见 1 条 match、`gate_status=accepted`
  4. E2E：`cases/demo_phase` → `review_needed` + `output_guard.status=ok`
  5. E2E：`cases/sampleco/2026-0001` → `output_guard.status=warning` + `schema.notes` 三项
  6. 代码审查：`app/local_ui.py` 无 `case_eligibility` import；`git diff scripts/` 为空
- **note_to_scribe**：若 Reviewer 验收通过，后续可补 runbook 启动说明；本票不写 `docs/**`

### Reviewer zh-Hant 走查（W-MVP-W5-LOCAL-UI-ZH-HANT · 2026-06-08）

**角色**：Reviewer · 新手视角繁中介面验收 · 仅更新 state，无代码变更。

#### Step 1 — 启动 UI

| 项 | 记录 |
|----|------|
| 启动命令 | `python app/local_ui.py --port 8777` |
| 访问 URL | `http://127.0.0.1:8777/` |
| HTTP 状态 | GET `/` → **200** ✓ |
| 页首标题 | **本機 MVP 介面** ✓ |
| 副标 | **MVP 案件工作台 — 僅封裝 CLI** ✓ |
| 警示条 | **非正式環境** · 單一使用者 · 僅限本機 · 無登入 · 無 SLA ✓ |

#### Step 2 — 繁中文案总体检查

- **四区块标题**：A. 查詢歷史案例 · B. 新建案例 + Gate · C. 既有案例 E2E · D. 執行結果 ✓
- **表单标签**：客戶代號、產品 SKU、欄位名稱（以逗號分隔）、來源檔案路徑、編碼、分隔符號、檔案格式、案例目錄 ✓
- **按钮**：執行查詢、刷新索引、建立案例並執行 Gate、執行 E2E ✓
- **刻意保留英文**：CLI / Gate / E2E / JSON / Schema / stderr；表头 `case_id` · `known_limits`；status 值与路径 ✓
- **整体语言感受**：像内部 demo 工作台，用语自然不拗口；技术词（Gate、E2E、Schema）与繁中标签搭配合理，新手能分清「标签是中文、结果是英文 token」。

#### Step 3 — demo_phase E2E（繁中介面）

| 标签层（繁中） | 值层（英文/数值） | 符合 |
|----------------|-------------------|------|
| 操作：e2e | — | ✓ |
| 整體結果：true | overall_ok = true | ✓ |
| 案例目錄 | `cases\demo_phase` | ✓ |
| Gate 狀態 | `review_needed` | ✓ |
| Schema 備註 | `phase_like, phase_demo` | ✓ |
| Schema 警示 | `—`（无 warnings） | ✓ |
| 輸出護欄狀態 | `ok` | ✓ |
| 輸出護欄比例 | `0.7143` | ✓ |
| 產物路徑 | report.json / report.md / eligibility_result.json / delivery_signoff.md / cleaned/Phase_cleaned.csv | ✓ |

#### Step 4 — sampleco/2026-0001 E2E（繁中介面 + 护栏）

| 标签层（繁中） | 值层（英文/数值） | 符合 |
|----------------|-------------------|------|
| Gate 狀態 | `accepted` | ✓ |
| Schema 備註 | `phase_like, multi_row_export, schema_ambiguous` | ✓ |
| Schema 警示 | `phase_like_headers_but_multi_row_or_sprint_pattern` | ✓ |
| 輸出護欄狀態 | `warning` | ✓ |
| 輸出護欄比例 | `0.0696` | ✓ |
| 整体叙事 | Highlights 即可读懂「gate 绿灯 + 护栏黄灯 + 低 ratio」；**不必**先看 Raw JSON | ✓ |

#### Step 5 — Lookup（繁中标签 + notes）

| 项 | 记录 |
|----|------|
| 输入 | `client_ref=sampleco` |
| 表头 | 案例目錄 · 客戶代號 · case_id · 產品 SKU · Gate 狀態 · known_limits ✓ |
| 符合笔数 | **符合筆數：1** ✓ |
| 备注 | **備註：只登记 demo_phase, sampleco/2026-0001**（索引层原文；UI 标签为繁中「備註：」） ✓ |
| match | `cases/sampleco/2026-0001` · `gate_status=accepted` ✓ |

- verification: Playwright 浏览器走查 + API 复验；`git diff scripts/` 为空 ✓

---

## C_REPORT

### Step 0 — 验收原则（Reviewer 声明）

- 本票**只验** UI 是否正确包装现有 CLI 主链（lookup / new-case+gate / E2E），**不**要求生产级体验。
- 验收路径严格依 Implementer `run_instructions` + `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`，不以票外知识补洞。
- 代码审查确认：`app/local_ui.py` **无** `case_eligibility` / `output_guard` import；`git diff scripts/` **为空**。

---

### Step 1 — 启动 UI

| 项 | 记录 |
|----|------|
| 启动命令 | `python app/local_ui.py`（可选 `--port 8765`；Reviewer 实测亦用 `--port 8766` 避端口占用） |
| 访问 URL | `http://127.0.0.1:8765/`（默认） |
| 控制台警示 | `INTERNAL · LOCAL MVP · NOT PROD · single-user localhost only` ✓ |
| 页面标题 | **Local MVP UI** ✓ |
| 页面 banner | **NOT PRODUCTION** · Single-user · Local only · No auth · No SLA ✓ |
| 四区块 | A Lookup · B New Case + Gate · C Existing Case E2E · D Results ✓ |

---

### Step 2 — Lookup 验收

| 输入 | `client_ref=sampleco` |
|------|------------------------|
| API | `POST /api/lookup` → `ok=true`，`matches` 长度 1 |
| matches[] | `case_dir=cases/sampleco/2026-0001` · `gate_status=accepted` · `known_limits=[]` ✓ |
| notes[] | 索引层 `notes: ["只登记 demo_phase, sampleco/2026-0001"]` 在 API JSON 中存在；**UI 结果区仅显示 `match_count: 1`，未单独列出顶层 `notes[]`**（小缺口） |
| demo 锚点补充 | `client_ref=internal-demo` → match `cases/demo_phase`，`known_limits` 含 `legacy_demo_path` · `rows<100` · `size<1024` · `manual_review_required` ✓（API；表格列可见） |

---

### Step 3 — demo_phase E2E

| 输入 | `cases/demo_phase`（UI 预设按钮 + Run E2E） |
|------|---------------------------------------------|
| overall_ok | `true` ✓ |
| gate_status | `review_needed` ✓（紫色 badge） |
| schema.notes | `phase_like, phase_demo` ✓（经 E2E 后追加 `check_case_eligibility.py --json` 只读 subprocess） |
| output_guard.status | `ok` ✓（绿色 badge） |
| output_guard.ratio | `0.7143` ✓ |
| warning / ok 区分 | `review_needed` vs `ok` 徽章颜色可辨 ✓ |

---

### Step 4 — sampleco E2E

| 输入 | `cases/sampleco/2026-0001` |
|------|----------------------------|
| overall_ok | `true` ✓ |
| gate_status | `accepted` ✓ |
| schema.notes | `phase_like, multi_row_export, schema_ambiguous` ✓ |
| output_guard.status | `warning` ✓（橙色 badge） |
| output_guard.ratio | `0.0696` ≈ 0.07 ✓ |
| demo 叙事 | 绿灯 gate + 黄灯 output_guard + 低 ratio **足以**支撑「勉强可用、需人工审视」故事 ✓ |

---

### Step 5 — Create case + gate

| 项 | 记录 |
|----|------|
| UI 支持 | B 区块「Create Case + Gate」✓ |
| 最小测试 | `source_file=cases/_experiment_samples/sampleco_milestone_export.csv` · `client_ref=reviewer-test` · `run_gate=true` |
| 返回 | `ok=true` · `case_dir=cases/reviewer-test/2026-0001` · `gate_status=review_needed` · `schema.notes=[schema_mismatch, missing_required_columns]` ✓ |
| FRAME 最低要求 | AC3(b) new-case+gate **满足** |

---

### Step 6 — 判定

- **verdict**: `accept_with_minor_edits`
- **strengths**:
  1. **真薄包装**：`app/local_ui.py` 仅 `subprocess.run` 调既有 `scripts/*.py`；`scripts/` 零 diff；无第二套 gate/clean 逻辑。
  2. **演示锚点信号齐全**：浏览器走查 demo_phase / sampleco 的 `overall_ok` · `gate_status` · `schema.notes` · `output_guard` 与 walkthrough §1.1/§1.2 一致。
  3. **NOT PROD 边界清晰**：页头 banner + 启动日志双处明示；footer 标明所包装 CLI。
  4. **结果区可读**：关键字段高亮 + 徽章色区分（accepted / review_needed / warning / ok）+ 可折叠 Raw JSON + artifact 路径列表。
- **gaps**:
  1. Lookup 结果区未展示索引顶层 `data.notes[]`（仅 `match_count`）；demo 走查 Step 0 的 disclaimer 在 UI 上不够显眼。
  2. Highlights 未展示 `schema.warnings[]`（sampleco gate 有 `phase_like_headers_but_multi_row_or_sprint_pattern`）。
  3. `favicon.ico` 404（控制台噪音；不影响功能）。
  4. `tests/test_local_ui.py` 未交付（Implementer 标 deferred；非本票 AC 硬要求）。
- **demo_readiness**: **已足以做本机 demo**——新人可按预设按钮在浏览器内复现 walkthrough 两条锚案核心信号；lookup + 建案 + E2E 三流均可触发。
- **required_edits**（仅说明层／小交互，不扩 scope）:
  1. Lookup 结果区：当 `data.notes[]` 存在时，在 `known-limits` 段落显示（勿只显示 `match_count`）。
  2. E2E / new-case highlights：增加一行 `schema.warnings`（有则显示，无则 `—`）。
  3. （可选）补空 `favicon.ico` 或 `<link rel="icon" href="data:,">` 消除 404。

---

### Step 7 — Scope out（Reviewer 确认）

- **不要求**：登录、权限、部署、数据库、全脚本进 UI、产品级美化。
- **只看**：本机 demo 是否成立、信号是否正确透传 CLI JSON。
- **建议 Orchestrator / Scribe**：verdict 可接受 → 可在 README 或 `docs/MVP_DEMO_WALKTHROUGH_v0.1.md` 追加一节「本机 UI 启动」（`python app/local_ui.py` + URL）；本票 Implementer 已刻意不写 `docs/**`。

---

### AC 对照

| AC | 结果 |
|----|------|
| AC1 本机启动四区块 | ✓ |
| AC2 两案关键信号 | ✓（lookup 顶层 notes 展示为小缺口） |
| AC3 至少一条主链动作 | ✓（E2E 两案 + new-case+gate） |
| AC4 复用 scripts 无复制逻辑 | ✓ |
| AC5 local MVP / not prod 文案 | ✓（等价文案已满足） |

- conclusion: **accept_with_minor_edits** — 薄包装定位成立，demo 信号正确；lookup notes 与 schema.warnings 展示可小改后更佳。
- blocking_issues: **无**
- checks_summary: 启动+页头 ✓ · lookup(sampleco/internal-demo) ✓ · E2E(demo_phase/sampleco) ✓ · new-case+gate ✓ · 代码/subprocess 审查 ✓ · 浏览器走查(Playwright) ✓
- risk_level: **low**（本机单用户；同步 subprocess 阻塞可接受）
- suggestions: Scribe 补 UI 启动一句到 walkthrough；Implementer 小改 lookup notes / schema.warnings 后可视为 **accepted**

---

### zh-Hant 子票判定（Reviewer · W-MVP-W5-LOCAL-UI-ZH-HANT · 2026-06-08）

- **verdict**: `accepted`
- **strengths**:
  1. 页首警示与四区块标题全繁中，新手第一眼即知「本机 demo、非正式环境」。
  2. Highlights 标签（Gate 狀態、Schema 備註/警示、輸出護欄狀態/比例）与 walkthrough 信号一一对应；status 值保持英文 token，徽章色可辨。
  3. demo_phase / sampleco 护栏故事在繁中界面仍可读懂：黄灯 gate + 绿灯护栏 vs 绿灯 gate + 黄灯护栏，单看 D 区 Highlights 足够。
  4. Lookup 已展示「備註：」与「符合筆數：」；索引 disclaimer 可见。
- **gaps**（仅文案润饰，不扩 scope）:
  1. E2E 状态条写「整體結果：true」，lookup 写「成功：true」——轻微用语不一致，不影响理解。
  2. `data.notes[]` 内容为索引层简体「只登记…」，非 UI 翻译问题；若日后统一索引文案可另票。
  3. Windows 下案例目录显示反斜杠（`cases\demo_phase`）；路径仍可读。
- **demo_readiness**: 繁中 UI 已足以支撑 demo_phase / sampleco 的本机示范；新人可按预设按钮完成走查。
- **scope_out**（重申）:
  - 不要求 UI 达产品级美术与互动。
  - 不要求多语切换；本票仅验证 zh-Hant 单版。
  - 不改动任何 `scripts/` 或 core pipeline。
- **handoff_to_orchestrator**: zh-Hant 层验收 **accepted**；建议将 W-MVP-W5-LOCAL-UI 一并标为 done，并于 Progress 补一句「Local MVP UI 已支援繁體中文介面」。

---

## D_REPORT

### scribe_note（W-MVP-W5-LOCAL-UI-SCRIBE · 2026-06-08）

**Reviewer required_edits 落实**（对照 C_REPORT §Step 6 required_edits）：

1. Lookup 结果区展示索引顶层 `data.notes[]`（sampleco 可见「只登记 demo_phase, sampleco/2026-0001」类 disclaimer）。
2. Highlights 增加 `schema.warnings` 行（E2E / new-case 共用；sampleco E2E 可见 `phase_like_headers_but_multi_row_or_sprint_pattern`）。
3. favicon：`<link rel="icon" href="data:,">` 消除浏览器 404 噪音。
4. 文档：`docs/MVP_DEMO_WALKTHROUGH_v0.1.md` §0 补本机 UI 启动说明（`python app/local_ui.py` · NOT PROD）。

- changed_files:
  - `app/templates/local-ui.html`
  - `app/static/local-ui.js`
  - `app/local_ui.py`（仅 E2E 展示层：`_gate_schema_fields` 透传 `schema_warnings[]`；无 gate 裁决逻辑）
  - `docs/MVP_DEMO_WALKTHROUGH_v0.1.md`
  - `04_Workflows/tickets/W-MVP-W5-LOCAL-UI_state.md`
- edits_summary:
  - Lookup「Notes」段落读取 `data.notes[]`；`match_count` / `matches[]` 表现不变。
  - Highlights 新增 `schema.warnings`；读取 `data.schema.warnings` · `data.schema_warnings` · `data.gate.dimensions.schema.warnings`。
  - walkthrough 增加本机 UI 启动一句；强调 local MVP / NOT PROD。
  - favicon 已处理（data URL 空 icon）。
- scope_out:
  - **未改** `scripts/` 与 `notebooks/csv_cleaning/` 业务逻辑。
  - **未** 引入登录 / DB / 云部署 / 新依赖。
  - `app/local_ui.py` 变更仅为只读 gate subprocess 字段透传（与既有 `schema_notes` 同路径），非 pipeline 逻辑。
- verification:
  - `POST /api/lookup` `{"client_ref":"sampleco"}` → `data.notes[]` 非空 ✓
  - `POST /api/e2e` `{"case_dir":"cases/sampleco/2026-0001"}` → `schema_warnings` 含 `phase_like_headers_but_multi_row_or_sprint_pattern` ✓
- handoff_to_orchestrator:
  - Reviewer **required_edits 三项均已满足**；建议将 W-MVP-W5-LOCAL-UI 总 verdict 从 `accept_with_minor_edits` 收口为 **`accepted`**。
  - 可选：于 `00_Agent_Work_Progress.md` 末尾追加一句「W-MVP-W5 local UI 可用于 demo_phase / sampleco 本机走查」。

- docs_updates: `docs/MVP_DEMO_WALKTHROUGH_v0.1.md` §0「本机 UI（可选 · W-MVP-W5）」
- progress_entry: *(deferred · 交 Orchestrator 决定是否 append Progress)*
- followup_suggestions: `tests/test_local_ui.py` smoke 仍 deferred（非 AC）；单步 gate 按钮仍 deferred

---

### scribe_note（W-MVP-W5-LOCAL-UI-ZH-HANT · 2026-06-08）

**任務**：Local MVP UI 前端展示文案本地化（zh-Hant）；僅改 HTML/JS 可見字串，不動 API contract / scripts / 業務邏輯。

- changed_files:
  - `app/templates/local-ui.html`
  - `app/static/local-ui.js`
  - `04_Workflows/tickets/W-MVP-W5-LOCAL-UI_state.md`
- translated_sections:
  - 頁面標題 / 副標題 / 非正式環境警示 banner
  - 四大區塊標題（A 查詢歷史案例 · B 新建案例 + Gate · C 既有案例 E2E · D 執行結果）
  - 表單 label / placeholder / checkbox / 按鈕
  - 結果區：Highlights 標籤、產物路徑、原始 JSON、查詢比對結果、空狀態說明
  - JS 動態標籤：操作、成功、整體結果、備註、符合筆數、表格欄標題、無符合案例、（回應中未含）
  - 頁尾 CLI 封裝說明
- any_strings_left_in_english_on_purpose:
  - 專業術語：CLI、Gate、E2E、JSON、Schema、stderr
  - 表單/API 欄位名（`name` 屬性）：client_ref、product_sku、schema_headers、case_dir 等
  - 預設值與路徑範例：CLEAN-BASIC、utf-8、cases/demo_phase、demo_phase 按鈕
  - 結果**值**保持英文：accepted / review_needed / warning / ok、true / false、gate token、artifact 路徑
  - Lookup 表頭 `case_id`、`known_limits`（技術鍵，值不翻譯）
  - Raw JSON 區塊內容（API 原樣輸出）
- verification_notes:
  - `git diff scripts/` 為空 ✓
  - `python app/local_ui.py --port 8777` → GET `/` 200；頁面含「非正式環境」「僅限本機」警示 ✓
  - POST `/api/lookup` `{"client_ref":"sampleco"}` → `ok=true`，JSON contract 未變 ✓
  - 未改 `app/local_ui.py`、未引入 i18n framework
