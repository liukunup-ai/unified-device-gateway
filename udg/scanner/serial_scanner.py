import serial.tools.list_ports
from typing import List


def scan_serial_ports() -> List[dict]:
    ports = []
    for p in serial.tools.list_ports.comports():
        if "BLTH" in p.device or "Bluetooth" in p.device:
            continue
        ports.append({"port": p.device, "type": "serial"})
    return ports