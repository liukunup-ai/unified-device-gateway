from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import asyncio


class DeviceType(Enum):
    IOS = "ios"
    ANDROID = "android"
    HARMONYOS = "harmonyos"
    SERIAL = "serial"


class DeviceStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class DeviceInfo:
    device_id: str
    device_type: DeviceType
    status: DeviceStatus
    udid: Optional[str] = None
    serial: Optional[str] = None
    ip_port: Optional[str] = None
    serial_port: Optional[str] = None
    host_id: str = ""
    tags: list = field(default_factory=list)
    groups: list = field(default_factory=list)
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

    async def reconnect(self) -> None:
        await self.disconnect()
        await self.connect()

    async def execute(self, command: str, params: dict, timeout_ms: int) -> dict:
        if not self._connected:
            return {"status": "error", "error": "DEVICE_OFFLINE", "output": None}
        try:
            async with asyncio.timeout(timeout_ms / 1000):
                method = getattr(self, command, None)
                if method and callable(method):
                    sig_params = self._get_params(method, params)
                    result = await method(**sig_params) if sig_params else await method()
                    return result
                return {"status": "error", "error": "UNKNOWN_COMMAND", "output": None}
        except asyncio.TimeoutError:
            return {"status": "error", "error": "TIMEOUT", "output": None}
        except Exception as e:
            return {"status": "error", "error": str(e), "output": None}

    def _get_params(self, method, params: dict) -> dict:
        import inspect
        sig = inspect.signature(method)
        return {k: v for k, v in params.items() if k in sig.parameters}

    async def shell(self, cmd: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def screenshot(self) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def install(self, path: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def push(self, local_path: str, remote_path: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def pull(self, remote_path: str, local_path: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def list_apps(self) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def uninstall(self, bundle_id: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def start_app(self, bundle_id: str, ability: str = "") -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def stop_app(self, bundle_id: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def get_battery(self) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def get_ip(self) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def get_current_app(self) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def tap(self, x: int, y: int) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def press(self, key: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def click_by_text(self, text: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def input_text(self, text: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def handle_alert(self, action: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def screenrecord(self, path: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def stop_screenrecord(self) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def dump_ui(self) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def assert_text(self, text: str) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}

    async def wda_command(self, params: dict) -> dict:
        return {"status": "error", "error": "NOT_SUPPORTED", "output": None}
