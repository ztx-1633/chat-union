# WebSocket channel adapter
import logging
import asyncio
import websockets
from typing import Dict, Any, Set
from .base_adapter import ChannelAdapter

class WebSocketAdapter(ChannelAdapter):
    """WebSocket通道适配器"""
    
    def __init__(self, channel_id: str, host: str = "localhost", port: int = 8765):
        super().__init__(channel_id)
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.loop = asyncio.get_event_loop()
    
    def startup(self):
        """启动WebSocket服务器"""
        super().startup()
        try:
            # 启动WebSocket服务器
            start_server = websockets.serve(self.handle_connection, self.host, self.port)
            self.server = self.loop.run_until_complete(start_server)
            self.logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Error starting WebSocket server: {e}")
            self.status = "error"
    
    def stop(self):
        """停止WebSocket服务器"""
        super().stop()
        if self.server:
            self.server.close()
            self.loop.run_until_complete(self.server.wait_closed())
            self.logger.info("WebSocket server stopped")
    
    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """处理WebSocket连接"""
        # 添加客户端到集合
        self.clients.add(websocket)
        self.logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            # 接收消息
            async for message in websocket:
                try:
                    # 解析消息
                    import json
                    message_data = json.loads(message)
                    # 处理消息
                    self.receive_message(message_data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error decoding message: {e}")
        except websockets.exceptions.ConnectionClosedOK:
            self.logger.info(f"Client disconnected: {websocket.remote_address}")
        except Exception as e:
            self.logger.error(f"Error handling connection: {e}")
        finally:
            # 从集合中移除客户端
            self.clients.remove(websocket)
    
    def send_message(self, message: Dict[str, Any]):
        """发送消息到所有客户端"""
        super().send_message(message)
        try:
            import json
            message_str = json.dumps(message)
            # 发送消息到所有客户端
            for client in self.clients:
                self.loop.create_task(self._send_to_client(client, message_str))
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
    
    async def _send_to_client(self, client: websockets.WebSocketServerProtocol, message: str):
        """发送消息到单个客户端"""
        try:
            await client.send(message)
        except Exception as e:
            self.logger.error(f"Error sending message to client: {e}")
    
    def receive_message(self, message: Dict[str, Any]):
        """接收消息"""
        super().receive_message(message)
        # 这里可以添加消息处理逻辑
        # 例如，将消息转发给消息分发器
    
    def get_status(self):
        """获取通道状态"""
        status = super().get_status()
        status["clients"] = len(self.clients)
        status["server"] = f"ws://{self.host}:{self.port}"
        return status
    
    def update_config(self, config: Dict[str, Any]):
        """更新通道配置"""
        super().update_config(config)
        # 更新主机和端口
        if "host" in config:
            self.host = config["host"]
        if "port" in config:
            self.port = config["port"]
