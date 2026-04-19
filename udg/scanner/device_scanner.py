import asyncio
import json
from typing import Optional

from udg.device.base import DeviceType
from udg.device.manager import DeviceManager
from udg.device.ios import IOSDevice
from udg.device.android import AndroidDevice
from udg.utils.cmd import CmdRunner


async def scan_ios_devices() -> list[dict]:
    result = await CmdRunner("ios", "list").run()
    if result.code != 0:
        return []
    try:
        data = json.loads(result.stdout)
        return [{"udid": udid, "type": "ios"} for udid in data.get("deviceList", [])]
    except json.JSONDecodeError:
        return []


async def scan_android_devices() -> list[dict]:
    result = await CmdRunner("adb", "devices").run()
    if result.code != 0:
        return []
    devices = []
    for line in result.stdout.strip().split("\n")[1:]:
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1] == "device":
            serial = parts[0]
            if ":" in serial:
                devices.append({"ip_port": serial, "type": "android"})
            else:
                devices.append({"serial": serial, "type": "android"})
    return devices


async def scan_all_devices(device_manager: DeviceManager) -> None:
    ios_devices = await scan_ios_devices()
    android_devices = await scan_android_devices()

    for info in ios_devices:
        from udg.device.base import DeviceInfo, DeviceStatus
        device = IOSDevice(DeviceInfo(
            device_id=info["udid"],
            device_type=DeviceType.IOS,
            status=DeviceStatus.ONLINE,
            udid=info["udid"],
        ))
        await device_manager.register_device(device)

    for info in android_devices:
        from udg.device.base import DeviceInfo, DeviceStatus
        if "serial" in info:
            device_id = info["serial"][:8]
            device = AndroidDevice(DeviceInfo(
                device_id=device_id,
                device_type=DeviceType.ANDROID,
                status=DeviceStatus.ONLINE,
                serial=info["serial"],
            ))
        else:
            device_id = info["ip_port"].replace(":", "_")
            device = AndroidDevice(DeviceInfo(
                device_id=device_id,
                device_type=DeviceType.ANDROID,
                status=DeviceStatus.ONLINE,
                ip_port=info["ip_port"],
            ))
        await device_manager.register_device(device)
