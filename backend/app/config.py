"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """应用配置"""
    # 应用基础配置
    APP_NAME: str = "数据分析系统"
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # 千问API配置
    QWEN_API_KEY: str = ""
    QWEN_MODEL_PLUS: str = "qwen-plus"
    QWEN_MODEL_TURBO: str = "qwen-turbo"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/app.db"
    
    # 文件存储路径
    UPLOAD_DIR: str = "./data/uploads"
    REPORT_DIR: str = "./data/reports"
    DASHBOARD_DIR: str = "./data/dashboards"
    RESULT_DIR: str = "./data/results"
    
    # 初始用户密码
    ADMIN_PASSWORD: str = "admin123"
    VIEWER_PASSWORD: str = "viewer123"
    
    # JWT配置
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（缓存）"""
    return Settings()


def ensure_directories():
    """确保所有存储目录存在"""
    settings = get_settings()
    dirs = [
        settings.UPLOAD_DIR,
        settings.REPORT_DIR,
        settings.DASHBOARD_DIR,
        settings.RESULT_DIR,
        "./data"  # 数据库目录
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)