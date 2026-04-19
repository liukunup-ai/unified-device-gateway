# Unified Device Gateway (UDG) 开发指南

## 目录

- [环境配置](#环境配置)
- [项目结构](#项目结构)
- [运行服务](#运行服务)
- [HTTP 调试](#http-调试)
- [gRPC 调试](#grpc-调试)
- [MCP 调试](#mcp-调试)
- [常见问题](#常见问题)

---

## 环境配置

### 前置要求

- Python 3.10+
- uv 包管理器

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/your-repo/unified-device-gateway.git
cd unified-device-gateway

# 使用 uv 安装
uv pip install -e .
```

### 环境变量配置

创建 `.env` 文件或设置环境变量：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `UDG_HTTP_PORT` | 8080 | HTTP 服务端口 |
| `UDG_GRPC_PORT` | 50000 | gRPC 服务端口 |
| `UDG_TOKEN` | 自动生成 | 认证令牌 |
| `UDG_MAX_CONNECTIONS` | 50 | 最大设备连接数 |
| `UDG_COMMAND_TIMEOUT_MS` | 60000 | 命令超时(毫秒) |
| `UDG_DEVICE_SCAN_INTERVAL` | 60 | 设备扫描间隔(秒) |
| `UDG_REDIS_URL` | None | Redis URL (可选) |
| `UDG_LOG_LEVEL` | INFO | 日志级别 |
| `UDG_LOG_PATH` | `~/.udg/logs/udg.log` | 日志文件路径 |
| `UDG_TOKEN_FILE` | `~/.udg/token` | 令牌存储文件 |

### 使用 uv 运行

```bash
# 安装依赖并运行
uv run udg start

# 查看当前 token
udg token show

# 轮换 token
udg token rotate
```

---

## 项目结构

```
udg/
├── __main__.py          # 入口点
├── __init__.py
├── cli.py               # CLI 命令定义
├── config.py            # 配置管理 (Pydantic Settings)
├── auth/
│   └── token.py         # Token 生成和验证
├── api/
│   ├── schemas.py       # Pydantic 数据模型
│   ├── device.proto     # gRPC 服务定义
│   ├── device_pb2.py    # 生成的 protobuf 代码
│   └── device_pb2_grpc.py  # 生成的 gRPC 代码
├── device/
│   ├── base.py          # 设备基类
│   ├── manager.py       # 设备管理器
│   ├── android.py       # Android 设备实现
│   ├── ios.py           # iOS 设备实现
│   └── serial.py        # 串口设备实现
├── executor/
│   └── runner.py        # 命令执行器
├── scanner/
│   └── serial_scanner.py # 串口扫描器
├── server/
│   ├── app.py           # 主服务器 (uvicorn 启动)
│   ├── http.py          # HTTP/FastAPI 服务
│   ├── grpc.py          # gRPC 服务
│   └── mcp.py           # MCP (Model Context Protocol) 服务
├── storage/
│   └── __init__.py
└── utils/
    ├── logging.py       # structlog JSON 日志配置
    └── metrics.py       # Prometheus 指标
```

---

## 运行服务

### 启动服务器

```bash
# 方式一: 使用 CLI
udg start

# 方式二: 使用模块直接运行
python -m udg

# 方式三: 使用 uvicorn (开发模式)
uvicorn udg.server.app:app --host 0.0.0.0 --port 8080 --reload
```

### 启动时输出

```
Starting HTTP server on port 8080...
Starting gRPC server on port 50051...
```

注意：gRPC 端口在 `udg/server/grpc.py` 中硬编码为 `50051`。

---

## HTTP 调试

### 服务端点

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/routes` | GET | 查看所有可用路由 | 否 |
| `/health` | GET | 健康检查 | 否 |
| `/health/ready` | GET | 就绪检查 | 否 |
| `/health/live` | GET | 存活检查 | 否 |
| `/metrics` | GET | Prometheus 指标 | 否 |
| `/api/v1/devices` | GET | 列出所有设备 | Bearer Token |
| `/api/v1/execute` | POST | 执行命令 | Bearer Token |
| `/mcp` | SSE | MCP 协议端点 | 否 |

### 查看所有接口

启动服务后，访问 `GET /routes` 查看所有可用端点：

```bash
curl http://localhost:8080/routes
```

响应示例：

```json
{
  "routes": [
    {"path": "/routes", "method": "GET", "description": "返回所有可用路由"},
    {"path": "/health", "method": "GET", "description": "健康检查"},
    {"path": "/health/ready", "method": "GET", "description": "就绪检查"},
    {"path": "/health/live", "method": "GET", "description": "存活检查"},
    {"path": "/metrics", "method": "GET", "description": "Prometheus 指标"},
    {"path": "/api/v1/devices", "method": "GET", "description": "列出所有设备", "auth": true},
    {"path": "/api/v1/execute", "method": "POST", "description": "批量执行命令", "auth": true},
    {"path": "/mcp", "method": "SSE", "description": "MCP 协议端点 (Server-Sent Events)"}
  ],
  "grpc_port": 50051
}
```

gRPC 方法列表：

```bash
grpcurl -plaintext localhost:50051 list
```

### 获取 Token

```bash
# 查看当前 token
udg token show

# Token 文件位置
cat ~/.udg/token
```

### cURL 调试示例

```bash
# 健康检查
curl http://localhost:8080/health

# 获取设备列表 (需要替换 YOUR_TOKEN)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8080/api/v1/devices

# 执行命令 (需要替换 YOUR_TOKEN)
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "commands": [
         {
           "id": "cmd-001",
           "device_id": "android-001",
           "command": "shell",
           "params": {"cmd": "ls -la"},
           "timeout_ms": 30000
         }
       ]
     }' \
     http://localhost:8080/api/v1/execute
```

### Python HTTP 客户端示例

```python
import httpx
import asyncio

TOKEN = "your-token-here"
BASE_URL = "http://localhost:8080"

async def debug_http():
    async with httpx.AsyncClient() as client:
        # 健康检查
        resp = await client.get(f"{BASE_URL}/health")
        print(f"Health: {resp.json()}")

        # 获取设备列表
        resp = await client.get(
            f"{BASE_URL}/api/v1/devices",
            headers={"Authorization": f"Bearer {TOKEN}"}
        )
        print(f"Devices: {resp.json()}")

        # 执行命令
        resp = await client.post(
            f"{BASE_URL}/api/v1/execute",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={
                "commands": [{
                    "id": "test-001",
                    "device_id": "android-001",
                    "command": "shell",
                    "params": {"cmd": "echo hello"},
                    "timeout_ms": 5000
                }]
            }
        )
        print(f"Execute: {resp.json()}")

asyncio.run(debug_http())
```

### HTTP 抓包调试

```bash
# 使用 tcpdump 抓取 HTTP 流量
sudo tcpdump -i lo0 -A 'port 8080'

# 使用 mitmproxy (需要安装)
mitmproxy --listen-port 8081 --proxy-port 8080
```

---

## gRPC 调试

### gRPC 服务定义

参见 `udg/api/device.proto`:

```protobuf
service DeviceGateway {
  rpc Execute(CommandRequest) returns (CommandResponse);
  rpc ListDevices(ListDevicesRequest) returns (ListDevicesResponse);
}
```

### 安装 grpcurl

```bash
# macOS
brew install grpcurl

# Linux
curl -sSL https://github.com/fullstorydev/grpcurl/releases/download/v1.8.7/grpcurl_1.8.7_linux_x86_64.tar.gz | tar -xz
sudo mv grpcurl /usr/local/bin/

# Python
uv pip install grpcio grpcio-tools
```

### grpcurl 调试示例

```bash
# 列出所有服务
grpcurl localhost:50051 list

# 列出服务方法
grpcurl localhost:50051 list udg.DeviceGateway

# 描述方法
grpcurl localhost:50051 describe udg.DeviceGateway.Execute

# 调用 ListDevices (无认证)
grpcurl -plaintext localhost:50051 udg.DeviceGateway/ListDevices

# 调用 Execute (无认证)
grpcurl -plaintext -d '{
  "commands": [{
    "id": "grpc-test-001",
    "device_id": "android-001",
    "command": "shell",
    "params": {"cmd": "echo hello from gRPC"},
    "timeout_ms": 5000
  }]
}' localhost:50051 udg.DeviceGateway/Execute
```

### Python gRPC 客户端示例

```python
import grpc
from udg.api import device_pb2, device_pb2_grpc

def debug_grpc():
    channel = grpc.insecure_channel('localhost:50051')
    stub = device_pb2_grpc.DeviceGatewayStub(channel)

    # ListDevices
    response = stub.ListDevices(device_pb2.ListDevicesRequest())
    print(f"Devices: {response}")

    # Execute
    request = device_pb2.CommandRequest(commands=[
        device_pb2.Command(
            id="grpc-test-001",
            device_id="android-001",
            command="shell",
            params={"cmd": "echo hello"},
            timeout_ms=5000
        )
    ])
    response = stub.Execute(request)
    print(f"Execute: {response}")

debug_grpc()
```

### gRPC 抓包调试

```bash
# 使用 grpcurl 记录请求
grpcurl -v -record-Datei grpc recording.bin localhost:50051 list

# 使用 grpc_debug 工具
uv pip install grpc-debug

# 或使用 BloomRPC (GUI 工具)
# https://github.com/bloomberg/bloomrpc
```

### 启用 gRPC 日志

```bash
# 设置 gRPC 日志环境变量
GRPC_VERBOSITY=debug GRPC_TRACE=all python -m udg
```

---

## MCP 调试

### MCP (Model Context Protocol) 概述

MCP 通过 SSE (Server-Sent Events) 在 HTTP 端口 8080 上提供服务。

### MCP 端点

- SSE 传输: `http://localhost:8080/mcp`

### MCP Inspector 调试

```bash
# 安装 MCP Inspector
npx @modelcontextprotocol/inspector

# 连接到 UDG
npx @modelcontextprotocol/inspector http://localhost:8080/mcp
```

### Python MCP 客户端示例

```python
from mcp.client.fastmcp import FastMCP
import asyncio

async def debug_mcp():
    client = FastMCP("udg-debug-client")

    # 调用 list_devices 工具
    result = await client.call_tool("list_devices")
    print(f"list_devices: {result}")

    # 调用 get_device_info 工具
    result = await client.call_tool("get_device_info", {"device_id": "android-001"})
    print(f"get_device_info: {result}")

    # 调用 execute_command 工具
    result = await client.call_tool("execute_command", {
        "device_id": "android-001",
        "command": "echo hello from MCP",
        "timeout": 10
    })
    print(f"execute_command: {result}")

    # 访问 device 资源
    resource = await client.read_resource("device://list")
    print(f"device://list: {resource}")

asyncio.run(debug_mcp())
```

### 使用 Claude Desktop 连接

在 `~/.claude/desktop-config.json` 中添加：

```json
{
  "mcpServers": {
    "udg": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### MCP 工具列表

| 工具名 | 参数 | 说明 |
|--------|------|------|
| `list_devices` | 无 | 列出所有设备 |
| `get_device_info` | `device_id: str` | 获取设备详情 |
| `execute_command` | `device_id`, `command`, `timeout` | 执行 shell 命令 |
| `screenshot` | `device_id: str` | 获取设备截图 |

### MCP 资源列表

| 资源 URI | 说明 |
|----------|------|
| `device://list` | 设备列表 JSON |
| `device://{device_id}` | 单个设备详情 JSON |

### SSE 手动调试

```bash
# 使用 curl 连接 SSE 端点
curl -N -H "Accept: text/event-stream" http://localhost:8080/mcp

# 使用 EventSource 浏览器调试
# 在浏览器控制台:
# const es = new EventSource('http://localhost:8080/mcp');
# es.onmessage = (e) => console.log('MCP event:', e.data);
```

---

## 常见问题

### 1. 端口占用

```bash
# 查找占用端口的进程
lsof -i :8080
lsof -i :50051

# 或
netstat -tlnp | grep 8080

# 杀死进程
kill -9 <PID>
```

### 2. Token 无效

```bash
# 重新生成 token
udg token rotate

# 检查 token 文件权限
ls -la ~/.udg/token
chmod 600 ~/.udg/token
```

### 3. gRPC 端口

gRPC 端口配置为 `50051`，确保环境变量或配置与代码一致。

### 4. MCP 连接失败

- 确认 MCP 端点 URL 正确: `http://localhost:8080/mcp`
- 检查服务器日志查看 MCP 初始化错误
- 确认防火墙允许 8080 端口

### 5. 设备连接问题

```bash
# Android (ADB)
adb devices
adb connect <device-ip>:5555

# iOS (需要 tidevice 或 WDA)
# 确保设备已信任计算机

# 串口设备
ls /dev/tty.*
```

### 6. 查看详细日志

```bash
# 设置日志级别为 DEBUG
UDG_LOG_LEVEL=DEBUG udg start

# 查看日志文件
tail -f ~/.udg/logs/udg.log | jq
```

### 7. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_device_manager.py -v

# 查看测试覆盖率
pytest --cov=udg --cov-report=html
```

---

## 开发调试技巧

### 使用 PyCharm/VSCode 调试

**launch.json (VSCode):**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "UDG Server",
      "type": "debugpy",
      "request": "launch",
      "module": "udg",
      "args": ["start"],
      "cwd": "${workspaceFolder}",
      "env": {
        "UDG_LOG_LEVEL": "DEBUG"
      }
    }
  ]
}
```

### IPython 交互式调试

```python
import IPython
from udg.server.app import app
from udg.config import settings

# 在 IPython 中测试
IPython.embed()
```

### 日志格式

日志输出为 JSON 格式，便于解析：

```json
{
  "event": "request",
  "timestamp": "2024-01-15T10:30:00.000000Z",
  "level": "info",
  "logger": "udg.server.http",
  "method": "GET",
  "path": "/health",
  "status": 200
}
```
