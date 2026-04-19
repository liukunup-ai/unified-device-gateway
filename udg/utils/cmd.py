import asyncio
from typing import Optional, NamedTuple, Union
from dataclasses import dataclass


class CmdResult(NamedTuple):
    code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.code == 0


@dataclass
class CmdResponse:
    status: str
    output: Optional[str] = None
    err_msg: Optional[str] = None

    @staticmethod
    def success(output: str = "") -> "CmdResponse":
        return CmdResponse(status="success", output=output)

    @staticmethod
    def error(error: str, output: Optional[str] = None) -> "CmdResponse":
        return CmdResponse(status="error", output=output, err_msg=error)

    @staticmethod
    def from_result(result: CmdResult) -> "CmdResponse":
        if result.code != 0:
            return CmdResponse.error(result.stderr, result.stdout)
        return CmdResponse.success(result.stdout)

    def to_dict(self) -> dict:
        return {"status": self.status, "output": self.output, "error": self.err_msg}


class CmdRunner:
    def __init__(self, *prefix: str):
        self.prefix = list(prefix)

    async def run(
        self,
        *args: str,
        timeout: Optional[float] = None,
    ) -> CmdResult:
        cmd = self.prefix + list(args)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            if timeout:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
            else:
                stdout, stderr = await proc.communicate()
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise
        return CmdResult(proc.returncode or 0, stdout.decode(), stderr.decode())

    async def exec(
        self,
        *args: str,
        timeout: Optional[float] = None,
    ) -> CmdResponse:
        result = await self.run(*args, timeout=timeout)
        return CmdResponse.from_result(result)

    async def check(
        self,
        *args: str,
        timeout: Optional[float] = None,
    ) -> CmdResponse:
        result = await self.run(*args, timeout=timeout)
        if result.code != 0:
            return CmdResponse.error(result.stderr, result.stdout)
        return CmdResponse.success(result.stdout)

    async def start(
        self,
        *args: str,
    ) -> asyncio.subprocess.Process:
        cmd = self.prefix + list(args)
        return await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    def with_args(self, *extra: str) -> "CmdRunner":
        return CmdRunner(*self.prefix, *extra)


