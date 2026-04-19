# Unified Device Gateway (udg) - Implementation Plan

## TL;DR

> **Quick Summary**: Build a Python library that acts as a unified device gateway, accepting commands via HTTP/gRPC/MCP protocols and proxying execution to connected devices (iOS via tidevice/wda/go-ios, Android via adb/uiautomator2, Serial via pyserial).
>
> **Deliverables**:
> - Python package `udg` installable via pip
> - CLI commands: `udg start`, `udg token show/rotate`, `udg device list/info/remove`
> - HTTP server on port 50001 (REST + MCP SSE)
> - gRPC server on port 50002
> - Prometheus metrics endpoint at `/metrics`
>
> **Estimated Effort**: XL (Large)
> **Parallel Execution**: YES - 5 waves
> **Critical Path**: Project scaffolding → Device abstraction → Protocol servers → Integration

---

## Context

### Original Request
Build a unified device gateway Python library using uv, with GitHub Actions CI. The service receives commands via HTTP/gRPC/MCP and executes them on connected devices (iOS, Android, Serial). Supports concurrent execution of multiple commands.

### Interview Summary

**Key Discussions**:
- Protocol: Standard MCP via HTTP/SSE, HTTP :50001, gRPC :50002
- Command format: Universal JSON format for all device types
- Concurrency: Fully parallel execution of independent commands
- Device management: Auto-discovery + manual config, keep-alive 1 hour, connection pool via env var
- Auth: Token-based, generated on start, stored in ~/.udg/token
- Error handling: Exponential backoff retry, 60s default timeout, per-command results
- Logging: structlog → JSON file → filebeats to ELK
- Monitoring: Prometheus metrics
- CLI: `udg device list` (not `udg devices list`)
- iOS: tidevice + facebook-wda + go-ios
- Android: adb commands + uiautomator2

**Research Findings**:
- Use `mcp` Python SDK for MCP protocol
- Use `uvicorn` for HTTP server
- Use `grpcio` + `grpcio-tools` for gRPC
- Use `structlog` for structured logging
- Use `prometheus-client` for metrics

### Metis Review

**Identified Gaps** (addressed):
- **Command schema**: Defined exact JSON format in schemas.py
- **Error codes**: Standardized error codes (DEVICE_NOT_FOUND, TIMEOUT, etc.)
- **Graceful shutdown**: SIGTERM handler with configurable drain period
- **Binary data**: Base64 encoding for screenshots in JSON responses
- **Redis fallback**: In-memory storage when Redis unavailable

**Guardrails Applied**:
- No WebSocket, no database, no web UI, no command queuing
- Single server instance (no clustering)
- Token in plaintext (acceptable for internal tool)

---

## Work Objectives

### Core Objective
Build a production-ready Python package `udg` that provides a unified interface for controlling iOS, Android, and Serial devices via HTTP, gRPC, and MCP protocols.

### Concrete Deliverables
- `pyproject.toml` with all dependencies
- CLI entry point `udg` with commands: start, token, device, log, version
- HTTP server (FastAPI/uvicorn) on port 50001
- gRPC server on port 50002
- MCP server via HTTP/SSE on `/mcp`
- Device abstraction layer with iOS, Android, Serial implementations
- Token authentication
- Prometheus metrics at `/metrics`
- Structured JSON logging to file

### Definition of Done
- [ ] `udg --version` returns version
- [ ] `udg start` starts all servers
- [ ] `curl http://localhost:50001/api/v1/devices` returns device list
- [ ] `grpcurl localhost:50002 list` shows DeviceGateway service
- [ ] MCP client can connect via SSE and list tools
- [ ] Commands execute on real devices

### Must Have
- Token auth on all endpoints
- Concurrent command execution
- Graceful shutdown (SIGTERM handling)
- Prometheus metrics
- Structured logging

### Must NOT Have (Guardrails)
- No WebSocket support
- No database (in-memory only, unless Redis configured)
- No web UI/dashboard
- No command queuing or scheduling
- No device groups/tags (v1)
- No file transfer beyond command results

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (new project)
- **Automated tests**: YES (tests after implementation)
- **Framework**: pytest + pytest-asyncio
- **Agent-Executed QA**: YES (manual verification of servers)

