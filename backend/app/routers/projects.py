"""
项目管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Project, User, DataSource
from app.routers.auth import get_current_user, get_current_admin
from app.utils.schemas import (
    ProjectCreate, ProjectUpdate, ProjectInfo, ProjectList, Message
)
from pydantic import BaseModel
from typing import List, Optional
import os

router = APIRouter(prefix="/projects", tags=["项目管理"])


class DataSourceInfo(BaseModel):
    """数据源信息"""
    id: int
    filename: str
    file_size: Optional[int] = None
    row_count: Optional[int] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProjectInfoWithData(ProjectInfo):
    """项目信息（含数据文件数量）"""
    data_count: int = 0


class DataSourceListResponse(BaseModel):
    """数据源列表响应"""
    files: List[DataSourceInfo]


@router.get("")
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目列表"""
    # 查询项目及其数据文件数量
    query = select(
        Project,
        func.count(DataSource.id).label('data_count')
    ).outerjoin(DataSource).group_by(Project.id)
    
    # 统计总数
    count_query = select(func.count()).select_from(Project)
    total = await db.scalar(count_query)
    
    # 分页查询
    result = await db.execute(query.offset(skip).limit(limit))
    rows = result.all()
    
    projects = []
    for row in rows:
        project = row[0]
        data_count = row[1]
        project_dict = {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_by': project.created_by,
            'created_at': project.created_at.isoformat() + 'Z' if project.created_at else None,
            'updated_at': project.updated_at.isoformat() + 'Z' if project.updated_at else None,
            'data_count': data_count
        }
        projects.append(project_dict)
    
    return {"total": total or 0, "projects": projects}
    
    return {"total": total or 0, "projects": projects}
    
    return {"total": total or 0, "projects": projects}


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


@router.get("/{project_id}/data-files", response_model=DataSourceListResponse)
async def get_project_data_files(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取项目的数据文件列表"""
    result = await db.execute(
        select(DataSource).where(DataSource.project_id == project_id).order_by(DataSource.uploaded_at.desc())
    )
    data_sources = result.scalars().all()
    
    files = []
    for ds in data_sources:
        files.append(DataSourceInfo(
            id=ds.id,
            filename=ds.filename,
            file_size=ds.file_size,
            row_count=ds.row_count,
            created_at=ds.uploaded_at.isoformat() if ds.uploaded_at else None
        ))
    
    return DataSourceListResponse(files=files)


@router.get("/data-files/{data_source_id}/download")
async def download_data_file(
    data_source_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """下载数据文件"""
    result = await db.execute(select(DataSource).where(DataSource.id == data_source_id))
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据文件不存在"
        )
    
    if not os.path.exists(data_source.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    return FileResponse(
        path=data_source.file_path,
        filename=data_source.filename,
        media_type='application/octet-stream'
    )


@router.delete("/data-files/{data_source_id}", response_model=Message)
async def delete_data_file(
    data_source_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除数据文件（管理员）"""
    result = await db.execute(select(DataSource).where(DataSource.id == data_source_id))
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据文件不存在"
        )
    
    # 删除物理文件
    if os.path.exists(data_source.file_path):
        os.remove(data_source.file_path)
    
    await db.delete(data_source)
    
    return Message(message=f"数据文件 {data_source.filename} 已删除")


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
    """删除项目（管理员）
    
    注意：此操作将彻底删除项目及其关联的所有数据，包括：
    - 数据文件（物理文件 + 数据库记录）
    - 报告（物理文件 + 数据库记录）
    - 看板（物理文件 + 数据库记录）
    """
    result = await db.execute(
        select(Project).options(selectinload(Project.data_sources))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 由于模型中定义了级联删除，数据库会自动删除关联记录
    # 但物理文件需要手动删除
    for ds in project.data_sources:
        if os.path.exists(ds.file_path):
            os.remove(ds.file_path)
    
    await db.delete(project)
    
    return Message(message=f"项目 {project.name} 已删除")