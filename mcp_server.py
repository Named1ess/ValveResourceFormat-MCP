"""
ValveResourceFormat MCP Server

使用官方 MCP SDK 重构的服务器，提供与 Valve Source 2 资源格式交互的工具。
"""

import asyncio
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional, Any

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32000,
            "message": "MCP SDK not found. Please install: pip install mcp"
        }
    }), file=sys.stderr)
    sys.exit(1)


# 全局配置
VRF_CLI_PATH: Optional[str] = None


def get_cli_path() -> str:
    """获取 CLI 路径，从环境变量读取"""
    global VRF_CLI_PATH
    if VRF_CLI_PATH:
        return VRF_CLI_PATH

    env_path = os.environ.get("VRF_CLI_PATH")
    if env_path and Path(env_path).exists():
        VRF_CLI_PATH = env_path
        return env_path

    error_msg = (
        f"VRF CLI not found. VRF_CLI_PATH='{env_path or '<not set>'}'. "
        "Please set VRF_CLI_PATH environment variable to point to Source2Viewer-CLI.exe"
    )
    raise FileNotFoundError(error_msg)


def run_cli(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """执行 VRF CLI 命令"""
    cli_path = get_cli_path()
    cmd = [cli_path] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, "", str(e) if str(e) else "Unknown error occurred"


def parse_vpk_list(output: str) -> list[dict[str, Any]]:
    """解析 VPK 列表输出"""
    files = []
    for line in output.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        # 格式: "path/to/file.ext CRC:xxxxxxxxxx size:xxxxx"
        parts = line.split(' CRC:')
        if parts:
            path = parts[0]
            size = 0
            crc = "0000000000"
            if len(parts) > 1:
                crc_part = parts[1]
                crc_size_parts = crc_part.split(' size:')
                if crc_size_parts:
                    crc = crc_size_parts[0]
                    if len(crc_size_parts) > 1:
                        try:
                            size = int(crc_size_parts[1])
                        except ValueError:
                            pass
            files.append({
                "path": path,
                "crc": crc,
                "size": size
            })
    return files


# ============================================================
# 工具定义
# ============================================================

def create_tools() -> list[Tool]:
    """创建 MCP 工具列表"""
    return [
        Tool(
            name="get_file_info",
            description="获取文件的基本信息（大小、类型、扩展名）",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="list_vpk_contents",
            description="列出 VPK 归档中的所有文件，支持按扩展名或路径过滤",
            inputSchema={
                "type": "object",
                "properties": {
                    "vpk_path": {
                        "type": "string",
                        "description": "VPK 文件路径"
                    },
                    "extension_filter": {
                        "type": "string",
                        "description": "逗号分隔的扩展名列表（如 'vmdl,vmat'）"
                    },
                    "path_filter": {
                        "type": "string",
                        "description": "路径前缀过滤（如 'models/'）"
                    }
                },
                "required": ["vpk_path"]
            }
        ),
        Tool(
            name="inspect_file",
            description="检查 Source 2 资源文件的结构、块和数据。VPK 内部文件请使用 'vpk_path::internal_path' 格式",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "资源文件路径，可以是文件系统路径或 'vpk_path::internal_path' 格式"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="decompile_resource",
            description="将 Source 2 资源文件反编译为可读的原始格式",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "要反编译的资源文件路径"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "可选的输出路径"
                    }
                },
                "required": ["input_path"]
            }
        ),
        Tool(
            name="export_gltf",
            description="将 3D 模型（.vmdl）导出为 glTF/glb 格式以便在其他工具中查看",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_path": {
                        "type": "string",
                        "description": "模型文件路径（.vmdl）"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "输出 glTF/glb 文件路径"
                    },
                    "include_animations": {
                        "type": "boolean",
                        "description": "是否在导出中包含动画",
                        "default": True
                    },
                    "include_materials": {
                        "type": "boolean",
                        "description": "是否在导出中包含材质",
                        "default": True
                    }
                },
                "required": ["model_path", "output_path"]
            }
        ),
        Tool(
            name="export_gltf_advanced",
            description="高级 glTF 导出，支持动画/网格过滤和 VPK 支持",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_path": {
                        "type": "string",
                        "description": "模型文件路径（.vmdl）或 VPK 内部路径"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "输出 glTF/glb 文件路径"
                    },
                    "vpk_path": {
                        "type": "string",
                        "description": "如果 model_path 是内部路径，则指定 VPK 路径"
                    },
                    "include_animations": {
                        "type": "boolean",
                        "description": "是否包含动画",
                        "default": True
                    },
                    "include_materials": {
                        "type": "boolean",
                        "description": "是否包含材质",
                        "default": True
                    },
                    "animation_list": {
                        "type": "string",
                        "description": "逗号分隔的要包含的动画名称列表"
                    },
                    "mesh_list": {
                        "type": "string",
                        "description": "逗号分隔的要包含的网格名称列表"
                    },
                    "textures_adapt": {
                        "type": "boolean",
                        "description": "对纹理执行 glTF 规范适配",
                        "default": False
                    },
                    "export_extras": {
                        "type": "boolean",
                        "description": "将额外的网格属性导出到 glTF extras",
                        "default": False
                    }
                },
                "required": ["model_path", "output_path"]
            }
        ),
        Tool(
            name="extract_texture",
            description="将纹理（.vtex）提取为图像文件（PNG/TGA）",
            inputSchema={
                "type": "object",
                "properties": {
                    "texture_path": {
                        "type": "string",
                        "description": "纹理文件路径（.vtex）"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "输出图像文件路径"
                    },
                    "decode_flags": {
                        "type": "string",
                        "description": "解码标志：'none'、'auto' 或 'focused'",
                        "default": "auto"
                    }
                },
                "required": ["texture_path", "output_path"]
            }
        ),
        Tool(
            name="list_directory_resources",
            description="列出目录中的所有 Source 2 资源文件，支持可选过滤",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "要扫描的目录路径"
                    },
                    "extension_filter": {
                        "type": "string",
                        "description": "逗号分隔的要包含的扩展名列表"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归扫描子目录",
                        "default": False
                    }
                },
                "required": ["directory"]
            }
        ),
        Tool(
            name="verify_vpk",
            description="验证 VPK 归档的完整性和签名",
            inputSchema={
                "type": "object",
                "properties": {
                    "vpk_path": {
                        "type": "string",
                        "description": "VPK 文件路径"
                    }
                },
                "required": ["vpk_path"]
            }
        ),
        Tool(
            name="decompile_vpk",
            description="将 VPK 归档中的所有资源反编译到指定输出目录",
            inputSchema={
                "type": "object",
                "properties": {
                    "vpk_path": {
                        "type": "string",
                        "description": "VPK 文件路径"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "反编译文件的输出目录"
                    },
                    "extension_filter": {
                        "type": "string",
                        "description": "逗号分隔的扩展名过滤器"
                    },
                    "path_filter": {
                        "type": "string",
                        "description": "路径前缀过滤器"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归到嵌套的 VPK",
                        "default": False
                    }
                },
                "required": ["vpk_path", "output_path"]
            }
        ),
        Tool(
            name="collect_stats",
            description="收集资源文件的统计信息。使用 'steam' 作为输入来扫描所有 Steam 库",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "文件/文件夹/VPK 路径，或 'steam' 扫描所有 Steam 库"
                    },
                    "include_files": {
                        "type": "boolean",
                        "description": "打印每个统计的示例文件名",
                        "default": False
                    },
                    "unique_deps": {
                        "type": "boolean",
                        "description": "收集所有唯一依赖项",
                        "default": False
                    },
                    "particles": {
                        "type": "boolean",
                        "description": "收集粒子算子、渲染器、发射器、初始化器",
                        "default": False
                    },
                    "vbib": {
                        "type": "boolean",
                        "description": "收集顶点属性统计",
                        "default": False
                    },
                    "with_loader": {
                        "type": "boolean",
                        "description": "使用 GameFileLoader 加载依赖项",
                        "default": False
                    },
                    "gltf_test": {
                        "type": "boolean",
                        "description": "测试每个支持文件的 glTF 导出代码路径",
                        "default": False
                    }
                },
                "required": ["input_path"]
            }
        ),
        Tool(
            name="vpk_dir",
            description="显示 VPK 归档的详细目录信息，包括文件偏移、CRC、元数据大小等",
            inputSchema={
                "type": "object",
                "properties": {
                    "vpk_path": {
                        "type": "string",
                        "description": "VPK 文件路径"
                    }
                },
                "required": ["vpk_path"]
            }
        ),
        Tool(
            name="inspect_block",
            description="检查 Source 2 资源文件的结构、块和数据。支持 -a 打印所有块，-b 指定特定块",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "资源文件路径，支持 'vpk_path::internal_path' 格式"
                    },
                    "print_all": {
                        "type": "boolean",
                        "description": "打印每个资源块的全部内容 (-a)",
                        "default": False
                    },
                    "block_name": {
                        "type": "string",
                        "description": "只打印指定块，如 DATA, RERL, REDI, NTRO (-b)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="set_threads",
            description="设置处理文件时的线程数，用于加速批量处理",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_count": {
                        "type": "integer",
                        "description": "线程数量，1 表示单线程，大于 1 表示并发处理",
                        "default": 1
                    }
                }
            }
        ),
        Tool(
            name="vpk_cache",
            description="使用 VPK 缓存清单跟踪更新，只写入变更的文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "vpk_path": {
                        "type": "string",
                        "description": "VPK 文件路径"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "输出目录"
                    },
                    "use_cache": {
                        "type": "boolean",
                        "description": "是否使用缓存",
                        "default": True
                    }
                },
                "required": ["vpk_path", "output_path"]
            }
        ),
        Tool(
            name="gltf_export",
            description="将 3D 模型（.vmdl）导出为 glTF 或 glb 格式",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_path": {
                        "type": "string",
                        "description": "模型文件路径（.vmdl），支持 VPK 内部路径"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "输出 glTF/glb 文件路径"
                    },
                    "format": {
                        "type": "string",
                        "description": "导出格式，gltf 或 glb",
                        "default": "glb"
                    },
                    "include_animations": {
                        "type": "boolean",
                        "description": "是否包含动画",
                        "default": True
                    },
                    "include_materials": {
                        "type": "boolean",
                        "description": "是否包含材质",
                        "default": True
                    },
                    "animation_list": {
                        "type": "string",
                        "description": "逗号分隔的要包含的动画名称列表"
                    },
                    "mesh_list": {
                        "type": "string",
                        "description": "逗号分隔的要包含的网格名称列表"
                    },
                    "textures_adapt": {
                        "type": "boolean",
                        "description": "对纹理执行 glTF 规范适配",
                        "default": False
                    },
                    "export_extras": {
                        "type": "boolean",
                        "description": "将额外的网格属性导出到 glTF extras",
                        "default": False
                    },
                    "vpk_path": {
                        "type": "string",
                        "description": "如果 model_path 是内部路径，需要指定此 VPK 路径"
                    }
                },
                "required": ["model_path", "output_path"]
            }
        ),
        Tool(
            name="dump_unknown_keys",
            description="收集统计信息时保存所有未知实体键哈希到 unknown_keys.txt",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "文件/文件夹/VPK 路径，或 'steam' 扫描所有 Steam 库"
                    },
                    "include_files": {
                        "type": "boolean",
                        "description": "是否打印示例文件名",
                        "default": False
                    }
                },
                "required": ["input_path"]
            }
        ),
        Tool(
            name="tools_asset_info",
            description="获取工具资源信息，支持简短模式只打印路径",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "资源文件路径，支持 'vpk_path::internal_path' 格式"
                    },
                    "short": {
                        "type": "boolean",
                        "description": "简短模式，只打印文件路径",
                        "default": False
                    }
                },
                "required": ["file_path"]
            }
        ),
    ]


