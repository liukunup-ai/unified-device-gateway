# Unified Device Gateway (udg)

A Python library for unified device control via HTTP, gRPC, and MCP protocols.

## Features

- HTTP REST API on port 50001
- gRPC service on port 50002
- MCP (Model Context Protocol) via SSE on port 50001
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
curl http://localhost:50001/health
curl http://localhost:50001/api/v1/devices
```

### gRPC

```bash
grpcurl localhost:50002 list
```

## Configuration

Environment variables:

- `UDG_HTTP_PORT`: HTTP server port (default: 50001)
- `UDG_GRPC_PORT`: gRPC server port (default: 50002)
- `UDG_TOKEN`: Auth token (generated if not set)
- `UDG_MAX_CONNECTIONS`: Max device connections (default: 50)
- `UDG_LOG_LEVEL`: Log level (default: INFO)

## License

MIT