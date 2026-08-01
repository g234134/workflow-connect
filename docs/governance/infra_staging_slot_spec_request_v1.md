# Infra staging slot + HTTPS endpoint · 規格請求表（H2 · W2-T2）

> **票**：`W2-T2-infra-staging-slot-spec-request-v1`  
> **對齊**：WAVE5 **H2** · execute-v2 前置 P-2 · `docs/governance-dual-unblock-checklist-v1.md` 五頂 #2  
> **H1 批文**：`GOV-DUAL-APPROVAL-2026-07-13-01`（`docs/governance/GOVERNANCE_DUAL_approval_template.md`）  
> **性質**：Infra **填寫用**請求表 · **≠** 已 provision · **≠** 改 `.env`／金鑰

---

## 0. non_claims

| 本表 **不是** | 說明 |
|---------------|------|
| ≠ H2 已解阻 | 表格齊 ≠ slot 已上線 |
| ≠ Round-2 GO／execute-v2 | 仍須 H3–H5 + 尚書省 GO |
| ≠ 可寫本機絕對路徑／密鑰原文 | 路徑見 `Master_Map.json` 邏輯名；密鑰僅 `[OK]`／`[FAILED]` 摘要 |
| ≠ localhost／自簽冒充真 staging | Round-1 local slot **不可**填入本表頂替 |

---

## 1. 請求元數據（Orchestrator 預填）

| 欄位 | 值 |
|------|-----|
| **request_id** | `INFRA-STAGING-SPEC-REQ-2026-07-13-01` |
| **requested_by** | 尚書省／執行 Orchestrator（H1 推進後） |
| **governance_dual_approval_id** | `GOV-DUAL-APPROVAL-2026-07-13-01` |
| **target_ticket** | `WH-P7-NOTIF-staging-integration-execute-v2`（P-2） |
| **tier** | `staging` · **explicit non-prod** |
| **deadline_discuss** | 可與 QUEUE H4（earliest 07-18）對齊討論；**≠** 提前 execute |

---

## 2. Infra 必填（人類／Infra）

| 欄位 | 填寫 | 備註 |
|------|------|------|
| **slot_name**（邏輯名） | ______________ | 例：`p7-notif-staging-slot-A`（**不**硬編磁碟路徑） |
| **https_host**（non-prod） | ______________ | FQDN only · **禁止** prod host · **禁止**僅 `localhost` 頂替 |
| **tls_class** | `[ ]` managed cert · `[ ]` org internal CA · `[ ]` other:___ | 摘要即可 |
| **allowlist_ready_for_h4** | `[ ]` yes · `[ ]` no · notes:___ | 與 H4 銜接 |
| **receiver_deploy_target**（H5 銜接） | ______________ | 部署目標邏輯名；**不**貼 secret |
| **health_probe_summary** | `status=____` · `http=____` | 僅 2xx／fail 原因；**不**貼 token |
| **env_matrix_ref** | ______________ | 見 Master_Map／既有 staging env 票邏輯名 |
| **provisioned_at** | YYYY-MM-DD | |
| **infra_signoff** | 姓名／日期 | |

---

## 3. 驗收（H2 解阻條件）

- [ ] `slot_name` + `https_host` 已寫入票／Progress（無密鑰）  
- [ ] host 明確 **non-prod** · 非 Round-1 localhost 冒充  
- [ ] 健康探針摘要可重跑（2xx 或誠實 fail）  
- [ ] cross-ref `GOV-DUAL-APPROVAL-2026-07-13-01`

**解阻後下一動**：開／推進 H3 Security sign-off；**仍禁止** execute-v2 直至 H3–H5 齊。

---

## 4. AI 禁止

- 填寫假 HTTPS host／假 slot  
- 改 `.env`、輸出金鑰原文  
- 宣稱 H2 已解阻或 Round-2 GO  
- 對真 staging 發 POST

---

## 5. 交接副署（2026-07-14 · 大唐副官／施工 worker · append）

> 依尚書省指令：批文 `GOV-DUAL-APPROVAL-2026-07-13-01` 簽名區已加**交接副署**；**H2–H5 仍 blocked**。本節 **不**填寫 §2 假資料。

