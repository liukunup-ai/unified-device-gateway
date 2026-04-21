from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from mcp.server.sse import SseServerTransport
from udg.api.schemas import ExecuteRequest, ExecuteResponse, DeviceListResponse, DeviceResponse, Command
from udg.auth.token import validate_token
from udg.config import settings
from udg.device.manager import get_device_manager
from udg.executor.runner import CommandExecutor
from udg.utils.metrics import get_metrics
from udg.server.mcp import mcp, init_mcp, get_mcp_app
from udg.scanner.device_scanner import scan_all_devices
from udg.scanner.serial_scanner import scan_serial_ports
from datetime import datetime
import re

device_manager = get_device_manager()
executor = CommandExecutor(device_manager)
init_mcp(device_manager, executor)

sse = SseServerTransport("/messages/")

app = FastAPI(title="UDG API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")


@app.on_event("startup")
async def startup():
    await scan_all_devices(device_manager)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/ready")
async def ready():
    return {"status": "ready"}


@app.get("/health/live")
async def live():
    return {"status": "live"}


@app.get("/metrics")
async def metrics():
    return get_metrics()


async def require_auth(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    token = auth_header.replace("Bearer ", "")
    if not validate_token(token, settings.token or ""):
        return JSONResponse({"detail": "Invalid token"}, status_code=401)
    return None


@app.post("/execute")
async def execute(req: ExecuteRequest, request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    token = auth_header.replace("Bearer ", "")
    if not validate_token(token, settings.token or ""):
        return JSONResponse({"detail": "Invalid token"}, status_code=401)

    results = await executor.execute_batch(req.commands)
    return ExecuteResponse(results=results).model_dump()


@app.get("/devices")
async def list_devices(request: Request):
    auth_error = await require_auth(request)
    if auth_error:
        return auth_error
    devices = await device_manager.list_devices()
    return DeviceListResponse(devices=[DeviceResponse(
        device_id=d.device_id,
        device_type=d.device_type.value,
        status=d.status.value
    ) for d in devices]).model_dump()


async def device_command(request: Request, command: str, params: dict):
    auth_error = await require_auth(request)
    if auth_error:
        return auth_error
    body = await request.json()
    device_id = body.get("device_id")
    if not device_id:
        return JSONResponse({"detail": "device_id required"}, status_code=400)
    cmd = Command(
        id=f"http-{datetime.now().timestamp()}",
        device_id=device_id,
        command=command,
        params=params,
        timeout_ms=body.get("timeout_ms", 30000)
    )
    results = await executor.execute_batch([cmd])
    return {"status": results[0].status, "output": results[0].output, "error": results[0].error}


@app.post("/push")
async def push(request: Request):
    body = await request.json()
    return await device_command(request, "push", {
        "local_path": body.get("local_path", ""),
        "remote_path": body.get("remote_path", "")
    })


@app.post("/pull")
async def pull(request: Request):
    body = await request.json()
    return await device_command(request, "pull", {
        "remote_path": body.get("remote_path", ""),
        "local_path": body.get("local_path", "")
    })


@app.get("/apps")
async def list_apps(request: Request):
    return await device_command(request, "list_apps", {})


@app.post("/install")
async def install(request: Request):
    body = await request.json()
    return await device_command(request, "install", {"path": body.get("path", "")})


@app.post("/uninstall")
async def uninstall(request: Request):
    body = await request.json()
    return await device_command(request, "uninstall", {"package": body.get("package", "")})


@app.post("/launch")
async def launch(request: Request):
    body = await request.json()
    return await device_command(request, "start_app", {"package": body.get("package", "")})


@app.post("/stop")
async def stop(request: Request):
    body = await request.json()
    return await device_command(request, "stop_app", {"package": body.get("package", "")})


@app.get("/battery")
async def battery(request: Request):
    return await device_command(request, "get_battery", {})


@app.get("/current/app")
async def current_app(request: Request):
    return await device_command(request, "get_current_app", {})


@app.post("/tap")
async def tap(request: Request):
    body = await request.json()
    return await device_command(request, "tap", {"x": body.get("x", 0), "y": body.get("y", 0)})


@app.post("/swipe")
async def swipe(request: Request):
    body = await request.json()
    return await device_command(request, "swipe", {
        "x1": body.get("x1", 0),
        "y1": body.get("y1", 0),
        "x2": body.get("x2", 0),
        "y2": body.get("y2", 0),
        "duration": body.get("duration", 300)
    })


@app.get("/screenshot")
async def screenshot(request: Request):
    return await device_command(request, "screenshot", {})


@app.get("/ip")
async def get_ip(request: Request):
    return await device_command(request, "get_ip", {})


@app.get("/ui/xml")
async def dump_ui(request: Request):
    return await device_command(request, "dump_ui", {})


@app.post("/press")
async def press(request: Request):
    body = await request.json()
    return await device_command(request, "press", {"key": body.get("key", "home")})


@app.post("/click-by-text")
async def click_by_text(request: Request):
    body = await request.json()
    return await device_command(request, "click_by_text", {"text": body.get("text", "")})


@app.post("/input")
async def input_text(request: Request):
    body = await request.json()
    return await device_command(request, "input_text", {"text": body.get("text", "")})


@app.post("/alert")
async def handle_alert(request: Request):
    body = await request.json()
    return await device_command(request, "handle_alert", {"action": body.get("action", "accept")})


@app.post("/assert/text")
async def assert_text(request: Request):
    body = await request.json()
    return await device_command(request, "assert_text", {"text": body.get("expected", "")})


@app.post("/record")
async def record(request: Request):
    body = await request.json()
    action = body.get("action", "start")
    if action == "stop":
        return await device_command(request, "stop_screenrecord", {})
    return await device_command(request, "screenrecord", {"path": body.get("path", "/sdcard/screen.mp4")})


@app.get("/serial/ports")
async def list_serial_ports(request: Request):
    auth_error = await require_auth(request)
    if auth_error:
        return auth_error
    ports = scan_serial_ports()
    return {"ports": ports}


async def serial_command(request: Request, command: str, params: dict):
    auth_error = await require_auth(request)
    if auth_error:
        return auth_error
    body = await request.json()
    port = body.get("port")
    if not port:
        return JSONResponse({"detail": "port required"}, status_code=400)
    safe_port = re.sub(r'[^a-zA-Z0-9_-]', '_', port)
    device_id = f"serial-{safe_port}"
    cmd = Command(
        id=f"http-{datetime.now().timestamp()}",
        device_id=device_id,
        command=command,
        params=params,
        timeout_ms=body.get("timeout_ms", 30000)
    )
    results = await executor.execute_batch([cmd])
    return {"status": results[0].status, "output": results[0].output, "error": results[0].error}


@app.post("/serial/write")
async def serial_write(request: Request):
    body = await request.json()
    return await serial_command(request, "write", {
        "data": body.get("data", ""),
        "read": body.get("read", False),
        "encoding": body.get("encoding", "utf-8")
    })


@app.post("/serial/read")
async def serial_read(request: Request):
    body = await request.json()
    return await serial_command(request, "read", {
        "size": body.get("size", body.get("bytes", 1024))
    })


@app.post("/serial/config")
async def serial_config_post(request: Request):
    body = await request.json()
    return await serial_command(request, "config", {
        "baudrate": body.get("baudrate", 115200),
        "parity": body.get("parity", "N"),
        "databits": body.get("databits", 8),
        "stopbits": body.get("stopbits", 1)
    })


@app.get("/serial/config")
async def serial_config_get(request: Request):
    auth_error = await require_auth(request)
    if auth_error:
        return auth_error
    port = request.query_params.get("port")
    if not port:
        return JSONResponse({"detail": "port query parameter required"}, status_code=400)
    safe_port = re.sub(r'[^a-zA-Z0-9_-]', '_', port)
    device_id = f"serial-{safe_port}"
    device = await device_manager.get_device(device_id)
    if device:
        return {
            "port": port,
            "baudrate": device.info.metadata.get("baudrate", 115200),
            "parity": device.info.metadata.get("parity", "N"),
            "databits": device.info.metadata.get("databits", 8),
            "stopbits": device.info.metadata.get("stopbits", 1)
        }
    return {
        "port": port,
        "baudrate": 115200,
        "parity": "N",
        "databits": 8,
        "stopbits": 1
    }


mcp_app = get_mcp_app()
app.mount("/mcp", mcp_app)