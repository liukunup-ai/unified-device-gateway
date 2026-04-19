import asyncio
import base64
import json
import os
import re
from datetime import datetime, timezone
import serial
from typing import Optional
from udg.device.base import BaseDevice, DeviceInfo


def _sanitize_device_id(device_id: str) -> str:
    """Sanitize device_id to prevent path traversal attacks."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', device_id)


def _get_log_file_path(device_id: str) -> str:
    log_dir = "/tmp/udg-serial-logs"
    os.makedirs(log_dir, exist_ok=True)
    safe_device_id = _sanitize_device_id(device_id)
    return os.path.join(log_dir, f"{safe_device_id}.jsonl")


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

    def _log_transaction(self, direction: str, data: str, size: int) -> None:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "device_id": self.info.device_id,
            "port": self.info.serial_port or "",
            "direction": direction,
            "data": data,
            "size": size,
        }
        log_path = _get_log_file_path(self.info.device_id)
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def execute(self, command: str, params: dict, timeout_ms: int) -> dict:
        if not self._connected:
            return {"status": "error", "error": "DEVICE_OFFLINE", "output": None}

        try:
            async with asyncio.timeout(timeout_ms / 1000):
                if command == "write":
                    return await self._write(params)
                elif command == "read":
                    return await self._read(params)
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
        encoding = params.get("encoding", "utf-8")

        if encoding == "base64":
            data_bytes = base64.b64decode(data)
        elif isinstance(data, str):
            data_bytes = data.encode("utf-8")
        else:
            data_bytes = data

        def _sync_write():
            if not self._serial:
                raise RuntimeError("Serial not connected")
            self._serial.write(data_bytes)
            if read_response:
                resp = self._serial.read_until(b"\n") or b""
                return resp.decode("utf-8", errors="replace")
            return f"Wrote {len(data_bytes)} bytes"

        result = await asyncio.to_thread(_sync_write)

        data_to_log = data_bytes.decode("utf-8", errors="replace") if encoding == "base64" else data
        await asyncio.to_thread(self._log_transaction, "write", data_to_log, len(data_bytes))

        if read_response:
            return {"status": "success", "output": result, "error": None}
        return {"status": "success", "output": result, "error": None}

    async def _read(self, params: dict) -> dict:
        size = params.get("size", 1)

        def _sync_read():
            if not self._serial:
                raise RuntimeError("Serial not connected")
            return self._serial.read(size)

        result = await asyncio.to_thread(_sync_read)
        result_str = result.decode("utf-8", errors="replace")

        self._log_transaction("read", result_str, len(result))

        return {"status": "success", "output": result_str, "error": None}

    async def _config(self, params: dict) -> dict:
        if "baudrate" in params:
            self._baudrate = int(params["baudrate"])
            self.info.metadata["baudrate"] = self._baudrate
        if "parity" in params:
            self._parity = params["parity"]
            self.info.metadata["parity"] = self._parity
        if "databits" in params:
            self._databits = int(params["databits"])
            self.info.metadata["databits"] = self._databits
        if "stopbits" in params:
            self._stopbits = int(params["stopbits"])
            self.info.metadata["stopbits"] = self._stopbits

        await self.disconnect()
        await self.connect()

        return {"status": "success", "output": "Configuration updated", "error": None}