### QA Policy
Every task includes agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/`.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation - scaffolding + config + base):
├── Task 1: Project scaffolding (pyproject.toml, __init__.py, __main__.py)
├── Task 2: Configuration management (settings, env vars, config file)
├── Task 3: Logging setup (structlog → JSON file)
├── Task 4: Token auth (generate, validate, rotate)
├── Task 5: Base device abstraction (BaseDevice, DeviceInfo, DeviceType)
└── Task 6: Storage abstraction (MemoryStorage, RedisStorage interface)

Wave 2 (Core - device implementations):
├── Task 7: DeviceManager (device registry, connection pool, auto-discovery)
├── Task 8: iOS device (tidevice + wda integration)
├── Task 9: Android device (adb + uiautomator2 integration)
└── Task 10: Serial device (pyserial integration)

Wave 3 (Protocol servers - MAX PARALLEL):
├── Task 11: API schemas (Pydantic models for request/response)
├── Task 12: Command executor (asyncio gather, timeout, error handling)
├── Task 13: HTTP server (FastAPI router, endpoints)
├── Task 14: gRPC server (proto definition, servicer)
├── Task 15: MCP server (mcp SDK integration, SSE transport)
└── Task 16: Prometheus metrics (middleware, endpoint)

Wave 4 (CLI + polish):
├── Task 17: CLI commands (start, token, device, log, version)
├── Task 18: Graceful shutdown handler
├── Task 19: Health check endpoint
└── Task 20: Serial scanner (auto-detect /dev/tty*)

Wave 5 (Integration + CI):
├── Task 21: GitHub Actions workflow (build wheels)
├── Task 22: Integration test script
└── Task 23: README and documentation

Wave FINAL (Verification):
├── Task F1: Plan compliance audit
├── Task F2: Code quality review
├── Task F3: Hands-on QA (start servers, test endpoints)
└── Task F4: Scope fidelity check
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | - | 2, 3, 4, 5, 6 |
| 2 | 1 | 3, 4, 5, 6 |
| 3 | 1 | 16, 17 |
| 4 | 1 | 13, 14, 15 |
| 5 | 1 | 7, 8, 9, 10 |
| 6 | 1 | 7 |
| 7 | 5, 6 | 8, 9, 10 |
| 8 | 5, 7 | 12 |
| 9 | 5, 7 | 12 |
| 10 | 5, 7 | 12 |
| 11 | 2 | 12, 13 |
| 12 | 8, 9, 10, 11 | 13, 14, 15 |
| 13 | 4, 11, 12 | F3 |
| 14 | 4, 12 | F3 |
| 15 | 4, 12 | F3 |
| 16 | 3, 13 | F3 |
| 17 | 3, 4 | F3 |
| 18 | 13, 14, 15 | F3 |
| 19 | 13 | F3 |
| 20 | 5 | 7 |
| 21 | 1 | - |
| 22 | 13, 14, 15, 16, 17, 18, 19, 20 | - |
| 23 | 22 | - |

### Agent Dispatch Summary

- **Wave 1**: 6 tasks → `quick` (scaffolding), `deep` (base classes)
- **Wave 2**: 4 tasks → `deep` (device integrations)
- **Wave 3**: 6 tasks → `deep` (protocol servers)
- **Wave 4**: 4 tasks → `quick` + `unspecified-high`
- **Wave 5**: 3 tasks → `unspecified-high` + `writing`
- **FINAL**: 4 tasks → `oracle`, `unspecified-high`, `unspecified-high`, `deep`

---

## TODOs

- [x] 1. **Project scaffolding** — `quick`

  **What to do**:
  - Create `pyproject.toml` with:
    - Package name: `udg`, version: `0.1.0`
    - Python 3.10+ requires (MCP SDK requirement)
    - Dependencies: fastapi, uvicorn, grpcio, grpcio-tools, mcp, pydantic, pydantic-settings, structlog, prometheus-client, redis, pyserial, pytest, pytest-asyncio, httpx (for testing)
    - Scripts: `udg = "udg.__main__:main"`
  - Create directory structure: `udg/{server,api,device,executor,auth,storage,scanner,utils}`
  - Create `udg/__init__.py` with `__version__ = "0.1.0"`
  - Create `udg/__main__.py` with CLI entry point

  **Must NOT do**:
  - No actual implementation code yet
  - No tests yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure scaffolding, file creation, no complex logic
  - **Skills**: []
    - No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2-6)
  - **Blocks**: Tasks 2, 3, 4, 5, 6
  - **Blocked By**: None

  **References**:
  - `pyproject.toml` example: standard Python packaging

  **Acceptance Criteria**:
  - [ ] `pyproject.toml` exists with all dependencies
  - [ ] `udg/__init__.py` exports `__version__`
  - [ ] `python -m udg --version` works

  **QA Scenarios**:

  \`\`\`
  Scenario: Package installs correctly
    Tool: Bash
    Preconditions: uv installed
    Steps:
      1. Run `uv pip install -e .` in project root
      2. Run `udg --version`
    Expected Result: Outputs "0.1.0"
    Evidence: .sisyphus/evidence/task-1-version.{ext}

  Scenario: CLI entry point works
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -m udg --help`
    Expected Result: Shows help with commands: start, token, device, log, version
    Evidence: .sisyphus/evidence/task-1-help.{ext}
  \`\`\`

  **Commit**: YES
  - Message: `feat(scaffolding): initial project structure`
  - Files: `pyproject.toml`, `udg/__init__.py`, `udg/__main__.py`, `udg/server/`, `udg/api/`, `udg/device/`, `udg/executor/`, `udg/auth/`, `udg/storage/`, `udg/scanner/`, `udg/utils/`

- [x] 2. **Configuration management** — `quick`

  **What to do**:
  - Create `udg/config.py` with Pydantic Settings:
    - `UDG_HTTP_PORT`: int = 50001
    - `UDG_GRPC_PORT`: int = 50002
    - `UDG_TOKEN`: Optional[str] = None (generated if not set)
    - `UDG_MAX_CONNECTIONS`: int = 50
    - `UDG_COMMAND_TIMEOUT_MS`: int = 60000
    - `UDG_DEVICE_SCAN_INTERVAL`: int = 60
    - `UDG_REDIS_URL`: Optional[str] = None
    - `UDG_LOG_LEVEL`: str = "INFO"
    - `UDG_LOG_PATH`: Path = ~/.udg/logs/udg.log
    - `UDG_TOKEN_FILE`: Path = ~/.udg/token
  - Support `~/.udg/config.toml` for additional config
  - Config hot-reload: settings changes take effect within 60s via polling

  **Must NOT do**:
  - No validation logic (only config parsing)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Config file creation, no complex logic

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5, 6)
  - **Blocks**: Task 3
  - **Blocked By**: Task 1

  **References**:
  - Pydantic Settings: `pydantic-settings` docs

  **Acceptance Criteria**:
  - [ ] `from udg.config import settings` works
  - [ ] Default values are correct
  - [ ] Env vars override defaults

  **QA Scenarios**:

  \`\`\`
  Scenario: Default configuration loads
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -c "from udg.config import settings; print(settings.http_port)"`
    Expected Result: Outputs "50001"
    Evidence: .sisyphus/evidence/task-2-defaults.{ext}

  Scenario: Environment variable override
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `UDG_HTTP_PORT=60001 python -c "from udg.config import settings; print(settings.http_port)"`
    Expected Result: Outputs "60001"
    Evidence: .sisyphus/evidence/task-2-env-override.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 1)

