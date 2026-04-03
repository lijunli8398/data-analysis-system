---
name: "dashboard-generator"
description: "HTML数据仪表盘生成器。用于将数据分析结果转换为交互式HTML看板。支持读取CSV数据文件，生成ECharts可视化图表。触发词：生成仪表盘、数据看板、HTML看板、可视化仪表盘、数据展示。"
---

# Dashboard Generator Skill

本技能用于将数据分析结果转换为交互式HTML仪表盘看板，支持多种图表类型和响应式布局。

## 适用场景

- 数据分析结果可视化展示
- 交互式数据看板生成
- 教育数据分析结果展示
- 企业数据报表可视化
- 多维度数据对比展示

## 输入数据要求

### 数据来源

本技能设计用于与 `education-data-analysis` skill协作，读取其输出的数据文件。

### 支持的数据文件格式

- **CSV文件**：标准CSV格式，UTF-8编码
- **JSON文件**：标准JSON格式

### 必需数据文件

#### 核心数据文件（必需）

1. **indicator_stats.csv** - 各指标统计数据
   ```
   指标,平均分,风险暴露率(%)
   亲子关系,70.15,30.50
   师生关系,81.98,14.11
   ...
   ```

2. **gender_analysis.csv** - 性别差异分析数据
   ```
   性别,人数,成长环境均分,学生发展均分,亲子关系,师生关系,同伴关系,校园安全,身心健康,情绪状态,运动健康,学习创新机会,学习习惯,学业达标
   男,4849,73.21,71.95,...
   女,4475,72.95,72.94,...
   ```

3. **scale_analysis.csv** - 办学规模分析数据
   ```
   办学规模,人数,成长环境均分,学生发展均分
   微规模,450,70.64,72.71
   小规模,1645,72.82,71.61
   ...
   ```

4. **nature_analysis.csv** - 办学性质分析数据
   ```
   办学性质,人数,成长环境均分,学生发展均分
   公办,8822,72.80,72.22
   民办,502,78.16,76.02
   ```

5. **quadrant_analysis.csv** - 四象限分析数据
   ```
   象限,成长环境_均分,学生发展_均分,人数
   第一象限-优势发展型,85.43,82.9,3481
   第二象限-逆境成长型,66.72,77.85,1187
   ...
   ```

6. **school_analysis.csv** 或 **school_position.csv** - 学校层面数据
   ```
   学校代码,成长环境_均分,学生发展_均分,学生人数
   25,79.51,79.31,661
   46,82.83,78.75,99
   ...
   ```

#### 可选数据文件

- **intervention_suggestions.csv** - 干预建议数据
- **analysis_summary.json** - 分析摘要数据

### 数据文件目录结构

```
data_source/
├── indicator_stats.csv        # 必需
├── gender_analysis.csv        # 必需
├── scale_analysis.csv         # 必需
├── nature_analysis.csv        # 必需
├── quadrant_analysis.csv      # 必需
├── school_analysis.csv        # 必需（或 school_position.csv）
├── intervention_suggestions.csv  # 可选
└── analysis_summary.json      # 可选
```

## 输出成果

### HTML仪表盘文件

生成完整的交互式HTML仪表盘，包含：

#### 1. 概览卡片区域
- 关键指标卡片展示
- 数据统计汇总
- 风险提示卡片

#### 2. 可视化图表区域
- **图表1**：各指标平均分对比柱状图
- **图表2**：各指标风险暴露率柱状图
- **图表3**：性别差异对比分组柱状图
- **图表4**：学校环境-发展定位散点图（气泡图）
- **图表5**：四象限分布饼图
- **图表6**：办学规模对比分组柱状图
- **图表7**：公办vs民办对比分组柱状图

#### 3. 数据表格区域
- 各指标详细数据表格
- 学校排名对比表格
- 四象限干预建议表格

#### 4. 技术特性
- ✅ **交互式图表**：支持鼠标悬停、缩放、数据提示
- ✅ **响应式布局**：自适应不同屏幕尺寸
- ✅ **美观设计**：渐变背景、卡片布局、现代配色
- ✅ **静态HTML**：无需后端服务器，可直接浏览器打开
- ✅ **ECharts引擎**：使用ECharts 5.x可视化库

## 使用方法

### 快速开始

```bash
# 基本用法：指定数据源目录
python scripts/dashboard_generator.py --data-source data/

# 自定义输出文件名
python scripts/dashboard_generator.py \
  --data-source data/ \
  --output dashboard.html

# 详细输出模式
python scripts/dashboard_generator.py \
  --data-source data/ \
  --verbose
```

### 与education-data-analysis协作

```bash
# 步骤1：运行education-data-analysis生成数据
python ~/.openclaw/workspace/skills/education-data-analysis/scripts/education_analysis.py \
  --data 学生指标得分清单.xlsx \
  --output analysis_output

# 步骤2：运行dashboard-generator生成仪表盘
python ~/.openclaw/workspace/skills/dashboard-generator/scripts/dashboard_generator.py \
  --data-source analysis_output/data/ \
  --output analysis_output/dashboard.html
```

### 一键生成（推荐）

```bash
# education-data-analysis新增参数（自动生成仪表盘）
python ~/.openclaw/workspace/skills/education-data-analysis/scripts/education_analysis.py \
  --data 学生指标得分清单.xlsx \
  --generate-dashboard
```

