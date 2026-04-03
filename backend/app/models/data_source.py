"""
数据源模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class DataSource(Base):
    """数据源表"""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # 文件大小(bytes)
    row_count = Column(Integer)  # 数据行数
    columns_json = Column(Text)  # 列信息JSON
    uploaded_by = Column(Integer)  # 用户ID
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    project = relationship("Project", back_populates="data_sources")
    
    def __repr__(self):
        return f"<DataSource(id={self.id}, filename='{self.filename}')>"