- [x] 3. **Logging setup** — `quick`

  **What to do**:
  - Create `udg/utils/logging.py`:
    - Configure structlog to output JSON to file
    - Add timestamps, log level, logger name
    - Output to `UDG_LOG_PATH` (default: `~/.udg/logs/udg.log`)
    - Create log directory if not exists
  - Log format: `{"timestamp": "...", "level": "INFO", "logger": "udg.server.http", "message": "..."}`
  - Export `get_logger()` function

  **Must NOT do**:
  - No ELK upload (user uses filebeats)
  - No console output by default

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple logging setup

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 16, 17
  - **Blocked By**: Task 1

  **References**:
  - structlog docs: JSON output configuration

  **Acceptance Criteria**:
  - [ ] `from udg.utils.logging import get_logger` works
  - [ ] Log file is created at configured path
  - [ ] Logs are in JSON format

  **QA Scenarios**:

  \`\`\`
  Scenario: Logger outputs JSON to file
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -c "from udg.utils.logging import get_logger; logger = get_logger(); logger.info('test', key='value')"`
      2. Check log file contents
    Expected Result: JSON line with timestamp, level, message, key=value
    Evidence: .sisyphus/evidence/task-3-json-log.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 1)

- [x] 4. **Token auth** — `deep`

  **What to do**:
  - Create `udg/auth/token.py`:
    - `generate_token()`: Generate random 32-byte hex string
    - `load_token(path: Path)`: Load from file, create if not exists
    - `save_token(token: str, path: Path)`: Save with permissions 0o600
    - `validate_token(token: str, expected: str) -> bool`: Constant-time comparison
    - `rotate_token(path: Path) -> str`: Generate new, save, return
  - Token stored at `~/.udg/token`
  - On service start: load or generate token, log token (first start only)

  **Must NOT do**:
  - No encryption (plaintext token acceptable for internal tool)
  - No token expiration

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Auth logic requires careful security considerations

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 13, 14, 15
  - **Blocked By**: Task 1

  **References**:
  - Python secrets module for token generation
  - os.chmod for file permissions

  **Acceptance Criteria**:
  - [ ] `generate_token()` returns 64-char hex string
  - [ ] Token file created with 0o600 permissions
  - [ ] `validate_token(correct, correct)` returns True
  - [ ] `validate_token(wrong, correct)` returns False

  **QA Scenarios**:

  \`\`\`
  Scenario: Token generation
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -c "from udg.auth.token import generate_token; print(len(generate_token()))"`
    Expected Result: Outputs "64"
    Evidence: .sisyphus/evidence/task-4-gen.{ext}

  Scenario: Token file permissions
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -c "from udg.auth.token import generate_token, save_token; t = generate_token(); save_token(t, path='/tmp/test_token'); import os; print(oct(os.stat('/tmp/test_token').st_mode)[-3:])"`
    Expected Result: Outputs "600"
    Evidence: .sisyphus/evidence/task-4-perms.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 1)

- [x] 5. **Base device abstraction** — `deep`

  **What to do**:
  - Create `udg/device/base.py`:
    ```python
    from abc import ABC, abstractmethod
    from dataclasses import dataclass, field
    from enum import Enum
    from typing import Any, Optional
    import asyncio

    class DeviceType(Enum):
        IOS = "ios"
        ANDROID = "android"
        SERIAL = "serial"

    class DeviceStatus(Enum):
        ONLINE = "online"
        OFFLINE = "offline"
        BUSY = "busy"
        ERROR = "error"

    @dataclass
    class DeviceInfo:
        device_id: str           # User-friendly name
        device_type: DeviceType
        status: DeviceStatus
        udid: Optional[str] = None
        serial: Optional[str] = None
        ip_port: Optional[str] = None
        serial_port: Optional[str] = None
        host_id: str = ""
        tags: list[str] = field(default_factory=list)
        groups: list[str] = field(default_factory=list)
        metadata: dict = field(default_factory=dict)

    class BaseDevice(ABC):
        def __init__(self, info: DeviceInfo):
            self.info = info
            self._lock = asyncio.Lock()
            self._connected = False

        @property
        def is_connected(self) -> bool:
            return self._connected

        @abstractmethod
        async def connect(self) -> None: ...

        @abstractmethod
        async def disconnect(self) -> None: ...

        @abstractmethod
        async def execute(self, command: str, params: dict, timeout_ms: int) -> dict: ...

        async def reconnect(self) -> None:
            await self.disconnect()
            await self.connect()
    ```

  **Must NOT do**:
  - No actual device connection code (that goes in implementations)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Abstract base class design for multiple device types

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 7, 8, 9, 10
  - **Blocked By**: Task 1

  **References**:
  - Python ABC module for abstract base classes
  - asyncio.Lock for concurrent access

  **Acceptance Criteria**:
  - [ ] `BaseDevice` is abstract (cannot instantiate)
  - [ ] `DeviceInfo` dataclass has all fields
  - [ ] `DeviceType` enum has IOS, ANDROID, SERIAL

  **QA Scenarios**:

  \`\`\`
  Scenario: BaseDevice is abstract
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -c "from udg.device.base import BaseDevice; BaseDevice()"`
    Expected Result: TypeError: Can't instantiate abstract class
    Evidence: .sisyphus/evidence/task-5-abstract.{ext}

  Scenario: DeviceInfo dataclass
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -c "from udg.device.base import DeviceInfo, DeviceType, DeviceStatus; d = DeviceInfo(device_id='test', device_type=DeviceType.IOS, status=DeviceStatus.ONLINE); print(d.device_id)"`
    Expected Result: Outputs "test"
    Evidence: .sisyphus/evidence/task-5-dataclass.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 1)

- [x] 6. **Storage abstraction** — `quick`

  **What to do**:
  - Create `udg/storage/__init__.py` with:
    ```python
    from abc import ABC, abstractmethod
    from typing import Optional

    class Storage(ABC):
        @abstractmethod
        async def get(self, key: str) -> Optional[dict]: ...

        @abstractmethod
        async def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None: ...

        @abstractmethod
        async def delete(self, key: str) -> None: ...

        @abstractmethod
        async def list_keys(self, prefix: str = "") -> list[str]: ...

    # Memory implementation (always available)
    class MemoryStorage(Storage):
        def __init__(self):
            self._data: dict[str, dict] = {}

        async def get(self, key: str) -> Optional[dict]:
            return self._data.get(key)

        async def set(self, key: str, value: dict, ttl: Optional[int] = None) -> None:
            self._data[key] = value

        async def delete(self, key: str) -> None:
            self._data.pop(key, None)

        async def list_keys(self, prefix: str = "") -> list[str]:
            return [k for k in self._data.keys() if k.startswith(prefix)]
    ```
  - Create `udg/storage/redis.py` for RedisStorage (optional, requires redis)
  - Factory: `create_storage(redis_url: Optional[str]) -> Storage`

  **Must NOT do**:
  - No actual Redis connection logic yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple interface definitions

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 7
  - **Blocked By**: Task 1

  **References**:
  - Python ABC module

  **Acceptance Criteria**:
  - [ ] `Storage` is abstract
  - [ ] `MemoryStorage` works without Redis
  - [ ] `create_storage(None)` returns MemoryStorage

  **QA Scenarios**:

  \`\`\`
  Scenario: MemoryStorage basic operations
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -c "import asyncio; from udg.storage import MemoryStorage; s = MemoryStorage(); asyncio.run(s.set('k1', {'v': 1})); print(asyncio.run(s.get('k1'))); asyncio.run(s.delete('k1')); print(asyncio.run(s.get('k1')))"`
    Expected Result: Outputs "{'v': 1}" then "None"
    Evidence: .sisyphus/evidence/task-6-memory.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 1)

