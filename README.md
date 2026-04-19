# Unified Device Gateway (udg)

A Python library for unified device control via HTTP, gRPC, and MCP protocols.

## Features

- HTTP REST API on port 8080
- gRPC service on port 50000
- MCP (Model Context Protocol) via SSE on port 8080
- Support for iOS (tidevice/wda), Android (adb/uiautomator2), and Serial devices
- Token-based authentication
- Prometheus metrics
- Structured JSON logging

## Installation

```bash
pip install udg
```

## Quick Start

```bash
# Start the server
udg start

# Show current token
udg token show

# Rotate token
udg token rotate

# List devices
udg device list
```

## API

### HTTP

```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/devices
```

### gRPC

```bash
grpcurl localhost:50000 list
```

### MCP (Model Context Protocol)

Connect via HTTP transport at `http://localhost:8080/mcp`.

#### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_devices` | List all connected devices | None |
| `get_device_info` | Get details for a specific device | `device_id: str` |
| `execute_command` | Execute shell command on device | `device_id: str`, `command: str`, `timeout: int = 30` |
| `screenshot` | Take screenshot from device | `device_id: str` |

#### MCP Resources

| Resource | URI | Description |
|----------|-----|-------------|
| Device List | `device://list` | JSON list of all devices |
| Device Info | `device://{device_id}` | JSON info for specific device |

#### MCP Client Example

```python
from mcp.client.fastmcp import FastMCP

client = FastMCP("udg-client")

# List devices
devices = await client.call_tool("list_devices")
print(devices)

# Get device info
info = await client.call_tool("get_device_info", {"device_id": "ios-001"})
print(info)

# Execute command
result = await client.call_tool("execute_command", {
    "device_id": "ios-001",
    "command": "ls -la",
    "timeout": 30
})
print(result)

# Take screenshot
screenshot = await client.call_tool("screenshot", {"device_id": "ios-001"})
print(screenshot)
```

#### Using with Claude Desktop

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "udg": {
      "command": "uv",
      "args": ["run", "--with", "mcp", "udg", "start"]
    }
  }
}
```

Or connect to a running server:

```json
{
  "mcpServers": {
    "udg": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

## Configuration

Environment variables:

- `UDG_HTTP_PORT`: HTTP server port (default: 8080)
- `UDG_GRPC_PORT`: gRPC server port (default: 50000)
- `UDG_TOKEN`: Auth token (generated if not set)
- `UDG_MAX_CONNECTIONS`: Max device connections (default: 50)
- `UDG_LOG_LEVEL`: Log level (default: INFO)

## License

MIT
