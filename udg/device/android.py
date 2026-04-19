import asyncio
import subprocess
import base64
from typing import Optional
from udg.device.base import BaseDevice, DeviceInfo


class AndroidDevice(BaseDevice):
    def __init__(self, info: DeviceInfo):
        super().__init__(info)

    async def _get_adb_args(self) -> list:
        if self.info.serial:
            return ["-s", self.info.serial]
        elif self.info.ip_port:
            return ["-s", self.info.ip_port]
        return []

    async def connect(self) -> None:
        args = await self._get_adb_args()
        if args:
            result = await asyncio.create_subprocess_exec(
                "adb", *args, "get-state",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            if result.returncode != 0:
                raise RuntimeError(f"adb connect failed: {stderr.decode()}")
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def execute(self, command: str, params: dict, timeout_ms: int) -> dict:
        if not self._connected:
            return {"status": "error", "error": "DEVICE_OFFLINE", "output": None}

        try:
            async with asyncio.timeout(timeout_ms / 1000):
                if command == "shell":
                    return await self._shell(params.get("cmd", ""))
                elif command == "uiautomator":
                    return await self._uiautomator(params)
                elif command == "screenshot":
                    return await self._screenshot()
                elif command == "install":
                    return await self._install(params.get("path", ""))
                else:
                    return {"status": "error", "error": "UNKNOWN_COMMAND", "output": None}
        except asyncio.TimeoutError:
            return {"status": "error", "error": "TIMEOUT", "output": None}
        except Exception as e:
            return {"status": "error", "error": str(e), "output": None}

    async def _shell(self, cmd: str) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "shell", cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _uiautomator(self, params: dict) -> dict:
        method = params.get("method", "dump")
        args = await self._get_adb_args()

        if method == "dump":
            await asyncio.create_subprocess_exec(
                "adb", *args, "shell", "uiautomator", "dump", "/sdcard/dump.xml",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            result = await asyncio.create_subprocess_exec(
                "adb", *args, "pull", "/sdcard/dump.xml",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            if result.returncode != 0:
                return {"status": "error", "error": stderr.decode(), "output": None}
            try:
                with open("dump.xml") as f:
                    content = f.read()
                return {"status": "success", "output": content, "error": None}
            except FileNotFoundError:
                return {"status": "error", "error": "dump failed", "output": None}
        else:
            cmd = params.get("cmd", f"uiautomator {method}")
            result = await asyncio.create_subprocess_exec(
                "adb", *args, "shell", cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            if result.returncode != 0:
                return {"status": "error", "error": stderr.decode(), "output": None}
            return {"status": "success", "output": stdout.decode(), "error": None}

    async def _screenshot(self) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "exec-out", "screencap", "-p",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        b64 = base64.b64encode(stdout).decode()
        return {"status": "success", "output": f"data:image/png;base64,{b64}", "error": None}

    async def _install(self, path: str) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "install", "-r", path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}