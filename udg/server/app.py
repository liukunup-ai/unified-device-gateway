import asyncio
import signal
import uvicorn
from udg.server.http import app
from udg.server.grpc import serve as grpc_serve
from udg.config import settings

shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    shutdown_event.set()

async def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    config = uvicorn.Config(app, host="0.0.0.0", port=settings.http_port, log_level="info")
    server = uvicorn.Server(config)

    print(f"Starting HTTP server on port {settings.http_port}...")

    task = asyncio.create_task(server.serve())
    await shutdown_event.wait()
    server.should_exit = True
    await task
    print("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())