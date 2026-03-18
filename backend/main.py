# Backend main file
import logging
import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from core.message_dispatcher import MessageDispatcher
from core.channel_manager import ChannelManager
from core.session_manager import SessionManager
from core.gateway_manager import get_gateway_manager
from core.monitoring_service import get_monitoring_service
from core.audit_log_manager import get_audit_log_manager
from core.revenue_distribution import get_revenue_distribution_service
from core.ecosystem_pool_manager import get_ecosystem_pool_manager
from adapters.sse_adapter import SSEAdapter
from adapters.wechat_adapter import WeChatAdapter
from adapters.discord_adapter import DiscordAdapter


class GatewayRegister(BaseModel):
    name: str
    version: str
    endpoint: str
    config: Optional[Dict[str, Any]] = None


class GatewayVersionDeploy(BaseModel):
    version: str
    change_log: str
    deployed_by: str


class GatewayMetrics(BaseModel):
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    network_in_bytes: Optional[int] = None
    network_out_bytes: Optional[int] = None
    active_connections: Optional[int] = None
    request_count: Optional[int] = None
    error_count: Optional[int] = None


class RevenueTransaction(BaseModel):
    source_gateway_id: str
    target_gateway_id: Optional[str] = None
    amount: float
    transaction_type: str
    details: Optional[str] = None


class FeeRatesUpdate(BaseModel):
    source_gateway_rate: Optional[float] = None
    ecosystem_pool_rate: Optional[float] = None


class PoolWithdrawal(BaseModel):
    amount: float
    description: str
    approved_by: str

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Chat Union Backend",
    description="多通讯通道后端服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Cache-Control"],
)

# 初始化核心服务
message_dispatcher = MessageDispatcher()
channel_manager = ChannelManager(message_dispatcher)
session_manager = SessionManager()
gateway_manager = get_gateway_manager()
monitoring_service = get_monitoring_service()
audit_log_manager = get_audit_log_manager()
revenue_service = get_revenue_distribution_service()
ecosystem_pool_manager = get_ecosystem_pool_manager()

# 存储WebSocket连接
websocket_connections = {}

# 启动默认通道
@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("Starting backend services...")
    # 启动SSE通道
    sse_adapter = SSEAdapter("sse")
    channel_manager.add_channel("sse", sse_adapter)
    logger.info("Backend services started")

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {"message": "Chat Union Backend", "status": "running"}

# 通道管理接口
@app.get("/api/channels")
async def get_channels():
    """获取所有通道"""
    channels = channel_manager.get_all_channels()
    return {"channels": channels}

@app.get("/api/channels/{channel_id}/status")
async def get_channel_status(channel_id: str):
    """获取通道状态"""
    status = channel_manager.get_channel_status(channel_id)
    return status

@app.post("/api/channels/{channel_id}/config")
async def update_channel_config(channel_id: str, config: Dict[str, Any]):
    """更新通道配置"""
    success = channel_manager.update_channel_config(channel_id, config)
    if not success:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")
    return {"message": f"Channel {channel_id} config updated"}

@app.post("/api/channels/{channel_id}/restart")
async def restart_channel(channel_id: str):
    """重启通道"""
    channel_manager.restart_channel(channel_id)
    return {"message": f"Channel {channel_id} restarted"}

# 消息接口
@app.post("/api/messages")
async def send_message(message: Dict[str, Any]):
    """发送消息"""
    message_dispatcher.dispatch_message(message)
    return {"message": "Message sent"}

# 会话管理接口
@app.post("/api/sessions")
async def create_session(session: Dict[str, Any]):
    """创建会话"""
    session_id = session.get("session_id")
    user_id = session.get("user_id")
    channel_id = session.get("channel_id")
    
    if not session_id or not user_id or not channel_id:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    session = session_manager.create_session(session_id, user_id, channel_id)
    return session

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session

@app.post("/api/sessions/{session_id}/messages")
async def add_message(session_id: str, message: Dict[str, Any]):
    """添加消息到会话"""
    success = session_manager.add_message(session_id, message)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return {"message": "Message added"}

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """获取会话消息"""
    messages = session_manager.get_session_messages(session_id)
    return {"messages": messages}

