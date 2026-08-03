import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from dashboard.backend.core.sse import connected_clients

router = APIRouter()

@router.get("/stream")
async def sse_stream(request: Request):
    """Server-Sent Events endpoint for real-time UI updates."""
    async def event_generator():
        q = asyncio.Queue()
        connected_clients.add(q)
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await q.get()
                yield f"data: {data}\n\n"
        finally:
            connected_clients.remove(q)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
