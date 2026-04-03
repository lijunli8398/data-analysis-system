#!/usr/bin/env python3
"""
仪表盘看板生成器
"""

import os
import json
from datetime import datetime
from pathlib import Path

from modules.llm_client import llm_client


class DashboardGenerator:
    """仪表盘看板生成器"""
    
    def generate(self,
                 result_path: str,
                 title: str,
                 prompt: str,
                 output_dir: Path) -> dict:
        """生成HTML看板"""
        
        dashboard_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        dashboards_dir = output_dir / "dashboards"
        dashboards_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            result_data = self._load_result(result_path)
            
            # 先生成默认图表（保证有数据）
            default_charts = self._get_default_charts(result_data)
            
            # 尝试用 LLM 增强图表
            if llm_client.is_available():
                llm_charts = llm_client.generate_echarts_config(prompt, result_data)
                # 如果 LLM 成功生成了图表，使用 LLM 图表
                if llm_charts and len(llm_charts) > 0:
                    echarts_configs = llm_charts
                else:
                    # LLM 失败，使用默认图表
                    echarts_configs = default_charts
            else:
                echarts_configs = default_charts
            
            html_path = dashboards_dir / f"{dashboard_id}.html"
            self._build_html_dashboard(title, echarts_configs, html_path)
            
            return {
                'dashboard_id': dashboard_id,
                'html_path': str(html_path),
                'charts': echarts_configs
            }
            
        except Exception as e:
            raise Exception(f"看板生成失败: {str(e)}")
    
    def _load_result(self, result_path: str) -> dict:
        if os.path.exists(result_path):
            with open(result_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _get_default_charts(self, result_data: dict) -> list:
        """根据分析结果生成默认图表配置"""
        
        charts = []
        
        # 1. 数据概览饼图
        basic_info = result_data.get('basic_info', {})
        if basic_info.get('total_rows'):
            charts.append({
                "title": {"text": "数据概览", "left": "center"},
                "tooltip": {"trigger": "item"},
                "legend": {"orient": "vertical", "left": "left"},
                "series": [{
                    "name": "数据统计",
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "data": [
                        {"name": "总记录数", "value": basic_info.get('total_rows', 0)},
                        {"name": "字段数", "value": basic_info.get('total_columns', 0)},
                        {"name": "重复记录", "value": basic_info.get('duplicate_rows', 0)}
                    ],
                    "itemStyle": {"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2}
                }]
            })
        
        # 2. 数值变量平均值柱状图
        numeric_analysis = result_data.get('numeric_analysis', {})
        if numeric_analysis.get('statistics'):
            stats = numeric_analysis['statistics']
            categories = list(stats.keys())[:6]
            means = [stats[col].get('mean', 0) for col in categories]
            
            charts.append({
                "title": {"text": "数值字段平均值对比", "left": "center"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {
                    "type": "category",
                    "data": [c[:8] for c in categories],
                    "axisLabel": {"rotate": 30}
                },
                "yAxis": {"type": "value"},
                "series": [{
                    "name": "平均值",
                    "type": "bar",
                    "data": [round(m, 2) for m in means],
                    "itemStyle": {
                        "color": {
                            "type": "linear",
                            "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": "#667eea"},
                                {"offset": 1, "color": "#764ba2"}
                            ]
                        },
                        "borderRadius": [5, 5, 0, 0]
                    }
                }]
            })
            
            # 3. 数值变量标准差柱状图
            stds = [stats[col].get('std', 0) for col in categories]
            charts.append({
                "title": {"text": "数值字段标准差", "left": "center"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {
                    "type": "category",
                    "data": [c[:8] for c in categories],
                    "axisLabel": {"rotate": 30}
                },
                "yAxis": {"type": "value"},
                "series": [{
                    "name": "标准差",
                    "type": "bar",
                    "data": [round(s, 2) for s in stds],
                    "itemStyle": {"color": "#f093fb", "borderRadius": [5, 5, 0, 0]}
                }]
            })
        
        # 4. 数据质量评估
        data_quality = result_data.get('data_quality', {})
        if data_quality:
            quality_data = [
                {"name": "完整字段", "value": data_quality.get('total_columns', 18) - data_quality.get('columns_with_missing', 0)},
                {"name": "缺失字段", "value": data_quality.get('columns_with_missing', 0)}
            ]
            charts.append({
                "title": {"text": "数据质量评估", "left": "center"},
                "tooltip": {"trigger": "item"},
                "legend": {"bottom": "5%"},
                "series": [{
                    "name": "数据质量",
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "data": quality_data,
                    "itemStyle": {"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2}
                }]
            })
        
        # 5. 分类变量唯一值数量
        categorical_analysis = result_data.get('categorical_analysis', {})
        if categorical_analysis.get('analysis'):
            cat_data = categorical_analysis['analysis']
            categories = list(cat_data.keys())[:5]
            unique_counts = [cat_data[col].get('unique_values', 0) for col in categories]
            
            charts.append({
                "title": {"text": "分类变量唯一值数量", "left": "center"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {
                    "type": "category",
                    "data": [c[:6] for c in categories],
                    "axisLabel": {"rotate": 30}
                },
                "yAxis": {"type": "value"},
                "series": [{
                    "name": "唯一值数量",
                    "type": "bar",
                    "data": unique_counts,
                    "itemStyle": {"color": "#4facfe", "borderRadius": [5, 5, 0, 0]}
                }]
            })
        
        # 如果没有数据，返回空图表提示
        if not charts:
            charts.append({
                "title": {"text": "暂无数据", "left": "center"},
                "graphic": {
                    "type": "text",
                    "left": "center",
                    "top": "middle",
                    "style": {"text": "请先生成报告以获取分析数据", "fontSize": 16}
                }
            })
        
        return charts
    
    def _build_html_dashboard(self, title: str, charts: list, output_path: Path) -> None:
        """生成HTML看板"""
        
        # 安全序列化图表配置
        safe_charts = []
        for config in charts:
            try:
                # 确保配置是字典
                if isinstance(config, dict):
                    safe_charts.append(config)
                else:
                    safe_charts.append({})
            except:
                safe_charts.append({})
        
        charts_html = ""
        for i in range(len(safe_charts)):
            charts_html += f'''
<div class="chart-card">
    <div id="chart_{i}" style="width: 100%; height: 350px;"></div>
</div>
'''
        
        scripts_html = "<script>\n"
        for i, chart_config in enumerate(safe_charts):
            try:
                config_json = json.dumps(chart_config, ensure_ascii=False, default=str)
                scripts_html += f'''
var chart_{i} = echarts.init(document.getElementById('chart_{i}'));
chart_{i}.setOption({config_json});
'''
            except Exception as e:
                scripts_html += f"console.error('Chart {i} error: {e}');\n"
        scripts_html += "</script>"
        
        html_content = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f5f7fa;
            padding: 20px;
        }}
        .dashboard-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .dashboard-header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .dashboard-header p {{ font-size: 14px; opacity: 0.9; }}
        .charts-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        .chart-card {{
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>📊 {title}</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="charts-container">
        {charts_html}
    </div>
    
    {scripts_html}
</body>
</html>
'''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)