# ============================================================
# 工具实现
# ============================================================

async def handle_get_file_info(args: dict) -> dict:
    """获取文件信息"""
    file_path = args.get("file_path")
    if not file_path:
        return {"success": False, "error": "file_path 是必填参数"}

    path = Path(file_path)
    if not path.exists():
        return {"success": False, "error": "文件不存在", "file": file_path}

    size = path.stat().st_size
    return {
        "success": True,
        "file": file_path,
        "name": path.name,
        "extension": path.suffix.lower(),
        "size": size,
        "size_formatted": _format_size(size)
    }


async def handle_list_vpk_contents(args: dict) -> dict:
    """列出 VPK 内容"""
    vpk_path = args.get("vpk_path")
    if not vpk_path:
        return {"success": False, "error": "vpk_path 是必填参数"}

    cli_args = ["-i", vpk_path, "--vpk_list"]

    extension_filter = args.get("extension_filter")
    if extension_filter:
        cli_args.extend(["--vpk_extensions", extension_filter])

    path_filter = args.get("path_filter")
    if path_filter:
        cli_args.extend(["--vpk_filepath", path_filter])

    returncode, stdout, stderr = await run_cli_async(cli_args)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法列出 VPK 内容",
            "vpk": vpk_path
        }

    files = parse_vpk_list(stdout)

    # 应用扩展名过滤（如果 CLI 没有支持）
    if extension_filter and not path_filter:
        exts = [f".{e.strip('.')}" for e in extension_filter.split(",")]
        files = [f for f in files if any(f["path"].endswith(e) for e in exts)]

    return {
        "success": True,
        "vpk": vpk_path,
        "files": [f["path"] for f in files],
        "file_count": len(files),
        "details": files
    }


