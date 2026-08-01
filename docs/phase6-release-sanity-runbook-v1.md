# Phase 6 — Release Sanity Runbook (v1)

> **Ticket**: `FP-G6-T2-release-sanity-runbook-v1` · Full-Phase G6 · P6 · **doc/spec** · evidence_tier **L-local**  
> **Date**: 2026-07-10

---

## non_claims（置頂 · 必讀）

| 本 runbook **不是** | 說明 |
|---------------------|------|
| ≠ GitHub **required** CI | 本頁命令為 **L-local release sanity**；**不**等於 branch protection 已掛 required check（WC-PRE） |
| ≠ INT **Tier-A** | 裝配／envelope／manifest 變更須另跑 INT gate；smoke 綠 **不覆蓋** Tier-A |
| ≠ **Phase%** 上調 | 本頁操作指引 **不**改 Dashboard／Progress Phase 完成度數字 |
| ≠ **P6 closure** | 全綠 = 本機 release sanity 通過；**≠** Phase 6 已結案 |
| ≠ **P7 Round-2 GO** | smoke 綠 **≠** Round-2 staging／prod GO |

**位階**

| 文件 | 角色 |
|------|------|
| **本檔** `docs/phase6-release-sanity-runbook-v1.md` | **操作單頁**（建議順序 · 可複製命令 · pass/fail 摘要） |
| [`docs/smoke-and-regression-contract-v1.md`](./smoke-and-regression-contract-v1.md) | **契約 SSOT**（gate 分層 · 輸出契約 · Non-Claims 全文） |
| [`04_Workflows/WORKFLOW_INDEX.md`](../04_Workflows/WORKFLOW_INDEX.md) **§1.5** | **Runner 索引**（MP／MC／CI-SMOKE 路徑與驗證句） |
| Dashboard §Multi-phase smoke | 進度／索引側車；**不改 Phase%** |

---

## 1. Purpose

發版前對 **MP-SMOKE → MC-SMOKE → CI-SMOKE** 做一次 **L-local release sanity** 操作指引。命令對齊 INDEX §1.5 與契約；細節與欄位契約以 `smoke-and-regression-contract-v1.md` 為準。

**NonScope**：不改 `scripts/**`／`tests/**`／`.github/workflows/**`；不升格 required CI；不替代 INT Tier-A。

---

## 2. 發版前建議順序（MP → MC → CI-SMOKE）

```text
1. MP-SMOKE   單 case 七步深挖（接線未斷）
2. MC-SMOKE   多 case fleet 掃（代表性 profile）
3. CI-SMOKE   單 case 合成 pass/fail + process exit
```

> 契約 §6 另列「Fleet 優先」深挖鏈（MC 再 MP）；**本 runbook 依 G6-T2 FRAME 固定 MP → MC → CI-SMOKE**。兩者皆為 L-local；擇一敘事時以本頁順序為發版操作預設。

---

## 3. 典型命令（對齊 INDEX §1.5）

### 3.1 MP-SMOKE

```bash
python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --format json
# 可選 dispatch 路徑：
python scripts/run_multi_phase_smoke_v1.py --case-ref demo_phase --enable-dispatch --format json
```

- **產物**：`outbox/verification/<case_slug>/multi_phase_smoke_run.json`
- **單元驗證（可選）**：`python -m unittest tests.test_multi_phase_smoke_v1 -v`

### 3.2 MC-SMOKE

```bash
# release pass 路徑（排除 phi_demo deny 探針）
python scripts/run_multi_case_smoke_v1.py --cases demo_phase,sampleco --format json
# 可選：預設列表含 phi_demo（預期部分 fail · 僅探針）
python scripts/run_multi_case_smoke_v1.py --format json
```

- **產物**：`outbox/verification/multi_case_smoke_run.json`

### 3.3 CI-SMOKE

```bash
python scripts/run_ci_smoke_check_v1.py --format text
# 或指定 case + json：
python scripts/run_ci_smoke_check_v1.py --case-ref demo_phase --format json
```

- **exit**：`0` = pass · `1` = fail（見下節）

---

## 4. Pass／Fail 判準摘要

| 步驟 | Pass | Fail／注意 |
|------|------|------------|
| **MP-SMOKE** | 頂層 `ok=true` · 七步皆 `ok` | 任一步 `ok=false` → 先修該 step，再進 MC |
| **MC-SMOKE**（release） | `--cases demo_phase,sampleco` 時 `failed_cases` 為空 · `ok=true` | 預設含 `phi_demo` 時 **預期** deny 探針 fail — **勿**當 release fail |
| **CI-SMOKE** | `multi_phase_smoke ok=true` · `std_case_metrics ok=true` · `notifications_failed_ack_count == 0`（預設 isolated outbox）· **exit 0** | 任一 check 失敗 → **exit 1**；共享 outbox 歷史 failed ack 見契約 §5.2（`--use-repo-outbox` 用 delta） |

完整規則與輸出鍵 → [`docs/smoke-and-regression-contract-v1.md`](./smoke-and-regression-contract-v1.md) §3–§5 · §8 Non-Claims。

---

## 5. Cross-references

| 資源 | 用途 |
|------|------|
| [`docs/smoke-and-regression-contract-v1.md`](./smoke-and-regression-contract-v1.md) | 契約 SSOT |
| [`04_Workflows/WORKFLOW_INDEX.md`](../04_Workflows/WORKFLOW_INDEX.md) §1.5 | MP／MC／CI-SMOKE runner 索引 |
| Dashboard §Multi-phase smoke | 發版 sanity 索引（Phase% 不變） |
| `docs/P8_P89_ADVISORY_CI_INDEX.md` | local-only／advisory 標籤（可選） |
| `docs/phase6-int-regression-gate-contract-v1.md` | INT Tier-A **分軌**（非本頁替代） |

---

## 6. Verification（本票 doc）

```bash
rg "MP-SMOKE|MC-SMOKE|CI-SMOKE|non_claims|smoke-and-regression" docs/phase6-release-sanity-runbook-v1.md
```

---

*phase6-release-sanity-runbook-v1 · FP-G6-T2 · doc-only · L-local · 2026-07-10*
