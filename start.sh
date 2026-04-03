#!/bin/bash
# 数据分析系统 - 独立启动脚本

cd /root/.openclaw/workspace/data-analysis-system/backend
source venv/bin/activate

# 设置环境变量
export QWEN_API_KEY=sk-02b15362af6b486bab8cdafa6612d611
export SECRET_KEY=data-analysis-secret-2026
export ADMIN_PASSWORD=admin123
export VIEWER_PASSWORD=viewer123

# 启动服务
nohup uvicorn app.main:app --host 0.0.0.0 --port 8502 > /var/log/data-analysis.log 2>&1 &

echo "服务已启动，PID: $!"
echo "日志文件: /var/log/data-analysis.log"
echo "访问地址: http://$(hostname -I | awk '{print $1}'):8502"