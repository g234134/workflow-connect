# P9 Payment Sandbox CI — First Run Human Runbook

> **用途**：human 手动触发 **P9 payment sandbox advisory CI** 首跑并回填证据。  
> **SSOT 票**：`04_Workflows/tickets/WH-P9-CI-payment-sandbox-smoke-v1_state.md`  
> **non-claims**：sandbox-only · advisory · **≠ prod · ≠ INT Tier-A · ≠ required CI**

---

## 背景

- **Workflow landing**：`.github/workflows/p9-payment-sandbox-smoke.yml` 已建 · job **P9 payment sandbox smoke (advisory)** · `continue-on-error: true`。
- **本地验证**：unittest **21/21 OK** · e2e **`ok=true` · `order_status=PAID`**（清 `artifacts/e2e/WC-DEMO-1` 后重跑）。
- **GitHub 首跑**：**待 human** — 票 B_REPORT **`<RUN_URL>`** placeholder · Progress 首跑段 **无真实 URL**。
- **首跑 ≠ CI pass 宣稱**：须 push/merge 含 yml 的变更至 **`main`** 后 **workflow_dispatch** 并取得 run URL。

---

## 操作步骤

1. 确认 **`main`** 已含 `p9-payment-sandbox-smoke.yml`（merge/push 完成）。
2. GitHub → Repo → **Actions** → 左栏选 **P9 payment sandbox smoke (advisory)**。
3. 右栏 **Run workflow**：
   - **Use workflow from**：**`main`**
4. 点 **Run workflow** · 等待 job **completed**（advisory · 不阻 merge）。
5. 复制 **run URL** 与 **run id** · 检查 summary artifact / log 含 `walkthrough_ok` + `order_status=PAID` 断言语义。

**Job 内 execute 命令（对照用）**：

```bash
GOV_PAYMENT_SANDBOX_ENABLED=1 python scripts/run_wc_m2_e2e_walkthrough.py \
  --ticket WC-DEMO-1 \
  --artifacts-root artifacts/e2e \
  --execute \
  --use-hitl-fixtures \
  --include-payment \
  --json
```

---

## 回填位置

| 目标 | 栏位 |
|------|------|
| **P9 CI 票** | B_REPORT **`<RUN_URL>`** / **`<RUN_ID>`**（替换 placeholder） |
| **Progress** | `04_Workflows/00_Agent_Work_Progress.md` **末尾 append** |

**Progress 末尾战报模板（复制后填 run URL/run id）**：

```markdown
## YYYY-MM-DD · P9 payment sandbox CI 首跑（GitHub · human dispatch）

- **票**：`WH-P9-CI-payment-sandbox-smoke-v1`
- **workflow**：`.github/workflows/p9-payment-sandbox-smoke.yml` · advisory · `continue-on-error: true`
- **run URL**：`<填入 Actions run URL>`
- **run id**：`<填入 run id>`
- **结果摘要**：（job log / summary artifact 一句 · walkthrough_ok + order_status=PAID）
- **non-claims**：sandbox-only · advisory · **≠ required / merge-blocking · ≠ prod 金流 · ≠ INT Tier-A**
- **变更档**：本档 append only · **未改** Phase% / branch protection / prod config
```

---

## Non-claims

- **sandbox-only** · mock adapter · `GOV_PAYMENT_SANDBOX_ENABLED=1` 仅 job scope。
- **advisory / non-blocking** · **≠ required check · ≠ merge gate**。
- **≠ prod 金流 · ≠ 真 payment provider / prod ledger**。
- **≠ INT Tier-A · ≠ manual HITL 验收**。
- **无 run URL 不得宣称 CI 首跑 pass**。

---

*版本：v1 · 2026-06-25 · Wave-next doc/SOP Scribe 落档*
