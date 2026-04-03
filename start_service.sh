#!/bin/bash
# 数据分析问数系统 - 启动脚本
# 确保服务持续运行

cd /root/.openclaw/workspace/data-analysis-system
source venv/bin/activate

# 设置环境变量
export DASHSCOPE_API_KEY=sk-02b15362af6b486bab8cdafa6612d611
export OPENAI_API_KEY=sk-02b15362af6b486bab8cdafa6612d611
export OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export LLM_MODEL=qwen-plus

# 检查端口是否被占用
check_port() {
    netstat -tlnp | grep -q ":8501 " && return 0 || return 1
}

# 停止旧进程
stop_old() {
    pkill -f "streamlit run app.py" 2>/dev/null
    sleep 2
}

# 启动服务
start_service() {
    nohup streamlit run app.py \
        --server.port 8501 \
        --server.address 0.0.0.0 \
        --server.headless true \
        --browser.gatherUsageStats false \
        > /var/log/data-analysis-system.log 2>&1 &
    
    echo "服务已启动，PID: $!"
    echo "访问地址: http://212.64.14.62:8501"
}

# 主流程
echo "=== 数据分析问数系统启动 ==="
echo "时间: $(date)"
echo ""

if check_port; then
    echo "端口 8501 已被占用，正在重启..."
    stop_old
fi

start_service

# 等待启动
sleep 5

if check_port; then
    echo "✅ 服务启动成功"
    echo "日志文件: /var/log/data-analysis-system.log"
else
    echo "❌ 服务启动失败，请检查日志"
    cat /var/log/data-analysis-system.log
fi