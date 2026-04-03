"""
Pydantic Schema定义
用于API请求/响应的数据验证
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ========== 用户相关 ==========

class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserInfo(BaseModel):
    """用户信息响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


# ========== 项目相关 ==========

class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectInfo(BaseModel):
    """项目信息响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime


class ProjectList(BaseModel):
    """项目列表响应"""
    total: int
    projects: List[ProjectInfo]


# ========== 数据源相关 ==========

class DataSourceInfo(BaseModel):
    """数据源信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    filename: str
    file_path: str
    file_size: int
    row_count: int
    columns_json: Optional[str]
    uploaded_by: int
    uploaded_at: datetime


class DataSourceList(BaseModel):
    """数据源列表"""
    total: int
    data_sources: List[DataSourceInfo]


# ========== 报告相关 ==========

class ReportGenerate(BaseModel):
    """生成报告请求"""
    project_id: int
    title: str = Field(..., min_length=1, max_length=200)


class ReportInfo(BaseModel):
    """报告信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    task_id: Optional[int]
    title: str
    file_path: str
    summary: Optional[str]
    insights_json: Optional[str]
    created_at: datetime


class ReportList(BaseModel):
    """报告列表"""
    total: int
    reports: List[ReportInfo]


# ========== 看板相关 ==========

class DashboardGenerate(BaseModel):
    """生成看板请求"""
    project_id: int
    title: str = Field(..., min_length=1, max_length=200)


class DashboardInfo(BaseModel):
    """看板信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    task_id: Optional[int]
    title: str
    file_path: str
    summary: Optional[str]
    insights_json: Optional[str]
    created_at: datetime


class DashboardList(BaseModel):
    """看板列表"""
    total: int
    dashboards: List[DashboardInfo]


# ========== 任务相关 ==========

class TaskInfo(BaseModel):
    """任务信息"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_type: str
    project_id: int
    status: str
    params_json: Optional[str]
    result_json: Optional[str]
    error_message: Optional[str]
    created_by: int
    created_at: datetime
    completed_at: Optional[datetime]


# ========== 聊天相关 ==========

class ChatQuery(BaseModel):
    """聊天查询请求"""
    project_id: Optional[int] = None  # NULL表示跨项目查询
    question: str = Field(..., min_length=1)


class ChatHistoryInfo(BaseModel):
    """聊天历史"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: Optional[int]
    question: str
    answer: str
    created_at: datetime


class ChatHistoryList(BaseModel):
    """聊天历史列表"""
    total: int
    history: List[ChatHistoryInfo]


# ========== 通用响应 ==========

class Message(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None