| 項 | 內容 |
|----|------|
| **誰填** | **Infra**（人類／Infra Agent；DarkOps 真施工須另開解禁票） |
| **填哪張表** | 本檔 **§2 Infra 必填** |
| **票** | `W2-T2-infra-staging-slot-spec-request-v1` |
| **blocked 原因** | 真 staging slot／non-prod HTTPS **尚未 provision**；規格請求表已備 ≠ H2 已解 |
| **待填欄（§2）** | `slot_name` · `https_host` · `tls_class` · `allowlist_ready_for_h4` · `receiver_deploy_target` · `health_probe_summary` · `env_matrix_ref` · `provisioned_at` · `infra_signoff` |
| **下一步** | Infra 填齊 §2 → 對照 §3 驗收勾選 → 解 H2 → 再串 H3–H5；**仍禁止** execute-v2／Round-2 GO |
| **批文副署依據** | `docs/governance/GOVERNANCE_DUAL_approval_template.md` §5 簽名區 · `worker_handoff_countersign=granted` |

---

## 6. Wave5 Tip H2 · HQ-Coordinator 催辦交接（2026-07-28 · append）

> 計劃 todos `stage-h2-infra` · **≠** AI 代填 §2 · **≠** H2 已解 · **≠** Round-2 GO

| 項 | 內容 |
|----|------|
| **誰填** | **Infra**（人類／Infra Agent；真 provision 另開票） |
| **填哪** | 本檔 **§2**（九欄全填） |
| **H1 依據** | `GOV-DUAL-APPROVAL-2026-07-13-01` · lifecycle **`approved`**（2026-07-28 具名） |
| **§2 仍空白** | `slot_name` · `https_host` · `tls_class` · `allowlist_ready_for_h4` · `receiver_deploy_target` · `health_probe_summary` · `env_matrix_ref` · `provisioned_at` · `infra_signoff` |
| **驗收** | §3 四勾選 + Progress／票 `W2-T2-infra-staging-slot-spec-request-v1` 引用 |
| **硬禁** | localhost／自簽冒充真 staging · AI 假 HTTPS · 改 `.env` · 貼金鑰 · 宣稱 Round-2 GO |
| **解阻後** | 開 H3（動作包 §3）；**仍禁** execute-v2 直至 H3–H5 齊 + 尚書省另明示 GO |
| **AI 本輪** | 僅催辦／交接／Progress 留痕；**未**寫入假 host |

---

## 7. Round-2 Track A · H2 催辦／驗收稽核（2026-07-28 · append）

> plan todo `track-a-h2` · **≠** AI 代填 §2 · **≠** H2 已解 · **≠** Round-2 GO

### 7.1 §2 九欄完整性核對（本輪稽核結果）

| 欄位 | 現況 | 驗收 |
|------|------|------|
| `slot_name` | **空白** | ❌ |
| `https_host` | **空白** | ❌ · **禁止** AI 填假 FQDN／localhost 頂替 |
| `tls_class` | **未勾** | ❌ |
| `allowlist_ready_for_h4` | **未勾** | ❌ |
| `receiver_deploy_target` | **空白** | ❌ |
| `health_probe_summary` | **空白** | ❌ |
| `env_matrix_ref` | **空白** | ❌ |
| `provisioned_at` | **空白** | ❌ |
| `infra_signoff` | **空白** | ❌ |

**稽核結論**：§2 **未齊** → H2 **仍 blocked** · §3 四勾選 **不可**勾選 · **未**宣稱解阻。

### 7.2 Infra 催辦清單（交人類／Infra）

1. Provision **真** non-prod staging slot（邏輯名寫入 `slot_name`）。
2. 填 `https_host`（FQDN only · **禁止** prod · **禁止**僅 localhost）。
3. 勾 `tls_class`；填探針摘要（僅 2xx／fail 原因 · **不**貼 token）。
4. 填 `allowlist_ready_for_h4`／`receiver_deploy_target`／`env_matrix_ref`／`provisioned_at`／`infra_signoff`。
5. 對照本檔 **§3** 四勾選 → 解 H2 → 再開 H3；**仍禁** execute-v2 直至 H3–H5 + 尚書省 GO。

### 7.3 AI 本輪邊界

