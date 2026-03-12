#!/usr/bin/env python3
"""
Example usage of the VRF MCP server tools.

This script demonstrates how to use the various tools available
through the MCP server to work with Source 2 resources.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


async def main():
    """Demonstrate MCP server capabilities."""
    from mcp_server import MCPServer, VRFServer

    # Initialize the VRF server
    # Try to find CLI.exe automatically
    cli_path = os.environ.get("VRF_CLI_PATH")

    if not cli_path:
        # Try common paths
        script_dir = Path(__file__).parent
        possible_paths = [
            script_dir.parent / "CLI" / "bin" / "Release" / "net10.0" / "win-x64" / "CLI.exe",
            script_dir.parent / "CLI" / "bin" / "Release" / "net9.0" / "win-x64" / "CLI.exe",
        ]
        for path in possible_paths:
            if path.exists():
                cli_path = str(path)
                break

    if not cli_path:
        print("Error: CLI.exe not found.")
        print("Please either:")
        print("  1. Set the VRF_CLI_PATH environment variable")
        print("  2. Build the CLI project from the ValveResourceFormat solution")
        return

    print(f"Using CLI at: {cli_path}")
    print("=" * 60)

    vrf = VRFServer(cli_path)
    mcp = MCPServer(cli_path)

    # Show available tools
    print("\nAvailable MCP Tools:")
    print("-" * 40)
    for tool in mcp.tools:
        print(f"  - {tool['name']}")
        print(f"    {tool['description'][:60]}...")
        print()

    # Example: Get file info (just showing the API structure)
    print("\n" + "=" * 60)
    print("Example: File Info Structure")
    print("-" * 40)

    # You can call these methods directly:
    # result = vrf.inspect_file("path/to/resource.vmdl")
    # result = vrf.list_vpk("path/to/pak01_dir.vpk")
    # result = vrf.export_gltf("model.vmdl", "output.glb")
    # result = vrf.extract_texture("texture.vtex", "output.png")

    print("""
# Example MCP Requests:

# 1. Inspect a resource file
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "inspect_file",
        "arguments": {
            "file_path": "models/player/tm_ctm_gsg9.vmdl"
        }
    }
}

# 2. List VPK contents
{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "list_vpk_contents",
        "arguments": {
            "vpk_path": "cs2/cs2_pak01_dir.vpk",
            "extension_filter": "vmdl,vmat",
            "path_filter": "models/"
        }
    }
}

# 3. Export model to glTF
{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "export_gltf",
        "arguments": {
            "model_path": "models/player/tm_ctm_gsg9.vmdl",
            "output_path": "output/tm_ctm_gsg9.glb",
            "include_animations": true,
            "include_materials": true
        }
    }
}

# 4. Decompile a resource
{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
        "name": "decompile_resource",
        "arguments": {
            "input_path": "materials/vgui/background_01.vmat",
            "output_path": "output/background_01.txt"
        }
    }
}
""")


if __name__ == "__main__":
    asyncio.run(main())
