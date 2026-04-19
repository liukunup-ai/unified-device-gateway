from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from udg.api.schemas import ExecuteRequest, ExecuteResponse, DeviceListResponse, DeviceResponse
from udg.auth.token import validate_token
from udg.config import settings
from udg.device.manager import DeviceManager
from udg.executor.runner import CommandExecutor
from udg.utils.metrics import get_metrics
from udg.server.mcp import mcp, init_mcp

device_manager = DeviceManager()
executor = CommandExecutor(device_manager)
init_mcp(device_manager, executor)

sse = SseServerTransport("/messages/")
session_manager = StreamableHTTPSessionManager(
    app=mcp._mcp_server,
    event_store=None,
    json_response=True,
    stateless=True,
)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def ready(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ready"})


async def live(request: Request) -> JSONResponse:
    return JSONResponse({"status": "live"})


async def metrics(request: Request) -> JSONResponse:
    return JSONResponse(get_metrics())


async def execute(request: Request) -> JSONResponse:
    body = await request.json()
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    token = auth_header.replace("Bearer ", "")
    if not validate_token(token, settings.token or ""):
        return JSONResponse({"detail": "Invalid token"}, status_code=401)

    req = ExecuteRequest(**body)
    results = await executor.execute_batch(req.commands)
    return JSONResponse(ExecuteResponse(results=results).model_dump())


async def list_devices(request: Request) -> JSONResponse:
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    devices = await device_manager.list_devices()
    return JSONResponse(DeviceListResponse(devices=[DeviceResponse(
        device_id=d.device_id,
        device_type=d.device_type.value,
        status=d.status.value
    ) for d in devices]).model_dump())


async def handle_sse(request: Request) -> None:
    async with sse.connect_sse(
        request.scope, request.receive, request._send,
    ) as (read_stream, write_stream):
        await mcp._mcp_server.run(
            read_stream, write_stream, mcp._mcp_server.create_initialization_options(),
        )


async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    await session_manager.handle_request(scope, receive, send)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with session_manager.run():
        yield


app = Starlette(
    lifespan=lifespan,
    routes=[
        Mount("/", app=handle_streamable_http),
        Route("/health", health),
        Route("/health/ready", ready),
        Route("/health/live", live),
        Route("/metrics", metrics),
        Route("/api/v1/execute", execute, methods=["POST"]),
        Route("/api/v1/devices", list_devices),
    ],
)
