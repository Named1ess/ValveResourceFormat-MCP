# ValveResourceFormat MCP Server

A Model Context Protocol (MCP) server that enables AI tools like Cursor to interact with Valve's Source 2 resource formats.

## Features

- **File Inspection**: Load and inspect Source 2 resource files (`.vmdl`, `.vmat`, `.vtex`, etc.)
- **VPK Operations**: List and extract contents from VPK archives
- **Resource Decompilation**: Decompile supported resource files to human-readable formats
- **glTF Export**: Export 3D models to glTF/glb format for viewing in other tools
- **Texture Operations**: Decode and export textures in various formats

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Starting the MCP Server

```bash
python mcp_server.py
```

### Configuration for Cursor

Add the following to your Cursor settings or project configuration:

```json
{
  "mcpServers": {
    "vrf": {
      "command": "python",
      "args": ["path/to/mcp_server.py"],
      "env": {
        "VRF_CLI_PATH": "path/to/CLI.exe"
      }
    }
  }
}
```

## Available Tools

### Resource Operations

- `inspect_file`: Inspect a Source 2 resource file and return detailed information
- `list_vpk_contents`: List all files in a VPK archive
- `extract_vpk_file`: Extract a specific file from a VPK archive
- `decompile_resource`: Decompile a resource file to its raw format
- `export_gltf`: Export a 3D model to glTF format
- `extract_texture`: Extract a texture to an image file
- `list_resources`: List resources in a directory or VPK with optional filtering

### Game Path Management

- `set_game_path`: Set the path to a Source 2 game installation
- `list_game_paths`: List configured game paths

## Requirements

- Python 3.10+
- .NET 8.0+ (for running the VRF CLI)
- ValveResourceFormat CLI tool (built from this repository)

## Architecture

The MCP server wraps the ValveResourceFormat CLI tool and provides a JSON-RPC interface for AI tools to interact with Source 2 resources. It handles:

- Process spawning and communication
- Output parsing and formatting
- Error handling and reporting
- File management for exports
