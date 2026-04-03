---
name: "education-data-qa"
description: "教育学情数据智能问数。基于education-data-analysis的分析结果，回答用户关于学生表现、指标得分、群体差异、学校对比等问题。触发词：问数、数据查询、教育数据问答、下钻分析。"
---

# Education Data QA Skill

教育学情数据智能问数技能，基于数据分析结果回答用户的下钻问题。

## 适用场景

- 对分析结果进行深入探究
- 多维度数据对比查询
- 快速获取关键数据指标
- 自然语言数据问答

## 输入数据要求

### 数据来源

本skill读取 `education-data-analysis` 的输出数据：

```
data_source/
├── indicator_stats.csv      # 各指标统计
├── gender_analysis.csv      # 性别差异分析
├── scale_analysis.csv       # 办学规模分析
├── nature_analysis.csv      # 办学性质分析
├── quadrant_analysis.csv    # 四象限分布
├── school_analysis.csv      # 学校层面数据
└── data_config.json         # 数据配置
```

## 支持的问题类型

### 1. 对比分析

**办学规模对比**
- "不同办学规模的学生表现有什么差异？"
- "大规模和小规模学校对比如何？"
- "哪个办学规模的学生发展最好？"

**性别差异**
- "男生和女生的表现有什么差异？"
- "男生的学业达标和女生相比怎么样？"
- "性别差异明显的指标有哪些？"

**办学性质对比**
- "公办和民办学校有什么区别？"
- "不同办学性质学校的学生发展对比"

### 2. 统计查询

**指标得分**
- "各指标的平均分是多少？"
- "哪个指标得分最高？"
- "亲子关系的平均分是多少？"

**风险分析**
- "哪些指标的风险暴露率最高？"
- "高风险指标有哪些？"
- "学业负担的风险暴露率是多少？"

### 3. 群体统计

**四象限分布**
- "第四象限的学生有多少？"
- "各象限学生分布情况"
- "重点关注型学生占比多少？"

**学校统计**
- "一共有多少所学校？"
- "学生总数是多少？"
- "男生女生各有多少人？"

### 4. 学校查询

**排名查询**
- "表现最好的学校是哪些？"
- "哪些学校需要重点关注？"
- "学校排名前5是哪些？"

**具体学校**
- "某学校的学生发展均分是多少？"
- "25号学校的表现怎么样？"

### 5. 关联分析

**指标关联**
- "成长环境和学生发展有什么关系？"
- "环境好的学校学生发展也好吗？"

**多维分析**
- "大规模学校的第四象限学生有多少？"
- "男生的风险指标有哪些？"

## 使用方法

### 基本用法

```bash
# 指定数据源和问题
python scripts/qa_engine.py --data-source <data_dir> --question "<问题>"

# 示例
python scripts/qa_engine.py \
  --data-source analysis_output/data \
  --question "不同办学规模的学生表现有什么差异？"
```

### 交互模式

```bash
# 进入交互问答模式
python scripts/qa_engine.py --data-source analysis_output/data --interactive

# 多轮对话
>>> 各指标的平均分是多少？
>>> 哪个指标风险最高？
>>> 第四象限学生有多少？
>>> exit
```

### 批量问答

```bash
# 从文件读取问题列表
python scripts/qa_engine.py \
  --data-source analysis_output/data \
  --questions questions.txt \
  --output answers.json
```

## 输出格式

### 文本回答

```
问题：不同办学规模的学生表现有什么差异？

根据数据分析，不同办学规模学生表现如下：

| 办学规模 | 人数 | 成长环境均分 | 学生发展均分 |
|---------|------|-------------|-------------|
| 大规模 | 3,502人 | 69.69分 | 71.75分 |
| 小规模 | 684人 | 66.78分 | 69.88分 |
| 微规模 | 84人 | 61.73分 | 70.89分 |

差异分析：大规模学校学生发展均分最高（71.75分），
微规模学校成长环境均分最低（61.73分），差距约8分。
```

