#!/usr/bin/env python3
"""
智能分析引擎 - 根据数据类型自动选择最优分析策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DataTypeProfile(Enum):
    """数据类型画像"""
    PURE_NUMERIC = "pure_numeric"      # 纯数值型
    PURE_CATEGORICAL = "pure_categorical"  # 纯分类型
    MIXED = "mixed"                    # 混合型
    TEXT_HEAVY = "text_heavy"          # 文本型
    TIME_SERIES = "time_series"        # 时间序列型


@dataclass
class AnalysisStrategy:
    """分析策略"""
    profile: DataTypeProfile
    recommended_charts: List[str]
    analysis_modules: List[str]
    llm_prompt_template: str
    quality_checkpoints: List[str]


class SmartAnalysisEngine:
    """智能分析引擎 - 自动适配数据类型"""
    
    def __init__(self):
        self.strategies = self._build_strategies()
    
    def analyze(self, df: pd.DataFrame, custom_prompt: str = "") -> Dict:
        """
        智能分析入口 - 自动选择最优策略
        """
        # 1. 数据画像
        profile = self._profile_data(df)
        
        # 2. 获取策略
        strategy = self.strategies[profile]
        
        # 3. 执行分析
        results = self._execute_analysis(df, strategy)
        
        # 4. 质量检查
        quality_score = self._check_quality(results, strategy)
        
        # 5. 如果质量不达标，补充分析
        if quality_score < 0.7:
            results = self._enhance_analysis(df, results, strategy)
        
        return {
            "profile": profile.value,
            "strategy": strategy.analysis_modules,
            "quality_score": quality_score,
            "results": results
        }
    
    def _profile_data(self, df: pd.DataFrame) -> DataTypeProfile:
        """
        数据画像 - 判断数据类型
        """
        total_cols = len(df.columns)
        numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
        categorical_cols = len(df.select_dtypes(include=['object', 'category']).columns)
        
        numeric_ratio = numeric_cols / total_cols if total_cols > 0 else 0
        categorical_ratio = categorical_cols / total_cols if total_cols > 0 else 0
        
        # 检查是否有时间列
        time_cols = self._detect_time_columns(df)
        
        # 检查是否是文本型（长文本）
        text_cols = self._detect_text_columns(df)
        
        # 判断数据类型
        if len(time_cols) > 0 and numeric_ratio > 0.3:
            return DataTypeProfile.TIME_SERIES
        
        if text_cols / total_cols > 0.5:
            return DataTypeProfile.TEXT_HEAVY
        
        if numeric_ratio > 0.7:
            return DataTypeProfile.PURE_NUMERIC
        
        if categorical_ratio > 0.7:
            return DataTypeProfile.PURE_CATEGORICAL
        
        return DataTypeProfile.MIXED
    
    def _detect_time_columns(self, df: pd.DataFrame) -> List[str]:
        """检测时间列"""
        time_cols = []
        for col in df.columns:
            try:
                if 'date' in col.lower() or 'time' in col.lower():
                    time_cols.append(col)
                elif df[col].dtype == 'datetime64[ns]':
                    time_cols.append(col)
            except:
                pass
        return time_cols
    
    def _detect_text_columns(self, df: pd.DataFrame) -> int:
        """检测文本列（平均长度>50）"""
        text_count = 0
        for col in df.select_dtypes(include=['object']).columns:
            try:
                avg_len = df[col].astype(str).str.len().mean()
                if avg_len > 50:
                    text_count += 1
            except:
                pass
        return text_count
    
    def _build_strategies(self) -> Dict[DataTypeProfile, AnalysisStrategy]:
        """
        构建各数据类型的分析策略
        """
        return {
            DataTypeProfile.PURE_NUMERIC: AnalysisStrategy(
                profile=DataTypeProfile.PURE_NUMERIC,
                recommended_charts=["histogram", "boxplot", "scatter", "heatmap", "line"],
                analysis_modules=[
                    "descriptive_stats",
                    "distribution_analysis",
                    "correlation_analysis", 
                    "outlier_detection",
                    "trend_analysis"
                ],
                llm_prompt_template="""
分析以下数值数据，给出：
1. 数据分布特征（正态/偏态/多峰）
2. 异常值分析（哪些字段有异常，可能原因）
3. 变量关系（强相关变量对的业务含义）
4. 业务洞察（数据反映的问题或机会）

数据概况：{summary}
""",
                quality_checkpoints=["has_descriptive_stats", "has_correlation", "has_insights"]
            ),
            
            DataTypeProfile.PURE_CATEGORICAL: AnalysisStrategy(
                profile=DataTypeProfile.PURE_CATEGORICAL,
                recommended_charts=["bar", "pie", "treemap", "sunburst"],
                analysis_modules=[
                    "frequency_analysis",
                    "cross_tabulation",
                    "dominance_analysis",
                    "diversity_analysis",
                    "pattern_mining"
                ],
                llm_prompt_template="""
