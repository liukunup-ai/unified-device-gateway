"""
MCP (Model Context Protocol) server implementation.

Uses FastMCP SDK to expose device management tools via MCP protocol.
"""
import json
import re
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


@mcp.tool()
async def serial_write(port: str, data: str, read_response: bool = False, encoding: str = "utf-8") -> str:
    """
    Write data to serial port.

    Args:
        port: Serial port path (e.g., /dev/ttyUSB0)
        data: Data to write
        read_response: Whether to read response after write
        encoding: Data encoding (utf-8 or base64)

    Returns:
        JSON object with write result.
    """
    from udg.api.schemas import Command
    from datetime import datetime

    safe_port = re.sub(r'[^a-zA-Z0-9_-]', '_', port)
    device_id = f"serial-{safe_port}"
    cmd = Command(
        id=f"mcp-{datetime.now().timestamp()}",
        device_id=device_id,
        command="write",
        params={"data": data, "read": read_response, "encoding": encoding},
        timeout_ms=5000
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
    }, indent=2)


@mcp.tool()
async def serial_read(port: str, bytes_to_read: int = 1024) -> str:
    """
    Read data from serial port.

    Args:
        port: Serial port path
        bytes_to_read: Number of bytes to read (default 1024)

    Returns:
        JSON object with read result.
    """
    from udg.api.schemas import Command
    from datetime import datetime

    safe_port = re.sub(r'[^a-zA-Z0-9_-]', '_', port)
    device_id = f"serial-{safe_port}"
    cmd = Command(
        id=f"mcp-{datetime.now().timestamp()}",
        device_id=device_id,
        command="read",
        params={"size": bytes_to_read},
        timeout_ms=5000
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
    }, indent=2)


@mcp.tool()
async def serial_set_config(port: str, baudrate: int = 115200, parity: str = "N", databits: int = 8, stopbits: int = 1) -> str:
    """
    Configure serial port parameters.

    Args:
        port: Serial port path
        baudrate: Baud rate (default 115200)
        parity: Parity (N/E/O, default N)
        databits: Data bits (5/6/7/8, default 8)
        stopbits: Stop bits (1/1.5/2, default 1)

    Returns:
        JSON object with config result.
    """
    from udg.api.schemas import Command
    from datetime import datetime

    safe_port = re.sub(r'[^a-zA-Z0-9_-]', '_', port)
    device_id = f"serial-{safe_port}"
    cmd = Command(
        id=f"mcp-{datetime.now().timestamp()}",
        device_id=device_id,
        command="config",
        params={"baudrate": baudrate, "parity": parity, "databits": databits, "stopbits": stopbits},
        timeout_ms=5000
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
    }, indent=2)


@mcp.tool()
async def serial_get_config(port: str) -> str:
    """
    Get serial port configuration.

    Args:
        port: Serial port path

    Returns:
        JSON object with current configuration.
    """
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})

    safe_port = re.sub(r'[^a-zA-Z0-9_-]', '_', port)
    device_id = f"serial-{safe_port}"
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})

    from udg.device.serial import SerialDevice
    if not isinstance(device, SerialDevice):
        return json.dumps({"error": "Device is not a SerialDevice", "code": "INVALID_DEVICE_TYPE"})

    return json.dumps({
        "device_id": device_id,
        "port": port,
        "baudrate": device._baudrate,
        "parity": device._parity,
        "databits": device._databits,
        "stopbits": device._stopbits,
    }, indent=2)


@mcp.tool()
async def get_ip(device_id: str) -> str:
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    try:
        result = await device.execute("get_ip", {}, 30000)
        return json.dumps({"device_id": device_id, "status": result.get("status"), "output": result.get("output")})
    except Exception as e:
        return json.dumps({"device_id": device_id, "status": "error", "error": str(e)})


@mcp.tool()
async def dump_ui(device_id: str) -> str:
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    try:
        result = await device.execute("dump_ui", {}, 30000)
        return json.dumps({"device_id": device_id, "status": result.get("status"), "output": result.get("output")})
    except Exception as e:
        return json.dumps({"device_id": device_id, "status": "error", "error": str(e)})


@mcp.tool()
async def click_by_text(device_id: str, text: str) -> str:
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    try:
        result = await device.execute("click_by_text", {"text": text}, 30000)
        return json.dumps({"device_id": device_id, "status": result.get("status"), "output": result.get("output")})
    except Exception as e:
        return json.dumps({"device_id": device_id, "status": "error", "error": str(e)})


@mcp.tool()
async def input_text_tool(device_id: str, text: str) -> str:
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    try:
        result = await device.execute("input_text", {"text": text}, 30000)
        return json.dumps({"device_id": device_id, "status": result.get("status"), "output": result.get("output")})
    except Exception as e:
        return json.dumps({"device_id": device_id, "status": "error", "error": str(e)})


@mcp.tool()
async def handle_alert(device_id: str, action: str = "accept") -> str:
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    try:
        result = await device.execute("handle_alert", {"action": action}, 30000)
        return json.dumps({"device_id": device_id, "status": result.get("status"), "output": result.get("output")})
    except Exception as e:
        return json.dumps({"device_id": device_id, "status": "error", "error": str(e)})


@mcp.tool()
async def assert_text(device_id: str, text: str) -> str:
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    try:
        result = await device.execute("assert_text", {"text": text}, 30000)
        return json.dumps({"device_id": device_id, "status": result.get("status"), "output": result.get("output")})
    except Exception as e:
        return json.dumps({"device_id": device_id, "status": "error", "error": str(e)})


@mcp.tool()
async def press(device_id: str, key: str = "home") -> str:
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    try:
        result = await device.execute("press", {"key": key}, 30000)
        return json.dumps({"device_id": device_id, "status": result.get("status"), "output": result.get("output")})
    except Exception as e:
        return json.dumps({"device_id": device_id, "status": "error", "error": str(e)})


@mcp.tool()
async def dump_ui_xml(device_id: str) -> str:
    if _device_manager is None:
        return json.dumps({"error": "Device manager not initialized"})
    device = await _device_manager.get_device(device_id)
    if not device:
        return json.dumps({"error": f"Device {device_id} not found", "code": "NOT_FOUND"})
    try:
        result = await device.execute("dump_ui", {}, 30000)
        return json.dumps({"device_id": device_id, "status": result.get("status"), "output": result.get("output")})
    except Exception as e:
        return json.dumps({"device_id": device_id, "status": "error", "error": str(e)})


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
