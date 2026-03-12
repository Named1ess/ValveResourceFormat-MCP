"""
ValveResourceFormat MCP Server

A Model Context Protocol (MCP) server that enables AI tools like Cursor
to interact with Valve's Source 2 resource formats.
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional
import argparse


class VRFServer:
    """Wrapper for ValveResourceFormat CLI operations."""

    def __init__(self, cli_path: Optional[str] = None):
        """
        Initialize the VRF server.

        Args:
            cli_path: Path to the VRF CLI executable. If not provided,
                     looks for CLI.exe in common locations.
        """
        if cli_path:
            self.cli_path = cli_path
        else:
            # Try to find CLI.exe in common locations
            self.cli_path = self._find_cli()

        if not self.cli_path or not Path(self.cli_path).exists():
            raise FileNotFoundError(
                f"VRF CLI not found at: {cli_path or 'default locations'}. "
                "Please build the CLI project or specify VRF_CLI_PATH environment variable."
            )

    def _find_cli(self) -> Optional[str]:
        """Find the VRF CLI executable."""
        # Check environment variable
        env_path = os.environ.get("VRF_CLI_PATH")
        if env_path and Path(env_path).exists():
            return env_path

        # Check relative to this file
        base_dir = Path(__file__).parent.parent
        possible_names = ["Source2Viewer-CLI.exe", "CLI.exe"]

        # Check directly in bin/Release or bin/Debug
        possible_base_dirs = [
            base_dir / "CLI" / "bin" / "Release",
            base_dir / "CLI" / "bin" / "Debug",
            base_dir / "CLI" / "bin" / "Release" / "net10.0" / "win-x64",
            base_dir / "CLI" / "bin" / "Debug" / "net10.0" / "win-x64",
            base_dir / "CLI" / "bin" / "Release" / "net9.0" / "win-x64",
            base_dir / "CLI" / "bin" / "Debug" / "net9.0" / "win-x64",
        ]

        for dir_path in possible_base_dirs:
            for name in possible_names:
                path = dir_path / name
                if path.exists():
                    return str(path)

        # Also check with runtime folder
        runtimes = ["win-x64", "linux-x64", "osx-x64", "any"]
        for runtime in runtimes:
            for name in possible_names:
                path = base_dir / "CLI" / "bin" / "Release" / "runtimes" / runtime / "native" / name
                if path.exists():
                    return str(path)

        # Check if CLI is in PATH
        try:
            for name in possible_names:
                result = subprocess.run(
                    ["where", name],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
        except Exception:
            pass

        return None

    def run_cli(self, args: list[str], timeout: int = 60) -> tuple[int, str, str]:
        """
        Run the VRF CLI with given arguments.

        Args:
            args: Command line arguments for CLI
            timeout: Timeout in seconds

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = [self.cli_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)

    def inspect_file(self, file_path: str) -> dict[str, Any]:
        """
        Inspect a Source 2 resource file.

        Args:
            file_path: Path to the resource file

        Returns:
            Dictionary containing file information
        """
        returncode, stdout, stderr = self.run_cli(["-i", file_path])

        if returncode != 0:
            return {
                "success": False,
                "error": stderr or "Failed to inspect file",
                "file": file_path
            }

        return {
            "success": True,
            "file": file_path,
            "output": stdout
        }

    def list_vpk(self, vpk_path: str, extension_filter: Optional[str] = None,
                 path_filter: Optional[str] = None) -> dict[str, Any]:
        """
        List contents of a VPK archive.

        Args:
            vpk_path: Path to the VPK file
            extension_filter: Optional extension filter (e.g., "vmdl,vmat")
            path_filter: Optional path filter (e.g., "models/")

        Returns:
            Dictionary containing VPK contents
        """
        args = ["-i", vpk_path, "--vpk_list"]

        if extension_filter:
            args.extend(["--vpk_extensions", extension_filter])

        if path_filter:
            args.extend(["--vpk_filepath", path_filter])

        returncode, stdout, stderr = self.run_cli(args)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr or "Failed to list VPK contents",
                "vpk": vpk_path
            }

        # Parse the output into a structured format
        files = []
        for line in stdout.strip().split('\n'):
            if line and not line.startswith(' '):
                files.append(line)

        return {
            "success": True,
            "vpk": vpk_path,
            "files": files,
            "file_count": len(files)
        }

    def decompile(self, input_path: str, output_path: Optional[str] = None) -> dict[str, Any]:
        """
        Decompile a resource file.

        Args:
            input_path: Path to the input file
            output_path: Optional output path

        Returns:
            Dictionary containing decompilation result
        """
        args = ["-i", input_path, "--decompile"]

        if output_path:
            args.extend(["-o", output_path])

        returncode, stdout, stderr = self.run_cli(args, timeout=120)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr or "Failed to decompile file",
                "input": input_path
            }

        return {
            "success": True,
            "input": input_path,
            "output": output_path or stdout,
            "output_path": output_path
        }

    def export_gltf(self, model_path: str, output_path: str,
                    include_animations: bool = True,
                    include_materials: bool = True) -> dict[str, Any]:
        """
        Export a 3D model to glTF format.

        Args:
            model_path: Path to the model file (.vmdl)
            output_path: Path for the output glTF/glb file
            include_animations: Whether to include animations
            include_materials: Whether to include materials

        Returns:
            Dictionary containing export result
        """
        args = [
            "-i", model_path,
            "--gltf_export_format", "glb",
            "-o", output_path
        ]

        if include_animations:
            args.append("--gltf_export_animations")

        if include_materials:
            args.append("--gltf_export_materials")

        returncode, stdout, stderr = self.run_cli(args, timeout=180)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr or "Failed to export glTF",
                "input": model_path
            }

        return {
            "success": True,
            "input": model_path,
            "output": output_path,
            "format": "glb"
        }

    def extract_texture(self, texture_path: str, output_path: str,
                        decode_flags: str = "auto") -> dict[str, Any]:
        """
        Extract a texture to an image file.

        Args:
            texture_path: Path to the texture file (.vtex)
            output_path: Path for the output image file
            decode_flags: Decode flags (none, auto, focused)

        Returns:
            Dictionary containing extraction result
        """
        args = [
            "-i", texture_path,
            "--decompile",
            "--texture_decode_flags", decode_flags,
            "-o", output_path
        ]

        returncode, stdout, stderr = self.run_cli(args, timeout=120)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr or "Failed to extract texture",
                "input": texture_path
            }

        return {
            "success": True,
            "input": texture_path,
            "output": output_path
        }

    def get_file_info(self, file_path: str) -> dict[str, Any]:
        """
        Get basic file information (size, type, etc.).

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing file information
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": "File not found",
                "file": file_path
            }

        # Get file extension
        ext = path.suffix.lower()

        # Get file size
        size = path.stat().st_size

        return {
            "success": True,
            "file": file_path,
            "name": path.name,
            "extension": ext,
            "size": size,
            "size_formatted": self._format_size(size)
        }

    def _format_size(self, size: int) -> str:
        """Format byte size to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"


