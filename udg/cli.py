import asyncio
import click
from udg import __version__


@click.group()
def cli():
    pass


@cli.command()
def version():
    click.echo(__version__)


@cli.command()
def start():
    click.echo("Starting udg server...")
    from udg.server.app import main as server_main
    asyncio.run(server_main())


@click.group()
def device():
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


@device.command(name="list")
def device_list():
    from udg.device.manager import get_device_manager
    from udg.scanner.device_scanner import scan_all_devices
    device_manager = get_device_manager()
    asyncio.run(scan_all_devices(device_manager))
    devices = asyncio.run(device_manager.list_devices())
    if not devices:
        click.echo("No devices found")
        return
    for d in devices:
        click.echo(f"- {d.device_id} ({d.device_type.value}): {d.status.value}")


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


cli.add_command(device)

if __name__ == "__main__":
    cli()