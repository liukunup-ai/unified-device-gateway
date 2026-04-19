import asyncio
import serial
from typing import Optional
from udg.device.base import BaseDevice, DeviceInfo


class SerialDevice(BaseDevice):
    def __init__(self, info: DeviceInfo):
        super().__init__(info)
        self._serial: Optional[serial.Serial] = None
        self._baudrate = info.metadata.get("baudrate", 115200)
        self._parity = info.metadata.get("parity", "N")
        self._databits = info.metadata.get("databits", 8)
        self._stopbits = info.metadata.get("stopbits", 1)

    async def connect(self) -> None:
        if not self.info.serial_port:
            raise ValueError("serial_port is required for SerialDevice")

        self._serial = serial.Serial(
            port=self.info.serial_port,
            baudrate=self._baudrate,
            parity=self._parity,
            bytesize=self._databits,
            stopbits=self._stopbits,
            timeout=1.0
        )
        self._connected = True

    async def disconnect(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._connected = False
        self._serial = None

    async def execute(self, command: str, params: dict, timeout_ms: int) -> dict:
        if not self._connected:
            return {"status": "error", "error": "DEVICE_OFFLINE", "output": None}

        try:
            async with asyncio.timeout(timeout_ms / 1000):
                if command == "write":
                    return await self._write(params)
                elif command == "config":
                    return await self._config(params)
                else:
                    return {"status": "error", "error": "UNKNOWN_COMMAND", "output": None}
        except asyncio.TimeoutError:
            return {"status": "error", "error": "TIMEOUT", "output": None}
        except Exception as e:
            return {"status": "error", "error": str(e), "output": None}

    async def _write(self, params: dict) -> dict:
        data = params.get("data", "")
        read_response = params.get("read", False)
        read_timeout = params.get("read_timeout", 1.0)

        if isinstance(data, str):
            data_bytes = data.encode("utf-8")
        else:
            data_bytes = data

        def _sync_write():
            if not self._serial:
                raise RuntimeError("Serial not connected")
            self._serial.write(data_bytes)
            if read_response:
                return self._serial.read_until(b"\n") or b""
            return b"Wrote"

        result = await asyncio.to_thread(_sync_write)
        if read_response:
            return {"status": "success", "output": result.decode("utf-8", errors="replace"), "error": None}
        return {"status": "success", "output": f"Wrote {len(data_bytes)} bytes", "error": None}

    async def _config(self, params: dict) -> dict:
        if "baudrate" in params:
            self._baudrate = int(params["baudrate"])
        if "parity" in params:
            self._parity = params["parity"]
        if "databits" in params:
            self._databits = int(params["databits"])
        if "stopbits" in params:
            self._stopbits = int(params["stopbits"])

        await self.disconnect()
        await self.connect()

        return {"status": "success", "output": "Configuration updated", "error": None}