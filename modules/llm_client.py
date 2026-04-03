#!/usr/bin/env python3
"""
LLM客户端封装 - 支持通义千问大模型
"""

import os
import json
import re
from typing import Optional, Dict, Any, List

# 导入OpenAI SDK
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class LLMClient:
    """LLM调用客户端 - 支持通义千问"""
    
    def __init__(self):
        # 从环境变量获取API配置
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = os.environ.get("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = os.environ.get("LLM_MODEL", "qwen-plus")
        
        # 初始化客户端
        self.client = None
        
        if self.api_key and HAS_OPENAI:
            self._init_client()
    
    def _init_client(self):
        """初始化OpenAI兼容客户端"""
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except Exception as e:
            print(f"LLM客户端初始化失败: {e}")
    
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        return self.client is not None
    
    def call(self, prompt: str, system_prompt: str = "") -> str:
        """调用LLM"""
        
        if not self.client:
            raise ValueError("LLM未配置，请设置DASHSCOPE_API_KEY环境变量")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    def extract_code(self, response: str) -> str:
        """从响应中提取Python代码"""
        pattern = r'```(?:python)?\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            return matches[0]
        return response
    
    def generate_echarts_config(self, prompt: str, result_data: Dict) -> List[Dict]:
        """生成echarts图表配置"""
        
        # 先检查 result_data 是否有足够数据
        basic_info = result_data.get('basic_info', {})
        cat_analysis = result_data.get('categorical_analysis', {})
        
        # 如果数据不足，返回默认图表
        if not basic_info and not cat_analysis:
            return self._get_default_dashboard_charts()
        
        system_prompt = """你是一个数据可视化专家。根据数据生成echarts图表配置。

【重要】输出格式要求：
必须输出一个JSON数组，包含2-4个图表配置对象。

示例输出：
```json
[
  {"title": {"text": "数据概览"}, "series": [{"type": "pie", "data": [{"name": "记录数", "value": 100}]}]}
]
```

只输出JSON数组，不要有任何其他文字说明！"""
        
        # 构建精简的数据摘要
        data_summary = {
            "总记录数": basic_info.get('total_rows', 0),
            "字段数": basic_info.get('total_columns', 0)
        }
        
        # 添加分类变量信息
        if cat_analysis.get('analysis'):
            for col, info in list(cat_analysis['analysis'].items())[:3]:
                top_vals = list(info.get('top_percentage', {}).items())[:3]
                data_summary[col] = dict(top_vals)
        
        full_prompt = f"""
需求：{prompt}

数据摘要：
{json.dumps(data_summary, ensure_ascii=False, indent=2)}

请生成2-4个echarts图表配置。直接输出JSON数组，不要有其他内容。
"""
        
        try:
            response = self.call(full_prompt, system_prompt)
            
            # 尝试多种方式解析 JSON
            configs = self._parse_json_array(response)
            
            # 如果解析成功且有内容
            if configs and len(configs) > 0:
                return configs
            
        except Exception as e:
            print(f"LLM生成图表配置失败: {e}")
        
        # LLM 失败时返回默认图表
        return self._get_default_dashboard_charts(result_data)
    
    def _parse_json_array(self, text: str) -> List[Dict]:
        """从文本中解析JSON数组"""
        
        import re
        
        # 方法1: 尝试直接解析
        text = text.strip()
        if text.startswith('['):
            try:
                return json.loads(text)
            except:
                pass
        
        # 方法2: 提取代码块中的 JSON
        code_block_pattern = r'```(?:json)?\s*\n([\s\S]*?)\n```'
        matches = re.findall(code_block_pattern, text)
        for match in matches:
            try:
                result = json.loads(match.strip())
                if isinstance(result, list):
                    return result
            except:
                continue
        
        # 方法3: 查找第一个 [ 和最后一个 ] 之间的内容
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        
        return []
    
    def _get_default_dashboard_charts(self, data: Dict = None) -> List[Dict]:
        """生成默认图表配置（LLM失败时使用）"""
        
        charts = []
        data = data or {}
        
        # 图表1: 数据概览饼图
        basic = data.get('basic_info', {})
        if basic.get('total_rows'):
            charts.append({
                "title": {"text": "📊 数据概览", "left": "center"},
                "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                "legend": {"bottom": "5%"},
                "series": [{
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "itemStyle": {"borderRadius": 10},
                    "data": [
                        {"name": "总记录数", "value": basic.get('total_rows', 0)},
                        {"name": "字段数", "value": basic.get('total_columns', 0)},
                        {"name": "重复记录", "value": basic.get('duplicate_rows', 0)}
                    ]
                }]
            })
        
        # 图表2: 数据质量
        quality = data.get('data_quality', {})
        if quality:
            total_cols = data.get('basic_info', {}).get('total_columns', 18)
            charts.append({
                "title": {"text": "📈 数据质量", "left": "center"},
                "tooltip": {"trigger": "item"},
                "series": [{
                    "type": "pie",
                    "radius": "60%",
                    "data": [
                        {"name": "完整字段", "value": total_cols - quality.get('columns_with_missing', 0)},
                        {"name": "缺失字段", "value": quality.get('columns_with_missing', 0)}
                    ]
                }]
            })
        
        # 图表3: 分类变量分布
        cat = data.get('categorical_analysis', {})
        if cat.get('analysis'):
            analysis = cat['analysis']
            col_name = list(analysis.keys())[0]
            info = analysis[col_name]
            
            # 构建饼图数据
            pie_data = []
            for name, pct in list(info.get('top_percentage', {}).items())[:5]:
                # 从百分比字符串提取数值
                if isinstance(pct, str):
                    val = float(pct.replace('%', ''))
                else:
                    val = pct
                pie_data.append({"name": name, "value": val})
            
            charts.append({
                "title": {"text": f"📊 {col_name}分布", "left": "center"},
                "tooltip": {"trigger": "item", "formatter": "{b}: {d}%"},
                "series": [{
                    "type": "pie",
                    "radius": "55%",
                    "data": pie_data
                }]
            })
            
            # 图表4: 分类变量唯一值数量
            if len(analysis) > 1:
                categories = list(analysis.keys())[:5]
                values = [analysis[c].get('unique_values', 0) for c in categories]
                
                charts.append({
                    "title": {"text": "📊 分类变量唯一值数", "left": "center"},
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {"type": "category", "data": [c[:6] for c in categories]},
                    "yAxis": {"type": "value"},
                    "series": [{
                        "type": "bar",
                        "data": values,
                        "itemStyle": {"color": "#667eea", "borderRadius": [5, 5, 0, 0]}
                    }]
                })
        
        # 如果没有任何图表，返回一个空状态提示
        if not charts:
            charts.append({
                "title": {"text": "暂无数据", "left": "center", "top": "center"},
                "graphic": {
                    "type": "text",
                    "left": "center",
                    "top": "middle",
                    "style": {"text": "请先生成报告以获取数据", "fontSize": 18, "fill": "#999"}
                }
            })
        
        return charts


# 单例实例
llm_client = LLMClient()