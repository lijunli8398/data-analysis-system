# 数据分析系统

基于 LLM + Skills 的教育数据分析系统，支持报告生成、看板生成和智能问数。

## 🎯 功能特性

- ✅ **项目管理** - 创建、编辑、删除项目
- ✅ **数据上传** - 支持 Excel/CSV/JSON 数据文件
- ✅ **报告生成** - 异步生成 Word 报告，LLM 增强摘要和洞察
- ✅ **看板生成** - 生成交互式 HTML 看板，LLM 增强解读
- ✅ **智能问数** - 自然语言查询数据，LLM + Python 计算
- ✅ **角色权限** - 管理员/查看者两种角色
- ✅ **Docker 部署** - 容器化部署，一键启动

## 📦 技术栈

- **后端**: FastAPI + SQLite + SQLAlchemy
- **前端**: Vue 3 + Element Plus + Vite
- **LLM**: 千问大模型 (qwen-plus/qwen-turbo)
- **Skills**: education-data-analysis + dashboard-generator

## 🚀 快速部署

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的千问 API Key
vim .env
```

### 2. Docker 启动

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 3. 访问系统

- **前端**: http://localhost
- **API 文档**: http://localhost:8000/docs

## 📝 使用说明

### 1. 登录系统

- **管理员**: admin / admin123
- **查看者**: viewer / viewer123

### 2. 创建项目（管理员）

- 进入"项目管理"
- 点击"新建项目"
- 输入项目名称和描述

### 3. 上传数据（管理员）

- 选择项目
- 点击"上传数据"
- 选择 Excel/CSV/JSON 文件

### 4. 生成报告（管理员）

- 进入"报告管理"
- 点击"生成报告"
- 选择项目和报告标题
- 等待异步任务完成

### 5. 查看报告/看板（全部）

- 报告列表查看详情或下载
- 看板列表查看交互式看板

### 6. 智能问数（全部）

- 进入"智能问数"
- 选择项目或跨项目查询
- 输入问题，如："不同办学规模的学生表现有什么差异？"

## 📂 目录结构

```
data-analysis-system/
├── backend/                    # 后端
│   ├── app/                   # FastAPI 应用
│   │   ├── main.py            # 入口
│   │   ├── models/            # 数据模型
│   │   ├── routers/           # API 路由
│   │   ├── services/          # 业务服务
│   │   └── utils/             # 工具函数
│   ├── skills/                # 集成的 Skills
│   ├── data/                  # 数据存储
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # 前端
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── api/               # API 调用
│   │   ├── stores/            # Pinia 状态
│   │   └ router/              # 路由配置
│   ├── Dockerfile
│   └ nginx.conf
│   └ package.json
│
├── docker-compose.yml          # Docker 编排
├── .env.example                # 环境变量模板
└── README.md                   # 本文件
```

## 🔧 开发说明

### 本地开发（后端）

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env

# 启动开发服务器
uvicorn app.main:app --reload
```

### 本地开发（前端）

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📊 API 文档

启动后访问: http://localhost:8000/docs

主要接口:

- `POST /api/auth/login` - 登录
- `GET /api/projects` - 项目列表
- `POST /api/upload` - 上传数据
- `POST /api/reports/generate` - 生成报告
- `POST /api/dashboards/generate` - 生成看板
- `POST /api/chat/query` - 智能问数

## ⚠️ 注意事项

1. **千问 API Key**: 必须配置有效的千问 API Key
2. **数据格式**: 上传的数据需要符合 education-data-analysis 的数据规范
3. **看板生成**: 需要先生成报告才能生成看板（依赖报告的 CSV 数据）
4. **异步任务**: 报告和看板生成是异步的，前端会定期刷新任务状态

## 📄 License

MIT