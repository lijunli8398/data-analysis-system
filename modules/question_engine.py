#!/usr/bin/env python3
"""
智能问数引擎
"""

import os
import json
from typing import Dict

from modules.llm_client import llm_client


class QuestionEngine:
    """智能问数引擎"""
    
    def ask(self, question: str, context: Dict) -> Dict:
        """回答问题"""
        
        if llm_client.is_available():
            response = llm_client.answer_question(question, context)
            
            if self._need_chart(question):
                chart_html = self._generate_simple_chart(context)
                if chart_html:
                    response['chart'] = chart_html
            
            return response
        
        else:
            return self._default_answer(question, context)
    
    def _need_chart(self, question: str) -> bool:
        keywords = ['趋势', '分布', '对比', '比较', '变化', '比例', '占比', '图表']
        return any(kw in question for kw in keywords)
    
    def _generate_simple_chart(self, context: Dict) -> str:
        if context.get('result_path') and os.path.exists(context['result_path']):
            with open(context['result_path'], 'r') as f:
                result_data = json.load(f)
            
            chart_config = self._create_chart_config(result_data)
            
            html = f'''
<div style="width: 100%; height: 300px;">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <div id="mini_chart" style="width: 100%; height: 100%;"></div>
    <script>
        var chart = echarts.init(document.getElementById('mini_chart'));
        chart.setOption({json.dumps(chart_config, ensure_ascii=False)});
    </script>
</div>
'''
            return html
        
        return ""
    
    def _create_chart_config(self, result_data: Dict) -> Dict:
        if result_data.get('numeric_summary'):
            numeric_summary = result_data.get('numeric_summary', {})
            categories = list(numeric_summary.keys())[:4]
            means = [v.get('mean', 0) for v in list(numeric_summary.values())[:4]]
            
            return {
                "title": {"text": "数据概览", "left": "center"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": categories},
                "yAxis": {"type": "value"},
                "series": [{
                    "name": "平均值",
                    "type": "bar",
                    "data": means,
                    "itemStyle": {"color": "#667eea"}
                }]
            }
        
        return {
            "title": {"text": "数据可视化", "left": "center"},
            "series": [{
                "type": "pie",
                "data": [{"name": "无数据", "value": 1}],
                "radius": "50%"
            }]
        }
    
    def _default_answer(self, question: str, context: Dict) -> Dict:
        result_data = {}
        if context.get('result_path') and os.path.exists(context['result_path']):
            with open(context['result_path'], 'r') as f:
                result_data = json.load(f)
        
        answer = f"针对您的问题「{question}」，基于当前数据分析结果：\n\n"
        
        if context.get('project_name'):
            answer += f"当前项目：{context['project_name']}\n"
        
        if result_data:
            if result_data.get('row_count'):
                answer += f"- 数据总记录数：{result_data.get('row_count')}\n"
            if result_data.get('column_count'):
                answer += f"- 字段数量：{result_data.get('column_count')}\n"
            
            if result_data.get('numeric_summary'):
                answer += "\n关键字段统计：\n"
                for col, stats in result_data.get('numeric_summary', {}).items():
                    answer += f"- {col}: 平均值 {stats.get('mean', 0):.2f}\n"
        
        answer += "\n💡 提示：配置通义千问API Key可获得更智能的分析回答。"
        
        return {
            'answer': answer,
            'type': 'text',
            'chart': self._generate_simple_chart(context) if self._need_chart(question) else None
        }