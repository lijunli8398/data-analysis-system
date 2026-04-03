"""
应用模块初始化
"""
from app.main import app
from app.config import get_settings
from app.database import get_db

__all__ = ["app", "get_settings", "get_db"]