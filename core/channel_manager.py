# Channel manager service
import logging
import threading
from typing import Dict, Any, List

class ChannelManager:
    """通道管理服务"""
    
    def __init__(self, message_dispatcher):
        self.logger = logging.getLogger(__name__)
        self.message_dispatcher = message_dispatcher
        self.channels = {}
        self.channel_threads = {}
        self.lock = threading.Lock()
    
    def add_channel(self, channel_id: str, channel):
        """添加通道"""
        with self.lock:
            if channel_id in self.channels:
                self.logger.warning(f"Channel {channel_id} already exists")
                return
            
            # 注册通道
            self.channels[channel_id] = channel
            self.message_dispatcher.register_channel(channel_id, channel)
            
            # 启动通道
            thread = threading.Thread(target=self._run_channel, args=(channel_id, channel), daemon=True)
            self.channel_threads[channel_id] = thread
            thread.start()
            
            self.logger.info(f"Channel {channel_id} added and started")
    
    def remove_channel(self, channel_id: str):
        """移除通道"""
        with self.lock:
            if channel_id not in self.channels:
                self.logger.warning(f"Channel {channel_id} not found")
                return
            
            # 停止通道
            channel = self.channels[channel_id]
            if hasattr(channel, 'stop'):
                try:
                    channel.stop()
                except Exception as e:
                    self.logger.error(f"Error stopping channel {channel_id}: {e}")
            
            # 注销通道
            self.message_dispatcher.unregister_channel(channel_id)
            del self.channels[channel_id]
            
            # 清理线程
            if channel_id in self.channel_threads:
                thread = self.channel_threads[channel_id]
                if thread.is_alive():
                    # 等待线程结束
                    thread.join(timeout=5)
                del self.channel_threads[channel_id]
            
            self.logger.info(f"Channel {channel_id} removed")
    
    def restart_channel(self, channel_id: str):
        """重启通道"""
        self.remove_channel(channel_id)
        # 重新添加通道
        # 这里需要根据通道类型重新创建通道实例
        # 暂时留空，后续实现
    
    def get_channel_status(self, channel_id: str):
        """获取通道状态"""
        with self.lock:
            if channel_id not in self.channels:
                return {"status": "not_found"}
            
            channel = self.channels[channel_id]
            if hasattr(channel, 'get_status'):
                return channel.get_status()
            else:
                return {"status": "unknown"}
    
    def get_all_channels(self):
        """获取所有通道"""
        with self.lock:
            return list(self.channels.keys())
    
    def update_channel_config(self, channel_id: str, config: Dict[str, Any]):
        """更新通道配置"""
        with self.lock:
            if channel_id not in self.channels:
                self.logger.warning(f"Channel {channel_id} not found")
                return False
            
            channel = self.channels[channel_id]
            if hasattr(channel, 'update_config'):
                try:
                    channel.update_config(config)
                    self.logger.info(f"Channel {channel_id} config updated")
                    return True
                except Exception as e:
                    self.logger.error(f"Error updating channel {channel_id} config: {e}")
                    return False
            else:
                self.logger.warning(f"Channel {channel_id} does not support config update")
                return False
    
    def _run_channel(self, channel_id: str, channel):
        """运行通道"""
        try:
            if hasattr(channel, 'startup'):
                channel.startup()
            else:
                self.logger.warning(f"Channel {channel_id} does not have startup method")
        except Exception as e:
            self.logger.error(f"Error running channel {channel_id}: {e}")
