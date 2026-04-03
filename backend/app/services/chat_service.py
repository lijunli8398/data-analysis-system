"""
智能问数服务
"""
import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import ChatHistory, DataSource
from app.services.llm_service import qwen_service
from app.config import get_settings
from app.utils.auth import hash_password

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
        # 1. LLM理解意图
        intent = await qwen_service.analyze_data_intent(question)
        
        # 2. 确定数据源
        data_files = await self._find_data_files(project_id, intent)
        
        if not data_files:
            # 如果没有数据文件，尝试直接用LLM回答
            return await qwen_service.chat(
                f"用户问: {question}\n但没有找到相关数据，请基于一般知识回答，并说明缺少数据支持。"
            )
        
        # 3. Python数据计算
        calculation_result = await self._execute_calculation(data_files, intent)
        
        # 4. LLM解读结果
        answer = await qwen_service.interpret_result(question, calculation_result)
        
        # 5. 保存聊天历史
        history = ChatHistory(
            project_id=project_id,
            user_id=user_id,
            question=question,
            answer=answer,
            data_sources_json=json.dumps(list(data_files.keys()), ensure_ascii=False)
        )
        
        self.db.add(history)
        await self.db.flush()
        
        return answer
    
    async def _find_data_files(
        self,
        project_id: Optional[int],
        intent: Dict
    ) -> Dict[str, pd.DataFrame]:
        """
        查找相关数据文件
        
        Args:
            project_id: 项目ID
            intent: 意图分析结果
        
        Returns:
            数据文件字典 {文件名: DataFrame}
        """
        data_files = {}
        
        # 查找CSV结果文件
        if project_id:
            # 单项目查询
            result_dir = Path(settings.RESULT_DIR) / f"project_{project_id}" / "data"
            
            if result_dir.exists():
                # 根据意图选择相关文件
                for metric in intent.get("metrics", []):
                    # 指标统计
                    if "指标" in metric or "平均" in metric or "风险" in metric:
                        csv_file = result_dir / "indicator_stats.csv"
                        if csv_file.exists():
                            data_files["indicator_stats"] = pd.read_csv(csv_file)
                    
                    # 性别差异
                    if "性别" in metric or "男生" in metric or "女生" in metric:
                        csv_file = result_dir / "gender_analysis.csv"
                        if csv_file.exists():
                            data_files["gender_analysis"] = pd.read_csv(csv_file)
                    
                    # 办学规模
                    if "规模" in metric or "微规模" in metric:
                        csv_file = result_dir / "scale_analysis.csv"
                        if csv_file.exists():
                            data_files["scale_analysis"] = pd.read_csv(csv_file)
                    
                    # 办学性质
                    if "公办" in metric or "民办" in metric:
                        csv_file = result_dir / "nature_analysis.csv"
                        if csv_file.exists():
                            data_files["nature_analysis"] = pd.read_csv(csv_file)
                    
                    # 四象限
                    if "象限" in metric or "学生类型" in metric:
                        csv_file = result_dir / "quadrant_analysis.csv"
                        if csv_file.exists():
                            data_files["quadrant_analysis"] = pd.read_csv(csv_file)
                    
                    # 学校层面
                    if "学校" in metric:
                        csv_file = result_dir / "school_analysis.csv"
                        if csv_file.exists():
                            data_files["school_analysis"] = pd.read_csv(csv_file)
        else:
            # 跨项目查询 - 查找所有项目的数据
            result_base_dir = Path(settings.RESULT_DIR)
            
            for project_dir in result_base_dir.iterdir():
                if project_dir.is_dir() and project_dir.name.startswith("project_"):
                    data_dir = project_dir / "data"
                    
                    if data_dir.exists():
                        for csv_file in data_dir.glob("*.csv"):
                            key = f"{project_dir.name}_{csv_file.stem}"
                            data_files[key] = pd.read_csv(csv_file)
        
        return data_files
    
    async def _execute_calculation(
        self,
        data_files: Dict[str, pd.DataFrame],
        intent: Dict
    ) -> Dict:
        """
        执行数据计算
        
        Args:
            data_files: 数据文件
            intent: 意图分析
        
        Returns:
            计算结果
        """
        result = {}
        
        question_type = intent.get("question_type", "unknown")
        
        for file_name, df in data_files.items():
            # 根据意图类型进行不同计算
            
            if "统计" in question_type or "平均" in question_type:
                # 简单统计
                if "平均分" in df.columns:
                    result[f"{file_name}_平均分"] = df["平均分"].mean()
                if "风险暴露率" in df.columns:
                    result[f"{file_name}_风险暴露率均值"] = df["风险暴露率"].mean()
            
            elif "对比" in question_type or "差异" in question_type:
                # 对比分析
                if "性别" in df.columns or "办学规模" in df.columns or "办学性质" in df.columns:
                    # 分组对比
                    group_col = None
                    for col in ["性别", "办学规模", "办学性质"]:
                        if col in df.columns:
                            group_col = col
                            break
                    
                    if group_col:
                        grouped = df.groupby(group_col).agg({
                            "成长环境均分": "mean",
                            "学生发展均分": "mean"
                        })
                        result[f"{file_name}_对比"] = grouped.to_dict()
            
            elif "分布" in question_type:
                # 分布分析
                if "象限" in df.columns:
                    quadrant_counts = df.groupby("象限")["人数"].sum()
                    result[f"{file_name}_分布"] = quadrant_counts.to_dict()
            
            # 默认返回原始数据摘要
            result[f"{file_name}_数据概况"] = {
                "行数": len(df),
                "列数": len(df.columns),
                "列名": list(df.columns)
            }
        
        return result