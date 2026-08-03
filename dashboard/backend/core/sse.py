import asyncio

# SSE Global State
connected_clients = set()
main_loop = None

def init_sse_state(loop):
    global main_loop
    main_loop = loop

def notify_clients(event_data: str):
    """Safely notifies all connected SSE clients from sync or async contexts."""
    if not main_loop:
        return
    for q in list(connected_clients):
        main_loop.call_soon_threadsafe(q.put_nowait, event_data)
