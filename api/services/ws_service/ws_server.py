import asyncio
from loguru import logger
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

async def recv_handler(ws):
    try:
        async for message in ws:
            logger.debug(f"recv: {message}")
            await ws.send(message)
    except ConnectionClosed as e:
        logger.info(f"closed: code={getattr(e, 'code', None)} reason={getattr(e, 'reason', None)}")
        
async def main():
    async with serve(recv_handler, "localhost", 5005) as server:
        logger.info("Websocket server listening on ws://0.0.0.0:5005")
        await asyncio.Future()
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        while(1):
            logger.critical(f"ERROR: {e}")
        
    except KeyboardInterrupt:
        logger.info("Shutting down")