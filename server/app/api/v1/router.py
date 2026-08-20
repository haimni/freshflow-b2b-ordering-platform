"""Collect all version 1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1.routes import (
    admin_catalog,
    admin_orders,
    admin_users,
    auth,
    catalog,
    customer_catalog,
    customer_orders,
    health,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(catalog.router)
api_router.include_router(customer_catalog.router)
api_router.include_router(customer_orders.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_orders.router)
api_router.include_router(admin_catalog.router)