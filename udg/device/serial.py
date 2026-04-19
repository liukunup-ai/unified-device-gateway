import asyncio
from typing import Optional
from udg.device.base import BaseDevice, DeviceInfo, DeviceType

class SerialDevice(BaseDevice):
    def __init__(self, info: DeviceInfo):
        super().__init__(info)
        self._last_used = 0.0

    async def connect(self) -> None:
        await asyncio.sleep(0)
        self._connected = True

    async def disconnect(self) -> None:
        await asyncio.sleep(0)
        self._connected = False

    async def execute(self, command: str, params: dict, timeout_ms: int) -> dict:
        if not self._connected:
            return {"status": "error", "error": "DEVICE_OFFLINE", "output": None}
        return {"status": "success", "output": f"command '{command}' executed", "error": None}