import asyncio
import click
import socket
from udg import __version__
from udg.config import settings


@click.group()
def cli():
    pass


@cli.command()
def version():
    click.echo(__version__)


@cli.command()
def help():
    """Show help information"""
    click.echo("""
Unified Device Gateway (UDG) - 统一设备网关

Usage: udg [COMMAND] [OPTIONS]

Commands:
  start           Start the UDG server
  token           Manage authentication token
  status          Show server status
  device          Device management commands

Token Commands:
  udg token show          Show current token
  udg token rotate        Rotate to a new token

Device Commands:
  udg device list          List all connected devices
  udg device push          Push file to device
  udg device pull          Pull file from device
  udg device apps          List installed apps
  udg device install       Install app
  udg device uninstall     Uninstall app
  udg device launch        Launch app
  udg device stop          Stop app
  udg device battery       Get battery status
  udg device current-app   Get current app
  udg device tap           Tap screen coordinates
  udg device swipe         Swipe screen
  udg device screenshot    Take screenshot
  udg device record        Record screen

Run 'udg device COMMAND --help' for more information on a command.
""")


@cli.command()
def status():
    """Show server status"""
    from udg.device.manager import get_device_manager

    http_listening = _is_port_open("127.0.0.1", settings.http_port)
    grpc_listening = _is_port_open("127.0.0.1", settings.grpc_port)

    device_manager = get_device_manager()
    devices = asyncio.run(device_manager.list_devices())

    click.echo("UDG Server Status")
    click.echo("=" * 40)
    click.echo(f"HTTP Server:     {'✓ Running' if http_listening else '✗ Not running'} (port {settings.http_port})")
    click.echo(f"gRPC Server:     {'✓ Running' if grpc_listening else '✗ Not running'} (port {settings.grpc_port})")
    click.echo(f"Devices:         {len(devices)} connected")
    click.echo(f"Token file:      {settings.token_file}")


def _is_port_open(host: str, port: int) -> bool:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


@click.group()
def token():
    """Manage authentication token"""
    pass


@token.command(name="show")
def token_show():
    """Show current authentication token"""
    from udg.auth.token import load_token
    token = load_token(settings.token_file)
    click.echo(token)


@token.command(name="rotate")
def token_rotate():
    """Rotate to a new authentication token"""
    from udg.auth.token import rotate_token, load_token
    new_token = rotate_token(settings.token_file)
    click.echo(f"Token rotated successfully. New token: {new_token}")


@cli.command()
def start():
    click.echo("Starting UDG server...")
    from udg.server.app import main as server_main
    asyncio.run(server_main())


@cli.command(name="list")
def list_devices():
    from udg.device.manager import get_device_manager
    from udg.scanner.device_scanner import scan_all_devices
    from udg.scanner.serial_scanner import scan_serial_ports
    device_manager = get_device_manager()
    asyncio.run(scan_all_devices(device_manager))
    devices = asyncio.run(device_manager.list_devices())
    serial_ports = scan_serial_ports()

    android_count = sum(1 for d in devices if d.device_type.value == "android")
    ios_count = sum(1 for d in devices if d.device_type.value == "ios")
    serial_count = len(serial_ports)
    click.echo(f"Android: {android_count}, iOS: {ios_count}, Serial: {serial_count}")

    for d in devices:
        click.echo(f"- {d.device_id} {d.device_type.value} {d.status.value}")
    for p in serial_ports:
        click.echo(f"- {p['port']} serial offline")


@click.group()
def device():
    pass


async def _run_serial_command(port: str, command: str, params: dict):
    from udg.device.manager import get_device_manager
    from udg.device.serial import SerialDevice
    from udg.device.base import DeviceInfo, DeviceType, DeviceStatus
    from udg.api.schemas import Command
    from datetime import datetime
    device_manager = get_device_manager()
    info = DeviceInfo(
        device_id=f"serial-{port}",
        device_type=DeviceType.SERIAL,
        serial_port=port,
        status=DeviceStatus.ONLINE
    )
    device = SerialDevice(info)
    await device.connect()
    cmd = Command(
        id=f"cli-{datetime.now().timestamp()}",
        device_id=info.device_id,
        command=command,
        params=params,
        timeout_ms=30000
    )
    result = await device.execute(cmd.command, cmd.params, cmd.timeout_ms)
    await device.disconnect()
    return result


@click.group()
def serial():
    pass


async def _run_device_command(device_id: str, command: str, params: dict):
    from udg.device.manager import get_device_manager
    from udg.api.schemas import Command
    from datetime import datetime
    device_manager = get_device_manager()
    device = await device_manager.get_device(device_id)
    if not device:
        return {"status": "error", "output": None, "error": f"Device {device_id} not found"}
    cmd = Command(
        id=f"cli-{datetime.now().timestamp()}",
        device_id=device_id,
        command=command,
        params=params,
        timeout_ms=30000
    )
    from udg.executor.runner import CommandExecutor
    executor = CommandExecutor(device_manager)
    results = await executor.execute_batch([cmd])
    return {"status": results[0].status, "output": results[0].output, "error": results[0].error}


def _print_result(result: dict):
    if result["status"] == "success":
        click.echo(result["output"] or "OK")
    else:
        click.echo(f"Error: {result['error']}", err=True)


