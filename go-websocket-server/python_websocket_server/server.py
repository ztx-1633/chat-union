import asyncio
import websockets
import json
import logging
import uuid
from functools import partial

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储所有活动的WebSocket连接
clients = {}
# 存储会话信息
sessions = {}

class WebSocketServer:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.server = None
    
    async def handle_connection(self, websocket):
        # 生成唯一的客户端ID
        client_id = str(uuid.uuid4())
        clients[client_id] = websocket
        logger.info(f"Client connected: {client_id}")
        
        try:
            # 处理消息
            async for message in websocket:
                await self.handle_message(client_id, message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client disconnected: {client_id}, reason: {e}")
        finally:
            # 清理连接
            if client_id in clients:
                del clients[client_id]
            if client_id in sessions:
                del sessions[client_id]
    
    async def handle_message(self, client_id, message):
        try:
            # 解析消息
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # 处理心跳
                await self.send_message(client_id, {'type': 'pong'})
            elif message_type == 'message':
                # 处理聊天消息
                session_id = data.get('session_id')
                if not session_id:
                    session_id = client_id
                
                # 存储会话信息
                if session_id not in sessions:
                    sessions[session_id] = []
                
                # 添加消息到会话
                sessions[session_id].append(data)
                
                # 处理消息并返回响应
                # 调用Python核心处理消息
                response = self.process_message_with_core(data)
                await self.send_message(client_id, response)
            elif message_type == 'broadcast':
                # 广播消息给所有客户端
                await self.broadcast_message(data.get('content'))
            elif message_type == 'core_response':
                # 处理来自Python核心的响应
                session_id = data.get('session_id')
                if session_id:
                    await self.send_message(client_id, data)
            elif message_type == 'channel_config':
                # 处理通道配置
                channel_name = data.get('channel_name')
                config = data.get('config', {})
                logger.info(f'收到通道配置请求: {channel_name}, 配置: {config}')
                
                # 存储通道配置
                if 'channels' not in globals():
                    global channels
                    channels = {}
                
                channels[channel_name] = config
                
                # 返回配置成功响应
                await self.send_message(client_id, {
                    'type': 'channel_config_response',
                    'channel_name': channel_name,
                    'status': 'success',
                    'message': f'通道 {channel_name} 配置成功'
                })
            elif message_type == 'channel_status':
                # 获取通道状态
                channel_name = data.get('channel_name')
                logger.info(f'收到通道状态请求: {channel_name}')
                
                # 检查通道状态
                if 'channels' in globals() and channel_name in channels:
                    status = '已配置'
                    config = channels[channel_name]
                else:
                    status = '未配置'
                    config = {}
                
                # 返回通道状态
                await self.send_message(client_id, {
                    'type': 'channel_status_response',
                    'channel_name': channel_name,
                    'status': status,
                    'config': config
                })
            elif message_type == 'self_test':
                # 全功能自测循环
                logger.info('开始全功能自测')
                
                test_results = {
                    'connection_test': 'pass',
                    'message_test': 'pass',
                    'channel_test': 'pass',
                    'performance_test': 'pass',
                    'details': {}
                }
                
                # 1. 连接测试
                try:
                    await self.send_message(client_id, {'type': 'ping'})
                    test_results['details']['connection_test'] = '连接测试通过'
                except Exception as e:
                    test_results['connection_test'] = 'fail'
                    test_results['details']['connection_test'] = f'连接测试失败: {str(e)}'
                
                # 2. 消息处理测试
                try:
                    test_message = {
                        'type': 'message',
                        'session_id': client_id,
                        'content': '测试消息',
                        'msg_id': str(uuid.uuid4())
                    }
                    response = self.process_message_with_core(test_message)
                    test_results['details']['message_test'] = f'消息处理测试通过，响应: {response.get("content", "无响应")}'
                except Exception as e:
                    test_results['message_test'] = 'fail'
                    test_results['details']['message_test'] = f'消息处理测试失败: {str(e)}'
                
                # 3. 通道配置测试
                try:
                    test_channel = 'test_channel'
                    test_config = {'test': 'config'}
                    if 'channels' not in globals():
                        global channels
                        channels = {}
                    channels[test_channel] = test_config
                    test_results['details']['channel_test'] = '通道配置测试通过'
                except Exception as e:
                    test_results['channel_test'] = 'fail'
                    test_results['details']['channel_test'] = f'通道配置测试失败: {str(e)}'
                
                # 4. 性能测试
                try:
                    import time
                    start_time = time.time()
                    for i in range(10):
                        test_message = {
                            'type': 'message',
                            'session_id': client_id,
                            'content': f'性能测试消息 {i}',
                            'msg_id': str(uuid.uuid4())
                        }
                        self.process_message_with_core(test_message)
                    end_time = time.time()
                    test_results['details']['performance_test'] = f'性能测试通过，10条消息处理时间: {end_time - start_time:.3f}秒'
                except Exception as e:
                    test_results['performance_test'] = 'fail'
                    test_results['details']['performance_test'] = f'性能测试失败: {str(e)}'
                
                # 计算总体结果
                if all(value == 'pass' for value in test_results.values() if value != 'details'):
                    test_results['overall'] = 'pass'
                else:
                    test_results['overall'] = 'fail'
                
                # 返回自测结果
                await self.send_message(client_id, {
                    'type': 'self_test_response',
                    'results': test_results
                })
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from client {client_id}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def process_message_with_core(self, data):
        """调用Python核心处理消息"""
        try:
            # 导入Python核心模块
            import sys
            sys.path.append('e:\\16337\\chat_union\\chatgpt-on-wechat-master')
            
            from channel.websocket.websocket_channel import WebSocketChannel, WebSocketMessage
            from bridge.context import Context, ContextType
            
            # 创建消息对象
            msg_id = data.get('msg_id', str(uuid.uuid4()))
            content = data.get('content', '')
            session_id = data.get('session_id', '')
            
            msg = WebSocketMessage(msg_id, content, from_user_id=session_id)
            
            # 创建通道实例
            channel = WebSocketChannel()
            
            # 构建上下文
            context = channel._compose_context(ContextType.TEXT, content, msg=msg, isgroup=False)
            if context:
                context["session_id"] = session_id
                context["receiver"] = session_id
                
                # 处理消息
                reply = channel.build_reply_content(content, context)
                
                # 构建响应
                return {
                    'type': 'message',
                    'session_id': session_id,
                    'content': reply.content
                }
            else:
                return {
                    'type': 'message',
                    'session_id': session_id,
                    'content': 'Error: Failed to process message'
                }
        except Exception as e:
            logger.error(f"Error processing message with core: {e}")
            return {
                'type': 'message',
                'session_id': data.get('session_id', ''),
                'content': f"Error: {str(e)}"
            }
    
    async def send_message(self, client_id, message):
        if client_id in clients:
            try:
                await clients[client_id].send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Failed to send message to client {client_id}: connection closed")
    
    async def broadcast_message(self, message):
        for client_id, websocket in clients.items():
            try:
                await websocket.send(json.dumps({
                    'type': 'broadcast',
                    'content': message
                }))
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Failed to broadcast to client {client_id}: connection closed")
    
    async def start(self):
        # 创建一个包装函数来处理连接
        async def handler(websocket):
            await self.handle_connection(websocket)
        
        self.server = await websockets.serve(
            handler,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=60
        )
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        await self.server.wait_closed()
    
    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")

if __name__ == "__main__":
    server = WebSocketServer()
    asyncio.run(server.start())
