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
    print(f"gRPC server on port {settings.grpc_port}")
    print()
    print("=" * 50)
    print("UDG Server Started Successfully!")
    print("=" * 50)
    print(f"HTTP API:     http://localhost:{settings.http_port}")
    print(f"gRPC:         localhost:{settings.grpc_port}")
    print(f"MCP SSE:      http://localhost:{settings.http_port}/mcp")
    print()
    print("API Documentation:")
    print(f"  Swagger UI: http://localhost:{settings.http_port}/docs")
    print(f"  ReDoc:      http://localhost:{settings.http_port}/redoc")
    print()
    print("Available endpoints:")
    print(f"  Health:   http://localhost:{settings.http_port}/health")
    print(f"  Devices:  http://localhost:{settings.http_port}/devices")
    print(f"  Metrics:  http://localhost:{settings.http_port}/metrics")
    print("=" * 50)

    task = asyncio.create_task(server.serve())
    await shutdown_event.wait()
    server.should_exit = True
    await task
    print("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())