class MCPServer:
    """MCP Server implementation for ValveResourceFormat."""

    def __init__(self, cli_path: Optional[str] = None):
        self.vrf = VRFServer(cli_path)
        self.tools = self._get_tools()

    def _get_tools(self) -> list[dict[str, Any]]:
        """Define the available MCP tools."""
        return [
            {
                "name": "inspect_file",
                "description": "Inspect a Source 2 resource file and return detailed information about its structure, blocks, and data.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the resource file to inspect"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "list_vpk_contents",
                "description": "List all files in a VPK (Valve Package) archive, with optional filtering by extension or path.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vpk_path": {
                            "type": "string",
                            "description": "Path to the VPK file"
                        },
                        "extension_filter": {
                            "type": "string",
                            "description": "Comma-separated list of extensions to filter (e.g., 'vmdl,vmat')"
                        },
                        "path_filter": {
                            "type": "string",
                            "description": "Path prefix to filter (e.g., 'models/')"
                        }
                    },
                    "required": ["vpk_path"]
                }
            },
            {
                "name": "decompile_resource",
                "description": "Decompile a Source 2 resource file to its raw, human-readable format.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input_path": {
                            "type": "string",
                            "description": "Path to the resource file to decompile"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Optional output path for the decompiled file"
                        }
                    },
                    "required": ["input_path"]
                }
            },
            {
                "name": "export_gltf",
                "description": "Export a 3D model (.vmdl) to glTF/glb format for viewing in other tools.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "model_path": {
                            "type": "string",
                            "description": "Path to the model file (.vmdl)"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path for the output glTF/glb file"
                        },
                        "include_animations": {
                            "type": "boolean",
                            "description": "Whether to include animations in the export",
                            "default": True
                        },
                        "include_materials": {
                            "type": "boolean",
                            "description": "Whether to include materials in the export",
                            "default": True
                        }
                    },
                    "required": ["model_path", "output_path"]
                }
            },
            {
                "name": "extract_texture",
                "description": "Extract a texture (.vtex) to an image file (PNG/TGA).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "texture_path": {
                            "type": "string",
                            "description": "Path to the texture file (.vtex)"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path for the output image file"
                        },
                        "decode_flags": {
                            "type": "string",
                            "description": "Decode flags: 'none', 'auto', or 'focused'",
                            "default": "auto"
                        }
                    },
                    "required": ["texture_path", "output_path"]
                }
            },
            {
                "name": "get_file_info",
                "description": "Get basic information about a file (size, type, extension).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "list_directory_resources",
                "description": "List all Source 2 resource files in a directory, with optional filtering.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Path to the directory to scan"
                        },
                        "extension_filter": {
                            "type": "string",
                            "description": "Comma-separated list of extensions to include"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to scan subdirectories recursively",
                            "default": False
                        }
                    },
                    "required": ["directory"]
                }
            }
        ]

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle an incoming MCP request."""
        method = request.get("method")
        request_id = request.get("id")

        # Handle initialize request (required by MCP protocol)
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "vrf-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": self.tools}
            }
        elif method == "tools/call":
            tool_name = request.get("name")
            tool_args = request.get("arguments", {})

            result = await self._call_tool(tool_name, tool_args)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    async def _call_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Call a specific tool with the given arguments."""
        loop = asyncio.get_event_loop()

        if tool_name == "inspect_file":
            return await loop.run_in_executor(None, self.vrf.inspect_file, args["file_path"])

        elif tool_name == "list_vpk_contents":
            return await loop.run_in_executor(
                None,
                self.vrf.list_vpk,
                args["vpk_path"],
                args.get("extension_filter"),
                args.get("path_filter")
            )

        elif tool_name == "decompile_resource":
            return await loop.run_in_executor(
                None,
                self.vrf.decompile,
                args["input_path"],
                args.get("output_path")
            )

        elif tool_name == "export_gltf":
            return await loop.run_in_executor(
                None,
                self.vrf.export_gltf,
                args["model_path"],
                args["output_path"],
                args.get("include_animations", True),
                args.get("include_materials", True)
            )

        elif tool_name == "extract_texture":
            return await loop.run_in_executor(
                None,
                self.vrf.extract_texture,
                args["texture_path"],
                args["output_path"],
                args.get("decode_flags", "auto")
            )

        elif tool_name == "get_file_info":
            return await loop.run_in_executor(None, self.vrf.get_file_info, args["file_path"])

        elif tool_name == "list_directory_resources":
            return await loop.run_in_executor(
                None,
                self._list_directory_resources,
                args["directory"],
                args.get("extension_filter"),
                args.get("recursive", False)
            )

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def _list_directory_resources(self, directory: str,
                                   extension_filter: Optional[str] = None,
                                   recursive: bool = False) -> dict[str, Any]:
        """List resource files in a directory."""
        path = Path(directory)

        if not path.exists() or not path.is_dir():
            return {
                "success": False,
                "error": "Directory not found",
                "directory": directory
            }

        # Default Source 2 extensions
        if extension_filter:
            extensions = [f".{ext.strip('.')}" for ext in extension_filter.split(",")]
        else:
            extensions = [
                ".vmdl", ".vmat", ".vtex", ".vani", ".vsndevts",
                ".vpcf", ".vmap", ".vrad", ".vrml", ".vrml_c",
                ".vbsp", ".vcd", ".vpk"
            ]

        files = []
        pattern = "**/*" if recursive else "*"

        for ext in extensions:
            files.extend(path.glob(f"{pattern}{ext}"))

        # Also look for compiled versions
        compiled_extensions = [f"{ext}_c" for ext in extensions]
        for ext in compiled_extensions:
            files.extend(path.glob(f"{pattern}{ext}"))

        # Get unique files and create list
        unique_files = sorted(set(f.relative_to(path) for f in files))

        return {
            "success": True,
            "directory": directory,
            "files": [str(f) for f in unique_files],
            "file_count": len(unique_files)
        }


async def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="ValveResourceFormat MCP Server")
    parser.add_argument(
        "--cli-path",
        type=str,
        help="Path to the VRF CLI executable"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port to listen on (for stdio mode, this is ignored)"
    )

    args = parser.parse_args()

    # Try to get CLI path from environment variable
    cli_path = args.cli_path or os.environ.get("VRF_CLI_PATH")

    try:
        server = MCPServer(cli_path)
    except FileNotFoundError as e:
        print(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }), file=sys.stderr)
        sys.exit(1)

    # Read requests from stdin and write responses to stdout
    # This follows the MCP stdio protocol
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(response))
                sys.stdout.flush()
                continue

            response = await server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()

        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32000,
                    "message": f"Server error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())
