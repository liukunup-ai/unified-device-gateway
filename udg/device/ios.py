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
                elif command == "push":
                    return await self._push(params.get("local_path", ""), params.get("remote_path", ""))
                elif command == "pull":
                    return await self._pull(params.get("remote_path", ""), params.get("local_path", ""))
                elif command == "list_apps":
                    return await self._list_apps()
                elif command == "uninstall":
                    return await self._uninstall(params.get("bundle_id", ""))
                elif command == "start_app":
                    return await self._start_app(params.get("bundle_id", ""))
                elif command == "stop_app":
                    return await self._stop_app(params.get("bundle_id", ""))
                elif command == "get_battery":
                    return await self._get_battery()
                elif command == "get_current_app":
                    return await self._get_current_app()
                elif command == "tap":
                    return await self._tap(params.get("x", 0), params.get("y", 0))
                elif command == "swipe":
                    return await self._swipe(params.get("x1", 0), params.get("y1", 0), params.get("x2", 0), params.get("y2", 0), params.get("duration", 500))
                elif command == "screenrecord":
                    return await self._screenrecord(params.get("local_path", "/tmp/screen.mp4"))
                elif command == "stop_screenrecord":
                    return await self._stop_screenrecord()
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

    async def _push(self, local_path: str, remote_path: str) -> dict:
        udid_arg = ["-u", self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "push", local_path, remote_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _pull(self, remote_path: str, local_path: str) -> dict:
        udid_arg = ["-u", self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "pull", remote_path, local_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _list_apps(self) -> dict:
        result = await self._wda_command({"method": "GET", "path": "/wda/apps"})
        return result

    async def _uninstall(self, bundle_id: str) -> dict:
        udid_arg = ["-u", self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "uninstall", bundle_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _start_app(self, bundle_id: str) -> dict:
        result = await self._wda_command({
            "method": "POST",
            "path": "/wda/apps/launch",
            "body": {"bundleId": bundle_id}
        })
        return result

    async def _stop_app(self, bundle_id: str) -> dict:
        result = await self._wda_command({
            "method": "POST",
            "path": "/wda/apps/terminate",
            "body": {"bundleId": bundle_id}
        })
        return result

    async def _get_battery(self) -> dict:
        result = await self._wda_command({"method": "GET", "path": "/wda/batteryInfo"})
        return result

    async def _get_current_app(self) -> dict:
        result = await self._wda_command({"method": "GET", "path": "/wda/activeElementInfo"})
        if result.get("status") == "success":
            try:
                info = json.loads(result.get("output", "{}"))
                bundle_id = info.get("contentTree", {}).get("bundleId", "unknown")
                return {"status": "success", "output": bundle_id, "error": None}
            except:
                pass
        return result

    async def _tap(self, x: int, y: int) -> dict:
        result = await self._wda_command({
            "method": "POST",
            "path": "/wda/touch/perform",
            "body": {"actions": [{"action": "tap", "x": x, "y": y}]}
        })
        return result

    async def _swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> dict:
        result = await self._wda_command({
            "method": "POST",
            "path": "/wda/touch/perform",
            "body": {"actions": [{"action": "press", "x": x1, "y": y1},
                                  {"action": "moveTo", "x": x2, "y": y2},
                                  {"action": "release"}]}
        })
        return result

    async def _screenrecord(self, local_path: str) -> dict:
        udid_arg = ["-u", self.info.udid] if self.info.udid else []
        proc = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "recordVideo", local_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self._screenrecord_proc = proc
        return {"status": "success", "output": f"Recording started, saving to {local_path}", "error": None}

    async def _stop_screenrecord(self) -> dict:
        if hasattr(self, "_screenrecord_proc") and self._screenrecord_proc:
            self._screenrecord_proc.terminate()
            await self._screenrecord_proc.wait()
            self._screenrecord_proc = None
        return {"status": "success", "output": "Recording stopped", "error": None}