分析以下分类数据，给出：
1. 类别分布特征（哪些类别占主导，是否存在不平衡）
2. 类别间关系（如果有多列，是否存在关联模式）
3. 业务含义解读（类别分布反映的业务现状）
4. 数据质量问题（类别命名是否规范，是否有异常类别）
5. 建议下一步分析方向

数据概况：{summary}
""",
                quality_checkpoints=["has_frequency", "has_cross_tab", "has_business_insights"]
            ),
            
            DataTypeProfile.MIXED: AnalysisStrategy(
                profile=DataTypeProfile.MIXED,
                recommended_charts=["histogram", "bar", "boxplot", "heatmap", "scatter"],
                analysis_modules=[
                    "descriptive_stats",
                    "frequency_analysis",
                    "group_comparison",
                    "correlation_analysis",
                    "segmentation_analysis"
                ],
                llm_prompt_template="""
分析以下混合型数据，给出：
1. 数值变量分布特征
2. 分类变量分布特征
3. 数值-分类关联（不同类别的数值差异）
4. 整体业务洞察
5. 重点关注的变量和关系

数据概况：{summary}
""",
                quality_checkpoints=["has_numeric_analysis", "has_categorical_analysis", "has_insights"]
            ),
            
            DataTypeProfile.TIME_SERIES: AnalysisStrategy(
                profile=DataTypeProfile.TIME_SERIES,
                recommended_charts=["line", "area", "scatter", "heatmap"],
                analysis_modules=[
                    "trend_analysis",
                    "seasonality_detection",
                    "change_point_detection",
                    "forecasting"
                ],
                llm_prompt_template="""
分析以下时间序列数据，给出：
1. 趋势特征（上升/下降/平稳）
2. 周期性（是否有季节性波动）
3. 异常时点（突变点、异常值）
4. 预测建议

数据概况：{summary}
""",
                quality_checkpoints=["has_trend", "has_seasonality", "has_forecast"]
            ),
            
            DataTypeProfile.TEXT_HEAVY: AnalysisStrategy(
                profile=DataTypeProfile.TEXT_HEAVY,
                recommended_charts=["wordcloud", "bar", "pie"],
                analysis_modules=[
                    "text_statistics",
                    "keyword_extraction",
                    "sentiment_analysis",
                    "topic_modeling"
                ],
                llm_prompt_template="""
分析以下文本数据，给出：
1. 文本基本统计（长度分布、词汇量）
2. 关键主题和关键词
3. 文本质量评估
4. 建议分析方向

