#!/usr/bin/env python3
"""
教育学情数据分析脚本

Usage:
    python education_analysis.py --data <data_file> [--output <output_dir>] [--verbose]
    
Example:
    python education_analysis.py --data data/学生指标得分清单.xlsx
    python education_analysis.py --data data/学生指标得分清单.xlsx --output custom_output --verbose
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import argparse
import sys
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体（使用系统已安装的字体）
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'Noto Sans CJK', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300

# 验证字体是否可用
import matplotlib.font_manager as fm
available_fonts = [f.name for f in fm.fontManager.ttflist]
chinese_fonts = [f for f in available_fonts if 'Noto' in f or 'WenQuanYi' in f or 'CJK' in f]
if chinese_fonts:
    plt.rcParams['font.sans-serif'] = chinese_fonts + ['DejaVu Sans']
    print(f"使用中文字体: {chinese_fonts[0]}")


class EducationDataAnalyzer:
    """教育学情数据分析器"""
    
    def __init__(self, data_path, output_dir='output'):
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.df = None
        self.df_clean = None
        
        # 指标名称映射
        self.indicator_names = {
            '成长环境_亲子关系': '亲子关系',
            '成长环境_师生关系': '师生关系',
            '成长环境_同伴关系': '同伴关系',
            '成长环境_校园安全': '校园安全',
            '学生发展_身心健康': '身心健康',
            '学生发展_情绪状态': '情绪状态',
            '学生发展_运动健康': '运动健康',
            '学生发展_学习创新机会': '学习创新机会',
            '学生发展_学习习惯': '学习习惯',
            '学生发展_学业达标': '学业达标'
        }
        
        # 成长环境指标列表
        self.env_indicators = [
            '成长环境_亲子关系',
            '成长环境_师生关系',
            '成长环境_同伴关系',
            '成长环境_校园安全'
        ]
        
        # 学生发展指标列表
        self.dev_indicators = [
            '学生发展_身心健康',
            '学生发展_情绪状态',
            '学生发展_运动健康',
            '学生发展_学习创新机会',
            '学生发展_学习习惯',
            '学生发展_学业达标'
        ]
        
        # 所有指标列表
        self.all_indicators = self.env_indicators + self.dev_indicators
        
        # 风险阈值
        self.risk_threshold = 60
        
        # 创建输出目录
        self._create_output_dirs()
        
    def _create_output_dirs(self):
        """创建输出目录结构"""
        dirs = ['data', 'report', 'report_charts']
        for dir_name in dirs:
            (self.output_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    def load_data(self, verbose=False):
        """加载并清洗数据"""
        if verbose:
            print(f"正在加载数据: {self.data_path}")
        
        # 读取原始数据
        df_raw = pd.read_excel(self.data_path, header=None)
        
        if verbose:
            print(f"原始数据维度: {df_raw.shape}")
        
        # 处理多级表头（跳过前3行）
        columns = ['办学规模', '办学性质', '学校代码', '年级', '班级', '考号', '姓名', '性别',
                   '成长环境_亲子关系', '成长环境_师生关系', '成长环境_同伴关系', '成长环境_校园安全',
                   '学生发展_身心健康', '学生发展_情绪状态', '学生发展_运动健康', 
                   '学生发展_学习创新机会', '学生发展_学习习惯', '学生发展_学业达标']
        
        df = df_raw.iloc[3:].copy()
        df.columns = columns
        df = df.reset_index(drop=True)
        
        # 转换数值列
        numeric_cols = self.all_indicators + ['成长环境_均分', '学生发展_均分']
        
        for col in self.all_indicators:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 计算综合得分
        df['成长环境_均分'] = df[self.env_indicators].mean(axis=1)
        df['学生发展_均分'] = df[self.dev_indicators].mean(axis=1)
        
        # 清理脏数据
        df_clean = df[~df['办学规模'].isin(['办学规模', '办学性质', '性别'])].copy()
        df_clean = df_clean[~df_clean['性别'].isin(['办学规模', '办学性质', '性别'])].copy()
        
        # 删除含缺失值的行
        df_clean = df_clean.dropna(subset=self.all_indicators + ['成长环境_均分', '学生发展_均分'])
        
        self.df = df
        self.df_clean = df_clean
        
        if verbose:
            print(f"清洗后数据量: {len(df_clean)}条记录")
            print(f"学校数量: {df_clean['学校代码'].nunique()}所")
        
        # 保存清洗后的数据
        df_clean.to_csv(self.output_dir / 'data' / 'analysis_data_clean.csv', 
                        index=False, encoding='utf-8-sig')
        
        return df_clean
    
    def analyze_overall(self, verbose=False):
        """整体学情分析"""
        if verbose:
            print("\n="*60)
            print("二、整体学情画像分析")
            print("="*60)
        
        df = self.df_clean
        
        # 1. 数据概况
        total_students = len(df)
        total_schools = df['学校代码'].nunique()
        
        gender_dist = df['性别'].value_counts()
        nature_dist = df['办学性质'].value_counts()
        scale_dist = df['办学规模'].value_counts()
        
        stats_summary = {
            '总学生数': total_students,
            '学校数量': total_schools,
            '男生数': gender_dist.get('男', 0),
            '女生数': gender_dist.get('女', 0),
            '公办学校学生数': nature_dist.get('公办', 0),
            '民办学校学生数': nature_dist.get('民办', 0)
        }
        
        if verbose:
            print(f"\n总样本量：{total_students}名学生")
            print(f"学校数量：{total_schools}所学校")
            print(f"男生：{gender_dist.get('男', 0)}人 ({gender_dist.get('男', 0)/total_students*100:.2f}%)")
            print(f"女生：{gender_dist.get('女', 0)}人 ({gender_dist.get('女', 0)/total_students*100:.2f}%)")
        
        # 保存基本统计
        with open(self.output_dir / 'data' / 'stats_summary.txt', 'w', encoding='utf-8') as f:
            f.write("教育学情数据基本统计\n")
            f.write("="*60 + "\n\n")
            f.write(f"总样本量：{total_students}名学生\n")
            f.write(f"学校数量：{total_schools}所学校\n\n")
            f.write("性别分布：\n")
            f.write(f"  男生：{gender_dist.get('男', 0)}人 ({gender_dist.get('男', 0)/total_students*100:.2f}%)\n")
            f.write(f"  女生：{gender_dist.get('女', 0)}人 ({gender_dist.get('女', 0)/total_students*100:.2f}%)\n\n")
            f.write("办学性质分布：\n")
            f.write(f"  公办：{nature_dist.get('公办', 0)}人 ({nature_dist.get('公办', 0)/total_students*100:.2f}%)\n")
            f.write(f"  民办：{nature_dist.get('民办', 0)}人 ({nature_dist.get('民办', 0)/total_students*100:.2f}%)\n\n")
            f.write("办学规模分布：\n")
            for scale, count in scale_dist.items():
                f.write(f"  {scale}：{count}人 ({count/total_students*100:.2f}%)\n")
        
        # 2. 各指标统计
        avg_scores = df[self.all_indicators].mean()
        risk_rates = {}
        
        for col in self.all_indicators:
            risk_rate = (df[col] < self.risk_threshold).sum() / len(df) * 100
            risk_rates[col] = risk_rate
        
        # 保存指标统计
        indicator_stats = pd.DataFrame({
            '指标': [self.indicator_names[col] for col in self.all_indicators],
            '平均分': [avg_scores[col] for col in self.all_indicators],
            '风险暴露率(%)': [risk_rates[col] for col in self.all_indicators]
        })
        
        indicator_stats.to_csv(self.output_dir / 'data' / 'indicator_stats.csv', 
                                index=False, encoding='utf-8-sig')
        
        if verbose:
            print("\n各指标平均分：")
            for col in self.all_indicators:
                print(f"  {self.indicator_names[col]}: {avg_scores[col]:.2f}")
            
            print("\n各指标风险暴露率（低于60分）：")
            for col in self.all_indicators:
                print(f"  {self.indicator_names[col]}: {risk_rates[col]:.2f}%")
        
        return stats_summary, indicator_stats
    
    def analyze_group_differences(self, verbose=False):
        """群体差异分析"""
        if verbose:
            print("\n="*60)
            print("三、群体差异分析")
            print("="*60)
        
        df = self.df_clean
        
        # 1. 性别差异
        gender_diff = pd.DataFrame()
        
        for gender in ['男', '女']:
            gender_data = df[df['性别'] == gender]
            row = {
                '性别': gender,
                '人数': len(gender_data),
                '成长环境均分': gender_data['成长环境_均分'].mean(),
                '学生发展均分': gender_data['学生发展_均分'].mean()
            }
            
            # 添加各指标
            for col in self.all_indicators:
                row[self.indicator_names[col]] = gender_data[col].mean()
            
            gender_diff = pd.concat([gender_diff, pd.DataFrame([row])], ignore_index=True)
        
        gender_diff.to_csv(self.output_dir / 'data' / 'gender_analysis.csv', 
                           index=False, encoding='utf-8-sig')
        
        if verbose:
            print("\n性别差异分析：")
            print(gender_diff)
        
        # 2. 办学规模差异
        scale_diff = pd.DataFrame()
        
        for scale in ['微规模', '小规模', '中规模', '大规模']:
            scale_data = df[df['办学规模'] == scale]
            if len(scale_data) > 0:
                row = {
                    '办学规模': scale,
                    '人数': len(scale_data),
                    '成长环境均分': scale_data['成长环境_均分'].mean(),
                    '学生发展均分': scale_data['学生发展_均分'].mean()
                }
                scale_diff = pd.concat([scale_diff, pd.DataFrame([row])], ignore_index=True)
        
        scale_diff.to_csv(self.output_dir / 'data' / 'scale_analysis.csv', 
                          index=False, encoding='utf-8-sig')
        
        if verbose:
            print("\n办学规模差异分析：")
            print(scale_diff)
        
        # 3. 办学性质差异
        nature_diff = pd.DataFrame()
        
        for nature in ['公办', '民办']:
            nature_data = df[df['办学性质'] == nature]
            if len(nature_data) > 0:
                row = {
                    '办学性质': nature,
                    '人数': len(nature_data),
                    '成长环境均分': nature_data['成长环境_均分'].mean(),
                    '学生发展均分': nature_data['学生发展_均分'].mean()
                }
                nature_diff = pd.concat([nature_diff, pd.DataFrame([row])], ignore_index=True)
        
        nature_diff.to_csv(self.output_dir / 'data' / 'nature_analysis.csv', 
                           index=False, encoding='utf-8-sig')
        
        if verbose:
            print("\n办学性质差异分析：")
            print(nature_diff)
        
        return gender_diff, scale_diff, nature_diff
    
    def analyze_school_level(self, verbose=False):
        """学校层面分析"""
        if verbose:
            print("\n="*60)
            print("四、学校层面分析")
            print("="*60)
        
        df = self.df_clean
        
        # 计算各学校平均分
        school_stats = df.groupby('学校代码').agg({
            '成长环境_均分': 'mean',
            '学生发展_均分': 'mean',
            '考号': 'count'
        }).rename(columns={'考号': '学生人数'}).round(2)
        
        school_stats = school_stats.sort_values('学生发展_均分', ascending=False)
        
        # 前5名学校
        top5 = school_stats.head(5)
        
        # 后5名学校
        bottom5 = school_stats.tail(5)
        
        if verbose:
            print("\n发展均分较高的学校（前5）：")
            print(top5)
            
            print("\n发展均分较低的学校（后5）：")
            print(bottom5)
        
        # 保存学校数据
        school_stats.to_csv(self.output_dir / 'data' / 'school_analysis.csv', 
                            encoding='utf-8-sig')
        
        # 学校定位数据（用于气泡图）
        school_position = school_stats.reset_index()
        school_position.to_csv(self.output_dir / 'data' / 'school_position.csv', 
                                index=False, encoding='utf-8-sig')
        
        return school_stats, top5, bottom5
    
    def analyze_quadrant(self, verbose=False):
        """四象限分层分析"""
        if verbose:
            print("\n="*60)
            print("五、学生分层分析")
            print("="*60)
        
        df = self.df_clean
        
        # 计算中位数
        env_median = df['成长环境_均分'].median()
        dev_median = df['学生发展_均分'].median()
        
        if verbose:
            print(f"\n成长环境中位数：{env_median:.2f}")
            print(f"学生发展中位数：{dev_median:.2f}")
        
        # 分配象限
        def classify_quadrant(row):
            env = row['成长环境_均分']
            dev = row['学生发展_均分']
            
            if env >= env_median and dev >= dev_median:
                return '第一象限-优势发展型'
            elif env < env_median and dev >= dev_median:
                return '第二象限-逆境成长型'
            elif env >= env_median and dev < dev_median:
                return '第三象限-潜力待发型'
            else:
                return '第四象限-重点关注型'
        
        df['象限'] = df.apply(classify_quadrant, axis=1)
        
        # 统计各象限人数
        quadrant_stats = df['象限'].value_counts()
        
        if verbose:
            print("\n四象限学生分布：")
            for quadrant, count in quadrant_stats.items():
                print(f"  {quadrant}: {count}人 ({count/len(df)*100:.2f}%)")
        
        # 各象限详细数据
        quadrant_detailed = df.groupby('象限').agg({
            '成长环境_均分': 'mean',
            '学生发展_均分': 'mean',
            '考号': 'count'
        }).rename(columns={'考号': '人数'}).round(2)
        
        quadrant_detailed.to_csv(self.output_dir / 'data' / 'quadrant_analysis.csv', 
                                  encoding='utf-8-sig')
        
        # 生成四象限干预建议
        intervention_suggestions = pd.DataFrame([
            {
                '象限': '第一象限-优势发展型',
                '人数': quadrant_stats.get('第一象限-优势发展型', 0),
                '特征': '成长环境良好，学生发展表现优秀',
                '干预建议': '继续保持优势，提供拓展性学习资源，培养领导力和创新能力，鼓励参与社会实践和竞赛活动'
            },
            {
                '象限': '第二象限-逆境成长型',
                '人数': quadrant_stats.get('第二象限-逆境成长型', 0),
                '特征': '成长环境欠佳，但学生发展表现优秀',
                '干预建议': '关注学生心理韧性，提供情感支持，改善成长环境，建立师生一对一帮扶机制，预防环境因素导致的潜在风险'
            },
            {
                '象限': '第三象限-潜力待发型',
                '人数': quadrant_stats.get('第三象限-潜力待发型', 0),
                '特征': '成长环境良好，但学生发展表现欠佳',
                '干预建议': '深入了解学生个体差异，提供个性化学习指导，激发学习兴趣，建立激励机制，探索适合的教学方法'
            },
            {
                '象限': '第四象限-重点关注型',
                '人数': quadrant_stats.get('第四象限-重点关注型', 0),
                '特征': '成长环境欠佳，学生发展表现欠佳',
                '干预建议': '优先干预，建立多维度帮扶体系，改善家庭和校园环境，提供心理辅导，制定个性化发展计划，定期跟踪评估'
            }
        ])
        
        intervention_suggestions.to_csv(self.output_dir / 'data' / 'intervention_suggestions.csv', 
                                        index=False, encoding='utf-8-sig')
        
        return quadrant_stats, quadrant_detailed, intervention_suggestions
    
    def generate_charts(self, verbose=False):
        """生成所有图表"""
        if verbose:
            print("\n="*60)
            print("生成可视化图表")
            print("="*60)
        
        # 读取数据
        indicator_stats = pd.read_csv(self.output_dir / 'data' / 'indicator_stats.csv')
        gender_analysis = pd.read_csv(self.output_dir / 'data' / 'gender_analysis.csv')
        scale_analysis = pd.read_csv(self.output_dir / 'data' / 'scale_analysis.csv')
        nature_analysis = pd.read_csv(self.output_dir / 'data' / 'nature_analysis.csv')
        school_stats = pd.read_csv(self.output_dir / 'data' / 'school_position.csv')
        quadrant_stats = pd.read_csv(self.output_dir / 'data' / 'quadrant_analysis.csv')
        
        charts_dir = self.output_dir / 'report_charts'
        
        # 图1: 各指标平均分对比
        fig, ax = plt.subplots(figsize=(12, 6))
        colors = ['#4472C4' if i < 4 else '#ED7D31' for i in range(len(indicator_stats))]
        bars = ax.bar(indicator_stats['指标'], indicator_stats['平均分'], color=colors)
        ax.set_ylabel('平均分', fontsize=12)
        ax.set_title('图1 各指标平均分对比', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 100)
        ax.axhline(y=60, color='red', linestyle='--', linewidth=1, label='及格线(60分)')
        ax.legend()
        
        for bar, value in zip(bars, indicator_stats['平均分']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                    f'{value:.1f}', ha='center', va='bottom', fontsize=9)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(charts_dir / '图1_各指标平均分对比.png', bbox_inches='tight')
        plt.close()
        
        if verbose:
            print("图1 已保存")
        
        # 图2: 各指标风险暴露率
        fig, ax = plt.subplots(figsize=(12, 6))
        colors = ['#FF6B6B' if rate > 40 else '#FFA07A' if rate > 20 else '#90EE90' 
                  for rate in indicator_stats['风险暴露率(%)']]
        bars = ax.bar(indicator_stats['指标'], indicator_stats['风险暴露率(%)'], color=colors)
        ax.set_ylabel('风险暴露率 (%)', fontsize=12)
        ax.set_title('图2 各指标风险暴露率（低于60分）', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 60)
        
        for bar, value in zip(bars, indicator_stats['风险暴露率(%)']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value:.1f}%', ha='center', va='bottom', fontsize=9)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(charts_dir / '图2_各指标风险暴露率.png', bbox_inches='tight')
        plt.close()
        
        if verbose:
            print("图2 已保存")
        
        # 图3: 性别差异对比
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        env_indicators_short = ['亲子关系', '师生关系', '同伴关系', '校园安全']
        x = np.arange(len(env_indicators_short))
        width = 0.35
        
        male_data = gender_analysis[gender_analysis['性别'] == '男'][['亲子关系', '师生关系', '同伴关系', '校园安全']].values[0]
        female_data = gender_analysis[gender_analysis['性别'] == '女'][['亲子关系', '师生关系', '同伴关系', '校园安全']].values[0]
        
        bars1 = axes[0].bar(x - width/2, male_data, width, label='男生', color='#4472C4')
        bars2 = axes[0].bar(x + width/2, female_data, width, label='女生', color='#ED7D31')
        axes[0].set_ylabel('平均分', fontsize=11)
        axes[0].set_title('成长环境维度性别差异', fontsize=12, fontweight='bold')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(env_indicators_short)
        axes[0].legend()
        axes[0].set_ylim(0, 100)
        
        dev_indicators_short = ['身心健康', '情绪状态', '运动健康', '学习创新机会', '学习习惯', '学业达标']
        x = np.arange(len(dev_indicators_short))
        
        male_data = gender_analysis[gender_analysis['性别'] == '男'][['身心健康', '情绪状态', '运动健康', '学习创新机会', '学习习惯', '学业达标']].values[0]
        female_data = gender_analysis[gender_analysis['性别'] == '女'][['身心健康', '情绪状态', '运动健康', '学习创新机会', '学习习惯', '学业达标']].values[0]
        
        bars1 = axes[1].bar(x - width/2, male_data, width, label='男生', color='#4472C4')
        bars2 = axes[1].bar(x + width/2, female_data, width, label='女生', color='#ED7D31')
        axes[1].set_ylabel('平均分', fontsize=11)
        axes[1].set_title('学生发展维度性别差异', fontsize=12, fontweight='bold')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(dev_indicators_short, rotation=45, ha='right')
        axes[1].legend()
        axes[1].set_ylim(0, 100)
        
        plt.suptitle('图3 性别差异分析', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(charts_dir / '图3_性别差异分析.png', bbox_inches='tight')
        plt.close()
        
        if verbose:
            print("图3 已保存")
        
        # 图4: 学校层面定位图
        fig, ax = plt.subplots(figsize=(12, 8))
        scatter = ax.scatter(school_stats['成长环境_均分'], school_stats['学生发展_均分'], 
                             s=school_stats['学生人数']/2, alpha=0.6, c='#4472C4', 
                             edgecolors='black', linewidth=0.5)
        
        ax.set_xlabel('成长环境均分', fontsize=12)
        ax.set_ylabel('学生发展均分', fontsize=12)
        ax.set_title('图4 学校层面环境-发展定位图（气泡大小代表样本量）', fontsize=14, fontweight='bold')
        
        ax.axhline(y=school_stats['学生发展_均分'].median(), color='red', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(x=school_stats['成长环境_均分'].median(), color='red', linestyle='--', linewidth=1, alpha=0.5)
        
        top5_schools = school_stats.nlargest(5, '学生发展_均分')['学校代码'].tolist()
        bottom5_schools = school_stats.nsmallest(5, '学生发展_均分')['学校代码'].tolist()
        
        for _, row in school_stats.iterrows():
            if row['学校代码'] in top5_schools or row['学校代码'] in bottom5_schools:
                ax.annotate(row['学校代码'], (row['成长环境_均分'], row['学生发展_均分']), 
                           fontsize=8, ha='center', va='bottom')
        
        ax.set_xlim(60, 90)
        ax.set_ylim(60, 85)
        plt.tight_layout()
        plt.savefig(charts_dir / '图4_学校层面定位图.png', bbox_inches='tight')
        plt.close()
        
        if verbose:
            print("图4 已保存")
        
        # 图5: 学生四象限分布
        quadrant_order = ['第一象限-优势发展型', '第二象限-逆境成长型', 
                         '第四象限-重点关注型', '第三象限-潜力待发型']
        quadrant_data = quadrant_stats[quadrant_stats['象限'].isin(quadrant_order)]
        quadrant_data = quadrant_data.set_index('象限').reindex(quadrant_order).reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#90EE90', '#87CEEB', '#FFB6C1', '#FF6B6B']
        bars = ax.bar(range(len(quadrant_data)), quadrant_data['人数'], color=colors)
        ax.set_xticks(range(len(quadrant_data)))
        ax.set_xticklabels(['第一象限\n优势发展型', '第二象限\n逆境成长型', 
                           '第四象限\n重点关注型', '第三象限\n潜力待发型'], fontsize=10)
        ax.set_ylabel('学生人数', fontsize=12)
        ax.set_title('图5 学生环境-发展四象限分布', fontsize=14, fontweight='bold')
        
        total = quadrant_data['人数'].sum()
        for i, (bar, value) in enumerate(zip(bars, quadrant_data['人数'])):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, 
                    f'{value}\n({value/total*100:.1f}%)', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(charts_dir / '图5_学生四象限分布.png', bbox_inches='tight')
        plt.close()
        
        if verbose:
            print("图5 已保存")
        
        # 图6: 办学规模对比
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(scale_analysis))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, scale_analysis['成长环境均分'], width, 
                       label='成长环境均分', color='#4472C4')
        bars2 = ax.bar(x + width/2, scale_analysis['学生发展均分'], width, 
                       label='学生发展均分', color='#ED7D31')
        
        ax.set_ylabel('平均分', fontsize=12)
        ax.set_title('图6 不同办学规模的环境与发展均分', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(scale_analysis['办学规模'])
        ax.legend()
        ax.set_ylim(0, 100)
        
        for bar, value in zip(bars1, scale_analysis['成长环境均分']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value:.1f}', ha='center', va='bottom', fontsize=9)
        for bar, value in zip(bars2, scale_analysis['学生发展均分']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value:.1f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(charts_dir / '图6_办学规模对比.png', bbox_inches='tight')
        plt.close()
        
        if verbose:
            print("图6 已保存")
        
        # 图7: 公办vs民办对比
        fig, ax = plt.subplots(figsize=(8, 6))
        x = np.arange(len(nature_analysis))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, nature_analysis['成长环境均分'], width, 
                       label='成长环境均分', color='#4472C4')
        bars2 = ax.bar(x + width/2, nature_analysis['学生发展均分'], width, 
                       label='学生发展均分', color='#ED7D31')
        
        ax.set_ylabel('平均分', fontsize=12)
        ax.set_title('图7 公办vs民办学校对比', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(nature_analysis['办学性质'])
        ax.legend()
        ax.set_ylim(0, 100)
        
        for bar, value in zip(bars1, nature_analysis['成长环境均分']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value:.1f}', ha='center', va='bottom', fontsize=9)
        for bar, value in zip(bars2, nature_analysis['学生发展均分']):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value:.1f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(charts_dir / '图7_公办民办对比.png', bbox_inches='tight')
        plt.close()
        
        if verbose:
            print("图7 已保存")
        
        if verbose:
            print("\n所有图表已生成完成！")
    
    def generate_report(self, verbose=False):
        """生成Word报告"""
        if verbose:
            print("\n="*60)
            print("生成Word报告")
            print("="*60)
        
        # 读取数据
        indicator_stats = pd.read_csv(self.output_dir / 'data' / 'indicator_stats.csv')
        gender_analysis = pd.read_csv(self.output_dir / 'data' / 'gender_analysis.csv')
        scale_analysis = pd.read_csv(self.output_dir / 'data' / 'scale_analysis.csv')
        nature_analysis = pd.read_csv(self.output_dir / 'data' / 'nature_analysis.csv')
        school_stats = pd.read_csv(self.output_dir / 'data' / 'school_position.csv')
        quadrant_stats = pd.read_csv(self.output_dir / 'data' / 'quadrant_analysis.csv')
        intervention_suggestions = pd.read_csv(self.output_dir / 'data' / 'intervention_suggestions.csv')
        
        # 创建Word文档
        doc = Document()
        
        # 设置标题样式
        def set_heading_style(doc, level, text):
            heading = doc.add_heading(text, level=level)
            heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
            return heading
        
        # ===== 文档标题 =====
        title = doc.add_heading('教育学情数据分析报告', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # ===== 一、数据概况与分析口径 =====
        set_heading_style(doc, 1, '一、数据概况与分析口径')
        
        doc.add_paragraph('本次分析基于学生指标得分清单数据，旨在全面了解学生成长环境和学生发展状况，识别需要重点关注的群体和学校，为教育决策提供数据支持。')
        
        # 数据概况
        doc.add_heading('1. 数据规模', level=2)
        df_clean = self.df_clean
        total_students = len(df_clean)
        total_schools = df_clean['学校代码'].nunique()
        
        p = doc.add_paragraph()
        p.add_run(f'总样本量：').bold = True
        p.add_run(f'{total_students}名学生\n')
        p.add_run(f'学校数量：').bold = True
        p.add_run(f'{total_schools}所学校\n')
        p.add_run(f'年级：').bold = True
        p.add_run(f'七年级')
        
        # 性别分布
        doc.add_heading('2. 性别分布', level=2)
        gender_dist = df_clean['性别'].value_counts()
        p = doc.add_paragraph()
        p.add_run(f'男生：').bold = True
        p.add_run(f'{gender_dist.get("男", 0)}人 ({gender_dist.get("男", 0)/total_students*100:.2f}%)\n')
        p.add_run(f'女生：').bold = True
        p.add_run(f'{gender_dist.get("女", 0)}人 ({gender_dist.get("女", 0)/total_students*100:.2f}%)')
        
        # 办学性质分布
        doc.add_heading('3. 办学性质分布', level=2)
        nature_dist = df_clean['办学性质'].value_counts()
        p = doc.add_paragraph()
        p.add_run(f'公办学校学生：').bold = True
        p.add_run(f'{nature_dist.get("公办", 0)}人 ({nature_dist.get("公办", 0)/total_students*100:.2f}%)\n')
        p.add_run(f'民办学校学生：').bold = True
        p.add_run(f'{nature_dist.get("民办", 0)}人 ({nature_dist.get("民办", 0)/total_students*100:.2f}%)')
        
        # 办学规模分布
        doc.add_heading('4. 办学规模分布', level=2)
        scale_dist = df_clean['办学规模'].value_counts()
        p = doc.add_paragraph()
        for scale in ['微规模', '小规模', '中规模', '大规模']:
            if scale in scale_dist.index:
                count = scale_dist[scale]
                p.add_run(f'{scale}：').bold = True
                p.add_run(f'{count}人 ({count/total_students*100:.2f}%)\n')
        
        # ===== 二、整体学情画像 =====
        set_heading_style(doc, 1, '二、整体学情画像')
        
        doc.add_paragraph('通过分析各指标的平均分和风险暴露率，可以全面了解学生的整体学情状况。')
        
        # 图1: 各指标平均分对比
        doc.add_heading('图 1 各指标平均分对比', level=2)
        doc.add_picture(str(self.output_dir / 'report_charts' / '图1_各指标平均分对比.png'), width=Inches(6))
        doc.add_paragraph()
        
        p = doc.add_paragraph()
        p.add_run('关键发现：').bold = True
        
        # 找出最高和最低指标
        max_indicator = indicator_stats.loc[indicator_stats['平均分'].idxmax()]
        min_indicator = indicator_stats.loc[indicator_stats['平均分'].idxmin()]
        
        p.add_run(f'\n• {max_indicator["指标"]}得分最高（{max_indicator["平均分"]:.2f}分）\n')
        p.add_run(f'• {min_indicator["指标"]}得分最低（{min_indicator["平均分"]:.2f}分）\n')
        
        # 找出低于60分的指标
        low_indicators = indicator_stats[indicator_stats['平均分'] < 60]
        if len(low_indicators) > 0:
            p.add_run(f'• {len(low_indicators)}个指标平均分低于及格线（60分）\n')
        
        # 图2: 各指标风险暴露率
        doc.add_heading('图 2 各指标风险暴露率（低于 60 分）', level=2)
        doc.add_picture(str(self.output_dir / 'report_charts' / '图2_各指标风险暴露率.png'), width=Inches(6))
        doc.add_paragraph()
        
        p = doc.add_paragraph()
        p.add_run('风险分析：').bold = True
        
        # 找出高风险指标
        high_risk = indicator_stats[indicator_stats['风险暴露率(%)'] > 40]
        if len(high_risk) > 0:
            p.add_run(f'\n• {len(high_risk)}个指标风险暴露率超过40%，需重点关注：')
            for _, row in high_risk.iterrows():
                p.add_run(f'\n  - {row["指标"]}：{row["风险暴露率(%)"]:.2f}%')
        
        # ===== 三、群体差异：谁更需要被看见 =====
        set_heading_style(doc, 1, '三、群体差异：谁更需要被看见')
        
        # 性别差异
        doc.add_heading('1. 各指标的不同性别差异', level=2)
        doc.add_picture(str(self.output_dir / 'report_charts' / '图3_性别差异分析.png'), width=Inches(6.5))
        doc.add_paragraph()
        
        # 性别差异表格
        table = doc.add_table(rows=2, cols=7)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ['指标', '男生', '女生', '差异', '指标', '男生', '女生']
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
        
        row1 = table.rows[1].cells
        row1[0].text = '成长环境均分'
        male_env = gender_analysis[gender_analysis['性别']=='男']['成长环境均分'].values[0]
        female_env = gender_analysis[gender_analysis['性别']=='女']['成长环境均分'].values[0]
        row1[1].text = f'{male_env:.2f}'
        row1[2].text = f'{female_env:.2f}'
        row1[3].text = f'{male_env - female_env:.2f}'
        row1[4].text = '学生发展均分'
        male_dev = gender_analysis[gender_analysis['性别']=='男']['学生发展均分'].values[0]
        female_dev = gender_analysis[gender_analysis['性别']=='女']['学生发展均分'].values[0]
        row1[5].text = f'{male_dev:.2f}'
        row1[6].text = f'{female_dev:.2f}'
        
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run('性别差异分析：').bold = True
        
        if male_dev > female_dev:
            p.add_run(f'\n• 男生学生发展均分高于女生{male_dev - female_dev:.2f}分\n')
        else:
            p.add_run(f'\n• 女生学生发展均分高于男生{female_dev - male_dev:.2f}分\n')
        
        if male_env > female_env:
            p.add_run(f'• 男生成长环境均分高于女生{male_env - female_env:.2f}分\n')
        else:
            p.add_run(f'• 女生成长环境均分高于男生{female_env - male_env:.2f}分\n')
        
        # 办学规模差异
        doc.add_heading('2. 不同办学规模的环境与发展均分', level=2)
        doc.add_picture(str(self.output_dir / 'report_charts' / '图6_办学规模对比.png'), width=Inches(6))
        doc.add_paragraph()
        
        # 办学规模表格
        table = doc.add_table(rows=len(scale_analysis)+1, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ['办学规模', '学生人数', '成长环境均分', '学生发展均分']
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
        
        for idx, row in scale_analysis.iterrows():
            cells = table.rows[idx+1].cells
            cells[0].text = str(row['办学规模'])
            cells[1].text = str(int(row['人数']))
            cells[2].text = f'{row["成长环境均分"]:.2f}'
            cells[3].text = f'{row["学生发展均分"]:.2f}'
        
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run('办学规模分析：').bold = True
        
        # 找出最佳规模
        best_scale = scale_analysis.loc[scale_analysis['学生发展均分'].idxmax()]
        p.add_run(f'\n• {best_scale["办学规模"]}学校学生表现最佳，学生发展均分{best_scale["学生发展均分"]:.2f}\n')
        
        # 公办vs民办
        doc.add_picture(str(self.output_dir / 'report_charts' / '图7_公办民办对比.png'), width=Inches(5))
        doc.add_paragraph()
        
        p = doc.add_paragraph()
        p.add_run('公办vs民办对比：').bold = True
        
        if len(nature_analysis) > 0:
            public_data = nature_analysis[nature_analysis['办学性质'] == '公办']
            private_data = nature_analysis[nature_analysis['办学性质'] == '民办']
            
            if len(public_data) > 0 and len(private_data) > 0:
                p.add_run(f'\n• 民办学校学生发展均分（{private_data["学生发展均分"].values[0]:.2f}）vs 公办学校（{public_data["学生发展均分"].values[0]:.2f}）\n')
                p.add_run(f'• 民办学校成长环境均分（{private_data["成长环境均分"].values[0]:.2f}）vs 公办学校（{public_data["成长环境均分"].values[0]:.2f}）\n')
        
        # ===== 四、学校层面：从平均分走向定位图 =====
        set_heading_style(doc, 1, '四、学校层面：从平均分走向定位图')
        
        doc.add_heading('图 4 学校层面环境-发展定位图（气泡大小代表样本量）', level=2)
        doc.add_picture(str(self.output_dir / 'report_charts' / '图4_学校层面定位图.png'), width=Inches(6))
        doc.add_paragraph()
        
        p = doc.add_paragraph()
        p.add_run('定位图解读：').bold = True
        p.add_run('\n• 横轴表示成长环境均分，纵轴表示学生发展均分\n')
        p.add_run('• 气泡大小代表该校学生样本量\n')
        p.add_run('• 右上方学校表现最佳（环境好、发展好）\n')
        p.add_run('• 左下方学校需要重点关注')
        
        # 表3: 发展均分较高的学校（前5）
        doc.add_heading('表 3 发展均分较高的学校（前 5）', level=2)
        table = doc.add_table(rows=6, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ['学校代码', '学生人数', '成长环境均分', '学生发展均分']
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
        
        top5 = school_stats.nlargest(5, '学生发展_均分')
        for idx, (_, row) in enumerate(top5.iterrows()):
            cells = table.rows[idx+1].cells
            cells[0].text = str(row['学校代码'])
            cells[1].text = str(int(row['学生人数']))
            cells[2].text = f'{row["成长环境_均分"]:.2f}'
            cells[3].text = f'{row["学生发展_均分"]:.2f}'
        
        # 表4: 发展均分较低的学校（后5）
        doc.add_heading('表 4 发展均分较低的学校（后 5）', level=2)
        table = doc.add_table(rows=6, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ['学校代码', '学生人数', '成长环境均分', '学生发展均分']
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
        
        bottom5 = school_stats.nsmallest(5, '学生发展_均分')
        for idx, (_, row) in enumerate(bottom5.iterrows()):
            cells = table.rows[idx+1].cells
            cells[0].text = str(row['学校代码'])
            cells[1].text = str(int(row['学生人数']))
            cells[2].text = f'{row["成长环境_均分"]:.2f}'
            cells[3].text = f'{row["学生发展_均分"]:.2f}'
        
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run('学校表现分析：').bold = True
        
        if len(top5) > 0:
            top_avg = top5['学生发展_均分'].mean()
            p.add_run(f'\n• 表现最佳的5所学校学生发展均分平均{top_avg:.2f}分\n')
        
        if len(bottom5) > 0:
            bottom_avg = bottom5['学生发展_均分'].mean()
            p.add_run(f'• 表现欠佳的5所学校学生发展均分平均{bottom_avg:.2f}分\n')
            p.add_run(f'• 学校间差异明显（差距{top_avg - bottom_avg:.2f}分），需要针对性地制定改进措施')
        
        # ===== 五、学生分层：四象限识别与干预优先级 =====
        set_heading_style(doc, 1, '五、学生分层：四象限识别与干预优先级')
        
        doc.add_heading('图 5 学生环境-发展四象限分布', level=2)
        doc.add_picture(str(self.output_dir / 'report_charts' / '图5_学生四象限分布.png'), width=Inches(6))
        doc.add_paragraph()
        
        p = doc.add_paragraph()
        p.add_run('四象限划分标准：').bold = True
        p.add_run('\n• 以成长环境和学生发展中位数为划分界限\n')
        p.add_run('• 第一象限：成长环境良好且学生发展良好\n')
        p.add_run('• 第二象限：成长环境欠佳但学生发展良好\n')
        p.add_run('• 第三象限：成长环境良好但学生发展欠佳\n')
        p.add_run('• 第四象限：成长环境欠佳且学生发展欠佳')
        
        # 表5: 四象限学生干预建议
        doc.add_heading('表 5 四象限学生干预建议', level=2)
        table = doc.add_table(rows=5, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ['象限', '学生人数', '主要特征', '干预建议']
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
        
        for idx, row in intervention_suggestions.iterrows():
            cells = table.rows[idx+1].cells
            cells[0].text = str(row['象限'])
            cells[1].text = str(int(row['人数']))
            cells[2].text = str(row['特征'])
            cells[3].text = str(row['干预建议'])
        
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run('重点关注：').bold = True
        
        # 找出第四象限占比
        quadrant4 = intervention_suggestions[intervention_suggestions['象限'] == '第四象限-重点关注型']
        if len(quadrant4) > 0:
            p.add_run(f'\n• 第四象限（重点关注型）学生占比最高，需要优先干预\n')
        
        # ===== 六、结论与改进建议 =====
        set_heading_style(doc, 1, '六、结论与改进建议')
        
        doc.add_heading('主要结论', level=2)
        p = doc.add_paragraph()
        p.add_run('1. 整体学情状况：').bold = True
        p.add_run('\n   根据数据分析，需要关注高风险指标的学生群体。\n\n')
        
        p.add_run('2. 群体差异明显：').bold = True
        p.add_run('\n   不同性别、办学规模、办学性质的学生表现存在差异，需要针对性干预。\n\n')
        
        p.add_run('3. 学校层面差异显著：').bold = True
        p.add_run('\n   表现最佳和表现欠佳的学校差距明显，需要重点帮扶。\n\n')
        
        p.add_run('4. 学生分层紧迫：').bold = True
        p.add_run('\n   第四象限学生需要优先干预，第二象限学生需要预防潜在风险。')
        
        doc.add_heading('改进建议', level=2)
        
        p = doc.add_paragraph()
        p.add_run('一、优先干预措施：').bold = True
        p.add_run('\n')
        p.add_run('1. 针对第四象限学生建立多维度帮扶体系\n')
        p.add_run('2. 针对高风险指标开展专项干预\n')
        p.add_run('3. 加强心理健康教育和同伴关系建设\n\n')
        
        p.add_run('二、针对性改进措施：').bold = True
        p.add_run('\n')
        p.add_run('1. 关注性别差异，提供针对性辅导\n')
        p.add_run('2. 对表现欠佳的学校进行重点帮扶\n')
        p.add_run('3. 加强学校间交流合作\n\n')
        
        p.add_run('三、长效机制建设：').bold = True
        p.add_run('\n')
        p.add_run('1. 建立定期评估机制\n')
        p.add_run('2. 建立预警机制\n')
        p.add_run('3. 建立资源调配机制')
        
        # 保存文档
        report_path = self.output_dir / 'report' / '教育学情数据分析报告.docx'
        doc.save(str(report_path))
        
        if verbose:
            print(f"Word报告已生成：{report_path}")
        
        return report_path
    
    def run_analysis(self, verbose=False):
        """执行完整分析流程"""
        # 1. 加载数据
        self.load_data(verbose)
        
        # 2. 整体学情分析
        self.analyze_overall(verbose)
        
        # 3. 群体差异分析
        self.analyze_group_differences(verbose)
        
        # 4. 学校层面分析
        self.analyze_school_level(verbose)
        
        # 5. 四象限分析
        self.analyze_quadrant(verbose)
        
        # 6. 生成图表
        self.generate_charts(verbose)
        
        # 7. 生成报告
        report_path = self.generate_report(verbose)
        
        if verbose:
            print("\n="*60)
            print("分析完成！")
            print("="*60)
            print(f"\n输出目录：{self.output_dir}")
            print(f"Word报告：{report_path}")
            print(f"数据文件：{self.output_dir / 'data'}")
            print(f"图表文件：{self.output_dir / 'report_charts'}")
        
        return report_path


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='教育学情数据分析脚本')
    parser.add_argument('--data', required=True, help='数据文件路径')
    parser.add_argument('--output', default='output', help='输出目录')
    parser.add_argument('--verbose', action='store_true', help='详细输出模式')
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 验证数据文件
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"错误: 数据文件不存在: {data_path}")
        sys.exit(1)
    
    # 创建分析器并执行分析
    analyzer = EducationDataAnalyzer(str(data_path), args.output)
    report_path = analyzer.run_analysis(args.verbose)
    
    print(f"\n教育学情数据分析完成！")
    print(f"报告位置: {report_path}")


if __name__ == '__main__':
    main()