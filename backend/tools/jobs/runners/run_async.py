import sys
import asyncio


# Small wrapper to allow save event loop policy in Windows
def run_async(task):
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(task)
