"""
MCP (Model Context Protocol) server implementation.

Uses FastMCP SDK to expose device management tools via MCP protocol.
"""
import json
from typing import Any
from mcp.server.fastmcp import FastMCP
from udg.device.base import DeviceType
from udg.auth.token import validate_token
from udg.config import settings

# Global references to shared state (set by http.py)
_device_manager = None
_executor = None


def init_mcp(device_manager, executor):
    """Initialize MCP with shared dependencies."""
    global _device_manager, _executor
    _device_manager = device_manager
    _executor = executor


def _validate_auth(token: str | None) -> bool:
    """Validate authorization token."""
    if not token:
        return False
    return validate_token(token, settings.token or "")


# Create FastMCP instance
mcp = FastMCP("udg", stateless_http=True)


@mcp.tool()
async def list_devices() -> str:
    """
    List all connected devices.

    Returns JSON array of device objects with id, type, status, and metadata.
    """
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    
    devices = await _device_manager.list_devices()
    result = [
        {
            "device_id": d.device_id,
            "device_type": d.device_type.value,
            "status": d.status.value,
            "udid": d.udid,
            "serial": d.serial,
            "ip_port": d.ip_port,
            "serial_port": d.serial_port,
        }
        for d in devices
    ]
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_device_info(device_id: str) -> str:
    """
    Get detailed information for a specific device.

    Args:
        device_id: The unique identifier of the device

    Returns:
        JSON object with device details or error if not found.
    """
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    
    return json.dumps({
        "device_id": device.info.device_id,
        "device_type": device.info.device_type.value,
        "status": device.info.status.value,
        "udid": device.info.udid,
        "serial": device.info.serial,
        "ip_port": device.info.ip_port,
        "serial_port": device.info.serial_port,
    }, indent=2)


@mcp.tool()
async def execute_command(device_id: str, command: str, timeout: int = 30) -> str:
    """
    Execute a shell command on a connected device.

    Args:
        device_id: The unique identifier of the target device
        command: The shell command to execute
        timeout: Command timeout in seconds (default: 30)

    Returns:
        JSON object with command result including output, status, and execution time.
    """
    if _device_manager is None or _executor is None:
        return json.dumps({"error": "Executor not initialized"})
    
    from udg.api.schemas import Command
    from datetime import datetime
    
    cmd = Command(
        id=f"mcp-{datetime.now().timestamp()}",
        device_id=device_id,
        command=command,
        params={},
        timeout_ms=timeout * 1000
    )
    
    results = await _executor.execute_batch([cmd])
    result = results[0]
    
    return json.dumps({
        "id": result.id,
        "device_id": result.device_id,
        "command": result.command,
        "status": result.status,
        "output": result.output,
        "error": result.error,
        "error_code": result.error_code,
        "execution_time_ms": result.execution_time_ms,
        "timestamp": result.timestamp.isoformat(),
    }, indent=2)


@mcp.tool()
async def screenshot(device_id: str) -> str:
    """
    Take a screenshot from a device.

    Args:
        device_id: The unique identifier of the target device

    Returns:
        JSON object with screenshot result (base64 encoded or file path).
    """
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    
    try:
        result = await device.execute("screenshot", {}, 30000)
        return json.dumps({
            "device_id": device_id,
            "status": result.get("status", "success"),
            "data": result.get("output"),
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "device_id": device_id,
            "status": "error",
            "error": str(e),
            "code": "SCREENSHOT_FAILED",
        })


@mcp.resource("device://list")
async def device_list_resource() -> str:
    """
    Get device list as a resource.

    Returns JSON array of all connected devices.
    """
    return await list_devices()


@mcp.resource("device://{device_id}")
async def device_info_resource(device_id: str) -> str:
    """
    Get specific device info as a resource.

    Args:
        device_id: The device identifier

    Returns JSON object with device details.
    """
    return await get_device_info(device_id)


def get_mcp_app():
    """Get the MCP ASGI app for mounting in FastAPI."""
    return mcp.streamable_http_app()
