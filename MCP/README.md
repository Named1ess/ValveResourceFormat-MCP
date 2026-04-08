# ValveResourceFormat MCP Server

一个让 AI 工具（如 Cursor）能够与 Valve Source 2 资源格式交互的 MCP（Model Context Protocol）服务器。

## 功能对照表

### CLI 原生功能 vs MCP 工具对照

| CLI 参数 | CLI 功能 | MCP 工具 | 说明 |
|----------|----------|----------|------|
| `-i <file>` | 检查文件 | `inspect_file` | 查看资源结构、块和数据 |
| `--vpk_list` | 列出 VPK 内容 | `list_vpk_contents` | 列出包内所有文件 |
| `--vpk_filepath <path>` | 读取 VPK 内文件 | `inspect_file` | 支持 `vpk::path` 格式 |
| `-d, --decompile` | 反编译资源 | `decompile_resource` | 转为可读格式 |
| `-i <vpk> -o <dir> -d` | 批量反编译 VPK | `decompile_vpk` | 解包整个 VPK |
| `--gltf_export_format glb` | 导出 glTF | `export_gltf` | 基础模型导出 |
| `--gltf_*` 高级选项 | glTF 高级导出 | `export_gltf_advanced` | 动画/网格过滤、VPK支持 |
| `--decompile` (texture) | 提取纹理 | `extract_texture` | 导出 PNG/TGA |
| `--vpk_verify` | 验证 VPK 完整性 | `verify_vpk` | 检查签名和哈希 |
| `--stats` | 统计分析 | `collect_stats` | 统计资源类型分布 |
| `--recursive` | 递归扫描目录 | `list_directory_resources` | 批量查找资源 |

### MCP 工具清单

| 工具 | 功能 | 主要参数 |
|------|------|----------|
| `inspect_file` | 检查资源文件结构 | `file_path`（支持 `vpk::path` 格式） |
| `list_vpk_contents` | 列出 VPK 内容 | `vpk_path`, `extension_filter`, `path_filter` |
| `decompile_resource` | 反编译单个资源 | `input_path`, `output_path` |
| `decompile_vpk` | 批量反编译 VPK | `vpk_path`, `output_path`, `extension_filter`, `recursive` |
| `export_gltf` | 导出 glTF 模型 | `model_path`, `output_path`, `include_animations`, `include_materials` |
| `export_gltf_advanced` | 高级 glTF 导出 | `model_path`, `vpk_path`, `animation_list`, `mesh_list` 等 |
| `extract_texture` | 提取纹理图片 | `texture_path`, `output_path`, `decode_flags` |
| `verify_vpk` | 验证 VPK 完整性 | `vpk_path` |
| `collect_stats` | 收集资源统计 | `input_path`, `include_files`, `unique_deps`, `particles`, `vbib` |
| `get_file_info` | 获取文件信息 | `file_path` |
| `list_directory_resources` | 列出目录资源 | `directory`, `extension_filter`, `recursive` |

## 安装

### 1. 安装 Python 依赖

```bash
cd MCP
pip install -r requirements.txt
```

### 2. 获取 VRF CLI

MCP 需要调用 ValveResourceFormat 的 CLI 工具。有两种方式：

**方式 A：使用预编译版本**

