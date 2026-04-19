import grpc
from concurrent import futures
from udg.api import device_pb2, device_pb2_grpc
from udg.device.manager import DeviceManager
from udg.executor.runner import CommandExecutor


class DeviceGatewayServicer(device_pb2_grpc.DeviceGatewayServicer):
    def __init__(self):
        self.device_manager = DeviceManager()
        self.executor = CommandExecutor(self.device_manager)

    def Execute(self, request, context):
        return device_pb2.CommandResponse(results=[])

    def ListDevices(self, request, context):
        return device_pb2.ListDevicesResponse(devices=[])


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    device_pb2_grpc.add_DeviceGatewayServicer_to_server(DeviceGatewayServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    return server