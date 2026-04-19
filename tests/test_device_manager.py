import pytest
from udg.device.manager import DeviceManager
from udg.device.base import DeviceInfo, DeviceType, DeviceStatus, BaseDevice

@pytest.mark.asyncio
async def test_device_manager_register():
    manager = DeviceManager()
    info = DeviceInfo(device_id="test", device_type=DeviceType.IOS, status=DeviceStatus.ONLINE)

    class DummyDevice(BaseDevice):
        def __init__(self, info):
            super().__init__(info)

        async def connect(self):
            pass

        async def disconnect(self):
            pass

        async def execute(self, command: str, params: dict, timeout_ms: int) -> dict:
            return {}

    device = DummyDevice(info)
    await manager.register_device(device)

    result = await manager.get_device("test")
    assert result is not None
    assert result.info.device_id == "test"