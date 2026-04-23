import asyncio
import base64
import json
from typing import Optional
from udg.device.base import BaseDevice, DeviceInfo
from udg.utils.cmd import CmdRunner


class AndroidDevice(BaseDevice):

    def __init__(self, info: DeviceInfo):
        super().__init__(info)
        self._adb: Optional[CmdRunner] = None
        self._u2 = None

    def _get_adb(self) -> CmdRunner:
        if self._adb:
            return self._adb
        if self.info.serial:
            self._adb = CmdRunner("adb", "-s", self.info.serial)
        elif self.info.ip_port:
            self._adb = CmdRunner("adb", "-s", self.info.ip_port)
        else:
            self._adb = CmdRunner("adb")
        return self._adb

    def _get_u2(self):
        if self._u2 is None:
            import uiautomator2 as u2
            if self.info.serial:
                self._u2 = u2.connect(self.info.serial)
            elif self.info.ip_port:
                self._u2 = u2.connect(self.info.ip_port)
            else:
                self._u2 = u2.connect()
        return self._u2

    async def connect(self) -> None:
        result = await self._get_adb().run("get-state")
        if result.code != 0:
            raise RuntimeError(f"adb connect failed: {result.stderr}")
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def shell(self, cmd: str) -> dict:
        result = await self._get_adb().run("shell", cmd)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def screenshot(self) -> dict:
        result = await self._get_adb().run("exec-out", "screencap", "-p")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        b64 = base64.b64encode(result.stdout.encode()).decode()
        return {"status": "success", "output": f"data:image/png;base64,{b64}", "error": None}

    async def install(self, path: str) -> dict:
        result = await self._get_adb().run("install", "-r", path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def push(self, local_path: str, remote_path: str) -> dict:
        result = await self._get_adb().run("push", local_path, remote_path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def pull(self, remote_path: str, local_path: str) -> dict:
        result = await self._get_adb().run("pull", remote_path, local_path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def list_apps(self) -> dict:
        result = await self._get_adb().run("shell", "pm", "list", "packages")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        packages = [line.replace("package:", "").strip() for line in result.stdout.strip().split("\n")]
        return {"status": "success", "output": json.dumps(packages), "error": None}

    async def uninstall(self, bundle_id: str) -> dict:
        result = await self._get_adb().run("uninstall", bundle_id)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def start_app(self, bundle_id: str, ability: str = "") -> dict:
        component = f"{bundle_id}/{ability}" if ability else bundle_id
        result = await self._get_adb().run("shell", "am", "start", "-n", component)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def stop_app(self, bundle_id: str) -> dict:
        result = await self._get_adb().run("shell", "am", "force-stop", bundle_id)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def get_battery(self) -> dict:
        result = await self._get_adb().run("shell", "dumpsys", "battery")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def get_current_app(self) -> dict:
        result = await self._get_adb().run("shell", "dumpsys", "activity", "activities")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        for line in result.stdout.split("\n"):
            if "mResumedActivity" in line or "mCurrentFocus" in line:
                return {"status": "success", "output": line.strip(), "error": None}
        return {"status": "success", "output": result.stdout, "error": None}

    async def tap(self, x: int, y: int) -> dict:
        result = await self._get_adb().run("shell", "input", "tap", str(x), str(y))
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": "tapped", "error": None}

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> dict:
        result = await self._get_adb().run("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration))
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": "swiped", "error": None}

    async def screenrecord(self, path: str = "/sdcard/screen.mp4") -> dict:
        proc = await self._get_adb().start("shell", "screenrecord", path)
        self._screen_record_proc = proc
        return {"status": "success", "output": f"Recording started, saving to {path}", "error": None}

    async def stop_screenrecord(self) -> dict:
        if hasattr(self, "_screen_record_proc") and self._screen_record_proc:
            self._screen_record_proc.terminate()
            await self._screen_record_proc.wait()
            self._screen_record_proc = None
        return {"status": "success", "output": "Recording stopped", "error": None}

    async def get_ip(self) -> dict:
        result = await self._get_adb().run("shell", "ifconfig", "wlan0")
        if result.code != 0:
            result = await self._get_adb().run("shell", "ifconfig")
            if result.code != 0:
                return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def press(self, key: str) -> dict:
        key_map = {
            "home": "KEYCODE_HOME",
            "back": "KEYCODE_BACK",
            "volup": "KEYCODE_VOLUME_UP",
            "voldown": "KEYCODE_VOLUME_DOWN",
            "power": "KEYCODE_POWER",
            "up": "KEYCODE_DPAD_UP",
            "down": "KEYCODE_DPAD_DOWN",
            "left": "KEYCODE_DPAD_LEFT",
            "right": "KEYCODE_DPAD_RIGHT",
            "enter": "KEYCODE_ENTER",
        }
        android_key = key_map.get(key.lower(), key.upper())
        result = await self._get_adb().run("shell", "input", "keyevent", android_key)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": "pressed", "error": None}

    async def input_text(self, text: str) -> dict:
        result = await self._get_adb().run("shell", "input", "text", text)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": "text input", "error": None}

    async def click_by_text(self, text: str) -> dict:
        loop = asyncio.get_event_loop()
        try:
            d = await loop.run_in_executor(None, self._get_u2)
            await loop.run_in_executor(None, lambda: d(text=text).click())
            return {"status": "success", "output": f"clicked by text: {text}", "error": None}
        except Exception as e:
            return {"status": "error", "output": None, "error": str(e)}

    async def handle_alert(self, action: str = "accept") -> dict:
        loop = asyncio.get_event_loop()
        try:
            d = await loop.run_in_executor(None, self._get_u2)
            if action == "dismiss":
                await loop.run_in_executor(None, lambda: d.alert.dismiss())
            else:
                await loop.run_in_executor(None, lambda: d.alert.accept())
            return {"status": "success", "output": f"alert {action}ed", "error": None}
        except Exception as e:
            return {"status": "error", "output": None, "error": str(e)}

    async def assert_text(self, text: str) -> dict:
        loop = asyncio.get_event_loop()
        try:
            d = await loop.run_in_executor(None, self._get_u2)
            ele = d(text=text)
            exists = await loop.run_in_executor(None, ele.exists)
            if exists:
                return {"status": "success", "output": f"text found: {text}", "error": None}
            return {"status": "error", "output": None, "error": f"text not found: {text}"}
        except Exception as e:
            return {"status": "error", "output": None, "error": str(e)}

    async def dump_ui(self) -> dict:
        adb = self._get_adb()
        await adb.run("shell", "uiautomator", "dump", "/sdcard/dump.xml")
        result = await adb.run("pull", "/sdcard/dump.xml")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        try:
            with open("dump.xml") as f:
                content = f.read()
            return {"status": "success", "output": content, "error": None}
        except FileNotFoundError:
            return {"status": "error", "output": None, "error": "dump failed"}
