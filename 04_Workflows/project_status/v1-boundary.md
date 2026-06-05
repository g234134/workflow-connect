# Gov Core System — V1 Boundary

## V1 已完成

- **LangGraph 編排**：`ask`、`ingest_verify` 流程已落地並可運行。
- **GraphRAG**：後端與 job flow 已整合至系統鏈路。
- **資料層**：PostgreSQL、Qdrant 已接入並用於既有流程。
- **可觀測性**：Langfuse 已接入。
- **UI**：Workbench（`gov-core-workbench.html`）已提供操作介面。
- **FastAPI 對外介面**：`GET /healthz`、`POST /api/ask`、`POST /api/ingest-verify`、`POST /api/graphrag/run` 已交付。
- **E2E 驗收**：全鏈路第一版與 live API 接通之驗收已通過。
- **V1 收尾項**：ENV-1、DEPLOY-1、SEC-1、OPS-1 已完成。

## 不再列為 V1 缺口

- **環境補齊（ENV-1）**：視為 V1 收尾已完成；不得再以「環境沒齊」回溯為 V1 未完成。
- **部署與啟動方式（DEPLOY-1）**：可重現之部署／啟動已納入 V1 收尾；不得再當成 V1 缺口。
- **安全與營運基線（SEC-1、OPS-1）**：已定義之安全與營運收尾已完成；不得單獨拆回當「V1 還沒做完」。
- **CORS 可配置**：已完成；不得再以 CORS 相關事項回溯為 V1 未完成。
- **Smoke test**：已完成；不得再以缺少 smoke 測試回溯為 V1 未完成。
- **Live API 對接**：E2E 已含 live API；不得以「還要對接真實環境」重新定義 V1 未完成。
- **上述項目若未來要升級或擴充**：屬新案（V2／部署／維運），不得改寫「V1 曾未完成」的敘述。

## 後續歸類為 V2 / 部署 / 維運

以下為代表性方向，**不是 V1 缺口**，須另立 V2、部署或維運任務／版本規劃處理：

- **固定環境部署**：正式機、reverse proxy、TLS、網域與對外服務形態。
- **存取控制**：認證、RBAC、rate limit、API key 等產品級 API 治理。
- **監控深化**：更完整的 monitoring、alerting、線上評測（evaluation）體系。
- **產品化與營運擴充**：多租戶、計費、營運儀表板、流程與權限之產品化延伸。
- **GraphRAG 演算法深化**：索引策略、檢索品質、圖結構與 pipeline 之進階優化。
- **效能與容量**：大規模負載、快取策略、成本與 SLO 導向之工程。

## Baseline Rule

- **V1 baseline 已凍結**：以上「V1 已完成」與「不再列為 V1 缺口」所列範圍，即 Gov Core System V1 的完成定義與封版邊界。
- **禁止回溯改寫 V1 完成定義**：後續新增或變更需求，不得將既有已收尾項目重新標記為「V1 未完成」以規避版本立案。
- **新工作須另案追蹤**：凡超出本文件 V1 邊界者，應以 **V2 功能** 或 **部署／維運專案** 之任務流、版本與驗收單獨立案；不得併入 V1 baseline 重新驗收範圍。
