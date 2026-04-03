"""
任务管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Task, User
from app.routers.auth import get_current_user
from app.utils.schemas import TaskInfo, Message

router = APIRouter(prefix="/tasks", tags=["任务管理"])


@router.get("/{task_id}", response_model=TaskInfo)
async def get_task_status(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务状态"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return TaskInfo.model_validate(task)


@router.get("", response_model=list[TaskInfo])
async def list_tasks(
    project_id: int = None,
    status: str = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    query = select(Task)
    
    if project_id:
        query = query.where(Task.project_id == project_id)
    if status:
        query = query.where(Task.status == status)
    
    result = await db.execute(query.offset(skip).limit(limit).order_by(Task.created_at.desc()))
    tasks = result.scalars().all()
    
    return [TaskInfo.model_validate(t) for t in tasks]