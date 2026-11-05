"""Windows: psycopg async requires SelectorEventLoop, not default ProactorEventLoop."""

import asyncio
import sys


def configure_asyncio_for_psycopg() -> None:
    """For entry points that let asyncio build the loop (scripts, pytest).

    Useless for uvicorn >= 0.36: it passes its own loop_factory to asyncio.run(),
    which bypasses the policy. Those runs need `--loop` + selector_loop_factory below.
    """
    if sys.platform != "win32":
        return
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


#: Pass to uvicorn as `--loop core.asyncio_platform:selector_loop_factory`
#: (or loop=... in uvicorn.run). A custom --loop target is handed straight to
#: asyncio.run(loop_factory=...), so it must build the loop, not return its class.
def selector_loop_factory() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop()
