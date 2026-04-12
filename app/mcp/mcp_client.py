"""
Lazy stdio MCP client: one subprocess and ClientSession are started on first
`call_tool` and run until the process exits. There is no graceful shutdown in v1
(see uvicorn --reload and orphan subprocess notes in project docs).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, cast

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.exceptions import McpError
from mcp.types import CallToolResult, TextContent

_logger = logging.getLogger(__name__)

_server_params: StdioServerParameters | None = None

_startup_lock = asyncio.Lock()
_worker_task: asyncio.Task[None] | None = None
_request_queue: asyncio.Queue[tuple[str, dict[str, Any], asyncio.Future[str]]] | None = None
_worker_boot: asyncio.Future[None] | None = None


def configure_stdio_server(params: StdioServerParameters) -> None:
    """Set the stdio server command/args. Must be called before the first `call_tool`."""
    global _server_params
    if _worker_task is not None:
        raise RuntimeError("cannot reconfigure MCP stdio server after connection started")
    _server_params = params


def _extract_text(result: CallToolResult) -> str:
    if result.isError:
        summary = _tool_error_summary(result)
        _logger.warning("MCP tool returned isError: %s", summary)
        raise RuntimeError("mcp tool failed")

    texts: list[str] = []
    for block in result.content:
        if isinstance(block, TextContent):
            texts.append(block.text)
        elif getattr(block, "type", None) == "text":
            texts.append(cast(Any, block).text)

    if texts:
        return "\n".join(texts)
    if result.structuredContent is not None:
        return json.dumps(result.structuredContent)
    return ""


def _tool_error_summary(result: CallToolResult) -> str:
    parts: list[str] = []
    for block in result.content:
        if isinstance(block, TextContent):
            parts.append(block.text[:200])
        elif getattr(block, "type", None) == "text":
            parts.append(cast(Any, block).text[:200])
    if parts:
        return " | ".join(parts)
    return "(no text content)"


async def _run_worker(boot: asyncio.Future[None]) -> None:
    params = _server_params
    assert params is not None
    assert _request_queue is not None

    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                if not boot.done():
                    boot.set_result(None)
                while True:
                    name, arguments, fut = await _request_queue.get()
                    try:
                        raw = await session.call_tool(
                            name, cast(dict[str, Any] | None, arguments)
                        )
                        text = _extract_text(raw)
                        if not fut.done():
                            fut.set_result(text)
                    except asyncio.CancelledError:
                        raise
                    except RuntimeError as e:
                        if str(e) != "mcp tool failed":
                            _logger.exception("unexpected RuntimeError from MCP tool path")
                        if not fut.done():
                            fut.set_exception(RuntimeError("mcp tool failed"))
                    except (McpError, OSError):
                        _logger.exception("MCP transport error during tools/call")
                        if not fut.done():
                            fut.set_exception(RuntimeError("mcp tool failed"))
                    except Exception:
                        _logger.exception("unexpected error during MCP tool call")
                        if not fut.done():
                            fut.set_exception(RuntimeError("mcp tool failed"))
    except Exception as e:
        _logger.exception("MCP worker failed")
        if not boot.done():
            boot.set_exception(e)


def _raise_if_worker_dead() -> None:
    if _worker_task is None or not _worker_task.done():
        return
    try:
        exc = _worker_task.exception()
    except asyncio.CancelledError:
        _logger.error("MCP worker was cancelled")
        raise RuntimeError("MCP worker has stopped") from None
    if exc is None:
        _logger.error("MCP worker task ended unexpectedly")
        raise RuntimeError("MCP worker has stopped")
    _logger.error("MCP worker task failed: %s", exc, exc_info=exc)
    raise RuntimeError("MCP worker has stopped") from exc


async def _ensure_worker() -> None:
    global _worker_task, _request_queue, _worker_boot

    if _server_params is None:
        raise RuntimeError(
            "MCP stdio server not configured; call configure_stdio_server(...) first"
        )

    async with _startup_lock:
        if _worker_task is None:
            loop = asyncio.get_running_loop()
            _worker_boot = loop.create_future()
            _request_queue = asyncio.Queue()
            _worker_task = asyncio.create_task(_run_worker(_worker_boot))

    assert _worker_boot is not None
    await _worker_boot
    _raise_if_worker_dead()


async def call_tool(
    name: str, arguments: dict[str, object] | None = None
) -> str:
    await _ensure_worker()
    _raise_if_worker_dead()
    assert _request_queue is not None

    loop = asyncio.get_running_loop()
    fut: asyncio.Future[str] = loop.create_future()
    args_any: dict[str, Any] = dict(arguments or {})

    await _request_queue.put((name, args_any, fut))
    try:
        return await fut
    except asyncio.CancelledError:
        if not fut.done():
            fut.cancel()
        raise