从 [ValveResourceFormat Releases](https://github.com/ValveResourceFormat/ValveResourceFormat/releases) 下载 CLI。

**方式 B：自行编译**

```bash
cd ValveResourceFormat
dotnet build CLI -c Release
# CLI.exe 将位于 CLI/bin/Release/net*/*/CLI.exe
```

### 3. 配置环境变量

```bash
# Windows
set VRF_CLI_PATH=C:\path\to\Source2Viewer-CLI.exe

# PowerShell
$env:VRF_CLI_PATH = "C:\path\to\Source2Viewer-CLI.exe"
```

## Cursor 配置

在 Cursor 设置中添加 MCP 服务器：

```json
{
  "mcpServers": {
    "vrf": {
      "command": "python",
      "args": ["C:/path/to/MCP/mcp_server.py"],
      "env": {
        "VRF_CLI_PATH": "C:/path/to/Source2Viewer-CLI.exe"
      }
    }
  }
}
```

或使用项目级配置（`cursor.config.json`）：

```json
{
  "mcpServers": {
    "vrf": {
      "command": "python",
      "args": ["${workspaceFolder}/MCP/mcp_server.py"],
      "env": {
        "VRF_CLI_PATH": "${workspaceFolder}/cli-windows-x64/Source2Viewer-CLI.exe"
      }
    }
  }
}
```

## 使用教程

### 基础操作

#### 1. 检查文件

检查普通文件：
```
inspect_file({
  "file_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/models/player/t_model.mdl"
})
```

检查 VPK 内文件：
```
inspect_file({
  "file_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/pak01_dir.vpk::materials/metalness_metallic.vmat_c"
})
```

#### 2. 列出 VPK 内容

列出所有文件：
```
list_vpk_contents({
  "vpk_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/pak01_dir.vpk"
})
```

按扩展名过滤：
```
list_vpk_contents({
  "vpk_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/pak01_dir.vpk",
  "extension_filter": "vmdl_c,vmat_c"
})
```

按路径过滤：
```
list_vpk_contents({
  "vpk_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/pak01_dir.vpk",
  "path_filter": "models/player/"
})
```

#### 3. 反编译资源

反编译单个文件：
```
decompile_resource({
  "input_path": "G:/path/to/resource.vmat_c",
  "output_path": "G:/path/to/output/"
})
```

#### 4. 批量反编译 VPK

```
decompile_vpk({
  "vpk_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/pak01_dir.vpk",
  "output_path": "G:/Temp/csgo_decompiled/",
  "extension_filter": "vmat_c,vmdl_c",
  "recursive": true
})
```

### 3D 模型操作

#### 5. 导出 glTF

```
export_gltf({
  "model_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/models/player/t_model.vmdl_c",
  "output_path": "G:/Temp/player.glb",
  "include_animations": true,
  "include_materials": true
})
```

#### 6. 高级 glTF 导出（VPK 内模型）

```
export_gltf_advanced({
  "model_path": "models/player/t_model.vmdl_c",
  "output_path": "G:/Temp/player.glb",
  "vpk_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/pak01_dir.vpk",
  "animation_list": "idle,walk",
  "mesh_list": "body,hands",
  "textures_adapt": true
})
```

### 纹理操作

#### 7. 提取纹理

```
extract_texture({
  "texture_path": "G:/path/to/texture.vtex_c",
  "output_path": "G:/Temp/output.png",
  "decode_flags": "auto"
})
```

### VPK 验证

#### 8. 验证 VPK 完整性

```
verify_vpk({
  "vpk_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/pak01_dir.vpk"
})
```

返回示例：
```
Verifying hashes...
[ 02.36%] Verifying MD5 hash at offset 103809024 in archive 9.
[ 49.53%] Verifying Blake3 hash at offset 52428800 in archive 226.
Success.
```

### 统计分析

#### 9. 收集资源统计

统计单个文件/目录：
```
collect_stats({
  "input_path": "G:/Temp/resources/",
  "include_files": true,
  "unique_deps": true
})
```

扫描所有 Steam 库：
```
collect_stats({
  "input_path": "steam",
  "particles": true,
  "vbib": true
})
```

### 目录操作

#### 10. 列出目录中的资源

```
list_directory_resources({
  "directory": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/",
  "extension_filter": "vmdl,vmat",
  "recursive": true
})
```

## 文件路径格式

MCP 支持两种文件路径格式：

### 普通路径
```
G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/models/player/t_model.mdl
```

### VPK 内部路径
格式：`<vpk_path>::<internal_path>`

```
vpk_path::materials/metalness_metallic.vmat_c
```

**示例**：
```
inspect_file({
  "file_path": "G:/SteamLibrary/steamapps/common/Counter-Strike Global Offensive/game/csgo/pak01_dir.vpk::models/player/t_model.vmdl_c"
})
```

## 常见问题

### Q: MCP 连接失败？

1. 确认 `VRF_CLI_PATH` 环境变量指向正确的 CLI.exe
2. 确认 CLI.exe 可独立运行（运行一次测试）

### Q: VPK 操作很慢？

VPK 文件较大时（如 CS2 的 pak01_dir.vpk 有 12 万+文件），操作会比较耗时：
- `verify_vpk` 可能需要 1-2 分钟
- `decompile_vpk` 可能需要 10+ 分钟

建议使用 `extension_filter` 和 `path_filter` 限制处理范围。

### Q: 支持哪些文件类型？

Source 2 常见资源类型：
- `.vmdl` / `.vmdl_c` - 3D 模型
- `.vmat` / `.vmat_c` - 材质
- `.vtex` / `.vtex_c` - 纹理
- `.vani` - 动画
- `.vpcf` - 粒子特效
- `.vsndevts` - 声音
- `.vmap` - 地图
- `.vrml` / `.vbsp` - 编译后资源

## 系统要求

- Python 3.10+
- .NET 8.0+（运行 VRF CLI）
- Windows/macOS/Linux

## 项目结构

```
MCP/
├── mcp_server.py      # MCP 服务器主程序
├── mcp_manifest.json  # MCP 工具清单
├── cursor.config.json # Cursor 项目配置
├── requirements.txt   # Python 依赖
└── README.md         # 本文档
```

## 许可证

本项目继承 ValveResourceFormat 的许可证。
