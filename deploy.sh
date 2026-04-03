#!/bin/bash

# 数据分析系统 - 快速部署脚本

echo "🚀 开始部署数据分析系统..."

# 1. 检查环境
echo "1️⃣ 检查环境..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "✅ Docker 和 Docker Compose 已安装"

# 2. 检查配置
echo "2️⃣ 检查配置..."

if [ ! -f ".env" ]; then
    echo "⚠️ .env 文件不存在"
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo ""
    echo "⚠️ 请编辑 .env 文件，填入你的千问 API Key:"
    echo "   vim .env"
    echo ""
    read -p "是否已配置好千问 API Key? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 请先配置 .env 文件后再运行此脚本"
        exit 1
    fi
fi

# 3. 构建镜像
echo "3️⃣ 构建 Docker 镜像..."
docker-compose build

# 4. 启动服务
echo "4️⃣ 启动服务..."
docker-compose up -d

# 5. 等待启动
echo "5️⃣ 等待服务启动..."
sleep 10

# 6. 检查状态
echo "6️⃣ 检查服务状态..."
docker-compose ps

echo ""
echo "🎉 部署完成!"
echo ""
echo "访问地址:"
echo "  - 前端: http://localhost"
echo "  - API文档: http://localhost:8000/docs"
echo ""
echo "登录账号:"
echo "  - 管理员: admin / admin123"
echo "  - 查看者: viewer / viewer123"
echo ""
echo "停止服务: docker-compose down"
echo "查看日志: docker-compose logs -f"
echo ""