#!/bin/bash

# 启动Go WebSocket服务器
echo "正在启动Go WebSocket服务器..."

# 检查Go是否安装
if ! command -v go &> /dev/null; then
    echo "错误: Go未安装，请先安装Go 1.18+"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
go mod tidy

# 构建并运行服务器
echo "构建并运行服务器..."
go run main.go
