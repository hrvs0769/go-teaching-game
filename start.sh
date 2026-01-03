#!/bin/bash

echo "正在启动围棋教学游戏..."
echo ""

cd backend

# 检查是否安装了Flask
if ! python -c "import flask" 2>/dev/null; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
fi

echo "启动服务器..."
echo "请在浏览器中访问: http://localhost:5001"
echo ""

python app.py
