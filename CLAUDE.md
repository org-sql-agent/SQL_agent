# SQL Agent — 專案導覽

Titanic 資料集的 AI 問答系統。使用者用自然語言提問，後端透過 LLM + tool call 查詢 SQLite、訓練 ML 模型預測，並回傳 ECharts 圖表或文字摘要。

## 架構概覽

```
使用者
  │
  ▼
Streamlit UI (app/web/ui.py, port 1111)
  │  POST /Service  { text, history: llm_history }
  ▼
FastAPI (app/main.py, port 8080)
  │
  ├─ Router  (app/api/routes/)
  │    └─ agent.py  →  AgentService.run()
  │
  ├─ Service (app/services/)
  │    ├─ agent_service.py   LLM 編排 + tool dispatch
  │    ├─ chart_service.py   ECharts 生成 / 文字摘要
  │    └─ compact/           對話歷史壓縮（超過 3000 token 觸發）
  │
  └─ DAO (app/db/dao/)
       └─ titanic_dao.py     SQLite SELECT + sklearn 即時訓練預測
```

**依賴方向：Router → Service → DAO（不可反向）**

## Tech Stack

| 項目 | 技術 |
|---|---|
| API | FastAPI + Uvicorn |
| LLM | OpenAI gpt-4o（tool calling） |
| DB | SQLite（`model/titanic.db`） |
| ML | scikit-learn（每次請求即時訓練，無持久化模型） |
| Frontend | Streamlit + streamlit-echarts |
| 套件管理 | Poetry（Docker 用 `requirements.txt`） |
| CI | GitHub Actions（lint + import check） |

## 主要檔案

| 檔案 | 職責 |
|---|---|
| `app/api/routes/agent.py` | POST `/Service` 入口，組裝 service singleton |
| `app/api/routes/health.py` | GET `/` health check |
| `app/api/schemas/agent.py` | `InputModel`、`OutputModel`、`HistoryMessage` |
| `app/services/agent_service.py` | LLM 呼叫、tool dispatch、`_handle_query_database`、`_handle_predict_feature` |
| `app/services/chart_service.py` | `generate_echarts`、`generate_summary`、`generate_prediction_explanation`、`generate_feature_importance_chart` |
| `app/services/compact/history_compactor.py` | `maybe_compact()`：token 估算，超過門檻就壓縮舊對話 |
| `app/db/dao/titanic_dao.py` | `TitanicDAO.query(sql)`、`TitanicDAO.predict(params)` |
| `app/config/settings.py` | 所有路徑常數 + `OPENAI_MODEL` |
| `app/utils/json_utils.py` | `clean_markdown_json()`：清除 LLM 回傳的 markdown code block |
| `app/web/ui.py` | Streamlit frontend，**盡量不動** |
| `app/db/init_db.py` | 把 `data/train.csv` 匯入 `model/titanic.db` |

## API 合約

### POST `/Service`

```json
// Request
{
  "text": "畫出各艙等生還率",
  "history": []   // llm_history（backend 壓縮後版本，非 display_history）
}

// Response — 文字
{ "data": { "type": "text", "content": "..." }, "llm_history": [...] }

// Response — 圖表
{ "data": { "type": "echarts", "content": "{...}", "summary": "..." }, "llm_history": [...] }
```

**`llm_history` 設計**：前端維護兩份 history：
- `display_history`：完整紀錄，只用於畫面渲染，永不刪減
- `llm_history`：送給後端的壓縮版，後端 compact 後回傳，前端存下來直接送下次請求

### GET `/`

```json
{ "reply": "pong" }
```

## 常用指令

```bash
# 初始化 DB（首次或資料更新後）
poetry run python -m app.db.init_db

# 啟動開發環境
docker compose up --build

# 只跑後端
poetry run uvicorn app.main:app --reload --port 8080

# 只跑前端
poetry run streamlit run app/web/ui.py --server.port 1111

# Lint
make lint

# 格式化
make format

# 更新 requirements.txt（修改 pyproject.toml 後）
make export-requirements
```

## 重要限制與注意事項

1. **API 路徑 `/Service` 不能改**：前端 hardcode 呼叫這個路徑
2. **SQLite 同步存取**：不用 async，route 以 `run_in_threadpool` 包住 service.run()
3. **module-level singleton**：`_agent_service` 在 `routes/agent.py` import 時建立，`main.py` 必須先呼叫 `load_dotenv()` 再 import router
4. **只允許 SELECT**：`TitanicDAO.query()` 有 SQL 白名單驗證，blocked keywords 包含 DROP/DELETE/UPDATE 等
5. **ML 模型不持久化**：`titanic_model.pkl` 目前未使用，每次請求即時 fit
6. **`data/` 不在 `.dockerignore`**：train.csv 需要在 container 內供 init_db 使用

## 新增功能的正確方式

新增一個 tool（例如讓 agent 能做統計檢定）：

1. `app/db/dao/titanic_dao.py` — 加資料存取方法
2. `app/services/chart_service.py` — 加對應的說明/圖表生成（若需要）
3. `app/services/agent_service.py` — 在 `_TOOLS` 加 tool definition、在 `run()` 的 dispatch 加 handler
4. `app/api/routes/agent.py` — 通常不需改動

新增一個 API endpoint：

1. `app/api/schemas/` — 加 request/response schema
2. `app/services/` — 加對應 service
3. `app/api/routes/` — 加薄 route，只做 HTTP 解析
4. `app/api/__init__.py` — include 新 router