- [x] 7. **DeviceManager** — `deep`

  **What to do**:
  - Create `udg/device/manager.py`:
    - `DeviceManager` class managing device registry
    - `_devices: dict[str, BaseDevice]` - device_id → device instance
    - `register_device(device: BaseDevice)` - add to registry
    - `unregister_device(device_id: str)` - remove from registry
    - `get_device(device_id: str) -> Optional[BaseDevice]`
    - `list_devices() -> list[DeviceInfo]` - all devices info
    - `get_devices_by_type(device_type: DeviceType) -> list[BaseDevice]`
    - Connection pool: track connections per device type
    - Auto-discovery: start scanner tasks on init
  - Implement connection limit: `UDG_MAX_CONNECTIONS` env var
  - Auto-scan interval: `UDG_DEVICE_SCAN_INTERVAL`

  **Must NOT do**:
  - No actual device scanning (separate Task 20)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex registry and connection pool logic

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 8, 9, 10)
  - **Blocks**: Tasks 8, 9, 10
  - **Blocked By**: Tasks 5, 6

  **References**:
  - asyncio.Lock for thread-safe registry access
  - Task 5 (BaseDevice) for device interface

  **Acceptance Criteria**:
  - [ ] `DeviceManager` can register/unregister devices
  - [ ] `list_devices()` returns all registered devices
  - [ ] Connection limit enforced

  **QA Scenarios**:

  \`\`\`
  Scenario: Device registration
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Create a mock device and register it
      2. List devices and verify it's there
      3. Unregister and verify it's gone
    Expected Result: Device appears and disappears from list
    Evidence: .sisyphus/evidence/task-7-reg.{ext}
  \`\`\`

  **Commit**: YES
  - Message: `feat(devices): add device abstraction and implementations`

- [x] 8. **iOS device implementation** — `deep`

  **What to do**:
  - Create `udg/device/ios.py`:
    - `IOSDevice(BaseDevice)` implementation
    - Use `tidevice` for device connection and basic commands
    - Use `facebook-wda` (WDAClient) for WebDriverAgent commands
    - Use `go-ios` via subprocess for additional operations
    - `connect()`: Establish tidevice connection, start WDA
    - `disconnect()`: Stop WDA, disconnect tidevice
    - `execute(command, params, timeout_ms)`:
      - If command == "shell": use tidevice shell
      - If command == "wda_command": use WDAClient
      - If command == "screenshot": use WDA screenshot
      - If command == "install": use tidevice install
    - Keep-alive: track last used time, disconnect after 1 hour idle
    - Support multiple iOS devices concurrently

  **Must NOT do**:
  - No UI automation logic (just command proxy)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex iOS integration with multiple libraries

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 5, 7

  **References**:
  - tidevice docs: https://github.com/SteamFire/tidevice
  - facebook-wda docs: https://github.com/openatx/facebook-wda
  - go-ios: https://github.com/danielpaulus/go-ios

  **Acceptance Criteria**:
  - [ ] IOSDevice inherits from BaseDevice
  - [ ] `connect()` establishes connection
  - [ ] `execute()` routes to correct library
  - [ ] Keeps connection alive for up to 1 hour

  **QA Scenarios**:

  \`\`\`
  Scenario: IOSDevice command routing
    Tool: Bash
    Preconditions: Package installed, mock/test environment
    Steps:
      1. Create IOSDevice instance
      2. Verify execute() routes wda_command to WDAClient
      3. Verify execute() routes shell to tidevice
    Expected Result: Correct routing without actual device
    Evidence: .sisyphus/evidence/task-8-routing.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 7)

- [x] 9. **Android device implementation** — `deep`

  **What to do**:
  - Create `udg/device/android.py`:
    - `AndroidDevice(BaseDevice)` implementation
    - Use `subprocess` to call `adb` commands directly
    - Use `uiautomator2` for UI automation (via `adb shell uiautomator`)
    - `connect()`: Run `adb connect <ip:port>` or verify USB connection
    - `disconnect()`: Run `adb disconnect`
    - `execute(command, params, timeout_ms)`:
      - If command == "shell": `adb shell <cmd>`
      - If command == "uiautomator": `adb shell uiautomator <params>`
      - If command == "screenshot": `adb exec-out screencap`
      - If command == "install": `adb install <apk>`
    - Keep-alive: track last used, reconnect on next command if disconnected

  **Must NOT do**:
  - No uiautomator2 server management (assume already installed on device)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Android integration via adb commands

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 5, 7

  **References**:
  - adb documentation
  - uiautomator2: https://github.com/openatx/uiautomator2

  **Acceptance Criteria**:
  - [ ] AndroidDevice inherits from BaseDevice
  - [ ] `execute()` routes to correct adb command
  - [ ] Handles both USB and network connections

  **QA Scenarios**:

  \`\`\`
  Scenario: AndroidDevice shell command
    Tool: Bash
    Preconditions: Package installed, mock adb
    Steps:
      1. Create AndroidDevice with mock info
      2. Verify shell command calls correct adb syntax
    Expected Result: `adb shell ls` executed correctly
    Evidence: .sisyphus/evidence/task-9-shell.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 7)

- [x] 10. **Serial device implementation** — `deep`

  **What to do**:
  - Create `udg/device/serial.py`:
    - `SerialDevice(BaseDevice)` implementation
    - Use `pyserial` for communication
    - `connect()`: Open serial port with configured params
    - `disconnect()`: Close serial port
    - `execute(command, params, timeout_ms)`:
      - If command == "write": `serial.write(data)`, optionally read response
      - If command == "config": Update serial params (baudrate, parity, etc.)
    - Default params: 115200, 8N1, no flow control
    - Timeout handling: use pyserial timeout parameter

  **Must NOT do**:
  - No protocol parsing (raw bytes only)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Serial communication requires careful handling

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 5, 7

  **References**:
  - pyserial docs: https://pyserial.readthedocs.io/

  **Acceptance Criteria**:
  - [ ] SerialDevice inherits from BaseDevice
  - [ ] `execute()` writes and optionally reads
  - [ ] Serial params configurable

  **QA Scenarios**:

  \`\`\`
  Scenario: SerialDevice write
    Tool: Bash
    Preconditions: Package installed, mock serial
    Steps:
      1. Create SerialDevice with test port
      2. Execute write command with data "AT\r\n"
      3. Verify data was "sent"
    Expected Result: Data logged/sent correctly
    Evidence: .sisyphus/evidence/task-10-write.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 7)

- [x] 11. **API schemas** — `deep`

  **What to do**:
  - Create `udg/api/schemas.py`:
    ```python
    from pydantic import BaseModel, Field
    from typing import Optional, Any
    from datetime import datetime

    # Request schemas
    class Command(BaseModel):
        id: str
        device_id: str
        command: str
        params: dict[str, Any] = Field(default_factory=dict)
        timeout_ms: int = 60000

    class ExecuteRequest(BaseModel):
        commands: list[Command]

    # Response schemas
    class CommandResult(BaseModel):
        id: str
        device_id: str
        command: str
        status: str  # "success" | "error" | "timeout"
        output: Optional[str] = None
        error: Optional[str] = None
        error_code: Optional[str] = None
        execution_time_ms: int
        timestamp: datetime

    class ExecuteResponse(BaseModel):
        results: list[CommandResult]

    # Device schemas
    class DeviceResponse(BaseModel):
        device_id: str
        device_type: str
        status: str
        # ... other DeviceInfo fields

    class DeviceListResponse(BaseModel):
        devices: list[DeviceResponse]

    # Error schemas
    class ErrorResponse(BaseModel):
        error: str
        code: str
        details: Optional[dict] = None
    ```

  **Must NOT do**:
  - No validation for device-specific commands (just store params)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Pydantic model design for API contracts

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 12-16)
  - **Blocks**: Tasks 12, 13
  - **Blocked By**: Task 2

  **References**:
  - Pydantic v2 docs

  **Acceptance Criteria**:
  - [ ] All schemas importable
  - [ ] `ExecuteRequest` validates command list
  - [ ] `CommandResult` has all required fields

  **QA Scenarios**:

  \`\`\`
  Scenario: Schema validation
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -c "from udg.api.schemas import ExecuteRequest, Command; req = ExecuteRequest(commands=[Command(id='1', device_id='d1', command='shell', params={'cmd': 'ls'})]); print(len(req.commands))"`
    Expected Result: Outputs "1"
    Evidence: .sisyphus/evidence/task-11-validate.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 13)

