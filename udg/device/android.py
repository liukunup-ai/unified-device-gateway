import asyncio
import subprocess
import base64
import json
from typing import Optional, Union
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
                elif command == "push":
                    return await self._push(params.get("local_path", ""), params.get("remote_path", ""))
                elif command == "pull":
                    return await self._pull(params.get("remote_path", ""), params.get("local_path", ""))
                elif command == "list_apps":
                    return await self._list_apps()
                elif command == "uninstall":
                    return await self._uninstall(params.get("package", ""))
                elif command == "start_app":
                    return await self._start_app(params.get("package", ""), params.get("activity") or None)
                elif command == "stop_app":
                    return await self._stop_app(params.get("package", ""))
                elif command == "get_battery":
                    return await self._get_battery()
                elif command == "get_current_app":
                    return await self._get_current_app()
                elif command == "tap":
                    return await self._tap(params.get("x", 0), params.get("y", 0))
                elif command == "swipe":
                    return await self._swipe(params.get("x1", 0), params.get("y1", 0), params.get("x2", 0), params.get("y2", 0), params.get("duration", 300))
                elif command == "screenrecord":
                    return await self._screenrecord(params.get("remote_path", "/sdcard/screen.mp4"))
                elif command == "stop_screenrecord":
                    return await self._stop_screenrecord()
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

    async def _push(self, local_path: str, remote_path: str) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "push", local_path, remote_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _pull(self, remote_path: str, local_path: str) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "pull", remote_path, local_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _list_apps(self) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "shell", "pm", "list", "packages",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        packages = [line.replace("package:", "").strip() for line in stdout.decode().strip().split("\n")]
        return {"status": "success", "output": json.dumps(packages), "error": None}

    async def _uninstall(self, package: str) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "uninstall", package,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _start_app(self, package: str, activity: Optional[str] = None) -> dict:
        args = await self._get_adb_args()
        if activity:
            component = f"{package}/{activity}"
        else:
            component = package
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "shell", "am", "start", "-n", component,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _stop_app(self, package: str) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "shell", "am", "force-stop", package,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _get_battery(self) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "shell", "dumpsys", "battery",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def _get_current_app(self) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "shell", "dumpsys", "activity", "activities",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        output = stdout.decode()
        for line in output.split("\n"):
            if "mResumedActivity" in line or "mCurrentFocus" in line:
                return {"status": "success", "output": line.strip(), "error": None}
        return {"status": "success", "output": output, "error": None}

    async def _tap(self, x: int, y: int) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "shell", "input", "tap", str(x), str(y),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": "tapped", "error": None}

    async def _swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> dict:
        args = await self._get_adb_args()
        result = await asyncio.create_subprocess_exec(
            "adb", *args, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": "swiped", "error": None}

    async def _screenrecord(self, remote_path: str) -> dict:
        args = await self._get_adb_args()
        proc = await asyncio.create_subprocess_exec(
            "adb", *args, "shell", "screenrecord", remote_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self._screenrecord_proc = proc
        return {"status": "success", "output": f"Recording started, saving to {remote_path}", "error": None}

    async def _stop_screenrecord(self) -> dict:
        if hasattr(self, "_screenrecord_proc") and self._screenrecord_proc:
            self._screenrecord_proc.terminate()
            await self._screenrecord_proc.wait()
            self._screenrecord_proc = None
        return {"status": "success", "output": "Recording stopped", "error": None}