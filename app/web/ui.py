import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

# Docker 內部後端位址（container-to-container）
BACKEND_URL = os.getenv("SERVICE_API_URL", "http://localhost:8080/Service")

app = FastAPI()


@app.get("/config.js", response_class=Response)
def config_js():
    """前端固定打 /api/service（UI server proxy），不暴露後端 hostname。"""
    return Response(
        content="const SERVICE_API_URL = '/api/service';",
        media_type="application/javascript",
    )


@app.post("/api/service")
async def proxy_service(request: Request):
    """
    把瀏覽器的 request 轉發給後端 FastAPI。
    解決瀏覽器無法解析 Docker 內部 hostname（http://api:8080）的問題。
    """
    body = await request.json()
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(BACKEND_URL, json=body)
        resp.raise_for_status()
        return resp.json()


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
