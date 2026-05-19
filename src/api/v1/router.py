from fastapi import APIRouter
from api.v1.endpoints import articles

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(articles.router, prefix="/articles", tags=["Articles V1"])