async def handle_inspect_file(args: dict) -> dict:
    """检查资源文件"""
    file_path = args.get("file_path")
    if not file_path:
        return {"success": False, "error": "file_path 是必填参数"}

    # 处理 VPK 内部路径格式
    if "::" in file_path:
        parts = file_path.split("::", 1)
        vpk_path = parts[0]
        internal_path = parts[1] if len(parts) > 1 else ""
        cli_args = ["-i", vpk_path, "--vpk_filepath", internal_path, "-a"]
    else:
        cli_args = ["-i", file_path]

    returncode, stdout, stderr = await run_cli_async(cli_args)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法检查文件",
            "file": file_path
        }

    return {
        "success": True,
        "file": file_path,
        "output": stdout
    }


async def handle_decompile_resource(args: dict) -> dict:
    """反编译资源"""
    input_path = args.get("input_path")
    if not input_path:
        return {"success": False, "error": "input_path 是必填参数"}

    output_path = args.get("output_path")

    # 处理 VPK 内部路径格式
    if "::" in input_path:
        parts = input_path.split("::", 1)
        vpk_path = parts[0]
        internal_path = parts[1] if len(parts) > 1 else ""
        cli_args = ["-i", vpk_path, "--vpk_filepath", internal_path, "--decompile"]
    else:
        cli_args = ["-i", input_path, "--decompile"]

    if output_path:
        cli_args.extend(["-o", output_path])

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=120)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法反编译文件",
            "input": input_path
        }

    return {
        "success": True,
        "input": input_path,
        "output": output_path or stdout,
        "output_path": output_path or ""
    }


