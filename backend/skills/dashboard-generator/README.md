# Dashboard Generator Skill

## 简介

本技能用于将数据分析结果转换为交互式HTML仪表盘看板，支持多种图表类型和响应式布局。

## 功能特点

✅ **自动化生成**：从CSV数据自动生成完整的HTML仪表盘
✅ **交互式图表**：使用ECharts引擎，支持鼠标交互、缩放、提示
✅ **响应式布局**：自适应不同屏幕尺寸（桌面、平板、手机）
✅ **美观设计**：现代UI设计，渐变背景，卡片布局
✅ **静态HTML**：无需后端服务器，可直接浏览器打开
✅ **多图表类型**：支持柱状图、散点图、饼图等多种图表

## 快速开始

### 1. 准备数据文件

确保数据源目录包含以下CSV文件：
- `indicator_stats.csv` - 指标统计数据
- `gender_analysis.csv` - 性别分析数据
- `scale_analysis.csv` - 办学规模分析数据
- `nature_analysis.csv` - 办学性质分析数据
- `quadrant_analysis.csv` - 四象限分析数据
- `school_analysis.csv` 或 `school_position.csv` - 学校分析数据

### 2. 执行生成

```bash
# 基本用法
python scripts/dashboard_generator.py --data-source data/

# 自定义输出文件
python scripts/dashboard_generator.py \
  --data-source data/ \
  --output dashboard.html

# 详细输出模式
python scripts/dashboard_generator.py \
  --data-source data/ \
  --verbose
```

### 3. 查看结果

**方式1：直接打开**
```bash
# macOS
open dashboard.html

# Linux
xdg-open dashboard.html

# Windows
start dashboard.html
```

**方式2：HTTP服务器**
```bash
# 启动HTTP服务器
python3 -m http.server 8080

# 浏览器访问
# http://localhost:8080/dashboard.html
```

## 与education-data-analysis协作

### 方式1：分步调用（推荐）

```bash
# 步骤1：运行education-data-analysis生成数据
python ~/.openclaw/workspace/skills/education-data-analysis/scripts/education_analysis.py \
  --data 学生指标得分清单.xlsx \
  --output analysis_result

# 步骤2：运行dashboard-generator生成仪表盘
python ~/.openclaw/workspace/skills/dashboard-generator/scripts/dashboard_generator.py \
  --data-source analysis_result/data/ \
  --output analysis_result/dashboard.html
```

### 方式2：自动调用（一键生成）

```bash
# education-data-analysis新增参数
python ~/.openclaw/workspace/skills/education-data-analysis/scripts/education_analysis.py \
  --data 学生指标得分清单.xlsx \
  --generate-dashboard
```

## 输出成果

### HTML仪表盘包含

#### 1. 概览卡片区域（6个关键指标卡片）
- 总学生数
- 男生/女生占比
- 公办学校学生比例
- 高风险指标数量
- 第四象限学生占比

#### 2. 可视化图表区域（7个图表）
- **图表1**：各指标平均分对比柱状图
- **图表2**：各指标风险暴露率柱状图
- **图表3**：性别差异对比分组柱状图
- **图表4**：学校环境-发展定位散点图（气泡图）
- **图表5**：四象限分布饼图
- **图表6**：办学规模对比分组柱状图
- **图表7**：公办vs民办对比分组柱状图

#### 3. 数据表格区域
- 各指标详细数据表格（带风险等级颜色）
- 学校排名对比表格（前5名 vs 后5名）
- 四象限干预建议表格（带背景色区分）

#### 4. 技术特性
- ✅ 响应式设计（自适应屏幕）
- ✅ 鼠标交互（悬停提示、点击交互）
- ✅ 图表自适应（窗口大小改变自动调整）
- ✅ 美观UI（渐变背景、卡片设计）

## 数据文件要求

### 必需数据文件

| 文件名 | 必需列 | 说明 |
|--------|--------|------|
| `indicator_stats.csv` | 指标, 平均分, 风险暴露率(%) | 各指标统计数据 |
| `gender_analysis.csv` | 性别, 人数, 成长环境均分, 学生发展均分, 各指标列 | 性别分析数据 |
| `scale_analysis.csv` | 办学规模, 人数, 成长环境均分, 学生发展均分 | 办学规模数据 |
| `nature_analysis.csv` | 办学性质, 人数, 成长环境均分, 学生发展均分 | 办学性质数据 |
| `quadrant_analysis.csv` | 象限, 成长环境_均分, 学生发展_均分, 人数 | 四象限数据 |
| `school_analysis.csv` 或 `school_position.csv` | 学校代码, 成长环境_均分, 学生发展_均分, 学生人数 | 学校分析数据 |

