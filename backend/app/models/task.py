"""
异步任务模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Task(Base):
    """异步任务表"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False)  # report, dashboard
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, running, completed, failed
    params_json = Column(Text)  # 任务参数
    result_json = Column(Text)  # 执行结果
    error_message = Column(Text)  # 错误信息
    created_by = Column(Integer)  # 用户ID
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Task(id={self.id}, type='{self.task_type}', status='{self.status}')>"