import asyncio
import websockets
import json

async def test_ws():
    try:
        async with websockets.connect('ws://localhost:8765') as ws:
            await ws.send(json.dumps({'type': 'ping'}))
            response = await ws.recv()
            print('WebSocket测试成功:', response)
    except Exception as e:
        print('WebSocket测试失败:', e)

if __name__ == '__main__':
    asyncio.run(test_ws())