| 做了 | **沒做** |
|------|----------|
| 催辦／完整性核對／票＋Progress 留痕 | 假 HTTPS／假 slot／改 `.env`／宣稱 H2 解阻／Round-2 GO |

---

## 8. Unlock 支 · Infra 限期實填包（2026-07-28 · append）

> plan todo `human-h2-fill` · 依裁決一頁 `wave5_h2_unlock_or_defer_decision_v1.md` **Unlock** 勾選後生效  
> **≠** AI 代填 · **≠** 假 host · **≠** H2 已解（須九欄＋§3）

### 8.1 SLA 綁定（Unlock 勾選後由尚書省／Infra 填）

| 欄 | 值 |
|----|-----|
| **裁決依據** | `WAVE5-H2-UNLOCK-OR-DEFER-2026-07-28-01` · 欄 A Unlock |
| **Infra owner** | ______________（須與裁決一頁一致） |
| **截止日** | ______________（預設 `2026-08-04` · 5 工作日） |
| **逾期** | 自動落入 Defer（見 `wave5_h2_defer_pivot_playbook_v1.md`）· **停止**無限催辦 |

### 8.2 §2 九欄實填清單（交 Infra · 禁止假值）

| # | 欄位 | 必填規則 | 現況 |
|---|------|----------|------|
| 1 | `slot_name` | 邏輯名 · 非磁碟路徑 | **空白** |
| 2 | `https_host` | **真** non-prod FQDN · **禁止** prod · **禁止**僅 localhost／自簽冒充 Round-2 | **空白** |
| 3 | `tls_class` | managed／org CA／other | **未勾** |
| 4 | `allowlist_ready_for_h4` | yes／no + notes | **未勾** |
| 5 | `receiver_deploy_target` | 邏輯名 · 不貼 secret | **空白** |
| 6 | `health_probe_summary` | `status=` + `http=` · 僅 2xx／fail 原因 | **空白** |
| 7 | `env_matrix_ref` | Master_Map／staging env 票邏輯名 | **空白** |
| 8 | `provisioned_at` | YYYY-MM-DD | **空白** |
| 9 | `infra_signoff` | 姓名／日期 | **空白** |

### 8.3 §3 四勾選（僅九欄齊後可勾 · 人類）

- [ ] `slot_name` + `https_host` 已寫入票／Progress（無密鑰）
- [ ] host 明確 **non-prod** · 非 Round-1 localhost 冒充
- [ ] 健康探針摘要可重跑（2xx 或誠實 fail）
- [ ] cross-ref `GOV-DUAL-APPROVAL-2026-07-13-01`

### 8.4 AI 覆核門檻（人類填後才可改 H2 狀態）

| 條件 | 未滿足時 |
|------|----------|
| 九欄非空（目視／字串非 `____`） | H2 **維持 blocked** |
| §3 四勾全選 | **不可**宣稱解阻 |
| `https_host` 非 localhost／非明顯假值 | **STOP** · 退回 Infra |

**本輪 AI**：僅交付本 SLA 包 + 完整性核對骨架；**未**寫入假 host；H2 **仍 blocked**。

### 8.5 Append · 2026-07-28 · Plan Implement · branch-unlock-fill STOP

> plan todo `branch-unlock-fill` · **UNLOCK 未勾** · Implement ≠ 代勾

| 項 | 現況 |
|----|------|
| 裁決 §3 UNLOCK | **未勾** |
| §2 九欄 | **仍全空白**（§7／§8.2） |
| §3 四勾選 | **不可勾** |
| AI | **未**寫假 host／localhost · H2 **仍 blocked** |

**解阻**：尚書省勾 UNLOCK（或回覆 `UNLOCK` + Infra owner）→ Infra 真填 §2 → §8.4 覆核後才可改 H2 狀態。

---

## 9. Append · 2026-07-28T03:46 · plan todo `branch-unlock` STOP（再覆核）

> **UNLOCK 仍未勾** · §2 九欄仍空白 · **未**假 host · **未**代簽 H3–H5 · **未** P-GO／execute-v2

**解阻後才做**：Infra 真填 §2 → H3–H5 真簽 → **另**明示 P-GO → execute-v2 S1–S4。