### JSON结构

```json
{
  "question": "不同办学规模的学生表现有什么差异？",
  "question_type": "comparison",
  "data_source": "scale_analysis.csv",
  "result": {
    "table": [...],
    "summary": "大规模学校学生发展均分最高...",
    "key_findings": [
      "大规模学校学生发展均分最高（71.75分）",
      "微规模学校成长环境均分最低（61.73分）"
    ]
  }
}
```

## 技术实现

### 问题解析流程

```
用户问题
    ↓
关键词提取（办学规模、性别、风险暴露率等）
    ↓
意图识别（对比、统计、排序、筛选）
    ↓
实体识别（指标名、分类值、学校代码等）
    ↓
数据查询（选择数据文件，执行操作）
    ↓
结果生成（表格 + 自然语言描述）
```

### 关键词映射

| 关键词 | 数据文件 | 字段 |
|-------|---------|------|
| 办学规模 | scale_analysis.csv | 办学规模 |
| 性别、男生、女生 | gender_analysis.csv | 性别 |
| 公办、民办 | nature_analysis.csv | 办学性质 |
| 第四象限、重点关注 | quadrant_analysis.csv | 象限 |
| 风险暴露率、高风险 | indicator_stats.csv | 风险暴露率(%) |
| 平均分、得分 | indicator_stats.csv | 平均分 |
| 学校、学校代码 | school_analysis.csv | 学校代码 |
| 成长环境 | *_analysis.csv | 成长环境均分 |
| 学生发展 | *_analysis.csv | 学生发展均分 |

### 意图识别

| 意图类型 | 关键词示例 | 操作 |
|---------|-----------|------|
| 对比 | 差异、对比、比较、区别 | 分组对比 |
| 统计 | 多少、几个、平均、最高、最低 | 统计计算 |
| 排序 | 排名、前几、最高、最低 | 排序 |
| 筛选 | 哪些、哪个、特定条件 | 筛选查询 |

## 与其他Skill协作

### education-data-analysis 协作

```bash
# 步骤1：数据分析
python education_analysis.py --data data.xlsx --output analysis_result

# 步骤2：智能问数
python qa_engine.py --data-source analysis_result/data --interactive
```

### 独立使用

如果有符合格式的数据文件，可直接使用：

```bash
python qa_engine.py --data-source my_data/ --question "各指标平均分是多少？"
```

## 依赖环境

### Python版本
- Python 3.7+

### 必需Python包
```bash
pip install pandas numpy jieba
```

## 扩展性

### 自定义问题模板

可在 `references/question_templates.md` 添加自定义问题模板：

```markdown
## 自定义问题模板

### 模板1：学校排名
- 问题格式：{学校类型}学校排名{前/后}{数量}
- 示例：公办学校排名前5
```

### 添加新数据源

在 `scripts/qa_engine.py` 中注册新的数据文件：

```python
DATA_SOURCES = {
    'new_analysis': {
        'file': 'new_analysis.csv',
        'keywords': ['新关键词1', '新关键词2'],
        'fields': ['字段1', '字段2']
    }
}
```

## 更新记录

- **v1.1** (2026-04-03): **增强版 - 分析路径规划**
  - ✅ 新增分析路径规划器（PathPlanner）
  - ✅ 支持多步骤分析路径
  - ✅ 支持多维度查询（学校+班级+象限组合）
  - ✅ 智能判断是否需要原始明细数据
  - ✅ 自动推导分析步骤
  - ✅ 支持复杂下钻查询
  - 示例："学校25各班级四象限分布"
  
- **v1.0** (2026-04-03): 初始版本
  - 支持5类问题类型
  - 自然语言问答
  - 表格 + 文字输出
  - 交互模式支持

## 相关文件

- `scripts/qa_engine.py` - 问数引擎主脚本
- `references/question_templates.md` - 问题模板参考
- `references/keywords_mapping.md` - 关键词映射表