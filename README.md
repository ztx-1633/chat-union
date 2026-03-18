<div align="center">

# 🚀 Chat-Union

<p>
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome">
</p>

高性能的多平台通讯通道集成系统，支持微信、SMS、Email、Discord、Slack、Telegram等多种通讯平台

</div>

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [功能模块](#功能模块)
- [部署指南](#部署指南)
- [API文档](#api文档)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## ✨ 功能特性

### 💬 通讯功能
- **多通道集成**：支持微信、SMS、Email、Discord、Slack、Telegram等多种通讯通道
- **统一界面**：现代化的Web界面，提供一致的用户体验
- **实时通信**：基于WebSocket的实时消息传递
- **会话管理**：支持工作区和会话的创建、切换和管理
- **通道配置**：每个通道都可以独立配置和管理
- **系统自测**：内置系统自测功能，确保各组件正常运行
- **响应式设计**：适配不同屏幕尺寸

### 🔧 协同运维功能
- **统一网关管理**：多网关注册、管理和版本控制
- **实时监控大盘**：网关性能监控、告警管理、数据可视化
- **操作审计日志**：完整的操作记录和审计追踪
- **生态分成系统**：源网关分成、生态池管理、交易记录
- **生态流水池**：5%生态分成储备，支持资金管理

## 🛠️ 技术栈

### 后端
- **框架**：FastAPI, Uvicorn
- **数据库**：SQLite (可扩展为其他数据库)
- **实时通信**：WebSocket
- **数据验证**：Pydantic

### 前端
- **HTML5, CSS3, JavaScript**
- **图表库**：Chart.js
- **UI库**：jQuery

### 部署
- **容器化**：Docker, Docker Compose

## 🚀 快速开始

### 前置条件

- Python 3.8+
- pip (Python包管理器)

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/yourusername/chat-union.git
cd chat-union
```

#### 2. 创建虚拟环境

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

#### 3. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 配置环境

```bash
# 复制环境配置文件
cp .env.example .env

# 根据需要修改 .env 文件
```

#### 5. 启动服务

**使用启动脚本 (推荐):**

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```bash
start.bat
```

**或手动启动:**

```bash
# 启动后端服务
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 6. 访问应用

在浏览器中打开：

- **聊天界面**: http://localhost:8000/frontend/index.html
- **管理控制台**: http://localhost:8000/frontend/admin.html

## 📁 项目结构

```
chat_union/
├── adapters/              # 通道适配器
│   ├── base_adapter.py
│   ├── discord_adapter.py
│   ├── sse_adapter.py
│   ├── websocket_adapter.py
│   └── wechat_adapter.py
├── backend/               # Python后端
│   ├── __init__.py
│   └── main.py
├── core/                  # 核心服务
│   ├── __init__.py
│   ├── channel_manager.py
│   ├── message_dispatcher.py
│   ├── session_manager.py
│   ├── database_schema.py       # 数据库schema和管理
│   ├── gateway_manager.py       # 网关管理服务
│   ├── monitoring_service.py    # 监控服务
│   ├── audit_log_manager.py     # 审计日志服务
│   ├── revenue_distribution.py  # 分成计算服务
│   └── ecosystem_pool_manager.py # 生态池管理服务
├── frontend/              # 前端界面
│   ├── css/
│   │   ├── style.css
│   │   └── admin.css
│   ├── js/
│   │   ├── script.js
│   │   └── admin.js
│   ├── index.html
│   └── admin.html      # 协同运维控制台
├── go_server/           # Go WebSocket服务器 (可选)
├── .env.example         # 环境配置示例
├── .gitignore          # Git忽略文件
├── Dockerfile          # Docker配置
├── docker-compose.yml  # Docker Compose配置
├── requirements.txt    # Python依赖
├── setup.py           # Python包配置
├── start.sh           # Linux/Mac启动脚本
├── start.bat          # Windows启动脚本
└── README.md
```

## 🎯 功能模块

### 协同运维控制台

访问管理控制台：http://localhost:8000/frontend/admin.html

#### 1. 监控大盘
- 实时显示网关总数、在线网关数、总请求数和错误率
- 网关性能图表（CPU使用率、内存使用率）
- 请求趋势图表
- 告警信息展示

#### 2. 网关管理
- 注册新网关
- 查看所有网关列表
- 发送网关心跳
- 查看网关详情

#### 3. 版本管理
- 查看所有网关的当前版本
- 版本状态监控
- 版本部署功能

#### 4. 审计日志
- 查看所有操作记录
- 按用户和操作类型筛选
- 操作统计信息

#### 5. 生态分成
- 创建分成交易
- 查看交易记录
- 分成比例设置（源网关5%，生态池5%）
- 交易统计

#### 6. 生态池管理
- 查看生态池余额
- 存入和提取资金
- 历史记录查询
- 统计信息展示

### 生态分成逻辑

系统采用双层分成机制：
1. **源网关分成**：每笔交易收取5%作为源网关服务费
2. **生态流水池**：每笔交易额外收取5%存入生态池，用于整个生态的储备和发展

**分成计算公式：**
- 源网关费用 = 交易金额 × 5%
- 生态池费用 = 交易金额 × 5%
- 净金额 = 交易金额 - 源网关费用 - 生态池费用

## 🐳 部署指南

### 使用 Docker

#### 1. 构建镜像

```bash
docker build -t chat-union:latest .
```

#### 2. 运行容器

```bash
docker run -d \
  --name chat-union \
  -p 8000:8000 \
  chat-union:latest
```

### 使用 Docker Compose

#### 1. 启动服务

```bash
docker-compose up -d
```

#### 2. 查看日志

```bash
docker-compose logs -f
```

#### 3. 停止服务

```bash
docker-compose down
```

## 📚 API文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

#### 网关管理
- `POST /api/admin/gateways` - 注册新网关
- `GET /api/admin/gateways` - 获取网关列表
- `POST /api/admin/gateways/{gateway_id}/heartbeat` - 发送心跳
- `POST /api/admin/gateways/{gateway_id}/metrics` - 上报监控指标

#### 监控
- `GET /api/admin/monitoring/dashboard` - 获取监控大盘数据
- `GET /api/admin/monitoring/gateways` - 获取所有网关状态
- `GET /api/admin/monitoring/alerts` - 获取告警信息

#### 审计日志
- `GET /api/admin/audit/logs` - 获取审计日志
- `GET /api/admin/audit/statistics` - 获取审计统计

#### 生态分成
- `POST /api/admin/revenue/transactions` - 创建交易
- `GET /api/admin/revenue/transactions` - 获取交易列表
- `GET /api/admin/revenue/statistics` - 获取分成统计
- `PUT /api/admin/revenue/fee-rates` - 更新分成比例

#### 生态池
- `GET /api/admin/ecosystem-pool/balance` - 获取余额
- `GET /api/admin/ecosystem-pool/history` - 获取历史记录
- `POST /api/admin/ecosystem-pool/withdraw` - 提取资金

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 开发流程

1. **Fork 项目**
2. **创建功能分支**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **提交更改**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **推送到分支**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **打开Pull Request**

### 代码规范

- 遵循 PEP 8 代码风格
- 使用 Black 格式化代码
- 添加必要的注释和文档字符串
- 编写测试用例

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📮 联系方式

- **项目链接**: https://github.com/yourusername/chat-union
- **问题反馈**: https://github.com/yourusername/chat-union/issues
- **邮箱**: 1633797949@qq.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个 Star！**

**享受多平台通讯和协同运维的便捷体验！** 🚀

</div>
