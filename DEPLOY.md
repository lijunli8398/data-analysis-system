# 数据分析系统 - Docker部署指南

## 快速部署

### 1. 配置环境变量

```bash
cd /root/.openclaw/workspace/data-analysis-system

# 创建.env文件
cat > .env << 'EOF'
QWEN_API_KEY=sk-02b15362af6b486bab8cdafa6612d611
SECRET_KEY=data-analysis-secret-2026
ADMIN_PASSWORD=admin123
VIEWER_PASSWORD=viewer123
EOF
```

### 2. 创建数据目录

```bash
mkdir -p data/{db,uploads,reports,dashboards,results}
```

### 3. 构建并启动

```bash
docker-compose up -d --build
```

### 4. 查看日志

```bash
docker-compose logs -f
```

### 5. 停止服务

```bash
docker-compose down
```

---

## 持久化文件说明

| 目录 | 说明 |
|-----|------|
| `data/db/` | SQLite数据库文件 |
| `data/uploads/` | 上传的Excel源数据 |
| `data/reports/` | 生成的Word报告 |
| `data/dashboards/` | 生成的HTML看板 |
| `data/results/` | 分析结果CSV文件 |

---

## 访问地址

- **前端**: http://服务器IP:8500
- **后端API**: http://服务器IP:8502
- **API文档**: http://服务器IP:8502/docs

---

## 登录账号

| 用户名 | 密码 | 角色 |
|-------|------|-----|
| admin | admin123 | 管理员 |
| viewer | viewer123 | 查看者 |

---

## 运维命令

```bash
# 查看服务状态
docker-compose ps

# 重启服务
docker-compose restart

# 查看后端日志
docker-compose logs -f backend

# 进入后端容器
docker exec -it data-analysis-backend bash

# 备份数据
tar -czvf data-backup-$(date +%Y%m%d).tar.gz data/

# 恢复数据
tar -xzvf data-backup-20260402.tar.gz
```

---

## 更新Skills

```bash
# 方式1: 挂载方式（推荐）
# Skills已挂载为只读，直接修改宿主机文件即可
vim backend/skills/education-data-analysis/scripts/education_analysis.py

# 方式2: 重新构建镜像
docker-compose up -d --build
```