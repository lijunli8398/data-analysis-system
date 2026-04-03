#!/bin/bash
# 数据分析系统 - 状态检查脚本

if pgrep -f "uvicorn app.main:app.*8502" > /dev/null; then
    PID=$(pgrep -f "uvicorn app.main:app.*8502")
    echo "✅ 服务运行中 (PID: $PID)"
    echo ""
    curl -s http://localhost:8502/health && echo " - 健康检查通过"
else
    echo "❌ 服务未运行"
fi