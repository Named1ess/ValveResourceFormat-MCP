#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct test of VRF functionality without MCP protocol overhead.
Run this to test the CLI functionality directly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import VRFServer


async def main():
    print("=" * 60)
    print("ValveResourceFormat MCP Server - Direct Test")
    print("=" * 60)

    # Try environment variable first, then auto-find
    cli_path = os.environ.get("VRF_CLI_PATH")

    if not cli_path:
        # Auto-find CLI
        vrf = VRFServer()
        cli_path = vrf.cli_path
    else:
        vrf = VRFServer(cli_path)

    if not cli_path:
        print("\n[X] Error: CLI.exe not found!")
        print("\nPlease either:")
        print("  1. Build the CLI project: dotnet build CLI/CLI.csproj -c Release")
        print("  2. Or set VRF_CLI_PATH environment variable:")
        print("     Windows: $env:VRF_CLI_PATH='path\\to\\Source2Viewer-CLI.exe'")
        print("     Linux/Mac: export VRF_CLI_PATH=/path/to/Source2Viewer-CLI")
        return

    print(f"\n[OK] Found CLI at: {cli_path}")

    # Test 1: Get file info
    print("\n" + "-" * 40)
    print("Test 1: Get file info")
    print("-" * 40)

    test_file = "C:\\Windows\\System32\\notepad.exe"
    result = vrf.get_file_info(test_file)
    print(f"Testing with: {test_file}")
    print(f"Result: {result}")

    # Test 2: Show available CLI commands
    print("\n" + "-" * 40)
    print("Test 2: Check CLI help")
    print("-" * 40)

    returncode, stdout, stderr = vrf.run_cli(["--help"])
    if returncode == 0:
        print("CLI is working! Available commands:")
        lines = stdout.split('\n')[:30]
        for line in lines:
            print(f"  {line}")
    else:
        print(f"CLI error: {stderr}")

    print("\n" + "=" * 60)
    print("Direct tests completed!")
    print("=" * 60)
    print("""
Now you can use the MCP server!

To test MCP protocol (stdin/stdout JSON-RPC):

1. Set environment variable:
   Windows: $env:VRF_CLI_PATH='C:\\path\\to\\Source2Viewer-CLI.exe'
   Linux/Mac: export VRF_CLI_PATH=/path/to/Source2Viewer-CLI

2. Run the MCP server:
   python MCP/mcp_server.py

3. Send JSON-RPC requests via stdin, receive responses via stdout

For Cursor integration, use cursor.config.json as template.
""")


if __name__ == "__main__":
    asyncio.run(main())
