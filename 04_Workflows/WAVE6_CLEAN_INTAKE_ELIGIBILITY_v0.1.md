# WAVE6_CLEAN_INTAKE_ELIGIBILITY_v0.1.md

> **角色**：CLEAN 工单准入判定规则（可移植层）。  
> **目的**：定义资料清洗战役（CLEAN Wave）的工单可接判定逻辑，确保 ENF 风险治理与人工核准边界落地。  
> **版本**：v0.1 草案，待尚书省裁决定稿号。  
> **对齐**：`HARNESS_CONSTITUTION.md` §7 禁区类型、`ENGINEERING_CONTRACT.md` 四流派、`00_Agent_Work_Conditions.md` 合规基线。

---

## 1. 文件定位

| 项目 | 说明 |
|------|------|
| **层级** | 战役级准入规则（与 WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md 对齐） |
| **适用范围** | 所有进入 CLEAN Wave 的资料清洗工单（intake questionnaire → eligibility → assignment） |
| **前置依赖** | 标准 intake 问卷与 JSON schema 已就位；Wave 1–5 / ENF 风险与合规治理基础已完成 |
| **输出目标** | `task_routing.py` 判定逻辑、人工复核队列、自动拒绝日志 |

---

## 2. 决策结果定义

| 结果 | 语义 | 下游动作 | 治理标签 |
|------|------|----------|----------|
| **ACCEPT** | 工单符合自动准入条件，可直接排程至 CLEAN pipeline | 进入 Wave 6 任务队列，分配 Data Agent / Infra Agent 资源 | `eligibility: auto_accepted` |
| **REVIEW** | 工单触发高敏感或大规模条件，需人工核准后方可执行 | 进入 ENF 复核队列，由 Governance Agent 或尚书省指派人工审核 | `eligibility: needs_enf_review` |
| **REJECT** | 工单违反合规红线或技术边界，不可进入 CLEAN pipeline | 记录拒绝原因，返回提交方修正或永久归档 | `eligibility: rejected` + `reject_reason_code` |

---

## 3. 判定条件维度

### 3.1 资料规模（Scale）

| 维度 | 下限 | 上限 | ACCEPT 区间 | REVIEW 区间 | REJECT 条件 |
|------|------|------|-------------|-------------|-------------|
| **行数（Rows）** | ≥ 100 | ≤ 10,000,000 | 100 – 1,000,000 | 1,000,001 – 10,000,000 | > 10,000,000（需拆单） |
| **档案大小（File Size）** | ≥ 1 KB | ≤ 10 GB | 1 KB – 1 GB | 1 GB – 10 GB | > 10 GB（技术边界） |
| **批次文件数（Batch Files）** | 1 | ≤ 1,000 | 1 – 100 | 101 – 1,000 | > 1,000（需分批） |

**判定逻辑**：
- 任一维度落入 REVIEW 区间 → 标记 `needs_enf_review`
- 任一维度突破 REJECT 条件 → 直接 `REJECT`，返回 `reason: scale_exceeds_capacity`
- 复合维度：行数与档案大小均达 REVIEW 区间 → 强制 REVIEW（不叠加为 REJECT）

### 3.2 来源合规性（Provenance）

| 来源类型 | 定义 | 判定结果 | 治理备注 |
|----------|------|----------|----------|
| **自有数据（Owned）** | 组织内部系统生成，具备完整数据所有权链 | ACCEPT | 需附 `data_owner` 字段 |
| **第三方授权（Licensed）** | 具备有效数据使用协议（DUA）或合同授权 | ACCEPT / REVIEW | 视授权范围与有效期；临近过期 → REVIEW |
| **公开数据集（Public）** | 政府开放数据、学术公开数据集（CC0 / CC-BY） | ACCEPT | 需附 `license_type` 与 `attribution_requirement` |
| **网抓 / Web Scraping** | 通过网络爬取获得，无明确合同授权 | **REJECT** | 违反 `Z-DATA-SOURCE` 合规红线 |
| **来源不明（Unknown）** | 无法追溯原始出处或所有权链断裂 | **REJECT** | `reason: provenance_unverifiable` |

