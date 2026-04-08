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
            env_val = os.environ.get("VRF_CLI_PATH", "<not set>")
            raise FileNotFoundError(
                f"VRF CLI not found. VRF_CLI_PATH='{env_val}'. "
                "Please set VRF_CLI_PATH environment variable to point to Source2Viewer-CLI.exe"
            )

    def _find_cli(self) -> Optional[str]:
        """Find the VRF CLI executable via VRF_CLI_PATH environment variable."""
        env_path = os.environ.get("VRF_CLI_PATH")
        if env_path and Path(env_path).exists():
            return env_path
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
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e) if str(e) else "Unknown error occurred"

    def inspect_file(self, file_path: str) -> dict[str, Any]:
        """
        Inspect a Source 2 resource file.

        Args:
            file_path: Path to the resource file. Can be a filesystem path
                      OR format 'vpk_path::internal_path' for files inside a VPK.

        Returns:
            Dictionary containing file information
        """
        if not file_path:
            return {
                "success": False,
                "error": "File path is empty",
                "file": ""
            }

        # Check if this is a VPK internal file request
        if "::" in file_path:
            parts = file_path.split("::", 1)
            vpk_path = parts[0] if len(parts) > 0 else ""
            vpk_file_path = parts[1] if len(parts) > 1 else ""
            if not vpk_path or not vpk_file_path:
                return {
                    "success": False,
                    "error": "Invalid VPK path format. Expected 'vpk_path::internal_path'",
                    "file": file_path
                }
            args = ["-i", vpk_path, "--vpk_filepath", vpk_file_path, "-a"]
        else:
            args = ["-i", file_path]

        returncode, stdout, stderr = self.run_cli(args)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr if stderr else "Failed to inspect file",
                "file": file_path
            }

        return {
            "success": True,
            "file": file_path,
            "output": stdout if stdout else ""
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
                "error": stderr if stderr else "Failed to list VPK contents",
                "vpk": vpk_path if vpk_path else "unknown"
            }

        # Parse the output into a structured format
        # VPK list output is: "path/to/file.ext CRC:xxxxxxxxxx size:xxxxx"
        files = []
        stdout_content = stdout if stdout else ""
        for line in stdout_content.strip().split('\n'):
            line = line.strip()
            if line:
                # Extract just the filepath (before " CRC:")
                parts = line.split(' CRC:')
                if parts and len(parts) > 0:
                    files.append(parts[0])

        return {
            "success": True,
            "vpk": vpk_path if vpk_path else "unknown",
            "files": files,
            "file_count": len(files)
        }

    def decompile(self, input_path: str, output_path: Optional[str] = None) -> dict[str, Any]:
        """
        Decompile a resource file.

        Args:
            input_path: Path to the input file or 'vpk_path::internal_path'
            output_path: Optional output path

        Returns:
            Dictionary containing decompilation result
        """
        if not input_path:
            return {
                "success": False,
                "error": "Input path is empty",
                "input": ""
            }

        # Handle VPK internal path format
        if "::" in input_path:
            parts = input_path.split("::", 1)
            vpk_path = parts[0] if len(parts) > 0 else ""
            internal_path = parts[1] if len(parts) > 1 else ""
            if not vpk_path or not internal_path:
                return {
                    "success": False,
                    "error": "Invalid VPK path format. Expected 'vpk_path::internal_path'",
                    "input": input_path
                }
            args = ["-i", vpk_path, "--vpk_filepath", internal_path, "--decompile"]
        else:
            args = ["-i", input_path, "--decompile"]

        if output_path:
            args.extend(["-o", output_path])

        returncode, stdout, stderr = self.run_cli(args, timeout=120)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr if stderr else "Failed to decompile file",
                "input": input_path if input_path else "unknown"
            }

        return {
            "success": True,
            "input": input_path if input_path else "unknown",
            "output": output_path if output_path else stdout if stdout else "",
            "output_path": output_path if output_path else ""
        }

    def export_gltf(self, model_path: str, output_path: str,
                    include_animations: bool = True,
                    include_materials: bool = True) -> dict[str, Any]:
        """
        Export a 3D model to glTF format.

        Args:
            model_path: Path to the model file (.vmdl) or 'vpk_path::internal_path'
            output_path: Path for the output glTF/glb file
            include_animations: Whether to include animations
            include_materials: Whether to include materials

        Returns:
            Dictionary containing export result
        """
        if not model_path:
            return {
                "success": False,
                "error": "Model path is empty",
                "input": ""
            }
        if not output_path:
            return {
                "success": False,
                "error": "Output path is empty",
                "input": model_path
            }

        # Handle VPK internal path format
        if "::" in model_path:
            parts = model_path.split("::", 1)
            vpk_path = parts[0] if len(parts) > 0 else ""
            internal_path = parts[1] if len(parts) > 1 else ""
            if not vpk_path or not internal_path:
                return {
                    "success": False,
                    "error": "Invalid VPK path format. Expected 'vpk_path::internal_path'",
                    "input": model_path
                }
            args = [
                "-i", vpk_path,
                "--vpk_filepath", internal_path,
                "-d",
                "--gltf_export_format", "glb",
                "-o", output_path
            ]
        else:
            args = [
                "-i", model_path,
                "-d",
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
                "error": stderr if stderr else "Failed to export glTF",
                "input": model_path if model_path else "unknown"
            }

        return {
            "success": True,
            "input": model_path if model_path else "unknown",
            "output": output_path if output_path else "",
            "format": "glb"
        }

    def extract_texture(self, texture_path: str, output_path: str,
                        decode_flags: str = "auto") -> dict[str, Any]:
        """
        Extract a texture to an image file.

        Args:
            texture_path: Path to the texture file (.vtex) or 'vpk_path::internal_path'
            output_path: Path for the output image file
            decode_flags: Decode flags (none, auto, focused)

        Returns:
            Dictionary containing extraction result
        """
        if not texture_path:
            return {
                "success": False,
                "error": "Texture path is empty",
                "input": ""
            }
        if not output_path:
            return {
                "success": False,
                "error": "Output path is empty",
                "input": texture_path
            }

        # Handle VPK internal path format
        if "::" in texture_path:
            parts = texture_path.split("::", 1)
            vpk_path = parts[0] if len(parts) > 0 else ""
            internal_path = parts[1] if len(parts) > 1 else ""
            if not vpk_path or not internal_path:
                return {
                    "success": False,
                    "error": "Invalid VPK path format. Expected 'vpk_path::internal_path'",
                    "input": texture_path
                }
            args = [
                "-i", vpk_path,
                "--vpk_filepath", internal_path,
                "--decompile",
                "--texture_decode_flags", decode_flags,
                "-o", output_path
            ]
        else:
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
                "error": stderr if stderr else "Failed to extract texture",
                "input": texture_path if texture_path else "unknown"
            }

        return {
            "success": True,
            "input": texture_path if texture_path else "unknown",
            "output": output_path if output_path else ""
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

        if not file_path:
            return {
                "success": False,
                "error": "File path is empty",
                "file": "unknown"
            }

        if not path.exists():
            return {
                "success": False,
                "error": "File not found",
                "file": file_path
            }

        # Get file extension
        ext = path.suffix.lower() if path.suffix else ""

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
        if size < 0:
            size = 0
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    def verify_vpk(self, vpk_path: str) -> dict[str, Any]:
        """
        Verify the integrity and signatures of a VPK archive.

        Args:
            vpk_path: Path to the VPK file

        Returns:
            Dictionary containing verification result
        """
        if not vpk_path:
            return {
                "success": False,
                "error": "VPK path is empty",
                "vpk": ""
            }

        args = ["-i", vpk_path, "--vpk_verify"]
        returncode, stdout, stderr = self.run_cli(args, timeout=120)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr if stderr else "Failed to verify VPK",
                "vpk": vpk_path
            }

        return {
            "success": True,
            "vpk": vpk_path,
            "output": stdout if stdout else ""
        }

    def collect_stats(self, input_path: str,
                      include_files: bool = False,
                      unique_deps: bool = False,
                      particles: bool = False,
                      vbib: bool = False) -> dict[str, Any]:
        """
        Collect statistics about resource files.

        Args:
            input_path: Path to file/folder/VPK or "steam" for all steam libraries
            include_files: Whether to print example file names
            unique_deps: Whether to collect unique dependencies
            particles: Whether to collect particle stats
            vbib: Whether to collect vertex attribute stats

        Returns:
            Dictionary containing statistics
        """
        if not input_path:
            return {
                "success": False,
                "error": "Input path is empty",
                "input": ""
            }

        args = ["-i", input_path, "--stats"]

        if include_files:
            args.append("--stats_print_files")
        if unique_deps:
            args.append("--stats_unique_deps")
        if particles:
            args.append("--stats_particles")
        if vbib:
            args.append("--stats_vbib")

        returncode, stdout, stderr = self.run_cli(args, timeout=300)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr if stderr else "Failed to collect stats",
                "input": input_path
            }

        return {
            "success": True,
            "input": input_path,
            "output": stdout if stdout else ""
        }

    def decompile_vpk(self, vpk_path: str, output_path: str,
                      extension_filter: Optional[str] = None,
                      path_filter: Optional[str] = None,
                      recursive: bool = False) -> dict[str, Any]:
        """
        Decompile all resources in a VPK archive.

        Args:
            vpk_path: Path to the VPK file
            output_path: Output directory for decompiled files
            extension_filter: Optional extension filter
            path_filter: Optional path filter
            recursive: Whether to recurse into nested VPKs

        Returns:
            Dictionary containing decompilation result
        """
        if not vpk_path:
            return {
                "success": False,
                "error": "VPK path is empty",
                "vpk": ""
            }
        if not output_path:
            return {
                "success": False,
                "error": "Output path is empty",
                "vpk": vpk_path if vpk_path else "unknown"
            }

        args = ["-i", vpk_path, "-o", output_path, "-d"]

        if extension_filter:
            args.extend(["--vpk_extensions", extension_filter])
        if path_filter:
            args.extend(["--vpk_filepath", path_filter])
        if recursive:
            args.append("--recursive_vpk")

        returncode, stdout, stderr = self.run_cli(args, timeout=600)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr if stderr else "Failed to decompile VPK",
                "vpk": vpk_path
            }

        return {
            "success": True,
            "vpk": vpk_path,
            "output_path": output_path,
            "output": stdout if stdout else ""
        }

    def export_gltf_advanced(self, model_path: str, output_path: str,
                             include_animations: bool = True,
                             include_materials: bool = True,
                             animation_list: Optional[str] = None,
                             mesh_list: Optional[str] = None,
                             textures_adapt: bool = False,
                             export_extras: bool = False,
                             vpk_path: Optional[str] = None) -> dict[str, Any]:
        """
        Export a 3D model to glTF format with advanced options.

        Args:
            model_path: Path to the model file (.vmdl)
            output_path: Path for the output glTF/glb file
            include_animations: Whether to include animations
            include_materials: Whether to include materials
            animation_list: Comma-separated animation names to include
            mesh_list: Comma-separated mesh names to include
            textures_adapt: Whether to perform glTF spec adaptations
            export_extras: Whether to export additional mesh properties
            vpk_path: VPK path if model_path is internal path

        Returns:
            Dictionary containing export result
        """
        if not model_path:
            return {
                "success": False,
                "error": "Model path is empty",
                "input": ""
            }
        if not output_path:
            return {
                "success": False,
                "error": "Output path is empty",
                "input": model_path
            }

        if vpk_path:
            args = ["-i", vpk_path, "--vpk_filepath", model_path, "-d"]
        else:
            args = ["-i", model_path, "-d"]

        args.extend([
            "--gltf_export_format", "glb",
            "-o", output_path
        ])

        if include_animations:
            args.append("--gltf_export_animations")
        if include_materials:
            args.append("--gltf_export_materials")
        if animation_list:
            args.extend(["--gltf_animation_list", animation_list])
        if mesh_list:
            args.extend(["--gltf_mesh_list", mesh_list])
        if textures_adapt:
            args.append("--gltf_textures_adapt")
        if export_extras:
            args.append("--gltf_export_extras")

        returncode, stdout, stderr = self.run_cli(args, timeout=180)

        if returncode != 0:
            return {
                "success": False,
                "error": stderr if stderr else "Failed to export glTF",
                "input": model_path
            }

        return {
            "success": True,
            "input": model_path,
            "output": output_path,
            "format": "glb"
        }


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
                "description": "Inspect a Source 2 resource file and return detailed information about its structure, blocks, and data. Use format 'vpk_path::internal_path' to inspect files inside a VPK archive.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the resource file. Can be a filesystem path OR format 'vpk_path::internal_path' for files inside a VPK (e.g., 'C:\\game\\pak01_dir.vpk::models/player.mdl')"
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
            },
            {
                "name": "verify_vpk",
                "description": "Verify the integrity and signatures of a VPK archive.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vpk_path": {
                            "type": "string",
                            "description": "Path to the VPK file"
                        }
                    },
                    "required": ["vpk_path"]
                }
            },
            {
                "name": "decompile_vpk",
                "description": "Decompile all resources in a VPK archive to a specified output directory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vpk_path": {
                            "type": "string",
                            "description": "Path to the VPK file"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Output directory for decompiled files"
                        },
                        "extension_filter": {
                            "type": "string",
                            "description": "Comma-separated list of extensions to filter"
                        },
                        "path_filter": {
                            "type": "string",
                            "description": "Path prefix filter"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to recurse into nested VPKs",
                            "default": False
                        }
                    },
                    "required": ["vpk_path", "output_path"]
                }
            },
            {
                "name": "collect_stats",
                "description": "Collect statistics about resource files. Use 'steam' as input to scan all Steam libraries.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input_path": {
                            "type": "string",
                            "description": "Path to file/folder/VPK, or 'steam' for all Steam libraries"
                        },
                        "include_files": {
                            "type": "boolean",
                            "description": "Print example file names for each stat",
                            "default": False
                        },
                        "unique_deps": {
                            "type": "boolean",
                            "description": "Collect all unique dependencies",
                            "default": False
                        },
                        "particles": {
                            "type": "boolean",
                            "description": "Collect particle operators, renderers, emitters, initializers",
                            "default": False
                        },
                        "vbib": {
                            "type": "boolean",
                            "description": "Collect vertex attribute stats",
                            "default": False
                        }
                    },
                    "required": ["input_path"]
                }
            },
            {
                "name": "export_gltf_advanced",
                "description": "Export a 3D model to glTF format with advanced options including animation/mesh filtering and VPK support.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "model_path": {
                            "type": "string",
                            "description": "Path to the model file (.vmdl) or internal path for VPK"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "Path for the output glTF/glb file"
                        },
                        "vpk_path": {
                            "type": "string",
                            "description": "VPK path if model_path is internal path"
                        },
                        "include_animations": {
                            "type": "boolean",
                            "description": "Whether to include animations",
                            "default": True
                        },
                        "include_materials": {
                            "type": "boolean",
                            "description": "Whether to include materials",
                            "default": True
                        },
                        "animation_list": {
                            "type": "string",
                            "description": "Comma-separated animation names to include (default all)"
                        },
                        "mesh_list": {
                            "type": "string",
                            "description": "Comma-separated mesh names to include (default all)"
                        },
                        "textures_adapt": {
                            "type": "boolean",
                            "description": "Perform glTF spec adaptations on textures",
                            "default": False
                        },
                        "export_extras": {
                            "type": "boolean",
                            "description": "Export additional mesh properties into glTF extras",
                            "default": False
                        }
                    },
                    "required": ["model_path", "output_path"]
                }
            }
        ]

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle an incoming MCP request."""
        method = request.get("method") if request else None
        request_id = request.get("id") if request else None

        if not method:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: method is missing"
                }
            }

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
                "result": {"tools": self.tools if self.tools else []}
            }
        elif method == "tools/call":
            params = request.get("params", {}) if request else {}
            tool_name = params.get("name") if params else None
            tool_args = params.get("arguments", {}) if params else {}

            if not tool_name:
                return {
                    "success": False,
                    "error": "Tool name is required"
                }

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
        args = args if args else {}

        if tool_name == "inspect_file":
            file_path = args.get("file_path") if args else None
            if not file_path:
                return {"success": False, "error": "file_path is required"}
            return await loop.run_in_executor(None, self.vrf.inspect_file, file_path)

        elif tool_name == "list_vpk_contents":
            vpk_path = args.get("vpk_path") if args else None
            if not vpk_path:
                return {"success": False, "error": "vpk_path is required"}
            return await loop.run_in_executor(
                None,
                self.vrf.list_vpk,
                vpk_path,
                args.get("extension_filter"),
                args.get("path_filter")
            )

        elif tool_name == "decompile_resource":
            input_path = args.get("input_path") if args else None
            if not input_path:
                return {"success": False, "error": "input_path is required"}
            return await loop.run_in_executor(
                None,
                self.vrf.decompile,
                input_path,
                args.get("output_path")
            )

        elif tool_name == "export_gltf":
            model_path = args.get("model_path") if args else None
            output_path = args.get("output_path") if args else None
            if not model_path:
                return {"success": False, "error": "model_path is required"}
            if not output_path:
                return {"success": False, "error": "output_path is required"}
            return await loop.run_in_executor(
                None,
                self.vrf.export_gltf,
                model_path,
                output_path,
                args.get("include_animations", True),
                args.get("include_materials", True)
            )

        elif tool_name == "extract_texture":
            texture_path = args.get("texture_path") if args else None
            output_path = args.get("output_path") if args else None
            if not texture_path:
                return {"success": False, "error": "texture_path is required"}
            if not output_path:
                return {"success": False, "error": "output_path is required"}
            return await loop.run_in_executor(
                None,
                self.vrf.extract_texture,
                texture_path,
                output_path,
                args.get("decode_flags", "auto")
            )

        elif tool_name == "get_file_info":
            file_path = args.get("file_path") if args else None
            if not file_path:
                return {"success": False, "error": "file_path is required"}
            return await loop.run_in_executor(None, self.vrf.get_file_info, file_path)

        elif tool_name == "list_directory_resources":
            directory = args.get("directory") if args else None
            if not directory:
                return {"success": False, "error": "directory is required"}
            return await loop.run_in_executor(
                None,
                self._list_directory_resources,
                directory,
                args.get("extension_filter"),
                args.get("recursive", False)
            )

        elif tool_name == "verify_vpk":
            vpk_path = args.get("vpk_path") if args else None
            if not vpk_path:
                return {"success": False, "error": "vpk_path is required"}
            return await loop.run_in_executor(None, self.vrf.verify_vpk, vpk_path)

        elif tool_name == "decompile_vpk":
            vpk_path = args.get("vpk_path") if args else None
            output_path = args.get("output_path") if args else None
            if not vpk_path:
                return {"success": False, "error": "vpk_path is required"}
            if not output_path:
                return {"success": False, "error": "output_path is required"}
            return await loop.run_in_executor(
                None,
                self.vrf.decompile_vpk,
                vpk_path,
                output_path,
                args.get("extension_filter"),
                args.get("path_filter"),
                args.get("recursive", False)
            )

        elif tool_name == "collect_stats":
            input_path = args.get("input_path") if args else None
            if not input_path:
                return {"success": False, "error": "input_path is required"}
            return await loop.run_in_executor(
                None,
                self.vrf.collect_stats,
                input_path,
                args.get("include_files", False),
                args.get("unique_deps", False),
                args.get("particles", False),
                args.get("vbib", False)
            )

        elif tool_name == "export_gltf_advanced":
            model_path = args.get("model_path") if args else None
            output_path = args.get("output_path") if args else None
            if not model_path:
                return {"success": False, "error": "model_path is required"}
            if not output_path:
                return {"success": False, "error": "output_path is required"}
            return await loop.run_in_executor(
                None,
                self.vrf.export_gltf_advanced,
                model_path,
                output_path,
                args.get("include_animations", True),
                args.get("include_materials", True),
                args.get("animation_list"),
                args.get("mesh_list"),
                args.get("textures_adapt", False),
                args.get("export_extras", False),
                args.get("vpk_path")
            )

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def _list_directory_resources(self, directory: str,
                                   extension_filter: Optional[str] = None,
                                   recursive: bool = False) -> dict[str, Any]:
        """List resource files in a directory."""
        if not directory:
            return {
                "success": False,
                "error": "Directory path is empty",
                "directory": ""
            }

        path = Path(directory)

        if not path.exists() or not path.is_dir():
            return {
                "success": False,
                "error": "Directory not found",
                "directory": directory if directory else "unknown"
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
            for f in path.glob(f"{pattern}{ext}"):
                if f.is_file():
                    files.append(f)

        # Also look for compiled versions (e.g., .vmdl_c)
        # Strip any existing _c suffix before adding to avoid .vmdl_c_c
        compiled_extensions = [f".{ext.strip('.').rstrip('_c')}_c" for ext in extensions]
        for ext in compiled_extensions:
            for f in path.glob(f"{pattern}{ext}"):
                if f.is_file():
                    files.append(f)

        # Get unique files and create list
        unique_files = sorted(set(f.relative_to(path) for f in files))

        return {
            "success": True,
            "directory": directory if directory else "unknown",
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
        error_msg = str(e) if str(e) else "VRF CLI executable not found"
        print(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32000,
                "message": error_msg
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
            error_msg = str(e) if str(e) else "Unknown server error occurred"
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32000,
                    "message": f"Server error: {error_msg}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())
