# 教育学情数据分析 Skill

## 简介

本技能专门用于教育学情数据的深度分析，自动生成完整的数据分析报告，包括学生成长环境、学生发展指标、群体差异、学校层面定位、四象限分层干预等核心分析模块。

## 功能特点

✅ **自动化分析流程**：从数据加载到报告生成，一键完成
✅ **多维度分析**：整体学情、群体差异、学校层面、学生分层
✅ **可视化图表**：7种专业图表，自动生成
✅ **Word报告**：完整结构化报告，包含分析和建议
✅ **数据导出**：CSV格式，便于进一步分析
✅ **四象限分层**：智能识别重点学生群体

## 快速开始

### 1. 准备数据文件

将教育学情数据文件（Excel或CSV格式）放入 `data/` 目录。

### 2. 执行分析

```bash
# 基本用法
python scripts/education_analysis.py --data data/学生指标得分清单.xlsx

# 详细输出模式
python scripts/education_analysis.py --data data/学生指标得分清单.xlsx --verbose

# 自定义输出目录
python scripts/education_analysis.py --data data/学生指标得分清单.xlsx --output my_output
```

### 3. 查看结果

分析完成后，在 `output/` 目录查看：
- 📄 Word报告：`output/report/教育学情数据分析报告.docx`
- 📊 可视化图表：`output/report_charts/` （7张PNG图表）
- 📈 数据文件：`output/data/` （多个CSV文件）

## 数据要求

### 必需列

**基本信息**：办学规模、办学性质、学校代码、年级、班级、考号、姓名、性别

**成长环境指标**（4个）：
- 亲子关系
- 师生关系
- 同伴关系
- 校园安全

**学生发展指标**（6个）：
- 身心健康
- 情绪状态
- 运动健康
- 学习创新机会
- 学习习惯
- 学业达标

### 数据格式

- **Excel**：支持多级表头，自动跳过前3行
- **CSV**：标准CSV格式，包含完整列名
- **得分范围**：0-100分
- **样本量**：建议 ≥ 100名学生

## 输出成果

### Word报告

完整的《教育学情数据分析报告》，包含：
1. 数据概况与分析口径
2. 整体学情画像（图表+分析）
3. 群体差异分析（性别、办学规模、办学性质）
4. 学校层面定位分析（前5名/后5名）
5. 学生四象限分层与干预建议
6. 结论与改进建议

### 可视化图表（7张）

- 图1：各指标平均分对比柱状图
- 图2：各指标风险暴露率柱状图
- 图3：性别差异对比图
- 图4：学校层面定位图（气泡图）
- 图5：学生四象限分布柱状图
- 图6：办学规模对比柱状图
- 图7：公办vs民办对比柱状图

### 数据文件（CSV）

- `indicator_stats.csv` - 各指标统计
- `gender_analysis.csv` - 性别差异分析
- `scale_analysis.csv` - 办学规模分析
- `nature_analysis.csv` - 办学性质分析
- `school_analysis.csv` - 学校层面统计
- `quadrant_analysis.csv` - 四象限分析
- `intervention_suggestions.csv` - 干预建议表

## 分析模块

### 1. 数据概况与分析口径
- 样本量统计
- 性别分布
- 办学性质分布
- 办学规模分布
- 数据质量检查

### 2. 整体学情画像
- 各指标平均分计算
- 风险暴露率分析（低于60分）
- 关键指标识别
- 优势指标识别

### 3. 群体差异分析
- 性别差异对比
- 办学规模差异对比
- 办学性质差异对比

### 4. 学校层面定位
- 学校环境-发展定位图
- 表现优秀学校识别（前5）
- 表现欠佳学校识别（后5）

### 5. 学生四象限分层
- 基于中位数四象限划分
- 各象限学生人数统计
- 个性化干预建议生成

### 6. 结论与改进建议
- 主要结论总结
- 优先干预措施
- 针对性改进措施
- 长效机制建设建议

## 配置说明

### 自定义指标名称

如果您的数据列名不同，可以修改 `scripts/education_analysis.py` 中的映射：

```python
self.indicator_names = {
    '成长环境_亲子关系': '亲子关系',  # 原始列名 -> 显示名称
    '成长环境_师生关系': '师生关系',
    ...
}
```

### 自定义阈值

```python
self.risk_threshold = 60  # 风险阈值（低于60分为风险）
```

## 依赖环境

### Python版本
- Python 3.7+
- 推荐 Python 3.9+

### 必需Python包

```bash
pip install pandas numpy matplotlib seaborn openpyxl python-docx
```

### 系统要求
- 中文字体支持（SimHei）
- 图表渲染环境

## 最佳实践

### 数据准备
1. 确保数据包含完整的指标列
2. 检查数据质量（缺失值、异常值）
3. 确认列名与配置匹配
4. 建议样本量 ≥ 100

### 分析执行
1. 先进行数据概况检查
2. 关注高风险指标（风险暴露率 > 40%）
3. 重点分析第四象限学生
4. 对比不同学校表现

### 报告使用
1. Word报告用于正式汇报
2. CSV数据用于深度分析
3. 图表用于可视化展示
4. 干预建议用于实际应用

## 注意事项

⚠️ **数据隐私**：确保数据已脱敏处理
⚠️ **样本量**：建议样本量 ≥ 100
⚠️ **指标完整性**：必须包含10个指标列
⚠️ **中文环境**：确保系统支持中文字体

## 示例分析流程

### 完整示例

```bash
# 1. 准备数据
mkdir -p data
# 将 学生指标得分清单.xlsx 放入 data/ 目录

# 2. 执行分析（详细模式）
python scripts/education_analysis.py \
  --data data/学生指标得分清单.xlsx \
  --verbose

# 3. 查看结果
ls -lh output/report/
ls -lh output/report_charts/
ls -lh output/data/

# 4. 打开Word报告
# 使用Word打开 output/report/教育学情数据分析报告.docx
```

### 自定义输出

```bash
python scripts/education_analysis.py \
  --data data/学生指标得分清单.xlsx \
  --output my_analysis \
  --verbose
```

## 文件结构

```
education-data-analysis/
├── SKILL.md                          # 技能说明文件
├── README.md                         # 本文件
├── scripts/
│   └ education_analysis.py           # 主分析脚本
├── templates/                        # 模板目录（未来扩展）
├── references/
│   ├── sample_config.json            # 配置示例
│   └ sample_data_structure.md        # 数据结构说明
└── data/                             # 数据输入目录（用户创建）
```

## 更新记录

- **v1.0** (2026-04-02): 初始版本
  - 完整的教育学情数据分析流程
  - 支持多级表头Excel文件
  - 自动生成Word报告和图表
  - 四象限分层分析
  - 群体差异和学校层面分析

## 技术支持

如有问题或建议，请：
1. 查看 `references/sample_data_structure.md` 了解数据要求
2. 查看 `references/sample_config.json` 了解配置选项
3. 查看 `SKILL.md` 了解详细技术细节

## 许可

本技能为OpenClaw平台专用技能，遵循OpenClaw技能规范。