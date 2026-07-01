import sys
import asyncio


# Small wrapper to allow safe event loop policy in Windows
# Without this, runners will not work in async
def run_async(task):
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(task)
