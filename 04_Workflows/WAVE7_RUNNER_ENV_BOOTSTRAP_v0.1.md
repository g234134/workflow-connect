# Wave 7 – RUNNER-ENV-BOOTSTRAP（v0.1）

> **票号**：`RUNNER-ENV-BOOTSTRAP`  
> **性质**：implementation ticket  
> **范围**：runner/orchestrator 唯一环境引导入口  
> **依据**：暗部 `core/repo_paths.py`（`ensure_repo_root_on_path()`）；`Master_Map.json` / `gov_paths`  
> **不做**：安装依赖、改 venv、读 `.env` 原文、启动 long-running 服务

---

## 0. 背景

runner/orchestrator 尚无统一环境引导；各模块若各自 parent-walk，易产生第二套 root 探测与路径解析分歧。本票提供 **唯一环境引导入口**。

---

## 1. 目标

提供 runner/orchestrator 的 **唯一环境引导入口**：repo root、`gov_core_system` venv、`gov_paths` 解析与 smoke 级自检，避免各模块各自 parent-walk。

---

## 2. 输入 / 输出

### 2.1 输入

| 输入 | 说明 |
|------|------|
| 可选 `--cabin gov_core_system` | 指定 cabin |
| 可选 dry-run | 仅检查不执行 |

### 2.2 输出

已 bootstrap 的 callable/上下文；结构化回传：

```text
{ok, repo_root_logical, paths_resolved, warnings[]}
```

失败时明确缺什么（地图键、venv marker、schema 文件）。

---

## 3. Done 条件（checklist）

- [ ] 复用暗部 `core/repo_paths.ensure_repo_root_on_path()` 模式，**不**新增第二套 root 探测。
- [ ] 能解析 Wave 7 交付根、staging 根、cleaned_full 逻辑别名（键名登记 `Master_Map.json`，不在代码写死磁盘串）。
- [ ] `bootstrap --check` 一条命令：venv import 核心模块 + JSON schema 可读 → exit 0。
- [ ] 文档/runbook 片段：从战车根如何启动 Wave 7 runner（相对路径示例）。
- [ ] 单测：mock 地图缺失时 `ok: false`。

---

## 4. 边界（明确不做）

- 不安装依赖
- 不改 venv
- 不读 `.env` 原文
- 不启动 long-running 服务

---

## 5. 依赖 / 前置

无（建议首张实施票）。

---

## 6. Runbook 片段（战车根启动）

从战车根（含 `04_Workflows/Master_Map.json`）在 **gov_core_system** venv 内执行：

```powershell
# 环境自检（路径解析 + 核心模块 import + JSON schema 可读）→ exit 0
python .\04_Workflows\_wave7_runner_bootstrap.py --check

# 仅解析 wave7_paths（dry-run，不跑 venv/schema 检查）
python .\04_Workflows\_wave7_runner_bootstrap.py --dry-run

# 指定 cabin（默认 gov_core_system）
python .\04_Workflows\_wave7_runner_bootstrap.py --cabin gov_core_system --check --pretty
```

程序化调用（orchestrator 内，勿第二套 parent-walk）：

```python
from core.wave7_runner_env_bootstrap import bootstrap_runner_env

result = bootstrap_runner_env(check=True)
# result: {ok, repo_root_logical, paths_resolved, warnings[]}
```

逻辑路径键见 `Master_Map.json` → `wave7_paths`（`cleaned_full` / `staging_root` / `delivery_root`）；runner 索引键 `wave7_runner_bootstrap`。

---

*Wave 7 implementation ticket · `04_Workflows/WAVE7_RUNNER_ENV_BOOTSTRAP_v0.1.md`*
