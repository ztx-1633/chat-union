# SSE channel adapter
import logging
import asyncio
from typing import Dict, Any, List
from .base_adapter import ChannelAdapter

class SSEAdapter(ChannelAdapter):
    """SSE通道适配器"""
    
    def __init__(self, channel_id: str):
        super().__init__(channel_id)
        self.clients: List[asyncio.Queue] = []
    
    def startup(self):
        """启动SSE通道"""
        super().startup()
        self.logger.info(f"SSE channel {self.channel_id} started")
    
    def stop(self):
        """停止SSE通道"""
        super().stop()
        # 清空客户端队列
        self.clients.clear()
        self.logger.info(f"SSE channel {self.channel_id} stopped")
    
    def add_client(self, queue: asyncio.Queue):
        """添加SSE客户端"""
        self.clients.append(queue)
        self.logger.info(f"SSE client added, total clients: {len(self.clients)}")
    
    def remove_client(self, queue: asyncio.Queue):
        """移除SSE客户端"""
        if queue in self.clients:
            self.clients.remove(queue)
            self.logger.info(f"SSE client removed, total clients: {len(self.clients)}")
    
    def send_message(self, message: Dict[str, Any]):
        """发送消息到所有SSE客户端"""
        super().send_message(message)
        try:
            import json
            message_str = json.dumps(message)
            # 发送消息到所有客户端
            for queue in self.clients:
                # 尝试将消息放入队列
                try:
                    queue.put_nowait(message_str)
                except asyncio.QueueFull:
                    self.logger.warning("SSE client queue full, message discarded")
        except Exception as e:
            self.logger.error(f"Error sending SSE message: {e}")
    
    def receive_message(self, message: Dict[str, Any]):
        """接收消息"""
        super().receive_message(message)
        # 这里可以添加消息处理逻辑
    
    def get_status(self):
        """获取通道状态"""
        status = super().get_status()
        status["clients"] = len(self.clients)
        status["type"] = "sse"
        return status
    
    def update_config(self, config: Dict[str, Any]):
        """更新通道配置"""
        super().update_config(config)
        # 这里可以添加配置更新逻辑
