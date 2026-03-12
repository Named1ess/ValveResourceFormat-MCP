#!/usr/bin/env python3
"""
Simple test client for the VRF MCP server.

This script demonstrates how to use the MCP server programmatically.
"""

import asyncio
import json
import sys
import subprocess
from pathlib import Path


class VRFMCPClient:
    """Client for interacting with the VRF MCP server."""

    def __init__(self, server_script: str, cli_path: str = None):
        self.server_script = server_script
        self.cli_path = cli_path
        self.process = None

    async def start(self):
        """Start the MCP server process."""
        env = {}
        if self.cli_path:
            env["VRF_CLI_PATH"] = self.cli_path

        self.process = await asyncio.create_subprocess_exec(
            sys.executable,
            self.server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**dict(__import__("os").environ), **env}
        )

    async def stop(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()

    async def send_request(self, method: str, params: dict = None, request_id=1):
        """Send a JSON-RPC request to the server."""
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode())
        await self.process.stdin.drain()

        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode())

        return response

    async def list_tools(self):
        """List available tools."""
        response = await self.send_request("tools/list")
        return response.get("result", {}).get("tools", [])

    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a specific tool."""
        response = await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        return response.get("result", {})


async def main():
    """Test the MCP server with some basic operations."""
    # Get paths
    script_dir = Path(__file__).parent
    server_script = script_dir / "mcp_server.py"

    # Try to find CLI
    possible_cli = [
        script_dir.parent / "CLI" / "bin" / "Release" / "net10.0" / "win-x64" / "CLI.exe",
        script_dir.parent / "CLI" / "bin" / "Release" / "net9.0" / "win-x64" / "CLI.exe",
    ]

    cli_path = None
    for path in possible_cli:
        if path.exists():
            cli_path = str(path)
            break

    if not cli_path:
        print("Warning: CLI.exe not found. Set VRF_CLI_PATH environment variable.")
        print("Testing without CLI (some features will fail)...")

    # Create and start client
    client = VRFMCPClient(str(server_script), cli_path)

    try:
        await client.start()
        print("Server started. Waiting for initialization...")

        # Give the server a moment to start
        await asyncio.sleep(1)

        # List available tools
        print("\n=== Available Tools ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool['name']}: {tool['description'][:60]}...")

        print("\n=== Test Complete ===")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
