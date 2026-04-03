"""
报告管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import os
from app.database import get_db
from app.models import Report, Project, Task, User, DataSource
from app.routers.auth import get_current_user, get_current_admin
from app.utils.schemas import ReportGenerate, ReportInfo, ReportList, Message
from app.services.task_service import AsyncTaskManager

router = APIRouter(prefix="/reports", tags=["报告管理"])


@router.get("", response_model=ReportList)
async def list_reports(
    project_id: int = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取报告列表"""
    query = select(Report)
    
    if project_id:
        query = query.where(Report.project_id == project_id)
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分页查询
    result = await db.execute(query.offset(skip).limit(limit).order_by(Report.created_at.desc()))
    reports = result.scalars().all()
    
    return ReportList(
        total=total or 0,
        reports=[ReportInfo.model_validate(r) for r in reports]
    )


@router.get("/{report_id}", response_model=ReportInfo)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取报告详情"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )
    
    return ReportInfo.model_validate(report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """下载报告文件"""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )
    
    if not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告文件不存在"
        )
    
    return FileResponse(
        report.file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=report.title + ".docx"
    )


@router.post("/generate", response_model=Message)
async def generate_report(
    report_data: ReportGenerate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """生成报告（管理员）- 创建异步任务"""
    
    # 验证项目存在且有数据源
    result = await db.execute(select(Project).where(Project.id == report_data.project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在"
        )
    
    # 检查数据源
    ds_result = await db.execute(
        select(DataSource).where(DataSource.project_id == report_data.project_id)
    )
    data_source = ds_result.scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目没有上传数据源"
        )
    
    # 创建异步任务
    task_manager = AsyncTaskManager(db, background_tasks)
    task_id = await task_manager.create_task(
        task_type="report",
        project_id=report_data.project_id,
        params={
            "title": report_data.title,
            "data_source_id": data_source.id
        },
        created_by=current_user.id
    )
    
    return Message(message=f"报告生成任务已创建，任务ID: {task_id}")


@router.delete("/{report_id}", response_model=Message)
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除报告（管理员）"""
    import os
    
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在"
        )
    
    # 删除物理文件
    if os.path.exists(report.file_path):
        os.remove(report.file_path)
    
    await db.delete(report)
    
    return Message(message=f"报告 {report.title} 已删除")