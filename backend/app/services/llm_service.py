"""
千问LLM服务
"""
import json
from typing import Optional, List, Dict
import dashscope
from dashscope import Generation
from app.config import get_settings

settings = get_settings()


class QwenService:
    """千问大模型服务"""
    
    def __init__(self):
        """初始化千问API"""
        dashscope.api_key = settings.QWEN_API_KEY
    
    async def chat(
        self,
        prompt: str,
        model: str = None,
        system_prompt: str = None,
        history: List[Dict] = None
    ) -> str:
        """
        调用千问聊天API
        
        Args:
            prompt: 用户输入
            model: 模型名称 (qwen-plus 或 qwen-turbo)
            system_prompt: 系统提示
            history: 对话历史
        
        Returns:
            模型回复
        """
        if model is None:
            model = settings.QWEN_MODEL_PLUS
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        if history:
            messages.extend(history)
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = Generation.call(
                model=model,
                messages=messages,
                result_format='message'
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"千问API调用失败: {response.code} - {response.message}")
                
        except Exception as e:
            raise Exception(f"LLM调用异常: {str(e)}")
    
    async def analyze_data_intent(self, question: str) -> Dict:
        """
        分析数据查询意图
        
        Args:
            question: 用户问题
        
        Returns:
            意图分析结果
        """
        system_prompt = """你是一个数据分析助手。用户会用自然语言询问数据相关的问题。
你需要分析用户的问题，识别：
1. 问题类型：统计查询、对比分析、趋势分析、分布分析等
2. 涉及的指标/维度
3. 分析范围：整体、按群体、按学校等

返回JSON格式的分析结果。"""
        
        prompt = f"""请分析以下数据查询问题：
"{question}"

返回JSON格式结果，包含：
{
    "question_type": "问题类型",
    "metrics": ["涉及的指标列表"],
    "dimensions": ["涉及的维度列表"],
    "scope": "分析范围",
    "needs_calculation": true/false,
    "calculation_hint": "计算方式提示"
}"""
        
        response = await self.chat(prompt, model=settings.QWEN_MODEL_TURBO, system_prompt=system_prompt)
        
        # 解析JSON
        try:
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)
        except:
            return {
                "question_type": "unknown",
                "metrics": [],
                "dimensions": [],
                "scope": "整体",
                "needs_calculation": False
            }
    
    async def interpret_result(self, question: str, data: Dict) -> str:
        """
        解读数据结果
        
        Args:
            question: 用户原始问题
            data: 数据计算结果
        
        Returns:
            自然语言解读
        """
        system_prompt = """你是一个数据分析专家。你需要将数据计算结果转换为通俗易懂的自然语言回答。
回答要：
1. 直接回答用户问题
2. 提供关键数据和数字
3. 指出重要发现或异常
4. 给出简短的结论或建议"""
        
        prompt = f"""用户问题："{question}"

数据结果：
{json.dumps(data, ensure_ascii=False, indent=2)}

请用自然语言解读这个结果，直接回答用户问题。"""
        
        return await self.chat(prompt, model=settings.QWEN_MODEL_TURBO, system_prompt=system_prompt)
    
    async def guide_analysis_skill(self, data_info: Dict) -> Dict:
        """
        指导education-data-analysis skill执行
        
        Args:
            data_info: 数据文件信息
        
        Returns:
            分析参数建议
        """
        system_prompt = """你是一个教育数据分析专家。你需要根据数据文件的信息，建议如何进行教育学情数据分析。

教育数据分析关注：
- 成长环境指标：亲子关系、师生关系、同伴关系、校园安全
- 学生发展指标：身心健康、情绪状态、运动健康、学习创新机会、学习习惯、学业达标
- 群体差异：性别、办学规模、办学性质
- 四象限分层：基于成长环境和学生发展划分学生类型"""

        prompt = f"""数据文件信息：
{json.dumps(data_info, ensure_ascii=False, indent=2)}

请分析这个数据文件，建议分析参数配置。返回JSON格式：
{
    "env_columns": ["成长环境指标列名"],
    "dev_columns": ["学生发展指标列名"],
    "analysis_focus": ["重点关注的分析维度"],
    "threshold": 风险阈值建议,
    "expected_insights": ["预期发现"]
}"""
        
        response = await self.chat(prompt, system_prompt=system_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            return json.loads(response[json_start:json_end])
        except:
            return {
                "env_columns": [],
                "dev_columns": [],
                "analysis_focus": [],
                "threshold": 60,
                "expected_insights": []
            }
    
    async def enhance_report(self, analysis_results: Dict) -> Dict:
        """
        增强报告内容
        
        Args:
            analysis_results: 分析结果数据
        
        Returns:
            增强的报告摘要和洞察
        """
        system_prompt = """你是一个教育数据分析专家。你需要基于数据分析结果，生成：
1. 报告摘要（2-3句话概括主要发现）
2. 关键洞察（3-5条重要发现）
3. 异常标注（指出异常或值得关注的数据点）"""

        prompt = f"""分析结果：
{json.dumps(analysis_results, ensure_ascii=False, indent=2)}

请生成报告增强内容。返回JSON格式：
{
    "summary": "报告摘要",
    "insights": ["关键洞察列表"],
    "warnings": ["异常或警告信息"]
}"""
        
        response = await self.chat(prompt, system_prompt=system_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            return json.loads(response[json_start:json_end])
        except:
            return {
                "summary": "数据分析完成",
                "insights": [],
                "warnings": []
            }
    
    async def enhance_dashboard(self, chart_data: Dict) -> Dict:
        """
        增强看板内容
        
        Args:
            chart_data: 图表数据
        
        Returns:
            图表解读和洞察
        """
        system_prompt = """你是一个数据可视化专家。你需要为每个图表生成简短的解读文字。"""

        prompt = f"""图表数据：
{json.dumps(chart_data, ensure_ascii=False, indent=2)}

请为每个图表生成解读。返回JSON格式：
{
    "chart_insights": {
        "chart1": "指标平均分对比解读",
        "chart2": "风险暴露率解读",
        ...
    },
    "key_highlights": ["看板亮点"]
}"""
        
        response = await self.chat(prompt, model=settings.QWEN_MODEL_TURBO, system_prompt=system_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            return json.loads(response[json_start:json_end])
        except:
            return {
                "chart_insights": {},
                "key_highlights": []
            }


# 全局服务实例
qwen_service = QwenService()