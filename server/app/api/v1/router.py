"""Collect all version 1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1.routes import auth, catalog, health

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(catalog.router)