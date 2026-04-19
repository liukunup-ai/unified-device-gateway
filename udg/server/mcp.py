from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Request
from sse_starlette.sse import EventSourceResponse

app = FastAPI()


@app.get("/mcp")
async def mcp_endpoint(request: Request, authorization: Optional[str] = Header(None)):
    async def event_generator():
        yield {"event": "message", "data": '{"tools": []}'}
    return EventSourceResponse(event_generator())