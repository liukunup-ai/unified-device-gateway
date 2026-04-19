import asyncio
import json
import os
import pytest
from unittest.mock import MagicMock, patch

from udg.device.serial import SerialDevice
from udg.device.base import DeviceInfo, DeviceType, DeviceStatus


@pytest.fixture
def device_info():
    return DeviceInfo(
        device_id="serial-001",
        device_type=DeviceType.SERIAL,
        status=DeviceStatus.OFFLINE,
        serial_port="/dev/ttyUSB0",
        metadata={"baudrate": 115200, "parity": "N", "databits": 8, "stopbits": 1}
    )


@pytest.fixture
def serial_device(device_info):
    return SerialDevice(device_info)


@pytest.fixture
def mock_serial():
    mock = MagicMock()
    mock.is_open = True
    mock.write = MagicMock(return_value=3)
    mock.read_until = MagicMock(return_value=b"OK\r\n")
    mock.read = MagicMock(return_value=b"RESPONSE")
    mock.close = MagicMock()
    return mock


@pytest.mark.asyncio
async def test_write_text_data(serial_device, mock_serial):
    with patch("serial.Serial", return_value=mock_serial):
        await serial_device.connect()

        result = await serial_device.execute("write", {"data": "AT\r\n"}, 5000)

        assert result["status"] == "success"
        assert "bytes" in result["output"]
        mock_serial.write.assert_called_once()
        call_args = mock_serial.write.call_args[0][0]
        assert call_args == b"AT\r\n"


@pytest.mark.asyncio
async def test_write_binary_data(serial_device, mock_serial):
    with patch("serial.Serial", return_value=mock_serial):
        await serial_device.connect()

        result = await serial_device.execute("write", {"data": "SGVsbG8=", "encoding": "base64"}, 5000)

        assert result["status"] == "success"
        mock_serial.write.assert_called_once()
        call_args = mock_serial.write.call_args[0][0]
        assert call_args == b"Hello"


@pytest.mark.asyncio
async def test_read_data(serial_device, mock_serial):
    with patch("serial.Serial", return_value=mock_serial):
        await serial_device.connect()

        result = await serial_device.execute("read", {"size": 10}, 5000)

        assert result["status"] == "success"
        assert result["output"] == "RESPONSE"
        mock_serial.read.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_config_update(serial_device, mock_serial):
    with patch("serial.Serial", return_value=mock_serial) as mock_serial_class:
        await serial_device.connect()

        result = await serial_device.execute("config", {"baudrate": 57600}, 5000)

        assert result["status"] == "success"
        assert serial_device._baudrate == 57600
        mock_serial.close.assert_called()
        assert mock_serial_class.call_count == 2


@pytest.mark.asyncio
async def test_write_logs_to_jsonl(serial_device, mock_serial):
    log_file = f"/tmp/udg-serial-logs/{serial_device.info.device_id}.jsonl"
    if os.path.exists(log_file):
        os.remove(log_file)

    with patch("serial.Serial", return_value=mock_serial):
        await serial_device.connect()
        result = await serial_device.execute("write", {"data": "AT\r\n"}, 5000)

        assert result["status"] == "success"
        assert os.path.exists(log_file)
        with open(log_file, "r") as f:
            log_entry = json.loads(f.readline())
            assert log_entry["direction"] == "write"
            assert log_entry["data"] == "AT\r\n"
            assert log_entry["size"] == 4
            assert "timestamp" in log_entry

    if os.path.exists(log_file):
        os.remove(log_file)


@pytest.mark.asyncio
async def test_read_logs_to_jsonl(serial_device, mock_serial):
    log_file = f"/tmp/udg-serial-logs/{serial_device.info.device_id}.jsonl"
    if os.path.exists(log_file):
        os.remove(log_file)

    with patch("serial.Serial", return_value=mock_serial):
        await serial_device.connect()
        result = await serial_device.execute("read", {"size": 10}, 5000)

        assert result["status"] == "success"
        assert os.path.exists(log_file)
        with open(log_file, "r") as f:
            log_entry = json.loads(f.readline())
            assert log_entry["direction"] == "read"
            assert log_entry["data"] == "RESPONSE"

    if os.path.exists(log_file):
        os.remove(log_file)