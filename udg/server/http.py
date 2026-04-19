from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from mcp.server.sse import SseServerTransport
from udg.api.schemas import ExecuteRequest, ExecuteResponse, DeviceListResponse, DeviceResponse
from udg.auth.token import validate_token
from udg.config import settings
from udg.device.manager import get_device_manager
from udg.executor.runner import CommandExecutor
from udg.utils.metrics import get_metrics
from udg.server.mcp import mcp, init_mcp, get_mcp_app
from udg.scanner.device_scanner import scan_all_devices

device_manager = get_device_manager()


async def startup_scan():
    await scan_all_devices(device_manager)
executor = CommandExecutor(device_manager)
init_mcp(device_manager, executor)

sse = SseServerTransport("/messages/")


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def ready(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ready"})


async def live(request: Request) -> JSONResponse:
    return JSONResponse({"status": "live"})


async def metrics(request: Request) -> JSONResponse:
    return JSONResponse(get_metrics())


async def list_routes(request: Request) -> JSONResponse:
    routes = [
        {"path": "/routes", "method": "GET", "description": "返回所有可用路由"},
        {"path": "/health", "method": "GET", "description": "健康检查"},
        {"path": "/health/ready", "method": "GET", "description": "就绪检查"},
        {"path": "/health/live", "method": "GET", "description": "存活检查"},
        {"path": "/metrics", "method": "GET", "description": "Prometheus 指标"},
        {"path": "/devices", "method": "GET", "description": "列出所有设备", "auth": True},
        {"path": "/push", "method": "POST", "description": "推送文件", "auth": True},
        {"path": "/pull", "method": "POST", "description": "拉取文件", "auth": True},
        {"path": "/apps", "method": "GET", "description": "列出应用", "auth": True},
        {"path": "/install", "method": "POST", "description": "安装应用", "auth": True},
        {"path": "/uninstall", "method": "POST", "description": "卸载应用", "auth": True},
        {"path": "/launch", "method": "POST", "description": "启动应用", "auth": True},
        {"path": "/stop", "method": "POST", "description": "停止应用", "auth": True},
        {"path": "/battery", "method": "GET", "description": "获取电量", "auth": True},
        {"path": "/current/app", "method": "GET", "description": "获取当前应用", "auth": True},
        {"path": "/tap", "method": "POST", "description": "点击屏幕", "auth": True},
        {"path": "/swipe", "method": "POST", "description": "滑动屏幕", "auth": True},
        {"path": "/screenshot", "method": "GET", "description": "截图", "auth": True},
        {"path": "/record", "method": "POST", "description": "录屏", "auth": True},
        {"path": "/execute", "method": "POST", "description": "批量执行命令", "auth": True},
        {"path": "/mcp", "method": "SSE", "description": "MCP 协议端点"},
    ]
    return JSONResponse({"routes": routes, "grpc_port": 50051})


def require_auth(request: Request) -> tuple[bool, JSONResponse | None]:
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False, JSONResponse({"detail": "Unauthorized"}, status_code=401)
    token = auth_header.replace("Bearer ", "")
    if not validate_token(token, settings.token or ""):
        return False, JSONResponse({"detail": "Invalid token"}, status_code=401)
    return True, None


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
    ok, resp = require_auth(request)
    if not ok:
        return resp
    devices = await device_manager.list_devices()
    return JSONResponse(DeviceListResponse(devices=[DeviceResponse(
        device_id=d.device_id,
        device_type=d.device_type.value,
        status=d.status.value
    ) for d in devices]).model_dump())


async def device_command(request: Request, command: str, params: dict) -> JSONResponse:
    ok, resp = require_auth(request)
    if not ok:
        return resp
    body = await request.json()
    device_id = body.get("device_id")
    if not device_id:
        return JSONResponse({"detail": "device_id required"}, status_code=400)
    from udg.api.schemas import Command
    from datetime import datetime
    cmd = Command(
        id=f"http-{datetime.now().timestamp()}",
        device_id=device_id,
        command=command,
        params=params,
        timeout_ms=body.get("timeout_ms", 30000)
    )
    results = await executor.execute_batch([cmd])
    return JSONResponse({"status": results[0].status, "output": results[0].output, "error": results[0].error})


async def push(request: Request) -> JSONResponse:
    body = await request.json()
    return await device_command(request, "push", {
        "local_path": body.get("local_path", ""),
        "remote_path": body.get("remote_path", "")
    })


async def pull(request: Request) -> JSONResponse:
    body = await request.json()
    return await device_command(request, "pull", {
        "remote_path": body.get("remote_path", ""),
        "local_path": body.get("local_path", "")
    })


async def list_apps(request: Request) -> JSONResponse:
    return await device_command(request, "list_apps", {})


async def install(request: Request) -> JSONResponse:
    body = await request.json()
    return await device_command(request, "install", {"path": body.get("path", "")})


async def uninstall(request: Request) -> JSONResponse:
    body = await request.json()
    return await device_command(request, "uninstall", {"package": body.get("package", "")})


async def launch(request: Request) -> JSONResponse:
    body = await request.json()
    return await device_command(request, "start_app", {"package": body.get("package", "")})


async def stop(request: Request) -> JSONResponse:
    body = await request.json()
    return await device_command(request, "stop_app", {"package": body.get("package", "")})


async def battery(request: Request) -> JSONResponse:
    body = dict(request.query_params)
    return await device_command(request, "get_battery", {})


async def current_app(request: Request) -> JSONResponse:
    return await device_command(request, "get_current_app", {})


async def tap(request: Request) -> JSONResponse:
    body = await request.json()
    return await device_command(request, "tap", {"x": body.get("x", 0), "y": body.get("y", 0)})


async def swipe(request: Request) -> JSONResponse:
    body = await request.json()
    return await device_command(request, "swipe", {
        "x1": body.get("x1", 0),
        "y1": body.get("y1", 0),
        "x2": body.get("x2", 0),
        "y2": body.get("y2", 0),
        "duration": body.get("duration", 300)
    })


async def screenshot(request: Request) -> JSONResponse:
    return await device_command(request, "screenshot", {})


async def record(request: Request) -> JSONResponse:
    body = await request.json()
    action = body.get("action", "start")
    if action == "stop":
        return await device_command(request, "stop_screenrecord", {})
    return await device_command(request, "screenrecord", {"path": body.get("path", "/sdcard/screen.mp4")})


async def handle_sse(request: Request) -> None:
    async with sse.connect_sse(
        request.scope, request.receive, request._send,
    ) as (read_stream, write_stream):
        await mcp._mcp_server.run(
            read_stream, write_stream, mcp._mcp_server.create_initialization_options(),
        )


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    await startup_scan()
    yield


mcp_app = get_mcp_app()

app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/health", health),
        Route("/health/ready", ready),
        Route("/health/live", live),
        Route("/metrics", metrics),
        Route("/routes", list_routes),
        Route("/devices", list_devices),
        Route("/push", push, methods=["POST"]),
        Route("/pull", pull, methods=["POST"]),
        Route("/apps", list_apps, methods=["GET"]),
        Route("/install", install, methods=["POST"]),
        Route("/uninstall", uninstall, methods=["POST"]),
        Route("/launch", launch, methods=["POST"]),
        Route("/stop", stop, methods=["POST"]),
        Route("/battery", battery, methods=["GET"]),
        Route("/current/app", current_app, methods=["GET"]),
        Route("/tap", tap, methods=["POST"]),
        Route("/swipe", swipe, methods=["POST"]),
        Route("/screenshot", screenshot, methods=["GET"]),
        Route("/record", record, methods=["POST"]),
        Route("/execute", execute, methods=["POST"]),
        Mount("/mcp", app=mcp_app),
    ],
)
