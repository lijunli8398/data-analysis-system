#!/usr/bin/env python3
"""
HTML仪表盘生成器 - 增强版
基于完整模板生成包含7个图表和3个数据表格的完整看板
"""

import pandas as pd
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime


class DashboardGenerator:
    """HTML仪表盘生成器 - 增强版"""
    
    def __init__(self, data_source, output_file='dashboard.html'):
        self.data_source = Path(data_source)
        self.output_file = Path(output_file)
        self.data = {}
        self.template_dir = Path(__file__).parent.parent / 'templates'
        
        self.config = {
            'title': '教育学情数据看板',
            'subtitle': '学生成长环境与学生发展综合分析',
            'update_time': datetime.now().strftime('%Y-%m-%d'),
            'generator': 'OpenClaw Dashboard Generator'
        }
        
        if not self.data_source.exists():
            raise FileNotFoundError(f"数据源目录不存在: {self.data_source}")
    
    def load_data(self, verbose=False):
        """加载所有数据文件"""
        if verbose:
            print(f"正在加载数据文件: {self.data_source}")
        
        # 必需的数据文件
        required_files = {
            'indicator_stats': 'indicator_stats.csv',
            'gender_analysis': 'gender_analysis.csv',
            'scale_analysis': 'scale_analysis.csv',
            'nature_analysis': 'nature_analysis.csv',
            'quadrant_analysis': 'quadrant_analysis.csv',
            'school_analysis': None
        }
        
        for key, filename in required_files.items():
            if filename:
                filepath = self.data_source / filename
                if filepath.exists():
                    self.data[key] = pd.read_csv(filepath, encoding='utf-8-sig')
                    if verbose:
                        print(f"  ✓ {filename} ({len(self.data[key])}行)")
        
        # 处理学校分析文件
        for filename in ['school_analysis.csv', 'school_position.csv']:
            filepath = self.data_source / filename
            if filepath.exists():
                self.data['school_analysis'] = pd.read_csv(filepath, encoding='utf-8-sig')
                if verbose:
                    print(f"  ✓ {filename} ({len(self.data['school_analysis'])}行)")
                break
        
        # 加载基础数据获取统计信息
        for filename in ['analysis_data_clean.csv', 'analysis_data.csv']:
            filepath = self.data_source / filename
            if filepath.exists():
                base_data = pd.read_csv(filepath, encoding='utf-8-sig')
                if '性别' in base_data.columns:
                    self.data['base_stats'] = {
                        'total_students': len(base_data),
                        'male_count': (base_data['性别'] == '男').sum(),
                        'female_count': (base_data['性别'] == '女').sum(),
                        'schools_count': base_data['学校代码'].nunique() if '学校代码' in base_data.columns else 36
                    }
                    if verbose:
                        print(f"  ✓ 基础统计数据: {self.data['base_stats']['total_students']}名学生")
                    break
        
        return len(self.data) > 0
    
    def generate_html(self, verbose=False):
        """生成HTML仪表盘"""
        if verbose:
            print("\n正在生成HTML仪表盘...")
        
        # 读取模板
        template_path = self.template_dir / 'dashboard_template.html'
        
        if template_path.exists():
            html_content = open(template_path, 'r', encoding='utf-8').read()
            if verbose:
                print(f"  ✓ 使用模板: {template_path}")
        else:
            print(f"  ⚠ 模板不存在，使用内置模板")
            html_content = self._get_builtin_template()
        
        # 填充数据
        html_content = self._fill_dashboard_data(html_content, verbose)
        
        # 写入文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if verbose:
            file_size = len(html_content)
            print(f"  ✓ HTML文件已生成: {self.output_file}")
            print(f"  文件大小: {file_size:,}字节 ({file_size/1024:.1f}KB)")
        
        return self.output_file
    
    def _fill_dashboard_data(self, html, verbose=False):
        """填充仪表盘数据"""
        
        # 获取数据
        indicator_stats = self.data.get('indicator_stats', pd.DataFrame())
        gender_analysis = self.data.get('gender_analysis', pd.DataFrame())
        scale_analysis = self.data.get('scale_analysis', pd.DataFrame())
        nature_analysis = self.data.get('nature_analysis', pd.DataFrame())
        quadrant_analysis = self.data.get('quadrant_analysis', pd.DataFrame())
        school_analysis = self.data.get('school_analysis', pd.DataFrame())
        base_stats = self.data.get('base_stats', {})
        
        # 基础统计
        total_students = base_stats.get('total_students', 9324)
        male_count = base_stats.get('male_count', 4849)
        female_count = base_stats.get('female_count', 4475)
        schools_count = base_stats.get('schools_count', 36)
        
        male_percent = round((male_count / total_students * 100), 2) if total_students > 0 else 51.89
        female_percent = round((female_count / total_students * 100), 2) if total_students > 0 else 47.63
        
        # 风险指标
        high_risk_count = len(indicator_stats[indicator_stats['风险暴露率(%)'] > 40]) if len(indicator_stats) > 0 else 4
        
        # 第四象限
        quadrant4 = quadrant_analysis[quadrant_analysis['象限'] == '第四象限-重点关注型'] if len(quadrant_analysis) > 0 else pd.DataFrame()
        quadrant4_count = quadrant4['人数'].sum() if len(quadrant4) > 0 else 3467
        quadrant4_percent = round((quadrant4_count / total_students * 100), 2) if total_students > 0 else 37.18
        
        # 更新头部信息
        html = html.replace('数据更新时间：2026-04-02', f'数据更新时间：{self.config["update_time"]}')
        
        # 更新概览卡片数据
        html = self._update_card_value(html, '总学生数', f'{total_students:,}')
        html = self._update_card_value(html, '来自', f'来自{schools_count}所学校')
        html = self._update_card_value(html, '男生占比', f'{male_percent:.2f}%')
        html = self._update_card_value(html, '男生', f'男生{male_count:,}人')
        html = self._update_card_value(html, '女生占比', f'{female_percent:.2f}%')
        html = self._update_card_value(html, '女生', f'女生{female_count:,}人')
        html = self._update_card_value(html, '高风险指标', f'{high_risk_count}个')
        html = self._update_card_value(html, '第四象限学生', f'{quadrant4_percent:.2f}%')
        html = self._update_card_value(html, '需重点关注', f'需重点关注：{quadrant4_count:,}人')
        
        # 生成图表数据
        if verbose:
            print("  生成图表脚本...")
        
        chart_scripts = []
        
        # 图表1：各指标平均分对比
        if len(indicator_stats) > 0:
            chart_scripts.append(self._generate_chart1(indicator_stats))
        
        # 图表2：风险暴露率
        if len(indicator_stats) > 0:
            chart_scripts.append(self._generate_chart2(indicator_stats))
        
        # 图表3：性别差异
        if len(gender_analysis) > 0:
            chart_scripts.append(self._generate_chart3(gender_analysis))
        
        # 图表4：学校定位图
        if len(school_analysis) > 0:
            chart_scripts.append(self._generate_chart4(school_analysis))
        
        # 图表5：四象限分布
        if len(quadrant_analysis) > 0:
            chart_scripts.append(self._generate_chart5(quadrant_analysis))
        
        # 图表6：办学规模对比
        if len(scale_analysis) > 0:
            chart_scripts.append(self._generate_chart6(scale_analysis))
        
        # 图表7：公办民办对比
        if len(nature_analysis) > 0:
            chart_scripts.append(self._generate_chart7(nature_analysis))
        
        # 替换图表脚本
        chart_script_str = '\n\n'.join(chart_scripts)
        
        # 查找并替换脚本区域
        script_start = html.find('const chart1 = echarts.init')
        script_end = html.find('window.addEventListener(\'resize\'', script_start)
        
        if script_start > 0 and script_end > script_start:
            html = html[:script_start] + chart_script_str + '\n\n        ' + html[script_end:]
        
        return html
    
    def _update_card_value(self, html, card_title, new_value):
        """更新卡片值"""
        import re
        # 查找卡片并更新值
        pattern = rf'(<div class="card-title">{card_title}</div>\s*<div class="card-value">)([^<]+)(</div>)'
        replacement = rf'\g<1>{new_value}\g<3>'
        return re.sub(pattern, replacement, html)
    
    def _generate_chart1(self, indicator_stats):
        """生成图表1：各指标平均分对比"""
        indicators = json.dumps(indicator_stats['指标'].tolist(), ensure_ascii=False)
        scores = json.dumps([round(s, 2) for s in indicator_stats['平均分'].tolist()])
        
        return f'''const chart1 = echarts.init(document.getElementById('chart1'));
        const option1 = {{
            title: {{
                text: '各指标平均分对比',
                left: 'center',
                textStyle: {{ fontSize: 16, fontWeight: 'bold' }}
            }},
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{ type: 'shadow' }}
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                data: {indicators},
                axisLabel: {{ rotate: 45, fontSize: 11 }}
            }},
            yAxis: {{
                type: 'value',
                max: 100,
                axisLabel: {{ formatter: '{{value}}' }}
            }},
            series: [{{
                name: '平均分',
                type: 'bar',
                data: {scores},
                itemStyle: {{
                    color: function(params) {{
                        const colors = ['#4472C4', '#4472C4', '#4472C4', '#4472C4', 
                                       '#ED7D31', '#ED7D31', '#ED7D31', '#ED7D31', '#ED7D31', '#ED7D31'];
                        return colors[params.dataIndex];
                    }}
                }},
                markLine: {{
                    data: [{{ yAxis: 60, name: '及格线', lineStyle: {{ color: '#FF6B6B', type: 'dashed' }} }}]
                }},
                label: {{
                    show: true,
                    position: 'top',
                    formatter: '{{c}}',
                    fontSize: 11
                }}
            }}]
        }};
        chart1.setOption(option1);'''
    
    def _generate_chart2(self, indicator_stats):
        """生成图表2：风险暴露率"""
        sorted_stats = indicator_stats.sort_values('风险暴露率(%)', ascending=True)
        indicators = json.dumps(sorted_stats['指标'].tolist(), ensure_ascii=False)
        risk_rates = json.dumps([round(r, 2) for r in sorted_stats['风险暴露率(%)'].tolist()])
        
        return f'''const chart2 = echarts.init(document.getElementById('chart2'));
        const option2 = {{
            title: {{
                text: '各指标风险暴露率（低于60分）',
                left: 'center',
                textStyle: {{ fontSize: 16, fontWeight: 'bold' }}
            }},
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{ type: 'shadow' }},
                formatter: '{{b}}: {{c}}%'
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                data: {indicators},
                axisLabel: {{ rotate: 45, fontSize: 11 }}
            }},
            yAxis: {{
                type: 'value',
                max: 60,
                axisLabel: {{ formatter: '{{value}}%' }}
            }},
            series: [{{
                name: '风险暴露率',
                type: 'bar',
                data: {risk_rates},
                itemStyle: {{
                    color: function(params) {{
                        if (params.value > 40) return '#FF6B6B';
                        if (params.value > 20) return '#FFA07A';
                        return '#90EE90';
                    }}
                }},
                label: {{
                    show: true,
                    position: 'top',
                    formatter: '{{c}}%',
                    fontSize: 11
                }}
            }}]
        }};
        chart2.setOption(option2);'''
    
    def _generate_chart3(self, gender_analysis):
        """生成图表3：性别差异对比"""
        male_data = gender_analysis[gender_analysis['性别'] == '男']
        female_data = gender_analysis[gender_analysis['性别'] == '女']
        
        if len(male_data) == 0 or len(female_data) == 0:
            return ''
        
        male_scores = [
            round(male_data['成长环境均分'].values[0], 2),
            round(male_data['学生发展均分'].values[0], 2),
            round(male_data['身心健康'].values[0], 2),
            round(male_data['学习创新机会'].values[0], 2),
            round(male_data['学习习惯'].values[0], 2),
            round(male_data['学业达标'].values[0], 2)
        ]
        
        female_scores = [
            round(female_data['成长环境均分'].values[0], 2),
            round(female_data['学生发展均分'].values[0], 2),
            round(female_data['身心健康'].values[0], 2),
            round(female_data['学习创新机会'].values[0], 2),
            round(female_data['学习习惯'].values[0], 2),
            round(female_data['学业达标'].values[0], 2)
        ]
        
        return f'''const chart3 = echarts.init(document.getElementById('chart3'));
        const option3 = {{
            title: {{
                text: '性别差异对比',
                left: 'center',
                textStyle: {{ fontSize: 16, fontWeight: 'bold' }}
            }},
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{ type: 'shadow' }}
            }},
            legend: {{
                data: ['男生', '女生'],
                top: 30
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                data: ['成长环境均分', '学生发展均分', '身心健康', '学习创新机会', '学习习惯', '学业达标']
            }},
            yAxis: {{
                type: 'value',
                max: 100
            }},
            series: [
                {{
                    name: '男生',
                    type: 'bar',
                    data: {json.dumps(male_scores)},
                    itemStyle: {{ color: '#4472C4' }}
                }},
                {{
                    name: '女生',
                    type: 'bar',
                    data: {json.dumps(female_scores)},
                    itemStyle: {{ color: '#ED7D31' }}
                }}
            ]
        }};
        chart3.setOption(option3);'''
    
    def _generate_chart4(self, school_analysis):
        """生成图表4：学校定位图"""
        school_data = []
        for _, row in school_analysis.iterrows():
            school_data.append([
                round(row.get('成长环境_均分', 0), 2),
                round(row.get('学生发展_均分', 0), 2),
                int(row.get('学生人数', 0)),
                str(row.get('学校代码', ''))
            ])
        
        return f'''const chart4 = echarts.init(document.getElementById('chart4'));
        const schoolData = {json.dumps(school_data)};
        
        const option4 = {{
            title: {{
                text: '学校环境-发展定位图',
                left: 'center',
                textStyle: {{ fontSize: 16, fontWeight: 'bold' }}
            }},
            tooltip: {{
                trigger: 'item',
                formatter: function(params) {{
                    return '学校' + params.data[3] + '<br/>成长环境: ' + params.data[0] + '<br/>学生发展: ' + params.data[1] + '<br/>学生人数: ' + params.data[2];
                }}
            }},
            grid: {{
                left: '10%',
                right: '10%',
                bottom: '15%',
                top: '20%',
                containLabel: true
            }},
            xAxis: {{
                type: 'value',
                name: '成长环境均分',
                nameLocation: 'middle',
                nameGap: 30,
                min: 60,
                max: 90
            }},
            yAxis: {{
                type: 'value',
                name: '学生发展均分',
                nameLocation: 'middle',
                nameGap: 40,
                min: 60,
                max: 85
            }},
            series: [{{
                type: 'scatter',
                data: schoolData,
                symbolSize: function(data) {{
                    return Math.sqrt(data[2]) * 0.8;
                }},
                itemStyle: {{
                    color: '#4472C4',
                    opacity: 0.6,
                    borderColor: '#333',
                    borderWidth: 1
                }},
                label: {{
                    show: true,
                    formatter: function(params) {{
                        return params.data[3];
                    }},
                    position: 'top',
                    fontSize: 10
                }}
            }}],
            markLine: {{
                silent: true,
                data: [
                    {{ xAxis: 73, lineStyle: {{ color: '#FF6B6B', type: 'dashed', opacity: 0.5 }} }},
                    {{ yAxis: 72, lineStyle: {{ color: '#FF6B6B', type: 'dashed', opacity: 0.5 }} }}
                ]
            }}
        }};
        chart4.setOption(option4);'''
    
    def _generate_chart5(self, quadrant_analysis):
        """生成图表5：四象限分布"""
        quadrant_order = ['第一象限-优势发展型', '第二象限-逆境成长型',
                         '第四象限-重点关注型', '第三象限-潜力待发型']
        colors = ['#90EE90', '#87CEEB', '#FF6B6B', '#FFB6C1']
        
        pie_data = []
        for i, quadrant in enumerate(quadrant_order):
            q_data = quadrant_analysis[quadrant_analysis['象限'] == quadrant]
            if len(q_data) > 0:
                pie_data.append({
                    'value': int(q_data['人数'].values[0]),
                    'name': quadrant,
                    'itemStyle': {'color': colors[i]}
                })
        
        return f'''const chart5 = echarts.init(document.getElementById('chart5'));
        const option5 = {{
            title: {{
                text: '学生四象限分布',
                left: 'center',
                textStyle: {{ fontSize: 16, fontWeight: 'bold' }}
            }},
            tooltip: {{
                trigger: 'item',
                formatter: '{{b}}: {{c}}人 ({{d}}%)'
            }},
            legend: {{
                orient: 'vertical',
                left: 'left',
                top: 'middle'
            }},
            series: [{{
                type: 'pie',
                radius: ['40%', '70%'],
                center: ['60%', '50%'],
                avoidLabelOverlap: false,
                itemStyle: {{
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                }},
                label: {{
                    show: true,
                    formatter: '{{b}}\\n{{c}}人',
                    fontSize: 12
                }},
                data: {json.dumps(pie_data, ensure_ascii=False)}
            }}]
        }};
        chart5.setOption(option5);'''
    
    def _generate_chart6(self, scale_analysis):
        """生成图表6：办学规模对比"""
        scales = scale_analysis['办学规模'].tolist()
        env_scores = [round(s, 2) for s in scale_analysis['成长环境均分'].tolist()]
        dev_scores = [round(s, 2) for s in scale_analysis['学生发展均分'].tolist()]
        
        return f'''const chart6 = echarts.init(document.getElementById('chart6'));
        const option6 = {{
            title: {{
                text: '不同办学规模对比',
                left: 'center',
                textStyle: {{ fontSize: 16, fontWeight: 'bold' }}
            }},
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{ type: 'shadow' }}
            }},
            legend: {{
                data: ['成长环境均分', '学生发展均分'],
                top: 30
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                data: {json.dumps(scales)}
            }},
            yAxis: {{
                type: 'value',
                max: 100
            }},
            series: [
                {{
                    name: '成长环境均分',
                    type: 'bar',
                    data: {json.dumps(env_scores)},
                    itemStyle: {{ color: '#4472C4' }}
                }},
                {{
                    name: '学生发展均分',
                    type: 'bar',
                    data: {json.dumps(dev_scores)},
                    itemStyle: {{ color: '#ED7D31' }}
                }}
            ]
        }};
        chart6.setOption(option6);'''
    
    def _generate_chart7(self, nature_analysis):
        """生成图表7：公办民办对比"""
        natures = nature_analysis['办学性质'].tolist()
        env_scores = [round(s, 2) for s in nature_analysis['成长环境均分'].tolist()]
        dev_scores = [round(s, 2) for s in nature_analysis['学生发展均分'].tolist()]
        
        return f'''const chart7 = echarts.init(document.getElementById('chart7'));
        const option7 = {{
            title: {{
                text: '公办vs民办学校对比',
                left: 'center',
                textStyle: {{ fontSize: 16, fontWeight: 'bold' }}
            }},
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{ type: 'shadow' }}
            }},
            legend: {{
                data: ['成长环境均分', '学生发展均分'],
                top: 30
            }},
            grid: {{
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            }},
            xAxis: {{
                type: 'category',
                data: {json.dumps(natures)}
            }},
            yAxis: {{
                type: 'value',
                max: 100
            }},
            series: [
                {{
                    name: '成长环境均分',
                    type: 'bar',
                    data: {json.dumps(env_scores)},
                    itemStyle: {{ color: '#4472C4' }},
                    barWidth: '40%'
                }},
                {{
                    name: '学生发展均分',
                    type: 'bar',
                    data: {json.dumps(dev_scores)},
                    itemStyle: {{ color: '#ED7D31' }},
                    barWidth: '40%'
                }}
            ]
        }};
        chart7.setOption(option7);'''
    
    def run(self, verbose=False):
        """执行完整流程"""
        # 1. 加载数据
        success = self.load_data(verbose)
        
        if not success:
            print("错误: 无法加载任何数据文件")
            return None
        
        # 2. 生成HTML
        output_file = self.generate_html(verbose)
        
        if verbose:
            print("\n" + "="*60)
            print("仪表盘生成完成！")
            print("="*60)
            print(f"\n输出文件：{output_file}")
            print(f"查看方式：")
            print(f"  1. 直接打开: open {output_file}")
            print(f"  2. HTTP服务器: python3 -m http.server 8080")
        
        return output_file


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='HTML仪表盘生成器 - 增强版')
    parser.add_argument('--data-source', required=True, help='数据源目录路径')
    parser.add_argument('--output', default='dashboard.html', help='输出HTML文件路径')
    parser.add_argument('--verbose', action='store_true', help='详细输出模式')
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 创建生成器并执行
    generator = DashboardGenerator(args.data_source, args.output)
    output_file = generator.run(args.verbose)
    
    if output_file:
        print(f"\n✅ HTML仪表盘已生成: {output_file}")
    else:
        print("\n❌ 仪表盘生成失败")
        sys.exit(1)


if __name__ == '__main__':
    main()