from typing import Optional
from fastapi import APIRouter, Header, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter()


@router.get("/mcp")
async def mcp_endpoint(request: Request, authorization: Optional[str] = Header(None)):
    async def event_generator():
        yield {"event": "message", "data": '{"tools": []}'}
    return EventSourceResponse(event_generator())