数据概况：{summary}
""",
                quality_checkpoints=["has_text_stats", "has_keywords", "has_topics"]
            )
        }
    
    def _execute_analysis(self, df: pd.DataFrame, strategy: AnalysisStrategy) -> Dict:
        """执行分析"""
        results = {}
        
        for module in strategy.analysis_modules:
            try:
                if module == "descriptive_stats":
                    results["descriptive_stats"] = self._analyze_descriptive(df)
                elif module == "distribution_analysis":
                    results["distribution_analysis"] = self._analyze_distribution(df)
                elif module == "correlation_analysis":
                    results["correlation_analysis"] = self._analyze_correlation(df)
                elif module == "frequency_analysis":
                    results["frequency_analysis"] = self._analyze_frequency(df)
                elif module == "cross_tabulation":
                    results["cross_tabulation"] = self._analyze_cross_tab(df)
                elif module == "group_comparison":
                    results["group_comparison"] = self._analyze_group_comparison(df)
                # ... 其他模块
            except Exception as e:
                results[f"{module}_error"] = str(e)
        
        return results
    
    def _analyze_descriptive(self, df: pd.DataFrame) -> Dict:
        """描述性统计"""
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) == 0:
            return {"message": "无数值字段"}
        
        return {
            "mean": numeric_df.mean().to_dict(),
            "std": numeric_df.std().to_dict(),
            "min": numeric_df.min().to_dict(),
            "max": numeric_df.max().to_dict(),
            "median": numeric_df.median().to_dict()
        }
    
    def _analyze_distribution(self, df: pd.DataFrame) -> Dict:
        """分布分析"""
        results = {}
        numeric_df = df.select_dtypes(include=[np.number])
        
        for col in numeric_df.columns:
            data = df[col].dropna()
            results[col] = {
                "skewness": float(data.skew()),
                "kurtosis": float(data.kurtosis()),
                "distribution_type": self._classify_distribution(data.skew(), data.kurtosis())
            }
        
        return results
    
    def _classify_distribution(self, skew: float, kurt: float) -> str:
        """分类分布类型"""
        if abs(skew) < 0.5 and abs(kurt - 3) < 1:
            return "近似正态分布"
        elif skew > 0.5:
            return "右偏分布"
        elif skew < -0.5:
            return "左偏分布"
        elif kurt > 4:
            return "尖峰分布"
        else:
            return "一般分布"
    
    def _analyze_correlation(self, df: pd.DataFrame) -> Dict:
        """相关性分析"""
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            return {"message": "数值字段不足，无法计算相关性"}
        
        corr = numeric_df.corr()
        return {
            "matrix": corr.to_dict(),
            "strong_correlations": self._find_strong_correlations(corr)
        }
    
    def _find_strong_correlations(self, corr: pd.DataFrame, threshold: float = 0.5) -> List[Dict]:
        """找出强相关变量对"""
        strong = []
        cols = corr.columns
        
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr.iloc[i, j]
                if abs(val) > threshold:
                    strong.append({
                        "var1": cols[i],
                        "var2": cols[j],
                        "correlation": float(val)
                    })
        
        return strong
    
    def _analyze_frequency(self, df: pd.DataFrame) -> Dict:
        """频次分析"""
        results = {}
        cat_df = df.select_dtypes(include=['object', 'category'])
        
        for col in cat_df.columns:
            value_counts = df[col].value_counts()
            results[col] = {
                "unique_count": df[col].nunique(),
                "top_values": value_counts.head(10).to_dict(),
                "distribution_balance": self._calculate_balance(value_counts)
            }
        
        return results
    
    def _calculate_balance(self, value_counts: pd.Series) -> Dict:
        """计算分布平衡度"""
        total = value_counts.sum()
        proportions = value_counts / total
        
        # 使用熵衡量平衡度
        entropy = -sum(p * np.log2(p) for p in proportions if p > 0)
        max_entropy = np.log2(len(value_counts))
        balance_ratio = entropy / max_entropy if max_entropy > 0 else 1.0
        
        return {
            "entropy": float(entropy),
            "balance_ratio": float(balance_ratio),
            "is_balanced": balance_ratio > 0.7
        }
    
    def _analyze_cross_tab(self, df: pd.DataFrame) -> Dict:
        """交叉分析"""
        results = {}
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # 只分析前4个分类变量的两两交叉
        for i, col1 in enumerate(cat_cols[:4]):
            for col2 in cat_cols[i+1:4]:
                cross = pd.crosstab(df[col1], df[col2], normalize='all')
                results[f"{col1}_vs_{col2}"] = {
                    "cross_tab": cross.to_dict(),
                    "chi2_pvalue": self._calculate_chi2(df, col1, col2)
                }
        
        return results
    
    def _calculate_chi2(self, df: pd.DataFrame, col1: str, col2: str) -> Optional[float]:
        """计算卡方检验p值"""
        try:
            from scipy.stats import chi2_contingency
            cross = pd.crosstab(df[col1], df[col2])
            _, p_value, _, _ = chi2_contingency(cross)
            return float(p_value)
        except:
            return None
    
    def _analyze_group_comparison(self, df: pd.DataFrame) -> Dict:
        """分组对比分析"""
        results = {}
        
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not cat_cols or not num_cols:
            return {"message": "需要同时有分类和数值字段"}
        
        # 对每个分类变量的每个类别，计算数值变量的均值
        for cat_col in cat_cols[:3]:
            for num_col in num_cols[:3]:
                group_stats = df.groupby(cat_col)[num_col].agg(['mean', 'std', 'count'])
                results[f"{cat_col}_by_{num_col}"] = {
                    "group_stats": group_stats.to_dict(),
                    "significant_difference": self._test_group_difference(df, cat_col, num_col)
                }
        
        return results
    
    def _test_group_difference(self, df: pd.DataFrame, cat_col: str, num_col: str) -> bool:
        """测试组间差异是否显著"""
        try:
            from scipy.stats import f_oneway
            groups = [group[num_col].dropna() for name, group in df.groupby(cat_col)]
            groups = [g for g in groups if len(g) > 1]
            
            if len(groups) < 2:
                return False
            
            _, p_value = f_oneway(*groups)
            return p_value < 0.05
        except:
            return False
    
    def _check_quality(self, results: Dict, strategy: AnalysisStrategy) -> float:
        """质量检查"""
        score = 0.0
        total = len(strategy.quality_checkpoints)
        
        for checkpoint in strategy.quality_checkpoints:
            if checkpoint.startswith("has_"):
                module = checkpoint.replace("has_", "")
                if module in results or any(module in k for k in results.keys()):
                    score += 1.0
                elif f"{module}_error" not in results:
                    score += 0.5  # 部分完成
        
        return score / total if total > 0 else 0.5
    
    def _enhance_analysis(self, df: pd.DataFrame, results: Dict, strategy: AnalysisStrategy) -> Dict:
        """增强分析"""
        # 添加通用分析
        if "frequency_analysis" not in results:
            results["frequency_analysis"] = self._analyze_frequency(df)
        
        if "basic_stats" not in results:
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 0:
                results["basic_stats"] = self._analyze_descriptive(df)
        
        return results


# 便捷函数
def smart_analyze(df: pd.DataFrame) -> Dict:
    """智能分析入口函数"""
    engine = SmartAnalysisEngine()
    return engine.analyze(df)