#!/usr/bin/env python3
"""
教育学情数据智能问数引擎 - 增强版

新增功能：
1. 分析路径规划 - 根据问题意图规划多步骤分析路径
2. 多维度查询 - 支持跨数据源的联合查询
3. 智能推理 - 自动推导需要的分析步骤

Usage:
    python qa_engine.py --data-source <data_dir> --question "<问题>"
    python qa_engine.py --data-source <data_dir> --interactive
"""

import pandas as pd
import numpy as np
import json
import re
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field


@dataclass
class AnalysisStep:
    """分析步骤"""
    step_id: int
    action: str  # query, filter, aggregate, compare, rank
    data_source: str
    description: str
    params: Dict = field(default_factory=dict)
    result: Dict = field(default_factory=dict)


@dataclass
class AnalysisPath:
    """分析路径"""
    question: str
    intent: str
    steps: List[AnalysisStep]
    final_result: Dict = field(default_factory=dict)


class PathPlanner:
    """分析路径规划器"""
    
    def __init__(self, data_sources: Dict[str, pd.DataFrame], config: Dict):
        self.data_sources = data_sources
        self.config = config
        
        # 数据源能力描述
        self.data_capabilities = {
            'indicator_stats': {
                'description': '各指标统计（平均分、风险暴露率）',
                'fields': ['指标', '平均分', '风险暴露率(%)'],
                'supports': ['统计查询', '指标排序', '风险分析']
            },
            'gender_analysis': {
                'description': '性别差异分析',
                'fields': ['性别', '人数', '成长环境均分', '学生发展均分'],
                'supports': ['性别对比', '性别统计', '指标性别差异']
            },
            'scale_analysis': {
                'description': '办学规模差异分析',
                'fields': ['办学规模', '人数', '成长环境均分', '学生发展均分'],
                'supports': ['办学规模对比', '办学规模统计']
            },
            'nature_analysis': {
                'description': '办学性质差异分析',
                'fields': ['办学性质', '人数', '成长环境均分', '学生发展均分'],
                'supports': ['办学性质对比', '办学性质统计']
            },
            'quadrant_analysis': {
                'description': '四象限学生分布',
                'fields': ['象限', '人数', '成长环境_均分', '学生发展_均分'],
                'supports': ['四象限统计', '象限分布', '分层查询']
            },
            'school_analysis': {
                'description': '学校层面数据',
                'fields': ['学校代码', '学生人数', '成长环境_均分', '学生发展_均分'],
                'supports': ['学校排名', '学校查询', '学校对比']
            },
            'raw_data': {
                'description': '原始学生数据（明细）',
                'fields': ['学校代码', '班级', '姓名', '性别', '各指标得分', '成长环境_均分', '学生发展_均分'],
                'supports': ['明细查询', '班级查询', '多条件筛选', '四象限计算']
            }
        }
    
    def plan(self, question: str) -> AnalysisPath:
        """规划分析路径
        
        Args:
            question: 用户问题
            
        Returns:
            AnalysisPath 对象
        """
        # 解析问题意图
        intent = self._parse_intent(question)
        
        # 规划步骤
        steps = self._plan_steps(question, intent)
        
        return AnalysisPath(
            question=question,
            intent=intent,
            steps=steps
        )
    
    def _parse_intent(self, question: str) -> Dict:
        """解析问题意图"""
        intent = {
            'type': 'unknown',
            'entities': [],
            'filters': [],
            'metrics': [],
            'dimensions': [],
            'aggregation': None,
            'needs_raw_data': False
        }
        
        # 实体识别
        entity_patterns = {
            'school': ['学校', '校', '学校代码'],
            'class': ['班级', '班'],
            'gender': ['男生', '女生', '性别', '男', '女'],
            'scale': ['办学规模', '大规模', '小规模', '微规模'],
            'nature': ['办学性质', '公办', '民办'],
            'quadrant': ['象限', '第一象限', '第二象限', '第三象限', '第四象限', 
                        '优势发展', '逆境成长', '潜力待发', '重点关注'],
            'indicator': ['指标', '平均分', '得分', '风险']
        }
        
        for entity_type, patterns in entity_patterns.items():
            for pattern in patterns:
                if pattern in question:
                    intent['entities'].append({
                        'type': entity_type,
                        'value': pattern
                    })
        
        # 维度识别
        dimension_keywords = {
            'school': ['学校', '校'],
            'class': ['班级', '班'],
            'gender': ['性别', '男生', '女生'],
            'scale': ['办学规模'],
            'nature': ['办学性质'],
            'quadrant': ['象限']
        }
        
        for dim, keywords in dimension_keywords.items():
            for kw in keywords:
                if kw in question:
                    intent['dimensions'].append(dim)
        
        # 过滤条件识别
        filter_patterns = [
            (r'学校代码[是为：:]*(\d+)', 'school_code'),
            (r'(\d+)号学校', 'school_code'),
            (r'学校(\d+)', 'school_code'),
            (r'(\d+)班', 'class_name'),
            (r'第([一二三四])象限', 'quadrant'),
        ]
        
        for pattern, filter_type in filter_patterns:
            match = re.search(pattern, question)
            if match:
                intent['filters'].append({
                    'type': filter_type,
                    'value': match.group(1)
                })
        
        # 判断是否需要原始数据
        if '班级' in question or '班' in question:
            intent['needs_raw_data'] = True
        
        # 多条件筛选
        if len(intent['filters']) > 1:
            intent['needs_raw_data'] = True
        
        # 象限 + 学校/班级 组合查询
        if '象限' in question and ('学校' in question or '班级' in question):
            intent['needs_raw_data'] = True
        
        # 意图类型判断
        if '差异' in question or '对比' in question or '比较' in question:
            intent['type'] = 'comparison'
        elif '排名' in question or '前' in question or '后' in question:
            intent['type'] = 'ranking'
        elif '多少' in question or '几个' in question or '分布' in question:
            intent['type'] = 'statistics'
        elif intent['filters']:
            intent['type'] = 'filter'
        else:
            intent['type'] = 'query'
        
        return intent
    
    def _plan_steps(self, question: str, intent: Dict) -> List[AnalysisStep]:
        """规划分析步骤"""
        steps = []
        step_id = 0
        
        # 复杂查询：需要原始数据
        if intent['needs_raw_data']:
            # 步骤1：加载原始数据
            step_id += 1
            steps.append(AnalysisStep(
                step_id=step_id,
                action='load_raw_data',
                data_source='raw_data',
                description='加载原始学生明细数据'
            ))
            
            # 步骤2：应用过滤条件
            if intent['filters']:
                step_id += 1
                filter_desc = '、'.join([f"{f['type']}={f['value']}" for f in intent['filters']])
                steps.append(AnalysisStep(
                    step_id=step_id,
                    action='filter',
                    data_source='raw_data',
                    description=f'筛选条件：{filter_desc}',
                    params={'filters': intent['filters']}
                ))
            
            # 步骤3：计算或统计
            if '象限' in question:
                step_id += 1
                steps.append(AnalysisStep(
                    step_id=step_id,
                    action='compute_quadrant',
                    data_source='raw_data',
                    description='计算四象限分布',
                    params={'group_by': intent['dimensions']}
                ))
            
            # 步骤4：聚合统计
            step_id += 1
            steps.append(AnalysisStep(
                step_id=step_id,
                action='aggregate',
                data_source='raw_data',
                description='按维度聚合统计',
                params={'dimensions': intent['dimensions']}
            ))
        
        # 简单查询：直接查汇总数据
        else:
            if intent['type'] == 'comparison':
                # 对比分析
                for dim in intent['dimensions']:
                    data_source = f"{dim}_analysis"
                    if data_source in self.data_sources:
                        step_id += 1
                        steps.append(AnalysisStep(
                            step_id=step_id,
                            action='compare',
                            data_source=data_source,
                            description=f'对比不同{dim}的表现差异'
                        ))
            
            elif intent['type'] == 'ranking':
                # 排名查询
                step_id += 1
                steps.append(AnalysisStep(
                    step_id=step_id,
                    action='rank',
                    data_source='school_analysis',
                    description='学校排名查询'
                ))
            
            elif intent['type'] == 'statistics':
                # 统计查询
                if '象限' in question:
                    step_id += 1
                    steps.append(AnalysisStep(
                        step_id=step_id,
                        action='query',
                        data_source='quadrant_analysis',
                        description='四象限统计查询'
                    ))
                elif '指标' in question or '平均分' in question:
                    step_id += 1
                    steps.append(AnalysisStep(
                        step_id=step_id,
                        action='query',
                        data_source='indicator_stats',
                        description='指标统计查询'
                    ))
            
            else:
                # 默认查询
                step_id += 1
                steps.append(AnalysisStep(
                    step_id=step_id,
                    action='query',
                    data_source='indicator_stats',
                    description='数据查询'
                ))
        
        return steps