### 可选数据文件

- `intervention_suggestions.csv` - 干预建议数据
- `analysis_summary.json` - 分析摘要数据
- `analysis_data_clean.csv` 或 `analysis_data.csv` - 基础数据（用于获取总人数等信息）

### CSV文件格式要求

- 编码：UTF-8 或 UTF-8-SIG
- 分隔符：逗号（,）
- 表头：第一行为列名
- 数值：支持整数和小数

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

### 浏览器要求
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+
- JavaScript必须启用

## 使用场景

### 场景1：教育学情数据展示
- 展示学生成长环境与学生发展指标
- 群体差异可视化对比
- 学校层面定位分析
- 四象限学生分层展示

### 场景2：企业数据分析
- 销售数据可视化
- 客户群体分析
- 业务指标监控
- 团队绩效对比

### 场景3：科研数据展示
- 实验数据分析
- 调研结果展示
- 学术报告可视化

## 配置说明

### 自定义配置

可以通过修改脚本中的配置自定义仪表盘：

```python
self.config = {
    'title': '自定义标题',
    'subtitle': '自定义副标题',
    'update_time': '2026-01-01',
    'generator': 'Custom Generator',
    'theme': 'blue-gradient'
}
```

### 图表配置

每个图表都支持自定义：

```python
# 跳过特定图表
# 在生成脚本中注释掉相应图表的生成代码

# 修改图表颜色
# 修改 _generate_chartX_data 方法中的 itemStyle.color
```

## 最佳实践

### 数据准备
1. ✅ 确保所有必需数据文件存在
2. ✅ 检查数据文件格式正确（UTF-8编码）
3. ✅ 验证数据完整性（无缺失值）
4. ✅ 确认列名与规范匹配

### 协作流程
1. ✅ 先运行 `education-data-analysis` 生成数据
2. ✅ 再运行 `dashboard-generator` 生成仪表盘
3. ✅ 或使用 `--generate-dashboard` 参数一键生成

### 结果展示
1. ✅ 直接浏览器打开HTML文件
2. ✅ 或通过HTTP服务器访问
3. ✅ 或集成到OpenClaw Canvas展示

## 注意事项

⚠️ **数据文件路径**：确保 `--data-source` 参数指向正确的数据目录
⚠️ **数据格式一致性**：数据文件必须符合约定格式和列名
⚠️ **浏览器兼容性**：需要现代浏览器支持，旧版IE不支持
⚠️ **JavaScript启用**：必须启用浏览器JavaScript功能
⚠️ **网络连接**：首次加载需要网络连接以加载ECharts库

## 故障排除

### 问题1：数据文件加载失败
**原因**：数据文件不存在或路径错误
**解决**：检查 `--data-source` 参数是否正确

### 问题2：图表显示不正常
**原因**：数据格式不符合要求
**解决**：检查CSV文件的列名和数据格式

### 问题3：HTML文件无法打开
**原因**：浏览器不支持或JavaScript未启用
**解决**：使用现代浏览器并启用JavaScript

### 问题4：ECharts加载失败
**原因**：网络连接问题或CDN不可访问
**解决**：检查网络连接或使用本地ECharts库

## 扩展性

### 添加自定义图表

可以在生成脚本中添加自定义图表：

```python
def _generate_chart8_data(self, custom_data):
    """生成自定义图表"""
    # 自定义图表逻辑
    return f'''
    const chart8 = echarts.init(document.getElementById('chart8'));
    const option8 = {{
        // ECharts配置
    }};
    chart8.setOption(option8);
    '''
```

### 自定义主题

可以创建不同的主题样式：

```python
themes = {
    'blue-gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'green-gradient': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    'orange-gradient': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
}
```

## 更新记录

- **v1.0** (2026-04-02): 初始版本
  - 支持7种图表类型
  - 响应式HTML仪表盘
  - 与education-data-analysis协作
  - ECharts可视化引擎
  - 自动化数据加载和图表生成

## 相关文件

- `scripts/dashboard_generator.py` - 主生成脚本
- `references/data_spec.md` - 数据规范文档
- `references/usage_example.md` - 使用示例

## 技术支持

如有问题或建议，请：
1. 查看 `references/data_spec.md` 了解数据要求
2. 查看 `references/usage_example.md` 了解使用示例
3. 查看 `SKILL.md` 了解详细技术细节

## 许可

本技能为OpenClaw平台专用技能，遵循OpenClaw技能规范。