**ENF 触发条件**：
- `source_type = licensed` 且 `license_expiry_days < 30` → 强制 REVIEW
- `source_type = public` 且 `attribution_requirement = true` → 标记 `needs_attribution_log`（ACCEPT 但需元数据记录）

### 3.3 敏感度分级（Sensitivity）

| 敏感度标签 | 定义 | 判定结果 | ENF 要求 |
|------------|------|----------|----------|
| **PII（个人识别信息）** | 可直接或间接识别个人身份的信息（姓名、身份证号、邮箱、电话等） | REVIEW | 强制 ENF 人工核准；需确认 `pii_handling_policy` 已签署 |
| **PHI（受保护健康信息）** | HIPAA / GDPR 定义的健康相关敏感数据 | **REJECT** | 当前 CLEAN Wave 未配置 PHI 合规 pipeline；需拆分至专项战役 |
| **金融敏感（Financial）** | 账户信息、交易记录、信用卡号等 PCI-DSS 相关数据 | REVIEW | 强制 ENF 人工核准；需确认 `financial_data_encryption_at_rest` 已启用 |
| **高商业机密（Trade Secret）** | 组织核心商业机密，泄露将造成重大损失 | REVIEW | 强制 ENF 人工核准；需 `data_classification = restricted` 标记 |
| **公开 / 内部（Public/Internal）** | 无敏感度或一般内部资料 | ACCEPT | 按常规流程处理 |

**复合敏感度判定**：
- 多标签并存时，取最高敏感度（PHI > Financial > PII > Trade Secret > Internal > Public）
- PHI 与任意其他标签并存 → 仍 REJECT（PHI 优先级最高）

### 3.4 非结构化程度（Structure）

| 结构类型 | 定义 | 判定结果 | 技术备注 |
|----------|------|----------|----------|
| **纯文本（Text-only）** | Markdown、TXT、CSV、JSON、日志文件等 | ACCEPT | 标准 CLEAN pipeline 完全支持 |
| **富文本 / 标记（Rich Markup）** | HTML、XML、LaTeX 等含结构标记的文本 | ACCEPT | 需启用 `markup_parser` 模块 |
| **图片（Image）** | PNG、JPG、GIF、WebP 等栅格图像 | REVIEW | 需 OCR / 视觉模型子 pipeline；触发资源评估 |
| **文档混合（Mixed Document）** | PDF、Word、PPT 等含文本+图像+表格 | REVIEW | 需拆解为多模态子任务；触发复杂度评估 |
| **音视频（Audio/Video）** | MP3、MP4、WAV 等 | **REJECT** | 当前 CLEAN Wave 未配置 AV 处理管道 |
| **二进制 / 未知（Binary/Unknown）** | 无法解析或识别的格式 | **REJECT** | `reason: unsupported_format` |

**复合结构判定**：
- 单一文件含多种结构类型（如扫描版 PDF 含图像层+文本层）→ 按最高复杂度处理（Mixed Document）
- 批次文件结构类型混杂 → 触发 `batch_homogeneity_check`，异质性 > 50% → REVIEW

---

## 4. 与治理对齐

### 4.1 强制 ENF / 人工核准的标签组合

| 触发条件 | 强制动作 | 元数据标记 |
|----------|----------|------------|
| `sensitivity: pii` + `source_type: licensed` | ENF 人工核准 | `enf_review_reason: pii_third_party` |
| `sensitivity: financial` + `scale.rows > 1,000,000` | ENF 人工核准 | `enf_review_reason: financial_large_scale` |
| `structure: mixed_document` + `scale.total_size > 1GB` | ENF 人工核准 + 资源预评估 | `enf_review_reason: multimodal_resource_intensive` |
| `source_type: licensed` + `license_expiry_days < 30` | ENF 人工核准 | `enf_review_reason: license_expiry_risk` |
| `structure: image` + `sensitivity: pii` | ENF 人工核准（OCR 准确性风险） | `enf_review_reason: ocr_pii_risk` |

### 4.2 直接 REJECT 的红线条件

