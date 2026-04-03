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
        
        # 分类值（从数据配置动态加载）
        self.gender_values = []
        self.scale_values = []
        self.nature_values = []
        
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
                    # 获取年级信息
                    grade = ''
                    if '年级' in base_data.columns:
                        grades = base_data['年级'].unique()
                        if len(grades) == 1:
                            grade = str(grades[0])
                        elif len(grades) > 1:
                            grade = '多年级'
                    
                    self.data['base_stats'] = {
                        'total_students': len(base_data),
                        'male_count': (base_data['性别'] == '男').sum(),
                        'female_count': (base_data['性别'] == '女').sum(),
                        'schools_count': base_data['学校代码'].nunique() if '学校代码' in base_data.columns else 0,
                        'grade': grade
                    }
                    if verbose:
                        print(f"  ✓ 基础统计数据: {self.data['base_stats']['total_students']}名学生, 年级: {grade}")
                break
        
        # 加载数据配置
        config_path = self.data_source / 'data_config.json'
        if config_path.exists():
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.data['config'] = config
                # 提取分类值
                self.gender_values = config.get('gender_values', [])
                self.scale_values = config.get('scale_values', [])
                self.nature_values = config.get('nature_values', [])
        else:
            self.gender_values = []
            self.scale_values = []
            self.nature_values = []
        
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
        
        # 内嵌 ECharts 脚本（避免 CDN 网络问题）
        echarts_path = self.template_dir.parent / 'static' / 'echarts.min.js'
        if echarts_path.exists():
            with open(echarts_path, 'r', encoding='utf-8') as f:
                echarts_script = f.read()
            # 替换 CDN 引用为内嵌脚本（使用字符串替换避免正则转义问题）
            cdn_pattern = '<script src="https://unpkg.com/echarts@5.4.3/dist/echarts.min.js"></script>'
            if cdn_pattern in html_content:
                html_content = html_content.replace(
                    cdn_pattern,
                    f'<script>\n{echarts_script}\n    </script>'
                )
                if verbose:
                    print(f"  ✓ 已内嵌 ECharts 脚本")
        
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
        """填充仪表盘数据（完全动态，无硬编码）"""
        
        # 获取数据
        indicator_stats = self.data.get('indicator_stats', pd.DataFrame())
        gender_analysis = self.data.get('gender_analysis', pd.DataFrame())
        scale_analysis = self.data.get('scale_analysis', pd.DataFrame())
        nature_analysis = self.data.get('nature_analysis', pd.DataFrame())
        quadrant_analysis = self.data.get('quadrant_analysis', pd.DataFrame())
        school_analysis = self.data.get('school_analysis', pd.DataFrame())
        base_stats = self.data.get('base_stats', {})
        
        # 基础统计（从数据源获取，无硬编码默认值）
        total_students = base_stats.get('total_students', 0)
        male_count = base_stats.get('male_count', 0)
        female_count = base_stats.get('female_count', 0)
        schools_count = base_stats.get('schools_count', 0)
        
        # 如果基础数据未加载，从gender_analysis获取
        if total_students == 0 and len(gender_analysis) > 0:
            male_count = int(gender_analysis[gender_analysis['性别'] == '男']['人数'].sum())
            female_count = int(gender_analysis[gender_analysis['性别'] == '女']['人数'].sum())
            total_students = male_count + female_count
        
        # 如果学校数未获取，从school_analysis获取
        if schools_count == 0 and len(school_analysis) > 0:
            schools_count = len(school_analysis)
        
        male_percent = round((male_count / total_students * 100), 2) if total_students > 0 else 0
        female_percent = round((female_count / total_students * 100), 2) if total_students > 0 else 0
        
        # 风险指标（从数据计算）
        high_risk_count = len(indicator_stats[indicator_stats['风险暴露率(%)'] > 40]) if len(indicator_stats) > 0 else 0
        
        # 第四象限（从数据获取，无硬编码默认值）
        quadrant4 = quadrant_analysis[quadrant_analysis['象限'] == '第四象限-重点关注型'] if len(quadrant_analysis) > 0 else pd.DataFrame()
        quadrant4_count = int(quadrant4['人数'].sum()) if len(quadrant4) > 0 else 0
        quadrant4_percent = round((quadrant4_count / total_students * 100), 2) if total_students > 0 else 0
        
        if verbose:
            print(f"  数据统计：{total_students}名学生，{schools_count}所学校")
            print(f"  性别分布：男生{male_count}人({male_percent}%)，女生{female_count}人({female_percent}%)")
            print(f"  第四象限：{quadrant4_count}人({quadrant4_percent}%)")
        
        # 更新头部信息
        html = html.replace('数据更新时间：2026-04-02', f'数据更新时间：{self.config["update_time"]}')
        
        # 动态更新标题（使用年级信息）
        grade = self.data.get('base_stats', {}).get('grade', '')
        if grade:
            new_subtitle = f'{grade}学生成长环境与学生发展综合分析'
            # 替换所有包含"学生成长环境与学生发展综合分析"的标题
            import re
            html = re.sub(r'[一二三四五六七八九十]+年级学生成长环境与学生发展综合分析', new_subtitle, html)
            # 更新数据来源
            html = html.replace("数据来源：学生指标得分清单", f"数据来源：{grade}学生指标得分清单")
            
        
        # 更新概览卡片数据
        html = self._update_card_value(html, '总学生数', f'{total_students:,}')
        html = self._update_card_desc(html, '总学生数', f'来自{schools_count}所学校')
        html = self._update_card_value(html, '男生占比', f'{male_percent:.2f}%')
        html = self._update_card_desc(html, '男生占比', f'男生{male_count:,}人')
        html = self._update_card_value(html, '女生占比', f'{female_percent:.2f}%')
        html = self._update_card_desc(html, '女生占比', f'女生{female_count:,}人')
        html = self._update_card_value(html, '高风险指标', f'{high_risk_count}个')
        html = self._update_card_value(html, '第四象限学生', f'{quadrant4_percent:.2f}%')
        html = self._update_card_desc(html, '第四象限学生', f'需重点关注：{quadrant4_count:,}人')
        
        # 动态更新办学性质卡片（如果存在）
        if len(self.nature_values) > 0:
            nature_name = self.nature_values[0]
            # 从 nature_analysis 获取数据
            if len(nature_analysis) > 0:
                nature_row = nature_analysis[nature_analysis['办学性质'] == nature_name]
                if len(nature_row) > 0:
                    nature_count = int(nature_row['人数'].values[0])
                    nature_percent = round((nature_count / total_students * 100), 2) if total_students > 0 else 0
                else:
                    nature_count = total_students
                    nature_percent = 100.00
            else:
                nature_count = total_students
                nature_percent = 100.00
            
            # 先更新值和描述（使用旧标题匹配），再更新标题
            old_card_title = '公办学校学生'  # 模板中的默认标题
            new_card_title = f'{nature_name}学校学生'
            
            html = self._update_card_value(html, old_card_title, f'{nature_percent:.2f}%')
            html = self._update_card_desc(html, old_card_title, f'{nature_count:,}人')
            if nature_name != '公办':  # 只有当办学性质不是公办时才更新标题
                html = self._update_card_title(html, old_card_title, new_card_title)
        
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
        
        # 更新数据表格（如果有数据）
        if len(indicator_stats) > 0:
            html = self._update_indicator_table(html, indicator_stats)
        
        if len(quadrant_analysis) > 0:
            html = self._update_quadrant_table(html, quadrant_analysis, total_students)
        
        return html
    
    def _update_card_desc(self, html, card_title, new_desc):
        """更新卡片描述"""
        import re
        pattern = rf'(<div class="card-title">{card_title}</div>\s*<div class="card-value">[^<]+</div>\s*<div class="card-desc">)([^<]+)(</div>)'
        replacement = rf'\g<1>{new_desc}\g<3>'
        return re.sub(pattern, replacement, html)
    
    def _update_card_title(self, html, old_title, new_title):
        """更新卡片标题"""
        import re
        pattern = rf'(<div class="card-title">){old_title}(</div>)'
        replacement = rf'\g<1>{new_title}\g<2>'
        return re.sub(pattern, replacement, html)
    
    def _update_indicator_table(self, html, indicator_stats):
        """更新指标统计表格"""
        # 生成表格行，包含风险等级样式
        def get_risk_class(rate):
            if rate > 40:
                return 'risk-high'
            elif rate > 20:
                return 'risk-medium'
            else:
                return 'risk-low'
        
        def get_risk_icon(rate):
            if rate > 40:
                return '❌ 高风险'
            elif rate > 20:
                return '⚠️ 中风险'
            else:
                return '✅ 低风险'
        
        rows = []
        for _, row in indicator_stats.iterrows():
            rate = row['风险暴露率(%)']
            risk_class = get_risk_class(rate)
            risk_icon = get_risk_icon(rate)
            rows.append(f'''                    <tr>
                        <td>{row['指标']}</td>
                        <td>{row['平均分']:.2f}</td>
                        <td class="{risk_class}">{rate:.2f}%</td>
                        <td>{risk_icon}</td>
                    </tr>''')
        
        table_content = '\n'.join(rows)
        
        # 替换表格内容 - 查找指标统计表格的tbody
        import re
        # 匹配"各指标详细数据"后面的第一个tbody
        pattern = r'(<div class="section-title">📊 各指标详细数据</div>.*?<tbody>)(.*?)(</tbody>)'
        replacement = rf'\1\n{table_content}\n                \3'
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)
        
        return html
    
    def _update_quadrant_table(self, html, quadrant_analysis, total_students):
        """更新四象限表格"""
        rows = []
        quadrant_order = ['第一象限-优势发展型', '第二象限-逆境成长型', 
                         '第三象限-潜力待发型', '第四象限-重点关注型']
        
        # 特征和建议
        features = {
            '第一象限-优势发展型': '成长环境良好，学生发展优秀',
            '第二象限-逆境成长型': '成长环境欠佳，学生发展良好',
            '第三象限-潜力待发型': '成长环境良好，学生发展欠佳',
            '第四象限-重点关注型': '成长环境欠佳，学生发展欠佳'
        }
        
        suggestions = {
            '第一象限-优势发展型': '继续保持优势，提供拓展资源',
            '第二象限-逆境成长型': '关注环境因素，预防潜在风险',
            '第三象限-潜力待发型': '激发学习兴趣，提供个性化指导',
            '第四象限-重点关注型': '优先干预，建立多维度帮扶体系'
        }
        
        bg_colors = {
            '第一象限-优势发展型': '#e8f5e9',
            '第二象限-逆境成长型': '#e3f2fd',
            '第三象限-潜力待发型': '#fff8e1',
            '第四象限-重点关注型': '#ffebee'
        }
        
        for quadrant in quadrant_order:
            q_data = quadrant_analysis[quadrant_analysis['象限'] == quadrant]
            if len(q_data) > 0:
                count = int(q_data['人数'].values[0])
                percent = count / total_students * 100 if total_students > 0 else 0
                
                short_name = quadrant.split('-')[0]
                type_name = quadrant.split('-')[1] if '-' in quadrant else quadrant
                
                rows.append(f'''                    <tr style="background: {bg_colors.get(quadrant, '#fff')};">
                        <td><strong>{short_name}</strong><br>{type_name}</td>
                        <td>{count:,}</td>
                        <td>{percent:.2f}%</td>
                        <td>{features.get(quadrant, '')}</td>
                        <td>{suggestions.get(quadrant, '')}</td>
                    </tr>''')
        
        table_content = '\n'.join(rows)
        
        # 替换表格内容 - 匹配正确的表格标题
        import re
        # 匹配"四象限干预建议"后面的第一个tbody
        pattern = r'(<div class="section-title">💡 四象限干预建议</div>.*?<tbody>)(.*?)(</tbody>)'
        replacement = rf'\1\n{table_content}\n                \3'
        html = re.sub(pattern, replacement, html, flags=re.DOTALL)
        
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
        """生成图表3：性别差异对比（动态列检测）"""
        male_data = gender_analysis[gender_analysis['性别'] == '男']
        female_data = gender_analysis[gender_analysis['性别'] == '女']
        
        if len(male_data) == 0 or len(female_data) == 0:
            return ''
        
        # 动态检测可用的指标列
        # 查找包含关键词的列名
        def find_column(columns, keywords):
            for col in columns:
                for kw in keywords:
                    if kw in str(col):
                        return col
            return None
        
        columns = gender_analysis.columns.tolist()
        
        # 基础分数列
        env_col = find_column(columns, ['成长环境均分', '成长环境_均分']) or '成长环境均分'
        dev_col = find_column(columns, ['学生发展均分', '学生发展_均分']) or '学生发展均分'
        
        # 动态选择4个代表性指标列
        indicator_cols = []
        indicator_labels = []
        
        # 优先选择：身心健康相关
        health_col = find_column(columns, ['身心健康', '情绪状态', '运动健康'])
        if health_col:
            indicator_cols.append(health_col)
            indicator_labels.append('身心健康' if '身心健康' in health_col else '情绪状态' if '情绪状态' in health_col else '运动健康')
        
        # 学习创新机会
        innovation_col = find_column(columns, ['学习创新机会', '创新'])
        if innovation_col:
            indicator_cols.append(innovation_col)
            indicator_labels.append('学习创新机会')
        
        # 学习习惯
        habit_col = find_column(columns, ['学习习惯', '习惯'])
        if habit_col:
            indicator_cols.append(habit_col)
            indicator_labels.append('学习习惯')
        
        # 学业达标
        achievement_col = find_column(columns, ['学业达标', '达标'])
        if achievement_col:
            indicator_cols.append(achievement_col)
            indicator_labels.append('学业达标')
        
        # 如果指标列不足4个，用其他可用列补充
        available_cols = [c for c in columns if c not in ['性别', '人数', env_col, dev_col] and c not in indicator_cols]
        while len(indicator_cols) < 4 and available_cols:
            col = available_cols.pop(0)
            indicator_cols.append(col)
            # 简化列名显示
            label = col.split('_')[-1] if '_' in col else col
            indicator_labels.append(label)
        
        # 构建数据
        categories = ['成长环境均分', '学生发展均分'] + indicator_labels[:4]
        
        male_scores = [
            round(male_data[env_col].values[0], 2) if env_col in male_data.columns else 0,
            round(male_data[dev_col].values[0], 2) if dev_col in male_data.columns else 0
        ]
        for col in indicator_cols[:4]:
            if col in male_data.columns:
                male_scores.append(round(male_data[col].values[0], 2))
            else:
                male_scores.append(0)
        
        female_scores = [
            round(female_data[env_col].values[0], 2) if env_col in female_data.columns else 0,
            round(female_data[dev_col].values[0], 2) if dev_col in female_data.columns else 0
        ]
        for col in indicator_cols[:4]:
            if col in female_data.columns:
                female_scores.append(round(female_data[col].values[0], 2))
            else:
                female_scores.append(0)
        
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
                data: {json.dumps(categories)}
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
        """生成图表4：学校定位图（动态范围）"""
        school_data = []
        env_scores = []
        dev_scores = []
        
        for _, row in school_analysis.iterrows():
            env_score = round(row.get('成长环境_均分', 0), 2)
            dev_score = round(row.get('学生发展_均分', 0), 2)
            student_count = int(row.get('学生人数', 0))
            school_code = str(row.get('学校代码', ''))
            
            school_data.append([env_score, dev_score, student_count, school_code])
            env_scores.append(env_score)
            dev_scores.append(dev_score)
        
        # 动态计算坐标轴范围
        env_min = min(env_scores) if env_scores else 60
        env_max = max(env_scores) if env_scores else 90
        dev_min = min(dev_scores) if dev_scores else 60
        dev_max = max(dev_scores) if dev_scores else 85
        
        # 添加边距
        env_range = env_max - env_min
        dev_range = dev_max - dev_min
        env_min = max(0, env_min - env_range * 0.1)
        env_max = min(100, env_max + env_range * 0.1)
        dev_min = max(0, dev_min - dev_range * 0.1)
        dev_max = min(100, dev_max + dev_range * 0.1)
        
        # 动态计算中位数参考线
        env_median = round(pd.Series(env_scores).median(), 2) if env_scores else 73
        dev_median = round(pd.Series(dev_scores).median(), 2) if dev_scores else 72
        
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
                min: {round(env_min, 1)},
                max: {round(env_max, 1)}
            }},
            yAxis: {{
                type: 'value',
                name: '学生发展均分',
                nameLocation: 'middle',
                nameGap: 40,
                min: {round(dev_min, 1)},
                max: {round(dev_max, 1)}
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
                    {{ xAxis: {env_median}, lineStyle: {{ color: '#FF6B6B', type: 'dashed', opacity: 0.5 }} }},
                    {{ yAxis: {dev_median}, lineStyle: {{ color: '#FF6B6B', type: 'dashed', opacity: 0.5 }} }}
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
        """生成图表7：办学性质对比（动态标题）"""
        natures = nature_analysis['办学性质'].tolist()
        env_scores = [round(s, 2) for s in nature_analysis['成长环境均分'].tolist()]
        dev_scores = [round(s, 2) for s in nature_analysis['学生发展均分'].tolist()]
        
        # 动态生成标题
        if len(natures) == 1:
            chart_title = f'{natures[0]}学校学生发展分析'
        else:
            chart_title = '、'.join(natures) + '学校对比'
        
        return f'''const chart7 = echarts.init(document.getElementById('chart7'));
        const option7 = {{
            title: {{
                text: '{chart_title}',
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