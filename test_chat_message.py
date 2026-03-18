import asyncio
import websockets
import json

async def test_chat_message():
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            # 发送聊天消息
            message = {
                'type': 'message',
                'session_id': 'test_session_123',
                'content': '你好，测试消息'
            }
            await ws.send(json.dumps(message))
            print('发送消息:', message)
            
            # 接收响应
            response = await ws.recv()
            print('收到响应:', response)
    except Exception as e:
        print('测试失败:', e)

if __name__ == '__main__':
    asyncio.run(test_chat_message())