class QueryExecutor:
    """查询执行器"""
    
    def __init__(self, data_sources: Dict[str, pd.DataFrame], raw_data: pd.DataFrame = None):
        self.data_sources = data_sources
        self.raw_data = raw_data
        
        # 存储中间结果
        self.intermediate_results = {}
    
    def execute(self, path: AnalysisPath) -> Dict:
        """执行分析路径
        
        Args:
            path: 分析路径
            
        Returns:
            执行结果
        """
        for step in path.steps:
            result = self._execute_step(step)
            step.result = result
            self.intermediate_results[step.step_id] = result
        
        # 汇总最终结果
        return self._summarize_results(path)
    
    def _execute_step(self, step: AnalysisStep) -> Dict:
        """执行单个步骤"""
        handlers = {
            'load_raw_data': self._load_raw_data,
            'filter': self._filter_data,
            'compute_quadrant': self._compute_quadrant,
            'aggregate': self._aggregate_data,
            'query': self._query_data,
            'compare': self._compare_data,
            'rank': self._rank_data
        }
        
        handler = handlers.get(step.action)
        if handler:
            return handler(step)
        return {'error': f'未知操作: {step.action}'}
    
    def _load_raw_data(self, step: AnalysisStep) -> Dict:
        """加载原始数据"""
        if self.raw_data is not None:
            return {
                'status': 'success',
                'row_count': len(self.raw_data),
                'columns': list(self.raw_data.columns)
            }
        return {'error': '原始数据不可用'}
    
    def _filter_data(self, step: AnalysisStep) -> Dict:
        """筛选数据"""
        df = self.raw_data
        if df is None:
            return {'error': '原始数据不可用'}
        
        filters = step.params.get('filters', [])
        filtered_df = df.copy()
        
        filter_desc = []
        for f in filters:
            ftype = f['type']
            fvalue = f['value']
            
            if ftype == 'school_code':
                # 处理学校代码（可能是整数或浮点数）
                try:
                    school_code = float(fvalue)
                    filtered_df = filtered_df[filtered_df['学校代码'] == school_code]
                    filter_desc.append(f"学校代码={fvalue}")
                except:
                    filtered_df = filtered_df[filtered_df['学校代码'].astype(str) == str(fvalue)]
                    filter_desc.append(f"学校代码={fvalue}")
            
            elif ftype == 'class_name':
                class_name = f"{fvalue}班" if not fvalue.endswith('班') else fvalue
                filtered_df = filtered_df[filtered_df['班级'] == class_name]
                filter_desc.append(f"班级={class_name}")
            
            elif ftype == 'quadrant':
                quadrant_map = {
                    '一': '第一象限-优势发展型',
                    '二': '第二象限-逆境成长型',
                    '三': '第三象限-潜力待发型',
                    '四': '第四象限-重点关注型'
                }
                q_name = quadrant_map.get(fvalue, fvalue)
                if '象限' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['象限'] == q_name]
                filter_desc.append(f"象限={q_name}")
        
        self.intermediate_results['filtered_data'] = filtered_df
        
        return {
            'status': 'success',
            'filter_conditions': filter_desc,
            'filtered_count': len(filtered_df)
        }
    
    def _compute_quadrant(self, step: AnalysisStep) -> Dict:
        """计算四象限"""
        df = self.intermediate_results.get('filtered_data', self.raw_data)
        if df is None:
            return {'error': '数据不可用'}
        
        # 计算中位数
        env_median = df['成长环境_均分'].median()
        dev_median = df['学生发展_均分'].median()
        
        def classify(row):
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
        
        df['象限'] = df.apply(classify, axis=1)
        self.intermediate_results['filtered_data'] = df
        
        return {
            'status': 'success',
            'env_median': env_median,
            'dev_median': dev_median
        }
    
    def _aggregate_data(self, step: AnalysisStep) -> Dict:
        """聚合数据"""
        df = self.intermediate_results.get('filtered_data', self.raw_data)
        if df is None:
            return {'error': '数据不可用'}
        
        dimensions = step.params.get('dimensions', [])
        
        if not dimensions:
            # 无分组，返回总计
            return {
                'status': 'success',
                'total_count': len(df),
                'summary': {
                    '成长环境均分': df['成长环境_均分'].mean(),
                    '学生发展均分': df['学生发展_均分'].mean()
                }
            }
        
        # 按维度分组统计
        results = {}
        for dim in dimensions:
            if dim == 'class' and '班级' in df.columns:
                grouped = df.groupby('班级').agg({
                    '成长环境_均分': 'mean',
                    '学生发展_均分': 'mean',
                    '姓名': 'count'
                }).round(2)
                grouped.columns = ['成长环境均分', '学生发展均分', '人数']
                results['班级'] = grouped.to_dict('index')
            
            elif dim == 'quadrant' and '象限' in df.columns:
                grouped = df.groupby('象限').agg({
                    '成长环境_均分': 'mean',
                    '学生发展_均分': 'mean',
                    '姓名': 'count'
                }).round(2)
                grouped.columns = ['成长环境均分', '学生发展均分', '人数']
                results['象限'] = grouped.to_dict('index')
        
        return {
            'status': 'success',
            'aggregation_results': results
        }
    
    def _query_data(self, step: AnalysisStep) -> Dict:
        """查询数据"""
        df = self.data_sources.get(step.data_source)
        if df is None:
            return {'error': f'数据源 {step.data_source} 不可用'}
        
        return {
            'status': 'success',
            'data': df.to_dict('records'),
            'row_count': len(df)
        }
    
    def _compare_data(self, step: AnalysisStep) -> Dict:
        """对比数据"""
        df = self.data_sources.get(step.data_source)
        if df is None:
            return {'error': f'数据源 {step.data_source} 不可用'}
        
        return {
            'status': 'success',
            'data': df.to_dict('records'),
            'row_count': len(df)
        }
    
    def _rank_data(self, step: AnalysisStep) -> Dict:
        """排名数据"""
        df = self.data_sources.get(step.data_source)
        if df is None:
            return {'error': f'数据源 {step.data_source} 不可用'}
        
        # 按学生发展均分排序
        df_sorted = df.sort_values('学生发展_均分', ascending=False)
        
        return {
            'status': 'success',
            'data': df_sorted.to_dict('records'),
            'row_count': len(df)
        }
    
    def _summarize_results(self, path: AnalysisPath) -> Dict:
        """汇总结果"""
        # 根据最后一步的结果生成最终答案
        last_step = path.steps[-1] if path.steps else None
        
        if last_step is None:
            return {'error': '没有执行任何分析步骤'}
        
        result = last_step.result
        
        # 如果有筛选后的数据，生成详细结果
        if 'filtered_data' in self.intermediate_results:
            df = self.intermediate_results['filtered_data']
            
            # 检查是否需要按班级和象限统计
            if '班级' in df.columns and '象限' in df.columns:
                quadrant_by_class = df.groupby(['班级', '象限']).size().unstack(fill_value=0)
                
                table_data = []
                for cls in sorted(quadrant_by_class.index):
                    row = {'班级': cls, '总人数': int(df[df['班级'] == cls].shape[0])}
                    for q in ['第一象限-优势发展型', '第二象限-逆境成长型', 
                             '第三象限-潜力待发型', '第四象限-重点关注型']:
                        row[q.split('-')[0]] = int(quadrant_by_class.loc[cls, q]) if q in quadrant_by_class.columns else 0
                    table_data.append(row)
                
                return {
                    'status': 'success',
                    'question': path.question,
                    'question_type': path.intent['type'],
                    'table': table_data,
                    'summary': f"共{len(df)}名学生，分布在{len(quadrant_by_class.index)}个班级",
                    'filter_conditions': [f"{f['type']}={f['value']}" for f in path.intent['filters']]
                }
        
        return result