| 条件 | REJECT 原因码 | 日志级别 | 后续动作 |
|------|---------------|----------|----------|
| `sensitivity: phi` | `phi_not_supported` | ERROR | 建议拆分至 PHI 专项战役 |
| `source_type: web_scraping` | `provenance_web_scrape` | ERROR | 建议获取正式授权后重新提交 |
| `source_type: unknown` | `provenance_unverifiable` | ERROR | 要求补充数据来源文档 |
| `structure: audio_video` | `format_av_unsupported` | ERROR | 建议提交至 AV 处理专项 |
| `structure: binary_unknown` | `format_unsupported` | WARNING | 建议转换格式后重新提交 |
| `scale.rows > 10,000,000` | `scale_exceeds_capacity` | ERROR | 建议拆分为多工单 |
| `scale.total_size > 10GB` | `scale_exceeds_capacity` | ERROR | 建议压缩或拆分 |
| `batch.files > 1,000` | `batch_size_exceeds` | WARNING | 建议分批提交 |

### 4.3 特殊豁免路径

| 豁免场景 | 条件 | 流程 | 审计要求 |
|----------|------|------|----------|
| **紧急合规清理** | 监管要求时限 < 7 天 | ACCEPT 但标记 `exemption: regulatory_deadline`，ENF 事后抽查 | 完整审计日志，事后 48h 内补核准 |
| **内部测试数据** | `purpose: internal_testing` + `scale < 10MB` | ACCEPT（跳过部分敏感检查） | 测试数据集需脱敏，标记 `synthetic: true` |
| **已审查历史工单** | 来源与结构与已通过 ENF 工单 100% 匹配 | ACCEPT，标记 `enf_exemption: historical_match` | 引用历史工单 ID，保留匹配算法版本 |

---

## 5. Scenario 判定示例

### 5.1 场景 A：小体量、低敏感、自有数据 → ACCEPT

| 字段 | 值 | 判定 |
|------|-----|------|
| `scale.rows` | 50,000 | ACCEPT |
| `scale.total_size` | 25 MB | ACCEPT |
| `source.type` | `owned` | ACCEPT |
| `source.owner` | `工程部` | ACCEPT |
| `sensitivity` | `internal` | ACCEPT |
| `structure` | `text_only` | ACCEPT |

**综合判定**：ACCEPT  
**工单 ID 示例**：`CLEAN-2026-0604-001`  
**排程优先级**：`normal`  
**预计处理时间**：< 2 小时

---

### 5.2 场景 B：大体量、高敏感、第三方授权 → REVIEW

| 字段 | 值 | 判定 |
|------|-----|------|
| `scale.rows` | 5,000,000 | REVIEW（行数 > 1M） |
| `scale.total_size` | 3.5 GB | REVIEW（大小 > 1GB） |
| `batch.files` | 450 | ACCEPT |
| `source.type` | `licensed` | ACCEPT |
| `source.license_expiry_days` | 45 | ACCEPT |
| `sensitivity` | `pii` + `financial` | REVIEW（PII 需 ENF） |
| `structure` | `mixed_document` | REVIEW（多模态需资源评估） |

**复合判定**：REVIEW（多维度触发）  
**工单 ID 示例**：`CLEAN-2026-0604-002`  
**ENF 队列**：`high_priority`（金融+PII）  
**人工审核要点**：
1. 确认 `license_expiry_days` 是否在项目周期内
2. 确认 `financial_data_encryption_at_rest` 已启用
3. 评估 OCR 准确性对 PII 识别的影响
4. 确认大规模处理的资源预留

---

### 5.3 场景 C：高风险来源 → REJECT

| 字段 | 值 | 判定 |
|------|-----|------|
| `scale.rows` | 200,000 | ACCEPT |
| `scale.total_size` | 150 MB | ACCEPT |
| `source.type` | `web_scraping` | **REJECT** |
| `source.url_pattern` | `*.social-media.com/posts/*` | **REJECT** |
| `sensitivity` | `pii` | 不适用 |
| `structure` | `mixed_document` | 不适用 |

**综合判定**：REJECT  
**工单 ID 示例**：`CLEAN-2026-0604-003`  
**拒绝原因码**：`provenance_web_scrape`  
**返回建议**：
> 当前工单数据来源为网络爬取（`web_scraping`），违反 `HARNESS_CONSTITUTION.md` §7 数据来源合规红线。建议：
> 1. 获取数据所有者正式授权（`licensed`）
> 2. 或改用组织自有数据（`owned`）
> 3. 或提交至公开数据集认证流程（`public`）
> 
> 修正后可重新提交至 CLEAN Wave。

