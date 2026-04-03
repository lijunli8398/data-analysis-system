"""
FastAPI主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
from pathlib import Path

from app.config import get_settings, ensure_directories
from app.database import init_db, AsyncSessionLocal
from app.models import User
from app.utils.auth import hash_password
from app.routers import (
    auth_router,
    projects_router,
    upload_router,
    reports_router,
    dashboards_router,
    chat_router,
    tasks_router
)

settings = get_settings()

# 前端静态文件路径
FRONTEND_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 启动数据分析系统...")
    
    # 确保目录存在
    ensure_directories()
    
    # 初始化数据库
    await init_db()
    
    # 创建初始用户
    await create_initial_users()
    
    print("✅ 系统启动完成")
    
    yield
    
    # 关闭时
    print("👋 关闭数据分析系统...")


async def create_initial_users():
    """创建初始用户"""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        
        # 检查是否已有用户
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            # 创建管理员
            admin = User(
                username="admin",
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role="admin"
            )
            db.add(admin)
            
            # 创建查看者
            viewer = User(
                username="viewer",
                password_hash=hash_password(settings.VIEWER_PASSWORD),
                role="viewer"
            )
            db.add(viewer)
            
            await db.commit()
            
            print(f"✅ 已创建初始用户:")
            print(f"   - 管理员: admin / {settings.ADMIN_PASSWORD}")
            print(f"   - 查看者: viewer / {settings.VIEWER_PASSWORD}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="基于LLM的教育数据分析系统，支持报告生成、看板生成和智能问数",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（添加/api前缀）
app.include_router(auth_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboards_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 挂载前端静态文件（放到最后，作为fallback）
if FRONTEND_DIST.exists():
    # 挂载静态资源目录
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
    
    @app.get("/")
    async def serve_index():
        """服务前端首页"""
        return FileResponse(FRONTEND_DIST / "index.html")
    
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        """SPA路由fallback"""
        # 如果是API路径，跳过
        if path.startswith("api/") or path.startswith("docs") or path.startswith("openapi"):
            return None
        # 其他路径返回index.html（SPA路由）
        file_path = FRONTEND_DIST / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root():
        """根路径（前端未构建时）"""
        return {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "docs": "/docs",
            "status": "running"
        }