async def handle_export_gltf(args: dict) -> dict:
    """导出 glTF"""
    model_path = args.get("model_path")
    output_path = args.get("output_path")

    if not model_path:
        return {"success": False, "error": "model_path 是必填参数"}
    if not output_path:
        return {"success": False, "error": "output_path 是必填参数"}

    include_animations = args.get("include_animations", True)
    include_materials = args.get("include_materials", True)

    # 处理 VPK 内部路径格式
    if "::" in model_path:
        parts = model_path.split("::", 1)
        vpk_path = parts[0]
        internal_path = parts[1] if len(parts) > 1 else ""
        cli_args = [
            "-i", vpk_path,
            "--vpk_filepath", internal_path,
            "-d",
            "--gltf_export_format", "glb",
            "-o", output_path
        ]
    else:
        cli_args = [
            "-i", model_path,
            "-d",
            "--gltf_export_format", "glb",
            "-o", output_path
        ]

    if include_animations:
        cli_args.append("--gltf_export_animations")
    if include_materials:
        cli_args.append("--gltf_export_materials")

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=180)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法导出 glTF",
            "input": model_path
        }

    return {
        "success": True,
        "input": model_path,
        "output": output_path,
        "format": "glb"
    }


async def handle_export_gltf_advanced(args: dict) -> dict:
    """高级 glTF 导出"""
    model_path = args.get("model_path")
    output_path = args.get("output_path")

    if not model_path:
        return {"success": False, "error": "model_path 是必填参数"}
    if not output_path:
        return {"success": False, "error": "output_path 是必填参数"}

    include_animations = args.get("include_animations", True)
    include_materials = args.get("include_materials", True)
    animation_list = args.get("animation_list")
    mesh_list = args.get("mesh_list")
    textures_adapt = args.get("textures_adapt", False)
    export_extras = args.get("export_extras", False)
    vpk_path = args.get("vpk_path")
    format_type = args.get("format", "glb")

    # 处理 VPK 内部路径格式
    if "::" in model_path:
        parts = model_path.split("::", 1)
        actual_vpk_path = parts[0]
        internal_path = parts[1] if len(parts) > 1 else ""
        cli_args = ["-i", actual_vpk_path, "--vpk_filepath", internal_path, "-d"]
    elif vpk_path:
        cli_args = ["-i", vpk_path, "--vpk_filepath", model_path, "-d"]
    else:
        cli_args = ["-i", model_path, "-d"]

    cli_args.extend(["--gltf_export_format", format_type, "-o", output_path])

    if include_animations:
        cli_args.append("--gltf_export_animations")
    if include_materials:
        cli_args.append("--gltf_export_materials")
    if animation_list:
        cli_args.extend(["--gltf_animation_list", animation_list])
    if mesh_list:
        cli_args.extend(["--gltf_mesh_list", mesh_list])
    if textures_adapt:
        cli_args.append("--gltf_textures_adapt")
    if export_extras:
        cli_args.append("--gltf_export_extras")

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=180)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法导出 glTF",
            "input": model_path
        }

    return {
        "success": True,
        "input": model_path,
        "output": output_path,
        "format": "glb"
    }


