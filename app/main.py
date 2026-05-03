# app/main.py
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # 先載入 env，確保後續 import 的 module 能讀到 OPENAI_API_KEY 等環境變數

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api import router  # noqa: E402
from app.utils.logger import setup_logger  # noqa: E402
from app.utils.openapi_utils import build_openapi_schema  # noqa: E402

logger = setup_logger("uvicorn.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用的生命週期管理（啟動 / 關閉階段）"""
    logger.info("🚀 Starting application lifespan...")
    # await init_core_mysql()
    # await init_qdrant()

    # await write_data()

    logger.info("✅ Application **Startup** complete.")
    yield  # --- 應用運行中 ---

    # 關閉階段
    logger.info("🧹 Shutting down resources...")
    logger.info("✅ Application **Shutdown** complete.")


def create_app() -> FastAPI:
    """建立 FastAPI Application"""
    env = os.getenv("APP_ENV", "dev")
    enable_docs = env != "prod"

    # FastAPI 應用初始化
    app = FastAPI(
        title="SQLAgent API",
        version="1.5.0",
        description="SQLAgent API",
        lifespan=lifespan,
        docs_url=None if not enable_docs else "/docs",
        redoc_url=None if not enable_docs else "/redoc",
        openapi_url=None if not enable_docs else "/openapi.json",
    )

    # 設定 CORS
    allow_origins = os.getenv("ALLOW_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 載入 API 路由
    app.include_router(router)

    # 自訂 OpenAPI Schema
    app.openapi = lambda: build_openapi_schema(
        app, "SQLAgent API", "1.5.0", "SQLAgent API"
    )

    return app


# --- App 實例 ---
app = create_app()