- [x] 12. **Command executor** — `deep`

  **What to do**:
  - Create `udg/executor/runner.py`:
    - `CommandExecutor` class:
      - Takes `DeviceManager` and `Storage`
      - `async def execute_batch(commands: list[Command]) -> list[CommandResult]`:
        - Use `asyncio.gather(*[execute_one(cmd) for cmd in commands])` for parallelism
        - Each `execute_one()`:
          1. Get device from DeviceManager
          2. If not found, return error result (DEVICE_NOT_FOUND)
          3. Call `device.execute(command, params, timeout_ms)`
          4. Wrap in try/except, return error result on exception
        4. Return all results in original command order
    - Error codes:
      - `DEVICE_NOT_FOUND`: Device not registered
      - `DEVICE_OFFLINE`: Device not connected
      - `DEVICE_BUSY`: Device currently executing another command
      - `TIMEOUT`: Command exceeded timeout
      - `COMMAND_FAILED`: Device rejected command
      - `CONNECTION_ERROR`: Failed to connect to device

  **Must NOT do**:
  - No command queuing (fire-and-forget)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Core execution logic with concurrency control

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: Tasks 13, 14, 15
  - **Blocked By**: Tasks 8, 9, 10, 11

  **References**:
  - asyncio.gather for concurrent execution
  - asyncio.wait_for for timeout

  **Acceptance Criteria**:
  - [ ] `execute_batch()` runs commands in parallel
  - [ ] Results returned in original order
  - [ ] Errors captured and returned with codes

  **QA Scenarios**:

  \`\`\`
  Scenario: Parallel execution
    Tool: Bash
    Preconditions: Package installed, mock devices
    Steps:
      1. Create 3 mock commands
      2. Execute batch and measure time
      3. Verify time is ~1s (not 3s) for 3 parallel 1s commands
    Expected Result: Parallel execution confirmed
    Evidence: .sisyphus/evidence/task-12-parallel.{ext}

  Scenario: Error handling
    Tool: Bash
    Preconditions: Package installed, mock device
    Steps:
      1. Send command to non-existent device
      2. Verify error result with DEVICE_NOT_FOUND code
    Expected Result: Error returned, not raised
    Evidence: .sisyphus/evidence/task-12-error.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 13)

- [x] 13. **HTTP server** — `deep`
- [x] 14. **gRPC server** — `deep`
- [x] 15. **MCP server** — `deep`
- [x] 16. **Prometheus metrics** — `quick`

  **What to do**:
  - Create `udg/utils/metrics.py`:
    ```python
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

    # HTTP metrics
    http_requests_total = Counter(
        'udg_http_requests_total',
        'Total HTTP requests',
        ['method', 'path', 'status']
    )
    http_request_duration_seconds = Histogram(
        'udg_http_request_duration_seconds',
        'HTTP request duration',
        ['method', 'path']
    )

    # Command metrics
    command_executions_total = Counter(
        'udg_command_executions_total',
        'Total command executions',
        ['device_type', 'command', 'status']
    )
    command_duration_seconds = Histogram(
        'udg_command_duration_seconds',
        'Command execution duration',
        ['device_type', 'command']
    )

    # Device metrics
    devices_connected = Gauge(
        'udg_devices_connected',
        'Number of connected devices',
        ['device_type']
    )
    commands_active = Gauge(
        'udg_commands_active',
        'Number of active commands'
    )

    # Auth metrics
    token_rotations_total = Counter(
        'udg_token_rotations_total',
        'Total token rotations'
    )
    ```
  - Add metrics middleware to HTTP server
  - Instrument CommandExecutor
  - Add `/metrics` endpoint returning Prometheus format

  **Must NOT do**:
  - No custom metrics beyond listed

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Metrics setup is straightforward

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: F3
  - **Blocked By**: Tasks 3, 13

  **References**:
  - prometheus_client docs

  **Acceptance Criteria**:
  - [ ] `/metrics` returns Prometheus format
  - [ ] HTTP requests increment counter
  - [ ] Command executions tracked

  **QA Scenarios**:

  \`\`\`
  Scenario: Metrics endpoint
    Tool: Bash
    Preconditions: Server running
    Steps:
      1. curl http://localhost:50001/metrics
    Expected Result: Prometheus text format with udg_ prefixed metrics
    Evidence: .sisyphus/evidence/task-16-metrics.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 15)

- [x] 17. **CLI commands** — `unspecified-high`
- [x] 18. **Graceful shutdown handler** — `quick`
- [x] 19. **Health check endpoint** — `quick`
- [x] 20. **Serial scanner** — `quick`

  **What to do**:
  - Create `udg/scanner/serial_scanner.py`:
    - `scan_serial_ports()`:
      - Linux: Scan `/dev/ttyUSB*`, `/dev/ttyACM*`, `/dev/ttyS*`
      - macOS: Scan `/dev/cu.*`, `/dev/tty.*`
      - Windows: Scan COM ports via `serial.tools.list_ports`
    - Return list of discovered ports
    - Configurable via `discovery.serial_patterns` in config
  - Create `udg/scanner/auto_scan.py`:
    - `AutoScanner` class:
      - Start on DeviceManager init
      - Run scan every `UDG_DEVICE_SCAN_INTERVAL` seconds
      - Register new devices automatically
      - Update device status on disconnect

  **Must NOT do**:
  - No manual device addition (that goes in config)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: File system scanning

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 7
  - **Blocked By**: Task 5

  **References**:
  - pyserial list_ports

  **Acceptance Criteria**:
  - [ ] `scan_serial_ports()` finds available ports
  - [ ] AutoScanner runs periodically

  **QA Scenarios**:

  \`\`\`
  Scenario: Serial port scan
    Tool: Bash
    Preconditions: Package installed
    Steps:
      1. Run `python -c "from udg.scanner.serial_scanner import scan_serial_ports; print(scan_serial_ports())"`
    Expected Result: List of available serial ports (may be empty)
    Evidence: .sisyphus/evidence/task-20-scan.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 15)

- [x] 21. **GitHub Actions workflow** — `unspecified-high`
- [x] 22. **Integration test script** — `unspecified-high`
- [x] 23. **README and documentation** — `writing`

  **What to do**:
  - Create `README.md`:
    - Project description
    - Installation (`uv pip install udg` or `pip install udg`)
    - Quick start guide
    - CLI commands reference
    - API documentation (HTTP, gRPC, MCP)
    - Configuration reference (env vars, config file)
    - Device support matrix
    - Prometheus metrics reference
  - Create `CHANGELOG.md` (empty v0.1.0 section)

  **Must NOT do**:
  - No API documentation for internal classes

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Documentation

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5
  - **Blocks**: None
  - **Blocked By**: Task 22

  **References**:
  - Keep a Changelog format

  **Acceptance Criteria**:
  - [ ] README is readable and complete
  - [ ] Installation instructions work

  **QA Scenarios**:

  \`\`\`
  Scenario: README quality
    Tool: Bash
    Preconditions: README exists
    Steps:
      1. Check README has all sections
      2. Verify code blocks are valid
    Expected Result: README has all required sections
    Evidence: .sisyphus/evidence/task-23-readme.{ext}
  \`\`\`

  **Commit**: NO (grouped with Task 21)

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist.

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m py_compile` on all .py files. Check for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code. Check AI slop: excessive comments, over-abstraction.

- [x] F3. **Hands-on QA** — `unspecified-high`
  Start from clean state. Execute EVERY QA scenario from EVERY task. Test cross-task integration. Save to `.sisyphus/evidence/final-qa/`.

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built, nothing beyond spec was built. Detect cross-task contamination.

---

## Commit Strategy

- **Wave 1**: `feat(scaffolding): initial project structure`
- **Wave 2**: `feat(devices): add device abstraction and implementations`
- **Wave 3**: `feat(protocols): add HTTP, gRPC, MCP servers`
- **Wave 4**: `feat(cli): add CLI commands and graceful shutdown`
- **Wave 5**: `ci(github): add release workflow and tests`

---

## Success Criteria

### Verification Commands
```bash
udg --version  # Expected: 0.1.0
udg start &   # Starts servers on 50001, 50002
curl http://localhost:50001/health  # Expected: {"status": "ok"}
curl http://localhost:50001/metrics # Expected: Prometheus format
curl http://localhost:50001/api/v1/device list # Expected: {"devices": []}
grpcurl localhost:50002 list  # Expected: DeviceGateway
```

### Final Checklist
- [ ] All Must Have items implemented
- [ ] All Must NOT Have items absent
- [ ] All tests pass
- [ ] Servers start and respond correctly