async def handle_extract_texture(args: dict) -> dict:
    """提取纹理"""
    texture_path = args.get("texture_path")
    output_path = args.get("output_path")

    if not texture_path:
        return {"success": False, "error": "texture_path 是必填参数"}
    if not output_path:
        return {"success": False, "error": "output_path 是必填参数"}

    decode_flags = args.get("decode_flags", "auto")

    # 处理 VPK 内部路径格式
    if "::" in texture_path:
        parts = texture_path.split("::", 1)
        vpk_path = parts[0]
        internal_path = parts[1] if len(parts) > 1 else ""
        cli_args = [
            "-i", vpk_path,
            "--vpk_filepath", internal_path,
            "--decompile",
            "--texture_decode_flags", decode_flags,
            "-o", output_path
        ]
    else:
        cli_args = [
            "-i", texture_path,
            "--decompile",
            "--texture_decode_flags", decode_flags,
            "-o", output_path
        ]

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=120)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法提取纹理",
            "input": texture_path
        }

    return {
        "success": True,
        "input": texture_path,
        "output": output_path
    }


async def handle_list_directory_resources(args: dict) -> dict:
    """列出目录中的资源"""
    directory = args.get("directory")
    if not directory:
        return {"success": False, "error": "directory 是必填参数"}

    extension_filter = args.get("extension_filter")
    recursive = args.get("recursive", False)

    path = Path(directory)
    if not path.exists() or not path.is_dir():
        return {"success": False, "error": "目录不存在", "directory": directory}

    # 默认 Source 2 扩展名
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
                files.append(str(f))

    # 也查找编译版本
    compiled_extensions = [f".{ext.rstrip('_c')}_c" for ext in extensions]
    for ext in compiled_extensions:
        for f in path.glob(f"{pattern}{ext}"):
            if f.is_file():
                files.append(str(f))

    unique_files = sorted(set(files))

    return {
        "success": True,
        "directory": directory,
        "files": [str(Path(f).relative_to(path)) for f in unique_files],
        "file_count": len(unique_files)
    }


async def handle_verify_vpk(args: dict) -> dict:
    """验证 VPK"""
    vpk_path = args.get("vpk_path")
    if not vpk_path:
        return {"success": False, "error": "vpk_path 是必填参数"}

    cli_args = ["-i", vpk_path, "--vpk_verify"]

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=120)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法验证 VPK",
            "vpk": vpk_path
        }

    return {
        "success": True,
        "vpk": vpk_path,
        "output": stdout
    }


async def handle_decompile_vpk(args: dict) -> dict:
    """批量反编译 VPK"""
    vpk_path = args.get("vpk_path")
    output_path = args.get("output_path")

    if not vpk_path:
        return {"success": False, "error": "vpk_path 是必填参数"}
    if not output_path:
        return {"success": False, "error": "output_path 是必填参数"}

    extension_filter = args.get("extension_filter")
    path_filter = args.get("path_filter")
    recursive = args.get("recursive", False)

    cli_args = ["-i", vpk_path, "-o", output_path, "-d"]

    if extension_filter:
        cli_args.extend(["--vpk_extensions", extension_filter])
    if path_filter:
        cli_args.extend(["--vpk_filepath", path_filter])
    if recursive:
        cli_args.append("--recursive_vpk")

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=600)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法反编译 VPK",
            "vpk": vpk_path
        }

    return {
        "success": True,
        "vpk": vpk_path,
        "output_path": output_path,
        "output": stdout
    }


