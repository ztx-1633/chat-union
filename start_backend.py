# Start backend service
import subprocess
import sys
import os

# 安装依赖
def install_dependencies():
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

# 启动后端服务
def start_backend():
    print("Starting backend service...")
    subprocess.run([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

if __name__ == "__main__":
    install_dependencies()
    start_backend()