@device.command(name="push")
@click.argument("device_id")
@click.argument("local_path")
@click.argument("remote_path")
def device_push(device_id, local_path, remote_path):
    result = asyncio.run(_run_device_command(device_id, "push", {"local_path": local_path, "remote_path": remote_path}))
    _print_result(result)


@device.command(name="pull")
@click.argument("device_id")
@click.argument("remote_path")
@click.argument("local_path")
def device_pull(device_id, remote_path, local_path):
    result = asyncio.run(_run_device_command(device_id, "pull", {"remote_path": remote_path, "local_path": local_path}))
    _print_result(result)


@device.command(name="apps")
@click.argument("device_id")
def device_apps(device_id):
    result = asyncio.run(_run_device_command(device_id, "list_apps", {}))
    _print_result(result)


@device.command(name="install")
@click.argument("device_id")
@click.argument("path")
def device_install(device_id, path):
    result = asyncio.run(_run_device_command(device_id, "install", {"path": path}))
    _print_result(result)


@device.command(name="uninstall")
@click.argument("device_id")
@click.argument("package")
def device_uninstall(device_id, package):
    result = asyncio.run(_run_device_command(device_id, "uninstall", {"package": package}))
    _print_result(result)


@device.command(name="launch")
@click.argument("device_id")
@click.argument("package")
def device_launch(device_id, package):
    result = asyncio.run(_run_device_command(device_id, "start_app", {"package": package}))
    _print_result(result)


@device.command(name="stop")
@click.argument("device_id")
@click.argument("package")
def device_stop(device_id, package):
    result = asyncio.run(_run_device_command(device_id, "stop_app", {"package": package}))
    _print_result(result)


@device.command(name="battery")
@click.argument("device_id")
def device_battery(device_id):
    result = asyncio.run(_run_device_command(device_id, "get_battery", {}))
    _print_result(result)


@device.command(name="current-app")
@click.argument("device_id")
def device_current_app(device_id):
    result = asyncio.run(_run_device_command(device_id, "get_current_app", {}))
    _print_result(result)


@device.command(name="tap")
@click.argument("device_id")
@click.argument("x", type=int)
@click.argument("y", type=int)
def device_tap(device_id, x, y):
    result = asyncio.run(_run_device_command(device_id, "tap", {"x": x, "y": y}))
    _print_result(result)


@device.command(name="swipe")
@click.argument("device_id")
@click.argument("x1", type=int)
@click.argument("y1", type=int)
@click.argument("x2", type=int)
@click.argument("y2", type=int)
def device_swipe(device_id, x1, y1, x2, y2):
    result = asyncio.run(_run_device_command(device_id, "swipe", {"x1": x1, "y1": y1, "x2": x2, "y2": y2}))
    _print_result(result)


@device.command(name="screenshot")
@click.argument("device_id")
def device_screenshot(device_id):
    result = asyncio.run(_run_device_command(device_id, "screenshot", {}))
    _print_result(result)


@device.command(name="record")
@click.argument("device_id")
@click.argument("path", required=False, default="/sdcard/screen.mp4")
def device_record(device_id, path):
    result = asyncio.run(_run_device_command(device_id, "screenrecord", {"path": path}))
    _print_result(result)


@serial.command(name="list")
def serial_list():
    """List available serial ports"""
    from udg.scanner.serial_scanner import scan_serial_ports
    ports = scan_serial_ports()
    if not ports:
        click.echo("No serial ports found")
        return
    for p in ports:
        click.echo(f"{p['port']} serial offline")


@serial.command(name="write")
@click.argument("port")
@click.argument("data")
@click.option("--read/--no-read", default=False, help="Read response after write")
@click.option("--encoding", default="utf-8", type=click.Choice(["utf-8", "base64"]), help="Data encoding")
def serial_write(port, data, read, encoding):
    """Write data to serial port"""
    result = asyncio.run(_run_serial_command(port, "write", {"data": data, "read": read, "encoding": encoding}))
    _print_result(result)


@serial.command(name="read")
@click.argument("port")
@click.option("--bytes", "size", default=1024, help="Number of bytes to read")
def serial_read(port, size):
    """Read data from serial port"""
    result = asyncio.run(_run_serial_command(port, "read", {"size": size}))
    _print_result(result)


@serial.command(name="config")
@click.argument("port")
@click.option("--baudrate", default=None, type=int, help="Baud rate")
@click.option("--parity", default=None, type=click.Choice(["N", "E", "O"]), help="Parity (N=None, E=Even, O=Odd)")
@click.option("--databits", default=None, type=int, help="Data bits (5, 6, 7, 8)")
@click.option("--stopbits", default=None, type=int, help="Stop bits (1, 2)")
def serial_config(port, baudrate, parity, databits, stopbits):
    """Configure serial port parameters"""
    params = {}
    if baudrate is not None:
        params["baudrate"] = baudrate
    if parity is not None:
        params["parity"] = parity
    if databits is not None:
        params["databits"] = databits
    if stopbits is not None:
        params["stopbits"] = stopbits
    if not params:
        click.echo("No configuration options provided")
        return
    result = asyncio.run(_run_serial_command(port, "config", params))
    _print_result(result)


cli.add_command(device)
cli.add_command(token)
cli.add_command(serial)

if __name__ == "__main__":
    cli()