async def handle_collect_stats(args: dict) -> dict:
    """收集统计信息"""
    input_path = args.get("input_path")
    if not input_path:
        return {"success": False, "error": "input_path 是必填参数"}

    include_files = args.get("include_files", False)
    unique_deps = args.get("unique_deps", False)
    particles = args.get("particles", False)
    vbib = args.get("vbib", False)
    with_loader = args.get("with_loader", False)
    gltf_test = args.get("gltf_test", False)

    cli_args = ["-i", input_path, "--stats"]

    if include_files:
        cli_args.append("--stats_print_files")
    if unique_deps:
        cli_args.append("--stats_unique_deps")
    if particles:
        cli_args.append("--stats_particles")
    if vbib:
        cli_args.append("--stats_vbib")
    if with_loader:
        cli_args.append("--stats_with_loader")
    if gltf_test:
        cli_args.append("--gltf_test")

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=600)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法收集统计",
            "input": input_path
        }

    return {
        "success": True,
        "input": input_path,
        "output": stdout
    }


async def handle_vpk_dir(args: dict) -> dict:
    """显示 VPK 详细目录信息"""
    vpk_path = args.get("vpk_path")
    if not vpk_path:
        return {"success": False, "error": "vpk_path 是必填参数"}

    cli_args = ["-i", vpk_path, "--vpk_dir"]

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=120)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法获取 VPK 目录",
            "vpk": vpk_path
        }

    return {
        "success": True,
        "vpk": vpk_path,
        "output": stdout
    }


async def handle_inspect_block(args: dict) -> dict:
    """检查资源文件块"""
    file_path = args.get("file_path")
    if not file_path:
        return {"success": False, "error": "file_path 是必填参数"}

    print_all = args.get("print_all", False)
    block_name = args.get("block_name")

    # 处理 VPK 内部路径格式
    if "::" in file_path:
        parts = file_path.split("::", 1)
        vpk_path = parts[0]
        internal_path = parts[1] if len(parts) > 1 else ""
        cli_args = ["-i", vpk_path, "--vpk_filepath", internal_path]
    else:
        cli_args = ["-i", file_path]

    if print_all:
        cli_args.append("-a")
    elif block_name:
        cli_args.extend(["-b", block_name])

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=120)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法检查文件",
            "file": file_path
        }

    return {
        "success": True,
        "file": file_path,
        "output": stdout
    }


async def handle_set_threads(args: dict) -> dict:
    """设置线程数"""
    thread_count = args.get("thread_count", 1)

    if thread_count < 1:
        return {"success": False, "error": "线程数必须大于 0"}

    return {
        "success": True,
        "thread_count": thread_count,
        "message": f"线程数已设置为 {thread_count}"
    }


async def handle_vpk_cache(args: dict) -> dict:
    """VPK 缓存反编译"""
    vpk_path = args.get("vpk_path")
    output_path = args.get("output_path")

    if not vpk_path:
        return {"success": False, "error": "vpk_path 是必填参数"}
    if not output_path:
        return {"success": False, "error": "output_path 是必填参数"}

    use_cache = args.get("use_cache", True)

    cli_args = ["-i", vpk_path, "-o", output_path, "-d"]

    if use_cache:
        cli_args.append("--vpk_cache")

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=600)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法反编译 VPK",
            "vpk": vpk_path
        }

    return {
        "success": True,
        "vpk": vpk_path,
        "output_path": output_path,
        "output": stdout
    }


