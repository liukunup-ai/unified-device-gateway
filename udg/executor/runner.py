import asyncio
from typing import List
from datetime import datetime
from udg.api.schemas import Command, CommandResult
from udg.device.manager import DeviceManager

class CommandExecutor:
    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
    
    async def execute_batch(self, commands: List[Command]) -> List[CommandResult]:
        tasks = [self._execute_one(cmd) for cmd in commands]
        return await asyncio.gather(*tasks)
    
    async def _execute_one(self, command: Command) -> CommandResult:
        device = await self.device_manager.get_device(command.device_id)
        if not device:
            return CommandResult(
                id=command.id,
                device_id=command.device_id,
                command=command.command,
                status="error",
                error="DEVICE_NOT_FOUND",
                error_code="DEVICE_NOT_FOUND",
                execution_time_ms=0,
                timestamp=datetime.now()
            )
        try:
            result = await device.execute(command.command, command.params, command.timeout_ms)
            return CommandResult(
                id=command.id,
                device_id=command.device_id,
                command=command.command,
                status=result.get("status", "success"),
                output=result.get("output"),
                error=result.get("error"),
                execution_time_ms=0,
                timestamp=datetime.now()
            )
        except Exception as e:
            return CommandResult(
                id=command.id,
                device_id=command.device_id,
                command=command.command,
                status="error",
                error=str(e),
                error_code="COMMAND_FAILED",
                execution_time_ms=0,
                timestamp=datetime.now()
            )