---

### 5.4 场景 D：敏感类型不支持 → REJECT

| 字段 | 值 | 判定 |
|------|-----|------|
| `scale.rows` | 10,000 | ACCEPT |
| `scale.total_size` | 5 MB | ACCEPT |
| `source.type` | `owned` | ACCEPT |
| `sensitivity` | `phi` | **REJECT** |
| `structure` | `text_only` | ACCEPT |
| `phi_subtype` | `medical_records` | **REJECT** |

**综合判定**：REJECT  
**工单 ID 示例**：`CLEAN-2026-0604-004`  
**拒绝原因码**：`phi_not_supported`  
**返回建议**：
> 当前工单包含 PHI（受保护健康信息），超出 CLEAN Wave 6 合规处理能力。建议：
> 1. 拆分至 `PHI-CLEAN-WAVE` 专项战役（需 HIPAA 合规环境）
> 2. 或先进行去标识化处理（de-identification），将敏感度降级至 `internal` 后重新提交

---

## 6. 判定流程图（文本描述）

```
Intake Questionnaire 提交
        │
        ▼
┌─────────────────────┐
│ 来源合规性检查       │
│ - web_scraping?     │──YES──► REJECT (provenance_web_scrape)
│ - unknown?          │──YES──► REJECT (provenance_unverifiable)
└─────────────────────┘
        │ NO
        ▼
┌─────────────────────┐
│ 敏感度检查           │
│ - phi?              │──YES──► REJECT (phi_not_supported)
│ - pii?              │──YES──► 标记 enf_review_reason
│ - financial?        │──YES──► 标记 enf_review_reason
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ 结构类型检查         │
│ - audio_video?      │──YES──► REJECT (format_av_unsupported)
│ - binary_unknown?   │──YES──► REJECT (format_unsupported)
│ - image?            │──YES──► 标记 enf_review_reason (ocr评估)
│ - mixed_document?   │──YES──► 标记 enf_review_reason (资源评估)
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ 规模检查             │
│ - rows > 10M?       │──YES──► REJECT (scale_exceeds_capacity)
│ - size > 10GB?      │──YES──► REJECT (scale_exceeds_capacity)
│ - rows > 1M?        │──YES──► 标记 enf_review_reason (大规模)
│ - size > 1GB?       │──YES──► 标记 enf_review_reason (大容量)
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ 豁免路径检查         │
│ - 紧急合规?         │──YES──► ACCEPT (标记 exemption)
│ - 历史匹配?         │──YES──► ACCEPT (标记 enf_exemption)
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ 最终判定             │
│ enf_review_reason   │──非空──► REVIEW
│ 存在?               │
└─────────────────────┘
        │ 空
        ▼
      ACCEPT
```

---

## 7. 结构化输出契约

判定结果必须返回结构化 `dict`，供 `task_routing.py` 消费：

```json
{
  "ok": true,
  "eligibility": "ACCEPT | REVIEW | REJECT",
  "reason_code": "scale_exceeds_capacity | provenance_web_scrape | phi_not_supported | ...",
  "human_readable": "工单规模超过当前处理能力上限（10M 行 / 10GB）",
  "dimensions": {
    "scale": { "status": "ACCEPT | REVIEW | REJECT", "details": "rows: 5000000, size: 3.5GB" },
    "provenance": { "status": "ACCEPT", "details": "licensed, expiry: 45d" },
    "sensitivity": { "status": "REVIEW", "flags": ["pii", "financial"] },
    "structure": { "status": "REVIEW", "type": "mixed_document" }
  },
  "enf_requirements": {
    "needs_review": true,
    "reasons": ["financial_large_scale", "multimodal_resource_intensive"],
    "priority": "high | normal | low"
  },
  "exemption": {
    "applied": false,
    "type": null
  },
  "next_action": {
    "for_reject": "请拆分为多个子工单重新提交",
    "for_review": "进入 ENF 复核队列，预计 24h 内人工响应",
    "for_accept": "进入 Wave 6 排程队列，预计 2h 内启动"
  }
}
```

