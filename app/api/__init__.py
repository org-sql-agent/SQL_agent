
# app/api/__init__.py
from fastapi import APIRouter

from app.api.routes.health import health
from app.api.routes.service import service


router = APIRouter()

router.include_router(health.router, tags=["Health"])
router.include_router(service.router, tags=["Service"])