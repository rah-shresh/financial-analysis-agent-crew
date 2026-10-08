"""
MCP Client (Phase 7)
 
Agents call `call_tool(name, arguments)` instead of importing yfinance /
feedparser / PyPortfolioOpt directly. Under the hood, this spawns
mcp_layer/server.py as a subprocess (once, the first time it's needed)
and talks to it over stdio using the real MCP protocol -- the exact same
mechanism Claude Desktop and other MCP-compatible applications use to
talk to MCP servers.
 
Why a background thread: LangGraph's agent nodes are plain synchronous
functions (per the existing graph design from earlier phases), but the
MCP SDK is async-only. Rather than rewriting every agent to be async
(a much bigger change than "wrap tools behind MCP," which is what
Phase 7 is actually supposed to be), a single background thread runs
one persistent asyncio event loop and one persistent connection to the
server subprocess. `call_tool()` is the plain synchronous function every
agent calls; underneath, it hands the request to that background loop
and blocks until the result comes back. The server subprocess is started
once and reused for the whole pipeline run, not re-spawned per call.
"""
 
import asyncio
import atexit
import json
import os
import sys
import threading
from contextlib import AsyncExitStack
 
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
 
SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "server.py")
 
 
class _MCPConnection:
    def __init__(self):
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self._ready = threading.Event()
        self._start_error: Exception | None = None
        self._lock = threading.Lock()
 
    def _thread_main(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect())
        except Exception as e:
            self._start_error = e
        finally:
            self._ready.set()
        self._loop.run_forever()
 
    async def _connect(self):
        self._exit_stack = AsyncExitStack()
        # The MCP SDK gives the subprocess only ~12 whitelisted env vars on Windows
        # by default; pass the full environment so it behaves like a normal process.
        server_params = StdioServerParameters(
            command=sys.executable, args=[SERVER_SCRIPT], env=dict(os.environ)
        )
        read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
        self._session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
 
    def ensure_started(self):
        with self._lock:
            if self._thread is not None:
                return
            self._thread = threading.Thread(target=self._thread_main, daemon=True, name="mcp-client-loop")
            self._thread.start()
        if not self._ready.wait(timeout=30):
            raise RuntimeError("Timed out starting the MCP server subprocess.")
        if self._start_error is not None:
            raise RuntimeError(f"Failed to start MCP connection: {self._start_error}")
 
    async def _call_tool_async(self, name: str, arguments: dict):
        result = await self._session.call_tool(name, arguments)
        if result.isError:
            # The tool raised an exception on the server side -- surface it
            # as a normal Python exception here, so agents' existing
            # try/except blocks (from earlier phases) keep working unchanged.
            error_text = "".join(
                block.text for block in result.content if hasattr(block, "text")
            )
            raise RuntimeError(error_text or "MCP tool call failed")
 
        # FastMCP tools that return a dict come back as a single text
        # content block containing JSON.
        text_parts = [block.text for block in result.content if hasattr(block, "text")]
        payload = "".join(text_parts)
        return json.loads(payload)
 
    def call_tool(self, name: str, arguments: dict, timeout: float = 120):
        self.ensure_started()
        future = asyncio.run_coroutine_threadsafe(self._call_tool_async(name, arguments), self._loop)
        try:
            return future.result(timeout=timeout)
        except Exception as e:
            # Some lower-level async/subprocess exceptions have an empty
            # str() (e.g. certain anyio internals), which is unhelpfully
            # blank to print. Always include the exception's type name so
            # there's something concrete to debug from.
            raise RuntimeError(
                f"MCP call_tool('{name}') failed: [{type(e).__name__}] {e}"
            ) from e
 
    def shutdown(self):
        if self._loop is None:
            return
 
        async def _close():
            if self._exit_stack is not None:
                await self._exit_stack.aclose()
 
        try:
            fut = asyncio.run_coroutine_threadsafe(_close(), self._loop)
            fut.result(timeout=10)
        except Exception:
            pass  # best-effort cleanup -- don't let shutdown issues crash the program
        self._loop.call_soon_threadsafe(self._loop.stop)
 
 
_connection = _MCPConnection()
atexit.register(_connection.shutdown)
 
 
def call_tool(name: str, arguments: dict | None = None, timeout: float = 120):
    """Public API agents use: call_tool("fetch_ohlcv", {"ticker": "TSLA"}).
    `timeout` (seconds) can be raised for tools with a slow first call."""
    return _connection.call_tool(name, arguments or {}, timeout=timeout)
 
