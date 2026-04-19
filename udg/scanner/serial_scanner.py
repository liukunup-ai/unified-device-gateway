import os
import platform
from pathlib import Path
from typing import List

def scan_serial_ports() -> List[str]:
    ports = []
    system = platform.system()
    
    if system == "Linux":
        for p in Path("/dev").glob("ttyUSB*"):
            ports.append(str(p))
        for p in Path("/dev").glob("ttyACM*"):
            ports.append(str(p))
    elif system == "Darwin":
        for p in Path("/dev").glob("cu.*"):
            ports.append(str(p))
    elif system == "Windows":
        import serial.tools.list_ports
        ports = [p.device for p in serial.tools.list_ports.comports()]
    
    return ports