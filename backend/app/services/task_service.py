"""
异步任务管理服务
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import BackgroundTasks
from app.models import Task
from app.config import get_settings

settings = get_settings()


class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self, db: AsyncSession, background_tasks: BackgroundTasks = None):
        self.db = db
        self.background_tasks = background_tasks
    
    async def create_task(
        self,
        task_type: str,
        project_id: int,
        params: Dict,
        created_by: int
    ) -> int:
        """
        创建异步任务
        
        Args:
            task_type: 任务类型 (report/dashboard)
            project_id: 项目ID
            params: 任务参数
            created_by: 创建用户ID
        
        Returns:
            任务ID
        """
        task = Task(
            task_type=task_type,
            project_id=project_id,
            status="pending",
            params_json=json.dumps(params, ensure_ascii=False),
            created_by=created_by
        )
        
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        
        # 使用BackgroundTasks启动后台执行
        if self.background_tasks:
            self.background_tasks.add_task(self._run_task_background, task.id)
        
        return task.id
    
    def _run_task_background(self, task_id: int):
        """在后台运行任务（同步包装器）"""
        import asyncio
        asyncio.run(self._execute_task_standalone(task_id))
    
    async def _execute_task_standalone(self, task_id: int):
        """独立执行任务（创建新的数据库会话）"""
        from app.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            try:
                # 获取任务
                result = await db.execute(select(Task).where(Task.id == task_id))
                task = result.scalar_one_or_none()
                
                if not task:
                    return
                
                # 更新状态为running
                task.status = "running"
                await db.commit()
                
                params = json.loads(task.params_json) if task.params_json else {}
                
                # 根据任务类型执行
                if task.task_type == "report":
                    from app.services.skill_service import SkillExecutor
                    executor = SkillExecutor(db)
                    result_data = await executor.run_education_analysis(
                        project_id=task.project_id,
                        params=params
                    )
                    
                    # 创建报告记录
                    await self._create_report_record(db, task, result_data)
                    
                elif task.task_type == "dashboard":
                    from app.services.skill_service import SkillExecutor
                    executor = SkillExecutor(db)
                    result_data = await executor.run_dashboard_generator(
                        project_id=task.project_id,
                        params=params
                    )
                    
                    # 创建看板记录
                    await self._create_dashboard_record(db, task, result_data)
                
                # 更新状态为completed
                task.status = "completed"
                task.result_json = json.dumps(result_data, ensure_ascii=False)
                task.completed_at = datetime.now()
                await db.commit()
                
            except Exception as e:
                # 更新状态为failed
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.now()
                await db.commit()
    
    async def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务"""
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()
    
    async def update_task_status(
        self,
        task_id: int,
        status: str,
        result: Dict = None,
        error: str = None
    ):
        """更新任务状态"""
        result_stmt = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result_stmt.scalar_one_or_none()
        
        if task:
            task.status = status
            if result:
                task.result_json = json.dumps(result, ensure_ascii=False)
            if error:
                task.error_message = error
            if status in ["completed", "failed"]:
                task.completed_at = datetime.now()
            
            await self.db.flush()
    
    async def _create_report_record(self, db, task: Task, result: Dict):
        """创建报告记录"""
        from app.models import Report
        
        report = Report(
            project_id=task.project_id,
            task_id=task.id,
            title=result.get("title", "教育数据分析报告"),
            file_path=result.get("report_path", ""),
            summary=result.get("summary", ""),
            insights_json=json.dumps(result.get("insights", []), ensure_ascii=False)
        )
        
        db.add(report)
        await db.flush()
    
    async def _create_dashboard_record(self, db, task: Task, result: Dict):
        """创建看板记录"""
        from app.models import Dashboard
        
        dashboard = Dashboard(
            project_id=task.project_id,
            task_id=task.id,
            title=result.get("title", "教育学情数据看板"),
            file_path=result.get("dashboard_path", ""),
            summary=result.get("summary", ""),
            insights_json=json.dumps(result.get("insights", []), ensure_ascii=False)
        )
        
        db.add(dashboard)
        await db.flush()