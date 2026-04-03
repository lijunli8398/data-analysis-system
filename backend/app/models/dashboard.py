"""
看板模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Dashboard(Base):
    """看板表"""
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    task_id = Column(Integer)
    title = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    summary = Column(Text)  # LLM生成的摘要
    insights_json = Column(Text)  # LLM生成的洞察
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    project = relationship("Project", back_populates="dashboards")
    
    def __repr__(self):
        return f"<Dashboard(id={self.id}, title='{self.title}')>"