# SSE接口
@app.get("/api/sse")
async def sse_endpoint():
    """SSE端点"""
    # 创建消息队列
    queue = asyncio.Queue(maxsize=100)
    
    # 获取SSE通道
    sse_channel = None
    if "sse" in channel_manager.channels:
        sse_channel = channel_manager.channels["sse"]
    
    if not sse_channel:
        return HTTPException(status_code=500, detail="SSE channel not available")
    
    # 添加客户端到SSE通道
    sse_channel.add_client(queue)
    
    async def event_generator():
        try:
            while True:
                # 等待消息
                message = await queue.get()
                # 发送SSE事件
                yield f"data: {message}\n\n"
        finally:
            # 移除客户端
            sse_channel.remove_client(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

# 消息发送接口
@app.post("/api/messages/send")
async def send_message_api(message: Dict[str, Any]):
    """发送消息API"""
    # 分发消息
    message_dispatcher.dispatch_message(message)
    return {"message": "Message sent"}

# ============ 网关管理API ============
@app.post("/api/admin/gateways")
async def register_gateway(gateway: GatewayRegister, request: Request):
    """注册新网关"""
    result = gateway_manager.register_gateway(
        name=gateway.name,
        version=gateway.version,
        endpoint=gateway.endpoint,
        config=gateway.config
    )
    return {"success": True, "gateway": result}

@app.get("/api/admin/gateways")
async def list_gateways():
    """获取所有网关列表"""
    gateways = gateway_manager.list_all_gateways()
    return {"success": True, "gateways": gateways}

@app.get("/api/admin/gateways/{gateway_id}")
async def get_gateway(gateway_id: str):
    """获取网关详情"""
    gateway = gateway_manager.get_gateway_info(gateway_id)
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return {"success": True, "gateway": gateway}

@app.post("/api/admin/gateways/{gateway_id}/heartbeat")
async def gateway_heartbeat(gateway_id: str):
    """网关心跳"""
    success = gateway_manager.update_gateway_heartbeat(gateway_id)
    return {"success": success}

@app.post("/api/admin/gateways/{gateway_id}/metrics")
async def report_gateway_metrics(gateway_id: str, metrics: GatewayMetrics):
    """上报网关监控指标"""
    success = gateway_manager.report_metrics(gateway_id, metrics.dict())
    return {"success": success}

@app.get("/api/admin/gateways/{gateway_id}/metrics")
async def get_gateway_metrics(gateway_id: str, limit: int = 100):
    """获取网关监控指标历史"""
    metrics = gateway_manager.get_gateway_metrics(gateway_id, limit)
    return {"success": True, "metrics": metrics}

@app.post("/api/admin/gateways/{gateway_id}/deploy")
async def deploy_gateway_version(gateway_id: str, deploy: GatewayVersionDeploy):
    """部署网关版本"""
    success = gateway_manager.deploy_gateway_version(
        gateway_id=gateway_id,
        version=deploy.version,
        change_log=deploy.change_log,
        deployed_by=deploy.deployed_by
    )
    return {"success": success is not None}

@app.get("/api/admin/gateways/versions")
async def get_all_versions():
    """获取所有网关版本信息"""
    versions = gateway_manager.get_all_versions()
    return {"success": True, "versions": versions}

# ============ 监控大盘API ============
@app.get("/api/admin/monitoring/dashboard")
async def get_dashboard_summary():
    """获取监控大盘摘要"""
    summary = monitoring_service.get_dashboard_summary()
    return {"success": True, "summary": summary}

@app.get("/api/admin/monitoring/gateways")
async def get_all_gateways_status():
    """获取所有网关状态"""
    status = monitoring_service.get_all_gateways_status()
    return {"success": True, "gateways": status}

@app.get("/api/admin/monitoring/gateways/{gateway_id}/performance")
async def get_gateway_performance(gateway_id: str, hours: int = 24):
    """获取网关性能数据"""
    performance = monitoring_service.get_gateway_performance(gateway_id, hours)
    return {"success": True, "performance": performance}

@app.get("/api/admin/monitoring/alerts")
async def get_alerts():
    """获取告警信息"""
    alerts = monitoring_service.get_alerts()
    return {"success": True, "alerts": alerts}

# ============ 审计日志API ============
@app.get("/api/admin/audit/logs")
async def get_audit_logs(limit: int = 100, offset: int = 0):
    """获取审计日志"""
    logs = audit_log_manager.get_logs(limit, offset)
    return {"success": True, "logs": logs}

@app.get("/api/admin/audit/logs/user/{user_id}")
async def get_user_logs(user_id: str, limit: int = 100):
    """获取用户审计日志"""
    logs = audit_log_manager.get_logs_by_user(user_id, limit)
    return {"success": True, "logs": logs}

@app.get("/api/admin/audit/statistics")
async def get_audit_statistics(hours: int = 24):
    """获取审计统计"""
    stats = audit_log_manager.get_statistics(hours)
    return {"success": True, "statistics": stats}

# ============ 生态分成API ============
@app.post("/api/admin/revenue/transactions")
async def create_revenue_transaction(transaction: RevenueTransaction):
    """创建分成交易"""
    result = revenue_service.create_transaction(
        source_gateway_id=transaction.source_gateway_id,
        target_gateway_id=transaction.target_gateway_id,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        details=transaction.details
    )
    return {"success": True, "transaction": result}

@app.get("/api/admin/revenue/transactions")
async def get_revenue_transactions(limit: int = 100):
    """获取分成交易记录"""
    transactions = revenue_service.get_transactions(limit)
    return {"success": True, "transactions": transactions}

@app.get("/api/admin/revenue/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """获取交易详情"""
    transaction = revenue_service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"success": True, "transaction": transaction}

@app.get("/api/admin/revenue/gateways/{gateway_id}/summary")
async def get_gateway_revenue_summary(gateway_id: str, days: int = 30):
    """获取网关分成摘要"""
    summary = revenue_service.get_gateway_revenue_summary(gateway_id, days)
    return {"success": True, "summary": summary}

@app.get("/api/admin/revenue/statistics")
async def get_revenue_statistics(days: int = 30):
    """获取整体分成统计"""
    stats = revenue_service.get_overall_statistics(days)
    return {"success": True, "statistics": stats}

@app.put("/api/admin/revenue/fee-rates")
async def update_fee_rates(rates: FeeRatesUpdate):
    """更新分成比例"""
    new_rates = revenue_service.update_fee_rates(
        source_gateway_rate=rates.source_gateway_rate,
        ecosystem_pool_rate=rates.ecosystem_pool_rate
    )
    return {"success": True, "fee_rates": new_rates}

# ============ 生态池管理API ============
@app.get("/api/admin/ecosystem-pool/balance")
async def get_pool_balance():
    """获取生态池余额"""
    balance = ecosystem_pool_manager.get_pool_balance()
    return {"success": True, "balance": balance}

@app.get("/api/admin/ecosystem-pool/history")
async def get_pool_history(limit: int = 100):
    """获取生态池历史记录"""
    history = ecosystem_pool_manager.get_pool_history(limit)
    return {"success": True, "history": history}

@app.get("/api/admin/ecosystem-pool/statistics")
async def get_pool_statistics(days: int = 30):
    """获取生态池统计"""
    stats = ecosystem_pool_manager.get_pool_statistics(days)
    return {"success": True, "statistics": stats}

@app.post("/api/admin/ecosystem-pool/withdraw")
async def withdraw_from_pool(withdrawal: PoolWithdrawal):
    """从生态池提取资金"""
    import uuid
    transaction_id = str(uuid.uuid4())
    result = ecosystem_pool_manager.withdraw_from_pool(
        transaction_id=transaction_id,
        amount=withdrawal.amount,
        description=withdrawal.description,
        approved_by=withdrawal.approved_by
    )
    if not result:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    return {"success": True, "transaction": result}

# 启动服务
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