class EducationDataQA:
    """教育学情数据智能问数引擎 - 增强版"""
    
    def __init__(self, data_source: str):
        self.data_source = Path(data_source)
        self.data = {}
        self.raw_data = None
        self.config = {}
        self.indicator_short_names = {}
        
        # 加载数据
        self._load_data()
        
        # 初始化规划器和执行器
        self.planner = PathPlanner(self.data, self.config)
        self.executor = QueryExecutor(self.data, self.raw_data)
    
    def _load_data(self):
        """加载所有数据文件"""
        data_files = {
            'indicator_stats': 'indicator_stats.csv',
            'gender_analysis': 'gender_analysis.csv',
            'scale_analysis': 'scale_analysis.csv',
            'nature_analysis': 'nature_analysis.csv',
            'quadrant_analysis': 'quadrant_analysis.csv',
            'school_analysis': 'school_analysis.csv',
            'school_position': 'school_position.csv'
        }
        
        for key, filename in data_files.items():
            filepath = self.data_source / filename
            if filepath.exists():
                self.data[key] = pd.read_csv(filepath, encoding='utf-8-sig')
        
        # 加载原始数据
        raw_file = self.data_source / 'analysis_data_clean.csv'
        if raw_file.exists():
            self.raw_data = pd.read_csv(raw_file, encoding='utf-8-sig')
        
        # 加载配置
        config_path = self.data_source / 'data_config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                self.indicator_short_names = self.config.get('indicator_names', {})
    
    def answer(self, question: str, verbose: bool = False) -> Dict[str, Any]:
        """回答问题（增强版：支持路径规划和多步查询）
        
        Args:
            question: 用户问题
            verbose: 是否输出详细过程
            
        Returns:
            包含答案的字典
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"问题：{question}")
            print(f"{'='*60}")
        
        # 1. 规划分析路径
        path = self.planner.plan(question)
        
        if verbose:
            print(f"\n问题意图：{path.intent['type']}")
            print(f"实体：{path.intent['entities']}")
            print(f"过滤条件：{path.intent['filters']}")
            print(f"是否需要原始数据：{path.intent['needs_raw_data']}")
            print(f"\n分析路径：")
            for step in path.steps:
                print(f"  步骤{step.step_id}: {step.description}")
        
        # 2. 执行分析路径
        result = self.executor.execute(path)
        
        if verbose:
            print(f"\n执行完成")
        
        # 3. 格式化输出
        return self._format_result(question, path, result)
    
    def _format_result(self, question: str, path: AnalysisPath, result: Dict) -> Dict:
        """格式化结果"""
        if 'error' in result:
            return result
        
        # 构建输出
        output = {
            'question': question,
            'question_type': path.intent['type'],
            'analysis_path': [step.description for step in path.steps],
            'filter_conditions': result.get('filter_conditions', [])
        }
        
        # 表格数据（从筛选后的数据）
        if 'table' in result:
            output['table'] = result['table']
            output['summary'] = result.get('summary', '')
        
        # 对比/排名数据（从查询结果）
        elif 'data' in result:
            data = result['data']
            if isinstance(data, list) and len(data) > 0:
                # 转换为表格格式
                output['table'] = data
                
                # 生成摘要
                if path.intent['type'] == 'comparison':
                    df = pd.DataFrame(data)
                    if '学生发展均分' in df.columns or '学生发展_均分' in df.columns:
                        col = '学生发展均分' if '学生发展均分' in df.columns else '学生发展_均分'
                        max_idx = df[col].idxmax()
                        min_idx = df[col].idxmin()
                        output['summary'] = f"{df.iloc[max_idx].get('办学规模', df.iloc[max_idx].get('性别', df.iloc[max_idx].get('办学性质', '')))}学生发展均分最高（{df.iloc[max_idx][col]:.2f}分），{df.iloc[min_idx].get('办学规模', df.iloc[min_idx].get('性别', df.iloc[min_idx].get('办学性质', '')))}最低（{df.iloc[min_idx][col]:.2f}分）"
                elif path.intent['type'] == 'ranking':
                    df = pd.DataFrame(data[:5])
                    output['summary'] = f"排名前5的学校：{', '.join([str(s) for s in df['学校代码'].tolist()])}"
        
        # 关键发现
        output['key_findings'] = self._extract_key_findings(result, output)
        
        return output
    
    def _extract_key_findings(self, result: Dict, output: Dict) -> List[str]:
        """提取关键发现"""
        findings = []
        
        # 从表格数据提取
        if 'table' in output and output['table']:
            table = output['table']
            
            if isinstance(table, list) and len(table) > 0:
                df = pd.DataFrame(table)
                
                # 数值统计
                if '总人数' in df.columns:
                    findings.append(f"共{df['总人数'].sum()}名学生")
                
                if '班级' in df.columns:
                    findings.append(f"分布在{len(df)}个班级")
                
                # 象限统计
                for col in ['第一象限', '第二象限', '第三象限', '第四象限']:
                    if col in df.columns:
                        total = df[col].sum()
                        if total > 0:
                            findings.append(f"{col}共{total}人")
                
                # 对比分析发现
                if '学生发展均分' in df.columns or '学生发展_均分' in df.columns:
                    col = '学生发展均分' if '学生发展均分' in df.columns else '学生发展_均分'
                    max_idx = df[col].idxmax()
                    min_idx = df[col].idxmin()
                    
                    name_col = None
                    for c in ['办学规模', '性别', '办学性质', '学校代码']:
                        if c in df.columns:
                            name_col = c
                            break
                    
                    if name_col:
                        findings.append(f"{df.iloc[max_idx][name_col]}学生发展均分最高（{df.iloc[max_idx][col]:.2f}分）")
                        findings.append(f"{df.iloc[min_idx][name_col]}学生发展均分最低（{df.iloc[min_idx][col]:.2f}分）")
        
        return findings
    
    def format_answer(self, result: Dict[str, Any]) -> str:
        """格式化答案为可读文本"""
        if 'error' in result:
            return f"抱歉，{result['error']}"
        
        lines = []
        lines.append(f"问题：{result.get('question', '')}")
        
        if result.get('filter_conditions'):
            lines.append(f"筛选条件：{', '.join(result['filter_conditions'])}")
        
        lines.append("")
        
        # 分析路径
        if result.get('analysis_path'):
            lines.append("分析步骤：")
            for i, step in enumerate(result['analysis_path'], 1):
                lines.append(f"  {i}. {step}")
            lines.append("")
        
        # 表格
        if 'table' in result and result['table']:
            headers = list(result['table'][0].keys())
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "|".join(['---'] * len(headers)) + "|")
            for row in result['table']:
                lines.append("| " + " | ".join(str(v) for v in row.values()) + " |")
            lines.append("")
        
        # 摘要
        if 'summary' in result:
            lines.append(result['summary'])
            lines.append("")
        
        # 关键发现
        if 'key_findings' in result:
            lines.append("关键发现：")
            for finding in result['key_findings']:
                lines.append(f"- {finding}")
        
        return "\n".join(lines)


def interactive_mode(qa_engine: EducationDataQA, verbose: bool = False):
    """交互模式"""
    print("=" * 60)
    print("教育学情数据智能问数系统（增强版）")
    print("=" * 60)
    print("输入问题进行查询，输入 'exit' 退出")
    print("支持复杂多维度查询，如：")
    print("  - 学校25各班级四象限分布")
    print("  - 学校代码25的学生中，四象限分布的学生是哪些班级？")
    print("  - 不同办学规模的学生表现有什么差异？")
    print("=" * 60)
    print()
    
    while True:
        try:
            question = input(">>> ").strip()
            
            if question.lower() in ['exit', 'quit', '退出', 'q']:
                print("再见！")
                break
            
            if not question:
                continue
            
            result = qa_engine.answer(question, verbose=verbose)
            print()
            print(qa_engine.format_answer(result))
            print()
            
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误：{e}")


def main():
    parser = argparse.ArgumentParser(description='教育学情数据智能问数引擎（增强版）')
    parser.add_argument('--data-source', required=True, help='数据源目录')
    parser.add_argument('--question', '-q', help='问题')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互模式')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细过程')
    parser.add_argument('--output', '-o', help='输出文件（JSON格式）')
    
    args = parser.parse_args()
    
    if not Path(args.data_source).exists():
        print(f"错误：数据源目录不存在: {args.data_source}")
        sys.exit(1)
    
    qa_engine = EducationDataQA(args.data_source)
    
    if args.interactive:
        interactive_mode(qa_engine, verbose=args.verbose)
        return
    
    if args.question:
        result = qa_engine.answer(args.question, verbose=args.verbose)
        print(qa_engine.format_answer(result))
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n结果已保存到: {args.output}")
        return
    
    interactive_mode(qa_engine, verbose=args.verbose)


if __name__ == '__main__':
    main()