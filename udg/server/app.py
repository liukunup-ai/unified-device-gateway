import asyncio
import signal
from udg.server.http import app
from udg.server.grpc import serve as grpc_serve

shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    shutdown_event.set()

async def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting servers...")
    print("HTTP server on port 50001")
    print("gRPC server on port 50002")
    
    await shutdown_event.wait()
    print("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())