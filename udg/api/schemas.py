from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime

class Command(BaseModel):
    id: str
    device_id: str
    command: str
    params: dict[str, Any] = Field(default_factory=dict)
    timeout_ms: int = 60000

class ExecuteRequest(BaseModel):
    commands: list[Command]

class CommandResult(BaseModel):
    id: str
    device_id: str
    command: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time_ms: int
    timestamp: datetime

class ExecuteResponse(BaseModel):
    results: list[CommandResult]

class DeviceResponse(BaseModel):
    device_id: str
    device_type: str
    status: str
    udid: Optional[str] = None
    serial: Optional[str] = None
    ip_port: Optional[str] = None
    serial_port: Optional[str] = None

class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]

class ErrorResponse(BaseModel):
    error: str
    code: str
    details: Optional[dict] = None