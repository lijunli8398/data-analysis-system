"""
项目管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Project, User
from app.routers.auth import get_current_user, get_current_admin
from app.utils.schemas import (
    ProjectCreate, ProjectUpdate, ProjectInfo, ProjectList, Message
)

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.get("", response_model=ProjectList)
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目列表"""
    query = select(Project)
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分页查询
    result = await db.execute(query.offset(skip).limit(limit))
    projects = result.scalars().all()
    
    return ProjectList(
        total=total or 0,
        projects=[ProjectInfo.model_validate(p) for p in projects]
    )


@router.get("/{project_id}", response_model=ProjectInfo)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单个项目详情"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    return ProjectInfo.model_validate(project)


@router.post("", response_model=ProjectInfo)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建项目（管理员）"""
    project = Project(
        name=project_data.name,
        description=project_data.description,
        created_by=current_user.id
    )
    
    db.add(project)
    await db.flush()
    await db.refresh(project)
    
    return ProjectInfo.model_validate(project)


@router.put("/{project_id}", response_model=ProjectInfo)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新项目（管理员）"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    if project_data.name:
        project.name = project_data.name
    if project_data.description:
        project.description = project_data.description
    
    await db.flush()
    await db.refresh(project)
    
    return ProjectInfo.model_validate(project)


@router.delete("/{project_id}", response_model=Message)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除项目（管理员）"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    await db.delete(project)
    
    return Message(message=f"项目 {project.name} 已删除")