"""
数据上传路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import json
import pandas as pd
from pathlib import Path
from app.database import get_db
from app.models import DataSource, Project, User
from app.routers.auth import get_current_admin
from app.config import get_settings
from app.utils.schemas import DataSourceInfo, DataSourceList, Message

router = APIRouter(prefix="/upload", tags=["数据上传"])
settings = get_settings()


@router.post("", response_model=DataSourceInfo)
async def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """上传数据文件（管理员）"""
    # 验证项目存在
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 验证文件类型
    allowed_extensions = {".xlsx", ".xls", ".csv", ".json"}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file_ext}。支持: {allowed_extensions}"
        )
    
    # 删除旧数据源（如果存在）
    old_result = await db.execute(
        select(DataSource).where(DataSource.project_id == project_id)
    )
    old_data_sources = old_result.scalars().all()
    
    for old_ds in old_data_sources:
        # 删除物理文件
        if os.path.exists(old_ds.file_path):
            os.remove(old_ds.file_path)
        await db.delete(old_ds)
    
    # 保存文件
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    safe_filename = f"project_{project_id}_{file.filename}"
    file_path = upload_dir / safe_filename
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 分析数据文件
    try:
        if file_ext in {".xlsx", ".xls"}:
            df = pd.read_excel(file_path)
        elif file_ext == ".csv":
            df = pd.read_csv(file_path)
        else:  # json
            df = pd.read_json(file_path)
        
        row_count = len(df)
        columns_json = json.dumps(list(df.columns), ensure_ascii=False)
        file_size = os.path.getsize(file_path)
        
    except Exception as e:
        os.remove(file_path)  # 删除无效文件
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"数据文件解析失败: {str(e)}"
        )
    
    # 创建数据源记录
    data_source = DataSource(
        project_id=project_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        row_count=row_count,
        columns_json=columns_json,
        uploaded_by=current_user.id
    )
    
    db.add(data_source)
    await db.flush()
    await db.refresh(data_source)
    
    return DataSourceInfo.model_validate(data_source)


@router.get("", response_model=DataSourceList)
async def list_data_sources(
    project_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取项目的数据源列表（管理员）"""
    result = await db.execute(
        select(DataSource).where(DataSource.project_id == project_id)
    )
    data_sources = result.scalars().all()
    
    return DataSourceList(
        total=len(data_sources),
        data_sources=[DataSourceInfo.model_validate(ds) for ds in data_sources]
    )


@router.delete("/{data_source_id}", response_model=Message)
async def delete_data_source(
    data_source_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除数据源（管理员）"""
    result = await db.execute(select(DataSource).where(DataSource.id == data_source_id))
    data_source = result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据源不存在"
        )
    
    # 删除物理文件
    if os.path.exists(data_source.file_path):
        os.remove(data_source.file_path)
    
    await db.delete(data_source)
    
    return Message(message=f"数据源 {data_source.filename} 已删除")