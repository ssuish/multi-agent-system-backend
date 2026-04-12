# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import logging
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import LongRunningFunctionTool
from google.genai import types

import os
import google.auth

from app.mcp import StdioServerParameters, call_tool, configure_stdio_server
from app.settings import get_settings

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

_logger = logging.getLogger(__name__)
_mcp_stdio_configured = False


async def call_mcp_tool(name: str, arguments_json: str) -> str:
    """Call a tool on the configured MCP server over stdio.

    Use when MCP is enabled and you need to invoke a tool provided by that server.

    Args:
        name: Tool name as advertised by the MCP server (tools/list).
        arguments_json: JSON object string for tool arguments; use "{}" or an empty string when there are none.

    Returns:
        Text content from the tool result, or a short status or error message.
    """
    global _mcp_stdio_configured

    settings = get_settings()
    if not settings.mcp_enabled:
        return "MCP disabled"

    if not _mcp_stdio_configured:
        raw_cmd = settings.mcp_server_command
        if not raw_cmd or not raw_cmd.strip():
            return "MCP is enabled but MCP_SERVER_COMMAND is not configured."
        try:
            parts = json.loads(raw_cmd)
        except json.JSONDecodeError as e:
            return f"MCP_SERVER_COMMAND is not valid JSON: {e}"
        if not isinstance(parts, list) or len(parts) < 1:
            return "MCP_SERVER_COMMAND must be a non-empty JSON array."
        if not all(isinstance(p, str) for p in parts):
            return "MCP_SERVER_COMMAND entries must be strings."
        configure_stdio_server(
            StdioServerParameters(command=parts[0], args=parts[1:])
        )
        _mcp_stdio_configured = True

    payload = (arguments_json or "").strip()
    if not payload:
        args_dict: dict[str, object] = {}
    else:
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as e:
            return f"arguments_json is not valid JSON: {e}"
        if not isinstance(parsed, dict):
            return "arguments_json must be a JSON object, not an array or primitive."
        args_dict = parsed

    try:
        return await call_tool(name, args_dict)
    except RuntimeError as e:
        _logger.exception("MCP call_tool failed: %s", e)
        return "MCP call failed; check logs and MCP server configuration."


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def request_user_input(message: str) -> dict:
    """Request additional input from the user.

    Use this tool when you need more information from the user to complete a task.
    Calling this tool will pause execution until the user responds.

    Args:
        message: The question or clarification request to show the user.
    """
    return {"status": "pending", "message": message}


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="An agent that can provide information about the weather and time.",
    instruction="You are a helpful AI assistant designed to provide accurate and useful information.",
    tools=[
        get_weather,
        get_current_time,
        call_mcp_tool,
        LongRunningFunctionTool(func=request_user_input),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
