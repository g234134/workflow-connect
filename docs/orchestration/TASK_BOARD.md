# 活任務板（TASK_BOARD）



> **維護者**：Cursor-Orchestrator（主）、你（拍板後更新）  

> **最後更新**：2026-06-02（T4c checkpoint）  

> **模板**：見 [`TASK_BOARD_TEMPLATE.md`](./TASK_BOARD_TEMPLATE.md)



---



## 當前階段



**階段名稱**：多 Agent 總調度骨架 — 小龍蝦白名單 smoke（T4 完成）  

**階段目標**：跑通 小龍蝦 白名單只讀 smoke → SEGMENT → Orchestrator 收尾全鏈路  

**階段負責**：Cursor-Orchestrator



---



### T1 — 建立 orchestration 文件骨架（主任務）



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T1 |

| **描述** | 在 `docs/orchestration/` 建立規則、模板、活文件、Orchestrator prompt |

| **負責角色** | Cursor-Orchestrator（協調）+ Cursor-Worker（若需補檔） |

| **狀態** | 已完成 |

| **依賴** | - |

| **備註** | 本輪施工票；不碰 core／agents runtime |

| **子任務** | T1a |



---



### T1a — 撰寫 AGENT_RULES / 模板 / README / ORCHESTRATOR_PROMPT



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T1a |

| **描述** | 完成全部 markdown 與可複製示例 |

| **負責角色** | Cursor-Worker |

| **狀態** | 已完成 |

| **依賴** | - |

| **備註** | SEGMENT 可記於 `segments/T1a__seg1__2026-06-02.md`（選填） |

| **子任務** | - |



---



### T2 — 試跑第一輪真實派工



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T2 |

| **描述** | 指定小實作任務，驗證 Orchestrator 拆段 + Worker 新 chat + SEGMENT |

| **負責角色** | Cursor-Orchestrator |

| **狀態** | 已完成 |

| **依賴** | T1 |

| **備註** | T2a 於 2026-06-02 完成；活文件於 T3c 對帳補正 |

| **子任務** | T2a |



---



### T2a — README §1 新增 T2 試跑 bullet + SEGMENT



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T2a |

| **描述** | 在 README §1 末尾新增 T2 試跑紀錄一行；建立 SEGMENT |

| **負責角色** | Cursor-Worker |

| **狀態** | 已完成 |

| **依賴** | T2 |

| **備註** | SEGMENT：`segments/T2a__seg1__2026-06-02.md` |

| **子任務** | - |



---



### T3 — BRIEF → Worker → SEGMENT 鏈路驗證（Hermes 降級版）



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T3 |

| **描述** | 驗證 BRIEF → Worker 施工 → SEGMENT → Orchestrator 收尾；README 補 T2 成果說明 |

| **負責角色** | Cursor-Orchestrator（T3a/T3c）+ Cursor-Worker（T3b） |

| **狀態** | 已完成 |

| **依賴** | T2 |

| **備註** | T3a BRIEF 由 Cursor-Orchestrator 代 Hermes（Hermes 16K vs 64K 暫不可用）；BRIEF_ID：`T3_BRIEF_README_ENHANCE_V1` |

| **子任務** | T3a、T3b、T3c |



---



### T3a — 產出 BRIEF（Cursor 代 Hermes）



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T3a |

| **描述** | 產出 `T3_BRIEF_README_ENHANCE_V1`，供 T3b Worker 施工 |

| **負責角色** | Cursor-Orchestrator（代 Hermes） |

| **狀態** | 已完成 |

| **依賴** | T3 |

| **備註** | BRIEF 於 Orchestrator chat 產出並經尚書省確認；未存 `briefs/`（可下一階段補） |

| **子任務** | - |



---



### T3b — 依 BRIEF 修改 README + SEGMENT



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T3b |

| **描述** | README §1 補「T2 試跑成果與後續用途」；建立 SEGMENT |

| **負責角色** | Cursor-Worker |

| **狀態** | 已完成 |

| **依賴** | T3a |

| **備註** | SEGMENT：`segments/T3b__seg1__2026-06-02.md` |

| **子任務** | - |



---



### T3c — Checkpoint：TASK_BOARD / HANDOFF 對帳收尾



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T3c |

| **描述** | 對帳 T2/T2a 狀態；更新活文件；記錄 Hermes 降級與 T3 鏈路結論 |

| **負責角色** | Cursor-Orchestrator |

| **狀態** | 已完成 |

| **依賴** | T3b |

| **備註** | 本輪 checkpoint |

| **子任務** | - |



---



### T4 — 小龍蝦白名單 smoke 鏈路驗證



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T4 |

| **描述** | 驗證 Orchestrator → 小龍蝦只讀 smoke → SEGMENT → Orchestrator 收尾全鏈路 |

| **負責角色** | Cursor-Orchestrator（T4c）+ 小龍蝦（T4a） |

| **狀態** | 已完成 |

| **依賴** | T3 |

| **備註** | 白名單只讀 smoke；非 runner 級 keys smoke |

| **子任務** | T4a、T4c |



---



### T4a — 小龍蝦只讀 smoke 掃描 + SEGMENT



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T4a |

| **描述** | 只讀掃描 `docs/orchestration/`，產 smoke 摘要與 SEGMENT；零改動 README／TASK_BOARD／HANDOFF／AGENT_RULES |

| **負責角色** | 小龍蝦 |

| **狀態** | 已完成 |

| **依賴** | T4 |

| **備註** | SEGMENT：`segments/T4a__exec1__2026-06-02__SEGMENT.md`；摘要：`segments/T4a__exec1__2026-06-02.md`；seg-1：`segments/T4a__seg1__2026-06-02.md`；ops 快照：`ops/T4a_smoke_snapshot_2026-06-02.md` |

| **子任務** | - |



---



### T4c — Checkpoint：TASK_BOARD / HANDOFF 對帳收尾



| 欄位 | 內容 |

|------|------|

| **TASK_ID** | T4c |

| **描述** | 對帳 T4／T4a 狀態；更新活文件；記錄小龍蝦 smoke 鏈路結論 |

| **負責角色** | Cursor-Orchestrator（建議稿）+ Cursor-Worker（T4d 落檔） |

| **狀態** | 已完成 |

| **依賴** | T4a |

| **備註** | 建議稿於 Orchestrator chat；活文件落檔票 T4d；SEGMENT：`segments/T4d__seg1__2026-06-02.md` |

| **子任務** | - |



---



## 歷史階段（封存參考）



*尚無。*


