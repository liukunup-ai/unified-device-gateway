from fastapi import FastAPI, HTTPException, Header
from typing import Optional
from udg.api.schemas import ExecuteRequest, ExecuteResponse, DeviceListResponse, DeviceResponse
from udg.auth.token import validate_token
from udg.config import settings
from udg.device.manager import DeviceManager
from udg.executor.runner import CommandExecutor

app = FastAPI()
device_manager = DeviceManager()
executor = CommandExecutor(device_manager)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/ready")
async def ready():
    return {"status": "ready"}


@app.get("/health/live")
async def live():
    return {"status": "live"}


@app.post("/api/v1/execute")
async def execute(request: ExecuteRequest, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.replace("Bearer ", "")
    if not validate_token(token, settings.token or ""):
        raise HTTPException(status_code=401, detail="Invalid token")
    results = await executor.execute_batch(request.commands)
    return ExecuteResponse(results=results)


@app.get("/api/v1/devices")
async def list_devices(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    devices = await device_manager.list_devices()
    return DeviceListResponse(devices=[DeviceResponse(device_id=d.device_id, device_type=d.device_type.value, status=d.status.value) for d in devices])