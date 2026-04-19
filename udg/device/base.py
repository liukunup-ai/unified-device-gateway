from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union
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

    @abstractmethod
    async def execute(self, command: str, params: dict, timeout_ms: int) -> dict: ...

    async def reconnect(self) -> None:
        await self.disconnect()
        await self.connect()