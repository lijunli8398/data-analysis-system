"""
Skill执行服务
集成education-data-analysis和dashboard-generator
"""
import os
import json
import subprocess
import pandas as pd
from pathlib import Path
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import DataSource
from app.config import get_settings

settings = get_settings()


def detect_columns(columns: List[str]) -> Dict[str, List[str]]:
    """
    智能检测成长环境和学生发展指标列名
    
    Args:
        columns: 所有列名列表
    
    Returns:
        {"env_columns": [...], "dev_columns": [...]}
    """
    env_columns = []
    dev_columns = []
    
    # 成长环境指标关键词
    env_keywords = ['亲子关系', '师生关系', '同伴关系', '校园安全', '成长环境']
    
    # 学生发展指标关键词
    dev_keywords = ['身心健康', '情绪状态', '运动健康', '学习创新', '学习习惯', '学业达标', '学生发展']
    
    for col in columns:
        col_lower = col.lower()
        for kw in env_keywords:
            if kw in col:
                env_columns.append(col)
                break
        
        for kw in dev_keywords:
            if kw in col:
                dev_columns.append(col)
                break
    
    return {"env_columns": env_columns, "dev_columns": dev_columns}


class SkillExecutor:
    """Skill执行器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Skills目录在backend/skills/下（使用绝对路径）
        backend_dir = Path(__file__).parent.parent.parent
        self.skill_base_path = backend_dir / "skills"
    
    async def run_education_analysis(
        self,
        project_id: int,
        params: Dict
    ) -> Dict:
        """
        执行教育数据分析Skill
        
        Args:
            project_id: 项目ID
            params: 参数 {title, data_source_id}
        
        Returns:
            执行结果 {report_path, csv_paths, summary, insights}
        """
        # 1. 获取数据源信息
        result = await self.db.execute(
            select(DataSource).where(DataSource.id == params["data_source_id"])
        )
        data_source = result.scalar_one_or_none()
        
        if not data_source:
            raise Exception("数据源不存在")
        
        # 2. 智能检测列名
        columns = json.loads(data_source.columns_json) if data_source.columns_json else []
        column_config = detect_columns(columns)
        
        # 3. 准备输出目录
        output_dir = Path(settings.RESULT_DIR) / f"project_{project_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. 调用education-analysis脚本
        skill_path = self.skill_base_path / "education-data-analysis"
        script_path = skill_path / "scripts" / "education_analysis.py"
        
        # 构建命令参数（脚本只支持--data和--output参数）
        cmd_args = [
            "python", str(script_path),
            "--data", data_source.file_path,
            "--output", str(output_dir)
        ]
        
        # 执行脚本
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode != 0:
            raise Exception(f"Skill执行失败: {result.stderr}")
        
        # 5. 找到生成的Word报告（在report子目录下）
        report_dir = output_dir / "report"
        report_path = None
        
        if report_dir.exists():
            for f in report_dir.glob("*.docx"):
                report_path = f
                break
        
        # 如果report子目录没有，再检查output_dir根目录
        if not report_path:
            for f in output_dir.glob("*.docx"):
                report_path = f
                break
        
        # 6. 简单的摘要生成
        summary = f"已完成对项目 {project_id} 的教育数据分析，生成报告和CSV数据文件。"
        
        return {
            "title": params.get("title", "教育数据分析报告"),
            "report_path": str(report_path) if report_path else "",
            "csv_dir": str(output_dir / "data"),
            "summary": summary,
            "insights": [],
            "warnings": []
        }
    
    async def run_dashboard_generator(
        self,
        project_id: int,
        params: Dict
    ) -> Dict:
        """
        执行看板生成Skill
        
        Args:
            project_id: 项目ID
            params: 参数 {title, result_dir}
        
        Returns:
            执行结果 {dashboard_path, summary, insights}
        """
        # 1. 检查数据目录
        data_dir = Path(params.get("result_dir", ""))
        
        if not data_dir.exists():
            raise Exception("数据结果目录不存在，请先生成报告")
        
        # 2. 准备输出目录
        dashboard_dir = Path(settings.DASHBOARD_DIR)
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = dashboard_dir / f"project_{project_id}_dashboard.html"
        
        # 3. 调用dashboard-generator脚本
        skill_path = self.skill_base_path / "dashboard-generator"
        script_path = skill_path / "scripts" / "dashboard_generator.py"
        
        cmd_args = [
            "python", str(script_path),
            "--data-source", str(data_dir),
            "--output", str(output_file)
        ]
        
        # 执行脚本
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=120  # 2分钟超时
        )
        
        if result.returncode != 0:
            raise Exception(f"Skill执行失败: {result.stderr}")
        
        # 4. 返回结果
        summary = f"已生成项目 {project_id} 的交互式数据看板。"
        
        return {
            "title": params.get("title", "教育学情数据看板"),
            "dashboard_path": str(output_file),
            "summary": summary,
            "insights": {},
            "key_highlights": []
        }