"""
聊天历史模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class ChatHistory(Base):
    """聊天历史表"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)  # NULL表示跨项目查询
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    data_sources_json = Column(Text)  # 使用的数据源
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<ChatHistory(id={self.id}, question='{self.question[:50]}...')>"