import grpc
import asyncio
from concurrent import futures
from udg.api import device_pb2, device_pb2_grpc
from udg.device.manager import DeviceManager
from udg.device.serial import SerialDevice
from udg.device.base import DeviceInfo, DeviceType, DeviceStatus
from udg.scanner.serial_scanner import scan_serial_ports
from udg.executor.runner import CommandExecutor


class DeviceGatewayServicer(device_pb2_grpc.DeviceGatewayServicer):
    def __init__(self):
        self.device_manager = DeviceManager()
        self.executor = CommandExecutor(self.device_manager)

    def Execute(self, request, context):
        return device_pb2.CommandResponse(results=[])

    def ListDevices(self, request, context):
        return device_pb2.ListDevicesResponse(devices=[])

    def _get_or_create_serial_device(self, port: str) -> "SerialDevice":
        device_id = f"serial-{port}"
        existing = asyncio.run(self.device_manager.get_device(device_id))
        if existing and isinstance(existing, SerialDevice):
            return existing

        info = DeviceInfo(
            device_id=device_id,
            device_type=DeviceType.SERIAL,
            status=DeviceStatus.OFFLINE,
            serial_port=port,
        )
        device = SerialDevice(info)
        asyncio.run(self.device_manager.register_device(device))
        return device

    def WriteSerial(self, request, context):
        port = request.port
        data = request.data
        read_response = request.read_response
        encoding = request.encoding or "utf-8"

        device = self._get_or_create_serial_device(port)

        async def _write():
            await device.connect()
            result = await device.execute(
                "write",
                {"data": data, "read": read_response, "encoding": encoding},
                timeout_ms=5000,
            )
            return result

        result = asyncio.run(_write())

        if result.get("status") == "success":
            return device_pb2.SerialWriteResponse(
                status=result.get("status", "success"),
                output=result.get("output", ""),
                error=result.get("error", ""),
            )
        return device_pb2.SerialWriteResponse(
            status=result.get("status", "error"),
            output="",
            error=result.get("error", "Unknown error"),
        )

    def ReadSerial(self, request, context):
        port = request.port
        bytes_count = request.bytes or 1

        device = self._get_or_create_serial_device(port)

        async def _read():
            await device.connect()
            result = await device.execute(
                "read",
                {"size": bytes_count},
                timeout_ms=5000,
            )
            return result

        result = asyncio.run(_read())

        if result.get("status") == "success":
            return device_pb2.SerialReadResponse(
                status=result.get("status", "success"),
                output=result.get("output", ""),
                error=result.get("error", ""),
            )
        return device_pb2.SerialReadResponse(
            status=result.get("status", "error"),
            output="",
            error=result.get("error", "Unknown error"),
        )

    def SetSerialConfig(self, request, context):
        port = request.port

        device = self._get_or_create_serial_device(port)

        async def _config():
            await device.connect()
            params = {}
            if request.baudrate:
                params["baudrate"] = str(request.baudrate)
            if request.parity:
                params["parity"] = request.parity
            if request.databits:
                params["databits"] = str(request.databits)
            if request.stopbits:
                params["stopbits"] = str(request.stopbits)
            result = await device.execute("config", params, timeout_ms=5000)
            return result

        result = asyncio.run(_config())

        if result.get("status") == "success":
            return device_pb2.SerialConfigResponse(
                status=result.get("status", "success"),
                output=result.get("output", ""),
                error=result.get("error", ""),
            )
        return device_pb2.SerialConfigResponse(
            status=result.get("status", "error"),
            output="",
            error=result.get("error", "Unknown error"),
        )

    def GetSerialConfig(self, request, context):
        port = request.port
        device_id = f"serial-{port}"

        async def _get_config():
            device = await self.device_manager.get_device(device_id)
            if not device:
                return {
                    "status": "error",
                    "output": "",
                    "error": "Device not found",
                }
            config = {
                "baudrate": device._baudrate,
                "parity": device._parity,
                "databits": device._databits,
                "stopbits": device._stopbits,
            }
            return {"status": "success", "output": str(config), "error": ""}

        result = asyncio.run(_get_config())

        if result.get("status") == "success":
            return device_pb2.SerialConfigResponse(
                status=result.get("status", "success"),
                output=result.get("output", ""),
                error=result.get("error", ""),
            )
        return device_pb2.SerialConfigResponse(
            status=result.get("status", "error"),
            output="",
            error=result.get("error", "Unknown error"),
        )

    def ListSerialPorts(self, request, context):
        ports = scan_serial_ports()
        serial_ports = [
            device_pb2.SerialPort(port=p["port"], type=p.get("type", "serial"))
            for p in ports
        ]
        return device_pb2.ListSerialPortsResponse(ports=serial_ports)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    device_pb2_grpc.add_DeviceGatewayServicer_to_server(DeviceGatewayServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    return server