import asyncio

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        future = asyncio.ensure_future(coro)
        return future
    else:
        return asyncio.run(coro)
