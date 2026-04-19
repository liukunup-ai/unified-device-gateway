import asyncio
from typing import Optional
from collections import defaultdict

from udg.device.base import BaseDevice, DeviceInfo, DeviceType
from udg.config import settings

_device_manager_instance: Optional["DeviceManager"] = None


def get_device_manager() -> "DeviceManager":
    global _device_manager_instance
    if _device_manager_instance is None:
        _device_manager_instance = DeviceManager()
    return _device_manager_instance


class DeviceManager:
    def __init__(self):
        self._devices: dict[str, BaseDevice] = {}
        self._devices_lock = asyncio.Lock()
        self._connection_counts: dict[DeviceType, int] = defaultdict(int)
        self._connection_lock = asyncio.Lock()
    
    async def register_device(self, device: BaseDevice) -> None:
        async with self._devices_lock:
            self._devices[device.info.device_id] = device
    
    async def unregister_device(self, device_id: str) -> Optional[BaseDevice]:
        async with self._devices_lock:
            return self._devices.pop(device_id, None)
    
    async def get_device(self, device_id: str) -> Optional[BaseDevice]:
        return self._devices.get(device_id)
    
    async def list_devices(self) -> list[DeviceInfo]:
        async with self._devices_lock:
            return [d.info for d in self._devices.values()]
    
    async def get_devices_by_type(self, device_type: DeviceType) -> list[BaseDevice]:
        async with self._devices_lock:
            return [d for d in self._devices.values() if d.info.device_type == device_type]
    
    async def can_connect(self, device_type: DeviceType) -> bool:
        async with self._connection_lock:
            return self._connection_counts[device_type] < settings.max_connections
    
    async def increment_connections(self, device_type: DeviceType) -> None:
        async with self._connection_lock:
            self._connection_counts[device_type] += 1
    
    async def decrement_connections(self, device_type: DeviceType) -> None:
        async with self._connection_lock:
            self._connection_counts[device_type] -= 1