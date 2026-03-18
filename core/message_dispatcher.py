# Message dispatcher service
import logging
from typing import Dict, Any, List

class MessageDispatcher:
    """消息分发服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.channels = {}
    
    def register_channel(self, channel_id: str, channel):
        """注册通道"""
        self.channels[channel_id] = channel
        self.logger.info(f"Channel {channel_id} registered")
    
    def unregister_channel(self, channel_id: str):
        """注销通道"""
        if channel_id in self.channels:
            del self.channels[channel_id]
            self.logger.info(f"Channel {channel_id} unregistered")
    
    def dispatch_message(self, message: Dict[str, Any]):
        """分发消息"""
        try:
            # 提取消息信息
            message_type = message.get('type', 'message')
            channel_id = message.get('channel_id')
            target_channel = message.get('target_channel')
            
            self.logger.info(f"Dispatching message: {message_type} from {channel_id} to {target_channel}")
            
            # 根据消息类型和目标通道进行分发
            if target_channel and target_channel in self.channels:
                # 发送到指定通道
                self.channels[target_channel].send_message(message)
            else:
                # 广播到所有通道
                for channel in self.channels.values():
                    channel.send_message(message)
        except Exception as e:
            self.logger.error(f"Error dispatching message: {e}")
    
    def handle_message(self, channel_id: str, message: Dict[str, Any]):
        """处理来自通道的消息"""
        try:
            # 添加通道ID到消息
            message['channel_id'] = channel_id
            
            # 分发消息
            self.dispatch_message(message)
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