## 配置说明

### 自定义仪表盘配置

可以通过配置文件自定义仪表盘样式和内容：

```json
{
  "dashboard": {
    "title": "教育学情数据看板",
    "theme": "blue-gradient",
    "charts": {
      "enable_all": true,
      "custom_charts": []
    },
    "layout": {
      "responsive": true,
      "max_width": 1600
    }
  }
}
```

### 图表配置

每个图表都可以自定义：

```python
# 跳过特定图表
--skip-charts chart4,chart7

# 自定义图表标题
--chart1-title "学生指标得分对比"

# 自定义颜色方案
--color-scheme corporate
```

## 依赖环境

### Python版本
- Python 3.7+
- 推荐 Python 3.9+

### 必需Python包
```bash
pip install pandas numpy
```

### 前端依赖（自动加载）
- **ECharts 5.4.3**：从CDN自动加载
- 无需本地安装前端库

### 系统要求
- 现代浏览器支持（Chrome、Firefox、Safari、Edge）
- JavaScript启用

## 技术细节

### HTML生成流程

1. **数据加载**：读取CSV数据文件
2. **数据处理**：转换为JavaScript数据格式
3. **模板渲染**：使用HTML模板引擎
4. **图表配置**：生成ECharts配置对象
5. **文件输出**：写入完整的HTML文件

### ECharts图表类型

| 图表编号 | 图表类型 | ECharts类型 | 数据来源 |
|---------|---------|------------|---------|
| chart1 | 平均分对比 | bar | indicator_stats.csv |
| chart2 | 风险暴露率 | bar | indicator_stats.csv |
| chart3 | 性别差异 | bar (group) | gender_analysis.csv |
| chart4 | 学校定位 | scatter | school_analysis.csv |
| chart5 | 四象限分布 | pie | quadrant_analysis.csv |
| chart6 | 办学规模对比 | bar (group) | scale_analysis.csv |
| chart7 | 公办民办对比 | bar (group) | nature_analysis.csv |

### 响应式设计

- **桌面端**：1600px最大宽度，多列布局
- **平板端**：自适应宽度，调整列数
- **移动端**：单列布局，优化触摸交互

### 性能优化

- **CDN加载**：ECharts从CDN加载，减少本地文件大小
- **懒加载**：图表按需初始化
- **压缩输出**：HTML文件约30KB

## 最佳实践

### 数据准备
1. 确保所有必需数据文件存在
2. 检查数据文件格式正确
3. 验证数据完整性

### 协作流程
1. 先运行 `education-data-analysis` 生成数据
2. 再运行 `dashboard-generator` 生成仪表盘
3. 或使用 `--generate-dashboard` 参数一键生成

### 结果展示
1. 直接浏览器打开HTML文件
2. 或通过HTTP服务器访问
3. 或集成到OpenClaw Canvas展示

## 注意事项

⚠️ **数据文件路径**：确保数据源目录正确
⚠️ **数据格式一致性**：数据文件必须符合约定格式
⚠️ **浏览器兼容性**：需要现代浏览器支持
⚠️ **JavaScript启用**：必须启用浏览器JavaScript

## 与其他Skill协作

### education-data-analysis协作

**协作机制**：数据驱动协作

```
education-data-analysis → 数据分析 → CSV输出 → dashboard-generator → HTML仪表盘
```

**数据约定**：
- 输出目录：`output/data/`
- 文件格式：CSV，UTF-8编码
- 文件命名：约定文件名（indicator_stats.csv等）

**调用方式**：

**方式1：分步调用**
```bash
# 分析数据
education-data-analysis --data data.xlsx --output analysis_result

# 生成仪表盘
dashboard-generator --data-source analysis_result/data/
```

**方式2：自动调用（通过参数）**
```bash
education-data-analysis --data data.xlsx --generate-dashboard
```

### 其他数据源协作

本skill也可独立使用，只要数据文件符合约定格式：

```bash
# 使用其他数据源
dashboard-generator --data-source my_data_directory/
```

## 扩展性

### 自定义图表

可以添加自定义图表：

```python
# 在配置中添加自定义图表
{
  "custom_charts": [
    {
      "id": "chart8",
      "type": "line",
      "title": "趋势分析",
      "data_source": "trend_data.csv"
    }
  ]
}
```

### 自定义主题

可以创建自定义主题：

```python
# 使用不同主题
--theme dark
--theme corporate
--theme minimal
```

## 更新记录

- **v1.1** (2026-04-03): **修复硬编码数据问题**
  - ✅ 移除所有硬编码默认值（学生数、性别比例、学校数等）
  - ✅ 基础统计从数据源动态获取
  - ✅ 图表坐标轴范围动态计算
  - ✅ 参考线（中位数）动态计算
  - ✅ 表格数据从CSV动态生成
  - 🔧 解决更换数据源时显示错误的问题
  
- **v1.0** (2026-04-02): 初始版本
  - 支持7种图表类型
  - 响应式HTML仪表盘
  - 与education-data-analysis协作
  - ECharts可视化引擎
  - ⚠️ 存在硬编码问题（已在v1.1修复）

## 相关文件

- `scripts/dashboard_generator.py` - 主生成脚本
- `templates/dashboard_template.html` - HTML模板文件
- `references/data_spec.md` - 数据规范文档
- `references/chart_config.md` - 图表配置说明