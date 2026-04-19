import asyncio
import subprocess
import json
import base64
from typing import Any, Optional
from pathlib import Path
from udg.device.base import BaseDevice, DeviceInfo, DeviceStatus


class IOSDevice(BaseDevice):
    def __init__(self, info: DeviceInfo):
        super().__init__(info)
        self._tidevice_process = None
        self._wda_client = None
        self._wda_url: Optional[str] = None

    async def connect(self) -> None:
        if self.info.udid:
            cmd = ["tidevice", "-u", self.info.udid, "list"]
        else:
            cmd = ["tidevice", "list"]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            raise RuntimeError(f"tidevice failed: {stderr.decode()}")
        self._connected = True

    async def disconnect(self) -> None:
        if self._tidevice_process:
            self._tidevice_process.terminate()
            self._tidevice_process = None
        self._wda_url = None
        self._connected = False

    async def execute(self, command: str, params: dict, timeout_ms: int) -> dict:
        if not self._connected:
            return {"status": "error", "error": "DEVICE_OFFLINE", "output": None}

        try:
            async with asyncio.timeout(timeout_ms / 1000):
                if command == "shell":
                    return await self._shell(params.get("cmd", ""))
                elif command == "wda_command":
                    return await self._wda_command(params)
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
        udid_arg = ["-u", self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "tidevice", *udid_arg, "shell", cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _wda_command(self, params: dict) -> dict:
        method = params.get("method", "GET").upper()
        path = params.get("path", "/status")
        body = params.get("body")

        if not self._wda_url:
            port = 8100
            if self.info.udid:
                result = await asyncio.create_subprocess_exec(
                    "tidevice", "-u", self.info.udid, "wda", "-p", str(port),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.sleep(2)
            self._wda_url = f"http://localhost:{port}"

        url = f"{self._wda_url}{path}"
        method_lower = method.lower()

        if method_lower == "get":
            result = await asyncio.create_subprocess_exec(
                "curl", "-s", "-X", method, url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        elif method_lower == "post":
            cmd = ["curl", "-s", "-X", method, url]
            if body:
                cmd.extend(["-d", json.dumps(body), "-H", "Content-Type: application/json"])
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            return {"status": "error", "error": f"Unsupported method: {method}", "output": None}

        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _screenshot(self) -> dict:
        udid_arg = ["-u", self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "tidevice", *udid_arg, " screenshot",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        b64 = base64.b64encode(stdout).decode()
        return {"status": "success", "output": f"data:image/png;base64,{b64}", "error": None}

    async def _install(self, path: str) -> dict:
        udid_arg = ["-u", self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "tidevice", *udid_arg, "install", path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}