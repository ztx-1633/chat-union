@echo off
REM Chat-Union Windows 启动脚本

echo =========================================
echo   Chat-Union 启动脚本
echo =========================================

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装 Python3.8+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📦 安装/更新依赖...
pip install --upgrade pip
pip install -r requirements.txt

REM 检查 .env 文件
if not exist ".env" (
    echo ⚠️  .env 文件不存在，从 .env.example 复制...
    copy .env.example .env
)

echo.
echo 🚀 启动 Chat-Union 后端服务...
echo 📱 访问地址: http://localhost:8000
echo 💬 聊天界面: http://localhost:8000/frontend/index.html
echo ⚙️  管理控制台: http://localhost:8000/frontend/admin.html
echo.
echo 按 Ctrl+C 停止服务
echo =========================================
echo.

REM 启动后端服务
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
