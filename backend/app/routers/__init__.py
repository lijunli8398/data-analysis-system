"""
路由模块初始化
"""
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.upload import router as upload_router
from app.routers.reports import router as reports_router
from app.routers.dashboards import router as dashboards_router
from app.routers.chat import router as chat_router
from app.routers.tasks import router as tasks_router

__all__ = [
    "auth_router",
    "projects_router",
    "upload_router",
    "reports_router",
    "dashboards_router",
    "chat_router",
    "tasks_router",
]