async def handle_gltf_export(args: dict) -> dict:
    """glTF/glb 导出"""
    model_path = args.get("model_path")
    output_path = args.get("output_path")

    if not model_path:
        return {"success": False, "error": "model_path 是必填参数"}
    if not output_path:
        return {"success": False, "error": "output_path 是必填参数"}

    format_type = args.get("format", "glb")
    include_animations = args.get("include_animations", True)
    include_materials = args.get("include_materials", True)
    animation_list = args.get("animation_list")
    mesh_list = args.get("mesh_list")
    textures_adapt = args.get("textures_adapt", False)
    export_extras = args.get("export_extras", False)
    vpk_path = args.get("vpk_path")

    # 处理 VPK 内部路径格式
    if "::" in model_path:
        parts = model_path.split("::", 1)
        actual_vpk_path = parts[0]
        internal_path = parts[1] if len(parts) > 1 else ""
        cli_args = ["-i", actual_vpk_path, "--vpk_filepath", internal_path, "-d"]
    elif vpk_path:
        cli_args = ["-i", vpk_path, "--vpk_filepath", model_path, "-d"]
    else:
        cli_args = ["-i", model_path, "-d"]

    cli_args.extend(["--gltf_export_format", format_type, "-o", output_path])

    if include_animations:
        cli_args.append("--gltf_export_animations")
    if include_materials:
        cli_args.append("--gltf_export_materials")
    if animation_list:
        cli_args.extend(["--gltf_animation_list", animation_list])
    if mesh_list:
        cli_args.extend(["--gltf_mesh_list", mesh_list])
    if textures_adapt:
        cli_args.append("--gltf_textures_adapt")
    if export_extras:
        cli_args.append("--gltf_export_extras")

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=180)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法导出 glTF",
            "input": model_path
        }

    return {
        "success": True,
        "input": model_path,
        "output": output_path,
        "format": format_type
    }


async def handle_dump_unknown_keys(args: dict) -> dict:
    """保存未知实体键哈希"""
    input_path = args.get("input_path")
    if not input_path:
        return {"success": False, "error": "input_path 是必填参数"}

    include_files = args.get("include_files", False)

    cli_args = ["-i", input_path, "--stats", "--dump_unknown_entity_keys"]

    if include_files:
        cli_args.append("--stats_print_files")

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=600)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法保存未知实体键",
            "input": input_path
        }

    return {
        "success": True,
        "input": input_path,
        "output": stdout
    }


async def handle_tools_asset_info(args: dict) -> dict:
    """工具资源信息"""
    file_path = args.get("file_path")
    if not file_path:
        return {"success": False, "error": "file_path 是必填参数"}

    short = args.get("short", False)

    # 处理 VPK 内部路径格式
    if "::" in file_path:
        parts = file_path.split("::", 1)
        vpk_path = parts[0]
        internal_path = parts[1] if len(parts) > 1 else ""
        cli_args = ["-i", vpk_path, "--vpk_filepath", internal_path]
    else:
        cli_args = ["-i", file_path]

    if short:
        cli_args.append("--tools_asset_info_short")

    returncode, stdout, stderr = await run_cli_async(cli_args, timeout=60)

    if returncode != 0:
        return {
            "success": False,
            "error": stderr or "无法获取工具资源信息",
            "file": file_path
        }

    return {
        "success": True,
        "file": file_path,
        "output": stdout
    }


# ============================================================
# 辅助函数
# ============================================================

def _format_size(size: int) -> str:
    """格式化字节大小为可读字符串"""
    if size < 0:
        size = 0
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


async def run_cli_async(args: list[str], timeout: int = 60) -> tuple[int, str, str]:
    """异步执行 CLI"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, run_cli, args, timeout)


# ============================================================
# MCP 服务器主程序
# ============================================================

async def main():
    """主入口点"""
    import asyncio

    # 检查 CLI 是否可用
    try:
        get_cli_path()
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

    server = Server("vrf-mcp-server", "1.1.0")
    tools = create_tools()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        handlers = {
            "get_file_info": handle_get_file_info,
            "list_vpk_contents": handle_list_vpk_contents,
            "inspect_file": handle_inspect_file,
            "decompile_resource": handle_decompile_resource,
            "export_gltf": handle_export_gltf,
            "export_gltf_advanced": handle_export_gltf_advanced,
            "extract_texture": handle_extract_texture,
            "list_directory_resources": handle_list_directory_resources,
            "verify_vpk": handle_verify_vpk,
            "decompile_vpk": handle_decompile_vpk,
            "collect_stats": handle_collect_stats,
            "vpk_dir": handle_vpk_dir,
            "inspect_block": handle_inspect_block,
            "set_threads": handle_set_threads,
            "vpk_cache": handle_vpk_cache,
            "gltf_export": handle_gltf_export,
            "dump_unknown_keys": handle_dump_unknown_keys,
            "tools_asset_info": handle_tools_asset_info,
        }

        handler = handlers.get(name)
        if not handler:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": f"未知工具: {name}"
            }))]

        result = await handler(arguments)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
