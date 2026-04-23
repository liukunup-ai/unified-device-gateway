import asyncio
import base64
import json
import subprocess
from typing import Optional
from udg.device.base import BaseDevice, DeviceInfo, DeviceStatus
from udg.utils.cmd import CmdRunner


class HarmonyOSDevice(BaseDevice):

    def __init__(self, info: DeviceInfo):
        super().__init__(info)
        self._hdc: Optional[CmdRunner] = None

    def _get_hdc(self) -> CmdRunner:
        if self._hdc:
            return self._hdc
        if self.info.serial:
            self._hdc = CmdRunner("hdc", "-t", self.info.serial)
        elif self.info.ip_port:
            self._hdc = CmdRunner("hdc", "-t", self.info.ip_port)
        else:
            self._hdc = CmdRunner("hdc")
        return self._hdc

    def _uitest_cmd(self, action: str, text: str = "", ability: str = "") -> list:
        cmd = ["hdc"]
        if self.info.serial:
            cmd.extend(["-t", self.info.serial])
        elif self.info.ip_port:
            cmd.extend(["-t", self.info.ip_port])
        cmd.append("shell")
        cmd.append("uitest")
        if text:
            cmd.extend(["-t", text])
        if ability:
            cmd.extend(["-a", ability])
        elif action:
            cmd.extend(["-a", action])
        return cmd

    async def connect(self) -> None:
        result = await self._get_hdc().run("list", "targets")
        if result.code != 0:
            raise RuntimeError(f"hdc connect failed: {result.stderr}")
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def shell(self, cmd: str) -> dict:
        result = await self._get_hdc().run("shell", cmd)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def screenshot(self) -> dict:
        result = await self._get_hdc().run("shell", "screencap", "-p", "/data/local/tmp/screenshot.png")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        result = await self._get_hdc().run("file", "recv", "/data/local/tmp/screenshot.png", "/tmp/screenshot.png")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        try:
            with open("/tmp/screenshot.png", "rb") as f:
                img_data = f.read()
            b64 = base64.b64encode(img_data).decode()
            return {"status": "success", "output": f"data:image/png;base64,{b64}", "error": None}
        except FileNotFoundError:
            return {"status": "error", "output": None, "error": "screenshot file not found"}

    async def install(self, path: str) -> dict:
        result = await self._get_hdc().run("install", "-r", path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def push(self, local_path: str, remote_path: str) -> dict:
        result = await self._get_hdc().run("file", "send", local_path, remote_path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": f"pushed {local_path} to {remote_path}", "error": None}

    async def pull(self, remote_path: str, local_path: str) -> dict:
        result = await self._get_hdc().run("file", "recv", remote_path, local_path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": f"pulled {remote_path} to {local_path}", "error": None}

    async def list_apps(self) -> dict:
        result = await self._get_hdc().run("shell", "bm", "dump", "-a")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        packages = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        return {"status": "success", "output": json.dumps(packages), "error": None}

    async def uninstall(self, bundle_id: str) -> dict:
        result = await self._get_hdc().run("uninstall", bundle_id)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def start_app(self, bundle_id: str, ability: str = "") -> dict:
        if ability:
            result = await self._get_hdc().run("shell", "aa", "start", "-d", bundle_id, "-n", ability)
        else:
            result = await self._get_hdc().run("shell", "aa", "start", "-d", bundle_id)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def stop_app(self, bundle_id: str) -> dict:
        result = await self._get_hdc().run("shell", "bm", "force-stop", bundle_id)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def get_battery(self) -> dict:
        result = await self._get_hdc().run("shell", "hidump", "-d", "battery")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def get_current_app(self) -> dict:
        result = await self._get_hdc().run("shell", "hidump", "-d", "top", "-a")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def tap(self, x: int, y: int) -> dict:
        result = await self._uitest_run("click", ability=f"{x},{y}")
        if result.get("status") == "success":
            return result
        return {"status": "success", "output": "tapped", "error": None}

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> dict:
        result = await self._uitest_run("swipe", ability=f"{x1},{y1},{x2},{y2},{duration}")
        if result.get("status") == "success":
            return result
        return {"status": "success", "output": "swiped", "error": None}

    async def screenrecord(self, path: str) -> dict:
        proc = await self._get_hdc().start("shell", "screenrecord", path)
        self._screenrecord_proc = proc
        return {"status": "success", "output": f"Recording started, saving to {path}", "error": None}

    async def stop_screenrecord(self) -> dict:
        if hasattr(self, "_screenrecord_proc") and self._screenrecord_proc:
            self._screenrecord_proc.terminate()
            await self._screenrecord_proc.wait()
            self._screenrecord_proc = None
        return {"status": "success", "output": "Recording stopped", "error": None}

    async def get_ip(self) -> dict:
        result = await self._get_hdc().run("shell", "ifconfig", "wlan0")
        if result.code != 0:
            result = await self._get_hdc().run("shell", "ifconfig")
            if result.code != 0:
                return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def press(self, key: str) -> dict:
        key_map = {
            "home": "HOME",
            "back": "BACK",
            "volup": "VOLUME_UP",
            "voldown": "VOLUME_DOWN",
            "power": "POWER",
        }
        hdc_key = key_map.get(key.lower(), key.upper())
        result = await self._uitest_run(hdc_key)
        if result.get("status") == "success":
            return result
        result = await self._get_hdc().run("shell", "input", "keyevent", hdc_key)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": "pressed", "error": None}

    async def input_text(self, text: str) -> dict:
        result = await self._uitest_run(ability=f"inputtext:{text}")
        if result.get("status") == "success":
            return result
        hdc_result = await self._get_hdc().run("shell", "input", "text", text)
        if hdc_result.code != 0:
            return {"status": "error", "output": None, "error": hdc_result.stderr}
        return {"status": "success", "output": "text input", "error": None}

    async def click_by_text(self, text: str) -> dict:
        return await self._uitest_run("click", text)

    async def handle_alert(self, action: str) -> dict:
        return await self._uitest_run(action if action == "dismiss" else "accept")

    async def assert_text(self, text: str) -> dict:
        result = await self._uitest_run("exists", text)
        if result.get("status") == "success":
            return {"status": "success", "output": f"text found: {text}", "error": None}
        return {"status": "error", "output": None, "error": f"text not found: {text}"}

    async def dump_ui(self) -> dict:
        result = await self._uitest_run("dump")
        if result.get("status") == "success":
            return result
        return {"status": "success", "output": result.get("output", ""), "error": None}

    async def _uitest_run(self, action: str = "", text: str = "", ability: str = "") -> dict:
        loop = asyncio.get_event_loop()
        try:
            cmd = self._uitest_cmd(action, text, ability)
            result = await loop.run_in_executor(None, lambda: subprocess.run(cmd, capture_output=True))
            if result.returncode == 0:
                output = result.stdout.decode() if result.stdout else ""
                return {"status": "success", "output": output, "error": None}
            return {"status": "error", "output": None, "error": result.stderr.decode() if result.stderr else "uitest failed"}
        except Exception as e:
            return {"status": "error", "output": None, "error": str(e)}