---

## 8. 验收与验证

### 8.1 单元测试覆盖

| 测试套件 | 覆盖场景数 | 关键断言 |
|----------|-----------|----------|
| `test_eligibility_scale` | 8 | 边界值（1M/10M 行，1GB/10GB）判定正确 |
| `test_eligibility_provenance` | 6 | web_scraping / unknown 直接 REJECT |
| `test_eligibility_sensitivity` | 7 | PHI 直接 REJECT；PII + Financial 强制 ENF |
| `test_eligibility_structure` | 6 | AV / Binary 直接 REJECT；Mixed 触发 REVIEW |
| `test_eligibility_composite` | 10 | 多维度复合场景判定 |
| `test_eligibility_exemption` | 4 | 紧急合规 / 历史匹配豁免路径 |

### 8.2 集成验证命令

```bash
# 验证场景 A（ACCEPT）
python -m eligibility.check --scenario small_low_risk_owned

# 验证场景 B（REVIEW）
python -m eligibility.check --scenario large_sensitive_licensed

# 验证场景 C（REJECT）
python -m eligibility.check --scenario web_scrape_pii

# 全量回归
python -m unittest tests.test_clean_eligibility -v
```

---

## 9. 演进路线

| 版本 | 目标 | 新增内容 |
|------|------|----------|
| **v0.2** | 精细化结构判定 | 增加 `structure.homogeneity_score` 计算，批次异质性量化 |
| **v0.3** | 动态阈值 | 引入 `capacity_utilization` 动态调整规模阈值（忙时收紧） |
| **v0.4** | PHI 专项支持 | 配合 `PHI-CLEAN-WAVE` 上线，移除 PHI 的 REJECT，改为专项路由 |
| **v0.5** | 机器学习辅助 | 引入历史工单结果训练 `enf_review_outcome_predictor`，优化人工审核效率 |

---

## 10. 与相关文档对齐

| 文档 | 关系 | 关键对齐点 |
|------|------|-----------|
| `WAVE6_CLEAN_PRODUCT_MATRIX_v0.1.md` | 上游 | 输入：产品矩阵定义的战役范围；输出：本产品内工单准入规则 |
| `WAVE6_CLEAN_DELIVERABLE_TEMPLATES_v0.1.md` | 并行 | 共享 `sensitivity` / `structure` 枚举定义 |
| `HARNESS_CONSTITUTION.md` §7 | 治理母本 | 禁区类型 `Z-DATA-SOURCE` / `Z-SENSITIVITY-PHI` 引用 |
| `ENGINEERING_CONTRACT.md` 附录 B | 输出契约 | 判定结果 `dict` 形状符合结构化回传规范 |
| `04_Workflows/TASK_ROUTING.md` | 下游消费 | 判定结果作为 `route_task()` 的 `eligibility_check` 输入 |

---

## 11. 修订历史

| 版本 | 日期 | 修订者 | 摘要 |
|------|------|--------|------|
| v0.1 | 2026-06-04 | HQ-Governance-Worker | 初始草案：三决策结果、四判定维度、三场景示例 |

---

## 附录 A：判定速查表

| 场景速写 | 规模 | 来源 | 敏感 | 结构 | 判定 | ENF |
|----------|------|------|------|------|------|-----|
| 小自有内部文本 | 小 | 自有 | 内部 | 文本 | ACCEPT | 否 |
| 大授权金融混合 | 大 | 授权 | 金融 | 混合 | REVIEW | 是 |
| 网抓任意任意 | 任意 | 网抓 | 任意 | 任意 | REJECT | 否 |
| 小自有 PHI 文本 | 小 | 自有 | PHI | 文本 | REJECT | 否 |
| 中授权 PII 图片 | 中 | 授权 | PII | 图片 | REVIEW | 是 |
| 大自有商业机密 | 大 | 自有 | 商业 | 文本 | REVIEW | 是 |
| 紧急监管小文本 | 小 | 自有 | 内部 | 文本 | ACCEPT* | 事后 |

\* 标记豁免
