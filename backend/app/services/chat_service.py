"""
智能问数服务
"""
import os
import json
import pandas as pd
import sys
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import ChatHistory, DataSource
from app.config import get_settings

settings = get_settings()


class ChatService:
    """智能问数服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def query(
        self,
        project_id: Optional[int],
        question: str,
        user_id: int
    ) -> str:
        """
        智能问答
        
        Args:
            project_id: 项目ID (None表示跨项目)
            question: 用户问题
            user_id: 用户ID
        
        Returns:
            回答
        """
        # 1. 确定数据源目录
        data_source = await self._get_data_source(project_id)
        
        if not data_source or not data_source.exists():
            return f"抱歉，项目 {project_id} 还没有分析结果数据。请先在[报告管理]中生成报告。"
        
        # 2. 调用 QA Engine
        try:
            # 动态导入 qa_engine（使用绝对路径）
            import importlib.util
            qa_engine_path = "/app/skills/education-data-qa/scripts/qa_engine.py"
            spec = importlib.util.spec_from_file_location("qa_engine", qa_engine_path)
            qa_engine = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(qa_engine)
            
            EducationDataQA = qa_engine.EducationDataQA
            
            qa = EducationDataQA(str(data_source))
            result = qa.answer(question)
            
            # 将结果转换为字符串
            if isinstance(result, dict):
                # 如果有错误
                if 'error' in result:
                    answer = f"抱歉，{result['error']}"
                # 构建格式化的回答
                else:
                    parts = []
                    
                    # 添加摘要
                    if 'summary' in result and result['summary']:
                        parts.append(result['summary'])
                    
                    # 添加表格数据
                    if 'table' in result and result['table']:
                        import pandas as pd
                        df = pd.DataFrame(result['table'])
                        parts.append("\n" + df.to_string(index=False))
                    
                    # 添加关键发现
                    if 'key_findings' in result and result['key_findings']:
                        parts.append("\n关键发现：")
                        for finding in result['key_findings']:
                            parts.append(f"- {finding}")
                    
                    answer = "\n".join(parts) if parts else "未找到相关数据"
            else:
                answer = str(result)
            
        except Exception as e:
            # 如果 QA Engine 失败，返回错误信息
            import traceback
            traceback.print_exc()
            answer = f"抱歉，查询过程中出现错误：{str(e)}"
        
        # 3. 保存聊天历史
        history = ChatHistory(
            project_id=project_id,
            user_id=user_id,
            question=question,
            answer=answer,
            data_sources_json=json.dumps([str(data_source)], ensure_ascii=False)
        )
        
        self.db.add(history)
        await self.db.flush()
        
        return answer
    
    async def _get_data_source(self, project_id: Optional[int]) -> Optional[Path]:
        """获取数据源目录"""
        if project_id:
            result_dir = Path(settings.RESULT_DIR) / f"project_{project_id}" / "data"
            if result_dir.exists():
                return result_dir
        return None