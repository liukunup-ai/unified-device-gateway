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
                elif command == "get_ip":
                    return await self._get_ip()
                elif command == "press":
                    return await self._press(params.get("key", "home"))
                elif command == "input_text":
                    return await self._input_text(params.get("text", ""))
                elif command == "click_by_text":
                    return await self._click_by_text(params.get("text", ""))
                elif command == "handle_alert":
                    return await self._handle_alert(params.get("action", "accept"))
                elif command == "assert_text":
                    return await self._assert_text(params.get("text", ""), params.get("timeout", 5))
                elif command == "dump_ui":
                    return await self._uiautomator({"method": "dump"})
                else:
                    return {"status": "error", "error": "UNKNOWN_COMMAND", "output": None}
        except asyncio.TimeoutError:
            return {"status": "error", "error": "TIMEOUT", "output": None}
        except Exception as e:
            return {"status": "error", "error": str(e), "output": None}

    async def _shell(self, cmd: str) -> dict:
        result = await self._get_adb().run("shell", cmd)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _screenshot(self) -> dict:
        result = await self._get_adb().run("exec-out", "screencap", "-p")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        b64 = base64.b64encode(result.stdout.encode()).decode()
        return {"status": "success", "output": f"data:image/png;base64,{b64}", "error": None}

    async def _install(self, path: str) -> dict:
        result = await self._get_adb().run("install", "-r", path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _push(self, local_path: str, remote_path: str) -> dict:
        result = await self._get_adb().run("push", local_path, remote_path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _pull(self, remote_path: str, local_path: str) -> dict:
        result = await self._get_adb().run("pull", remote_path, local_path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _list_apps(self) -> dict:
        result = await self._get_adb().run("shell", "pm", "list", "packages")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        packages = [line.replace("package:", "").strip() for line in result.stdout.strip().split("\n")]
        return {"status": "success", "output": json.dumps(packages), "error": None}

    async def _uninstall(self, package: str) -> dict:
        result = await self._get_adb().run("uninstall", package)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _start_app(self, package: str, activity: Optional[str] = None) -> dict:
        component = f"{package}/{activity}" if activity else package
        result = await self._get_adb().run("shell", "am", "start", "-n", component)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _stop_app(self, package: str) -> dict:
        result = await self._get_adb().run("shell", "am", "force-stop", package)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _get_battery(self) -> dict:
        result = await self._get_adb().run("shell", "dumpsys", "battery")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _get_current_app(self) -> dict:
        result = await self._get_adb().run("shell", "dumpsys", "activity", "activities")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        for line in result.stdout.split("\n"):
            if "mResumedActivity" in line or "mCurrentFocus" in line:
                return {"status": "success", "output": line.strip(), "error": None}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _tap(self, x: int, y: int) -> dict:
        result = await self._get_adb().run("shell", "input", "tap", str(x), str(y))
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": "tapped", "error": None}

    async def _swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> dict:
        result = await self._get_adb().run("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration))
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": "swiped", "error": None}

    async def _screenrecord(self, remote_path: str) -> dict:
        proc = await self._get_adb().start("shell", "screenrecord", remote_path)
        self._screen_record_proc = proc
        return {"status": "success", "output": f"Recording started, saving to {remote_path}", "error": None}

    async def _stop_screenrecord(self) -> dict:
        if hasattr(self, "_screen_record_proc") and self._screen_record_proc:
            self._screen_record_proc.terminate()
            await self._screen_record_proc.wait()
            self._screen_record_proc = None
        return {"status": "success", "output": "Recording stopped", "error": None}

    async def _uiautomator(self, params: dict) -> dict:
        method = params.get("method", "dump")
        adb = self._get_adb()

        if method == "dump":
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
        else:
            cmd = params.get("cmd", f"uiautomator {method}")
            result = await adb.run("shell", cmd)
            if result.code != 0:
                return {"status": "error", "output": None, "error": result.stderr}
            return {"status": "success", "output": result.stdout, "error": None}

    async def _get_ip(self) -> dict:
        result = await self._get_adb().run("shell", "ifconfig", "wlan0")
        if result.code != 0:
            result = await self._get_adb().run("shell", "ifconfig")
            if result.code != 0:
                return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _press(self, key: str) -> dict:
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

    async def _input_text(self, text: str) -> dict:
        result = await self._get_adb().run("shell", "input", "text", text)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": "text input", "error": None}

    async def _click_by_text(self, text: str) -> dict:
        loop = asyncio.get_event_loop()
        try:
            d = await loop.run_in_executor(None, self._get_u2)
            await loop.run_in_executor(None, lambda: d(text=text).click())
            return {"status": "success", "output": f"clicked by text: {text}", "error": None}
        except Exception as e:
            return {"status": "error", "output": None, "error": str(e)}

    async def _handle_alert(self, action: str = "accept") -> dict:
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

    async def _assert_text(self, text: str, timeout: int = 5) -> dict:
        loop = asyncio.get_event_loop()
        try:
            d = await loop.run_in_executor(None, self._get_u2)
            ele = d(text=text)
            exists = await loop.run_in_executor(None, ele.exists)
            if exists:
                return {"status": "success", "output": f"text found: {text}", "error": None}
            else:
                return {"status": "error", "output": None, "error": f"text not found: {text}"}
        except Exception as e:
            return {"status": "error", "output": None, "error": str(e)}