"""
智能问数路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import ChatHistory, User
from app.routers.auth import get_current_user
from app.utils.schemas import ChatQuery, ChatHistoryInfo, ChatHistoryList, Message

router = APIRouter(prefix="/chat", tags=["智能问数"])


@router.post("/query", response_model=Message)
async def chat_query(
    query_data: ChatQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """智能问数 - 提交问题"""
    from app.services.chat_service import ChatService
    
    chat_service = ChatService(db)
    
    # 执行问答
    answer = await chat_service.query(
        project_id=query_data.project_id,
        question=query_data.question,
        user_id=current_user.id
    )
    
    return Message(message=answer)


@router.get("/history", response_model=ChatHistoryList)
async def get_chat_history(
    project_id: int = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取聊天历史"""
    query = select(ChatHistory).where(ChatHistory.user_id == current_user.id)
    
    if project_id:
        query = query.where(ChatHistory.project_id == project_id)
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # 分页查询
    result = await db.execute(query.offset(skip).limit(limit).order_by(ChatHistory.created_at.desc()))
    history = result.scalars().all()
    
    return ChatHistoryList(
        total=total or 0,
        history=[ChatHistoryInfo.model_validate(h) for h in history]
    )


@router.delete("/history/{history_id}", response_model=Message)
async def delete_chat_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除聊天历史"""
    result = await db.execute(
        select(ChatHistory).where(
            ChatHistory.id == history_id,
            ChatHistory.user_id == current_user.id
        )
    )
    history = result.scalar_one_or_none()
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天历史不存在"
        )
    
    await db.delete(history)
    
    return Message(message="聊天历史已删除")