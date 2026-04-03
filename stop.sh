#!/bin/bash
# 数据分析系统 - 停止脚本

pkill -f "uvicorn app.main:app.*8502"
echo "服务已停止"