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

    async def execute(self, command: str, params: dict, timeout_ms: int) -> dict:
        if not self._connected:
            return {"status": "error", "error": "DEVICE_OFFLINE", "output": None}

        try:
            async with asyncio.timeout(timeout_ms / 1000):
                if command == "shell":
                    return await self._shell(params.get("cmd", ""))
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
                    return await self._start_app(params.get("bundle_id", ""), params.get("ability_name", ""))
                elif command == "stop_app":
                    return await self._stop_app(params.get("bundle_id", ""))
                elif command == "get_battery":
                    return await self._get_battery()
                elif command == "get_current_app":
                    return await self._get_current_app()
                elif command == "tap":
                    return await self._tap(params.get("x", 0), params.get("y", 0))
                elif command == "swipe":
                    return await self._swipe(params.get("x1", 0), params.get("y1", 0), params.get("x2", 0), params.get("y2", 0), params.get("duration", 300))
                elif command == "screenrecord":
                    return await self._screenrecord(params.get("remote_path", "/data/local/tmp/screen.mp4"))
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
                    return await self._assert_text(params.get("text", ""))
                elif command == "dump_ui":
                    return await self._dump_ui()
                else:
                    return {"status": "error", "error": "UNKNOWN_COMMAND", "output": None}
        except asyncio.TimeoutError:
            return {"status": "error", "error": "TIMEOUT", "output": None}
        except Exception as e:
            return {"status": "error", "error": str(e), "output": None}

    async def _shell(self, cmd: str) -> dict:
        result = await self._get_hdc().run("shell", cmd)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _screenshot(self) -> dict:
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

    async def _install(self, path: str) -> dict:
        result = await self._get_hdc().run("install", "-r", path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _push(self, local_path: str, remote_path: str) -> dict:
        result = await self._get_hdc().run("file", "send", local_path, remote_path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": f"pushed {local_path} to {remote_path}", "error": None}

    async def _pull(self, remote_path: str, local_path: str) -> dict:
        result = await self._get_hdc().run("file", "recv", remote_path, local_path)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": f"pulled {remote_path} to {local_path}", "error": None}

    async def _list_apps(self) -> dict:
        result = await self._get_hdc().run("shell", "bm", "dump", "-a")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        packages = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        return {"status": "success", "output": json.dumps(packages), "error": None}

    async def _uninstall(self, bundle_id: str) -> dict:
        result = await self._get_hdc().run("uninstall", bundle_id)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _start_app(self, bundle_id: str, ability_name: str = "") -> dict:
        if ability_name:
            result = await self._get_hdc().run("shell", "aa", "start", "-d", bundle_id, "-n", ability_name)
        else:
            result = await self._get_hdc().run("shell", "aa", "start", "-d", bundle_id)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _stop_app(self, bundle_id: str) -> dict:
        result = await self._get_hdc().run("shell", "bm", "force-stop", bundle_id)
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _get_battery(self) -> dict:
        result = await self._get_hdc().run("shell", "hidump", "-d", "battery")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _get_current_app(self) -> dict:
        result = await self._get_hdc().run("shell", "hidump", "-d", "top", "-a")
        if result.code != 0:
            return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

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

    async def _tap(self, x: int, y: int) -> dict:
        result = await self._uitest_run("click", ability=f"{x},{y}")
        if result.get("status") == "success":
            return result
        return {"status": "success", "output": "tapped", "error": None}

    async def _swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> dict:
        result = await self._uitest_run("swipe", ability=f"{x1},{y1},{x2},{y2},{duration}")
        if result.get("status") == "success":
            return result
        return {"status": "success", "output": "swiped", "error": None}

    async def _screenrecord(self, remote_path: str) -> dict:
        proc = await self._get_hdc().start("shell", "screenrecord", remote_path)
        self._screenrecord_proc = proc
        return {"status": "success", "output": f"Recording started, saving to {remote_path}", "error": None}

    async def _stop_screenrecord(self) -> dict:
        if hasattr(self, "_screenrecord_proc") and self._screenrecord_proc:
            self._screenrecord_proc.terminate()
            await self._screenrecord_proc.wait()
            self._screenrecord_proc = None
        return {"status": "success", "output": "Recording stopped", "error": None}

    async def _get_ip(self) -> dict:
        result = await self._get_hdc().run("shell", "ifconfig", "wlan0")
        if result.code != 0:
            result = await self._get_hdc().run("shell", "ifconfig")
            if result.code != 0:
                return {"status": "error", "output": None, "error": result.stderr}
        return {"status": "success", "output": result.stdout, "error": None}

    async def _press(self, key: str) -> dict:
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

    async def _input_text(self, text: str) -> dict:
        result = await self._uitest_run(ability=f"inputtext:{text}")
        if result.get("status") == "success":
            return result
        hdc_result = await self._get_hdc().run("shell", "input", "text", text)
        if hdc_result.code != 0:
            return {"status": "error", "output": None, "error": hdc_result.stderr}
        return {"status": "success", "output": "text input", "error": None}

    async def _click_by_text(self, text: str) -> dict:
        return await self._uitest_run("click", text)

    async def _handle_alert(self, action: str = "accept") -> dict:
        return await self._uitest_run(action if action == "dismiss" else "accept")

    async def _assert_text(self, text: str) -> dict:
        result = await self._uitest_run("exists", text)
        if result.get("status") == "success":
            return {"status": "success", "output": f"text found: {text}", "error": None}
        return {"status": "error", "output": None, "error": f"text not found: {text}"}

    async def _dump_ui(self) -> dict:
        result = await self._uitest_run("dump")
        if result.get("status") == "success":
            return result
        return {"status": "success", "output": result.get("output", ""), "error": None}