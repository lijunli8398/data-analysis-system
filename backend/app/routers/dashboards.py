"""
看板管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import os
from app.database import get_db
from app.models import Dashboard, Project, DataSource, User
from app.routers.auth import get_current_user, get_current_admin
from app.utils.schemas import DashboardGenerate, DashboardInfo, DashboardList, Message
from app.services.task_service import AsyncTaskManager

router = APIRouter(prefix="/dashboards", tags=["看板管理"])


@router.get("", response_model=DashboardList)
async def list_dashboards(
    project_id: int = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取看板列表"""
    query = select(Dashboard)
    
    if project_id:
        query = query.where(Dashboard.project_id == project_id)
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分页查询
    result = await db.execute(query.offset(skip).limit(limit).order_by(Dashboard.created_at.desc()))
    dashboards = result.scalars().all()
    
    return DashboardList(
        total=total or 0,
        dashboards=[DashboardInfo.model_validate(d) for d in dashboards]
    )


@router.get("/{dashboard_id}", response_model=DashboardInfo)
async def get_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取看板详情"""
    result = await db.execute(select(Dashboard).where(Dashboard.id == dashboard_id))
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="看板不存在"
        )
    
    return DashboardInfo.model_validate(dashboard)


@router.get("/{dashboard_id}/view", response_class=HTMLResponse)
async def view_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """查看看板内容（HTML）"""
    result = await db.execute(select(Dashboard).where(Dashboard.id == dashboard_id))
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="看板不存在"
        )
    
    if not os.path.exists(dashboard.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="看板文件不存在"
        )
    
    with open(dashboard.file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return HTMLResponse(content=html_content)


@router.get("/{dashboard_id}/download")
async def download_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """下载看板文件"""
    result = await db.execute(select(Dashboard).where(Dashboard.id == dashboard_id))
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="看板不存在"
        )
    
    if not os.path.exists(dashboard.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="看板文件不存在"
        )
    
    return FileResponse(
        dashboard.file_path,
        media_type="text/html",
        filename=dashboard.title + ".html"
    )


@router.post("/generate", response_model=Message)
async def generate_dashboard(
    dashboard_data: DashboardGenerate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """生成看板（管理员）- 创建异步任务"""
    
    # 验证项目存在
    result = await db.execute(select(Project).where(Project.id == dashboard_data.project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查是否有报告生成的结果数据
    result_dir = os.path.join("./data/results", f"project_{dashboard_data.project_id}")
    data_dir = os.path.join(result_dir, "data")
    
    if not os.path.exists(data_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目没有分析结果数据，请先生成报告"
        )
    
    # 创建异步任务
    task_manager = AsyncTaskManager(db, background_tasks)
    task_id = await task_manager.create_task(
        task_type="dashboard",
        project_id=dashboard_data.project_id,
        params={
            "title": dashboard_data.title,
            "result_dir": data_dir  # 传递data目录
        },
        created_by=current_user.id
    )
    
    return Message(message=f"看板生成任务已创建，任务ID: {task_id}")


@router.delete("/{dashboard_id}", response_model=Message)
async def delete_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除看板（管理员）"""
    result = await db.execute(select(Dashboard).where(Dashboard.id == dashboard_id))
    dashboard = result.scalar_one_or_none()
    
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="看板不存在"
        )
    
    # 删除物理文件
    if os.path.exists(dashboard.file_path):
        os.remove(dashboard.file_path)
    
    await db.delete(dashboard)
    
    return Message(message=f"看板 {dashboard.title} 已删除")