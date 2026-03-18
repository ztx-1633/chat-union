# Base channel adapter
import logging
from typing import Dict, Any

class ChannelAdapter:
    """通道适配器基类"""
    
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self.logger = logging.getLogger(f"adapter.{channel_id}")
        self.config = {}
        self.status = "inactive"
    
    def startup(self):
        """启动通道"""
        self.logger.info(f"Starting channel {self.channel_id}")
        self.status = "active"
    
    def stop(self):
        """停止通道"""
        self.logger.info(f"Stopping channel {self.channel_id}")
        self.status = "inactive"
    
    def send_message(self, message: Dict[str, Any]):
        """发送消息"""
        self.logger.info(f"Sending message from channel {self.channel_id}: {message}")
    
    def receive_message(self, message: Dict[str, Any]):
        """接收消息"""
        self.logger.info(f"Receiving message from channel {self.channel_id}: {message}")
    
    def get_status(self):
        """获取通道状态"""
        return {
            "channel_id": self.channel_id,
            "status": self.status,
            "config": self.config
        }
    
    def update_config(self, config: Dict[str, Any]):
        """更新通道配置"""
        self.logger.info(f"Updating config for channel {self.channel_id}: {config}")
        self.config.update(config)
    
    def handle_event(self, event: Dict[str, Any]):
        """处理通道事件"""
        self.logger.info(f"Handling event from channel {self.channel_id}: {event}")
