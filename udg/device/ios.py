import asyncio
import json
import base64
from typing import Optional
from udg.device.base import BaseDevice, DeviceInfo


class IOSDevice(BaseDevice):

    def __init__(self, info: DeviceInfo):
        super().__init__(info)
        self._wda_url: Optional[str] = None

    async def connect(self) -> None:
        cmd = ["ios", "list", "--details"]
        if self.info.udid:
            cmd = ["ios", "--udid=" + self.info.udid, "list", "--details"]
        result = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            raise RuntimeError(f"go-ios failed: {stderr.decode()}")
        self._connected = True

    async def disconnect(self) -> None:
        self._wda_url = None
        self._connected = False

    async def shell(self, cmd: str) -> dict:
        udid_arg = ["--udid=" + self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "shell", cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def screenshot(self) -> dict:
        udid_arg = ["--udid=" + self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "screenshot",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        b64 = base64.b64encode(stdout).decode()
        return {"status": "success", "output": f"data:image/png;base64,{b64}", "error": None}

    async def install(self, path: str) -> dict:
        udid_arg = ["--udid=" + self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "install", "--path=" + path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def push(self, local_path: str, remote_path: str) -> dict:
        udid_arg = ["--udid=" + self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "file", "push",
            "--local=" + local_path, "--remote=" + remote_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def pull(self, remote_path: str, local_path: str) -> dict:
        udid_arg = ["--udid=" + self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "file", "pull",
            "--remote=" + remote_path, "--local=" + local_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def list_apps(self) -> dict:
        return await self.wda_command({"method": "GET", "path": "/wda/apps"})

    async def uninstall(self, bundle_id: str) -> dict:
        udid_arg = ["--udid=" + self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "uninstall", bundle_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def start_app(self, bundle_id: str, ability: str = "") -> dict:
        return await self.wda_command({
            "method": "POST",
            "path": "/wda/apps/launch",
            "body": {"bundleId": bundle_id}
        })

    async def stop_app(self, bundle_id: str) -> dict:
        return await self.wda_command({
            "method": "POST",
            "path": "/wda/apps/terminate",
            "body": {"bundleId": bundle_id}
        })

    async def get_battery(self) -> dict:
        return await self.wda_command({"method": "GET", "path": "/wda/batteryInfo"})

    async def get_current_app(self) -> dict:
        result = await self.wda_command({"method": "GET", "path": "/wda/activeAppInfo"})
        if result.get("status") == "success":
            try:
                info = json.loads(result.get("output", "{}"))
                bundle_id = info.get("bundleId", "unknown")
                return {"status": "success", "output": bundle_id, "error": None}
            except:
                pass
        return result

    async def tap(self, x: int, y: int) -> dict:
        return await self.wda_command({
            "method": "POST",
            "path": "/wda/touch/perform",
            "body": {"actions": [{"action": "tap", "x": x, "y": y}]}
        })

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> dict:
        return await self.wda_command({
            "method": "POST",
            "path": "/wda/touch/perform",
            "body": {"actions": [
                {"action": "press", "x": x1, "y": y1},
                {"action": "wait", "ms": duration},
                {"action": "moveTo", "x": x2, "y": y2},
                {"action": "release"}
            ]}
        })

    async def screenrecord(self, path: str = "/tmp/screen.mp4") -> dict:
        udid_arg = ["--udid=" + self.info.udid] if self.info.udid else []
        proc = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "recordVideo", "--output=" + path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self._screenrecord_proc = proc
        return {"status": "success", "output": f"Recording started, saving to {path}", "error": None}

    async def stop_screenrecord(self) -> dict:
        if hasattr(self, "_screenrecord_proc") and self._screenrecord_proc:
            self._screenrecord_proc.terminate()
            await self._screenrecord_proc.wait()
            self._screenrecord_proc = None
        return {"status": "success", "output": "Recording stopped", "error": None}

    async def get_ip(self) -> dict:
        udid_arg = ["--udid=" + self.info.udid] if self.info.udid else []
        result = await asyncio.create_subprocess_exec(
            "ios", *udid_arg, "diag", "--network",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await result.communicate()
        if result.returncode != 0:
            return {"status": "error", "error": stderr.decode(), "output": None}
        return {"status": "success", "output": stdout.decode(), "error": None}

    async def dump_ui(self) -> dict:
        return await self.wda_command({"method": "GET", "path": "/wda/source"})

    async def click_by_text(self, text: str) -> dict:
        return await self.wda_command({
            "method": "POST",
            "path": "/wda/element/text",
            "body": {"text": text}
        })

    async def input_text(self, text: str) -> dict:
        return await self.wda_command({
            "method": "POST",
            "path": "/wda/element/focused/setValue",
            "body": {"value": text}
        })

    async def handle_alert(self, action: str = "accept") -> dict:
        if action == "dismiss":
            return await self.wda_command({"method": "POST", "path": "/wda/alert/dismiss"})
        return await self.wda_command({"method": "POST", "path": "/wda/alert/accept"})

    async def assert_text(self, text: str) -> dict:
        return await self.wda_command({
            "method": "POST",
            "path": "/wda/element/text/exists",
            "body": {"text": text}
        })

    async def wda_command(self, params: dict) -> dict:
        method = params.get("method", "GET").upper()
        path = params.get("path", "/status")
        body = params.get("body")

        if not self._wda_url:
            port = 8100
            if self.info.udid:
                await asyncio.create_subprocess_exec(
                    "ios", "--udid=" + self.info.udid, "runwda",
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
