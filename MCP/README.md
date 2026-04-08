# ValveResourceFormat MCP Server

一个让 AI 工具（如 Cursor）能够与 Valve Source 2 资源格式交互的 MCP 服务器。

## 快速开始

### 1. 下载 CLI

前往 [ValveResourceFormat Releases](https://github.com/ValveResourceFormat/ValveResourceFormat/releases) 下载最新版 CLI（选择 `Source2Viewer-CLI-win-x.x.zip`）。

### 2. 配置 Cursor

编辑 `C:\Users\Administrator\.cursor\mcp.json`，添加以下配置（将路径改为你的实际路径）：

```json
{
  "mcpServers": {
    "vrf": {
      "command": "python",
      "args": ["C:\\Users\\Administrator\\Documents\\GitHub\\ValveResourceFormat-MCP\\MCP\\mcp_server.py"],
      "env": {
        "VRF_CLI_PATH": "C:\\Users\\Administrator\\Documents\\GitHub\\ValveResourceFormat-MCP\\cli-windows-x64\\Source2Viewer-CLI.exe"
      }
    }
  }
}
```

### 3. 重启 Cursor

保存配置后，重启 Cursor 使 MCP 服务器生效。

## 支持的功能

| 工具 | 功能 |
|------|------|
| `inspect_file` | 检查资源文件结构（支持 VPK 内文件） |
| `list_vpk_contents` | 列出 VPK 内容 |
| `decompile_resource` | 反编译单个资源 |
| `decompile_vpk` | 批量反编译 VPK |
| `export_gltf` | 导出 glTF 模型 |
| `export_gltf_advanced` | 高级 glTF 导出（支持 VPK 内模型） |
| `extract_texture` | 提取纹理图片 |
| `verify_vpk` | 验证 VPK 完整性 |
| `collect_stats` | 收集资源统计 |
| `get_file_info` | 获取文件信息 |
| `list_directory_resources` | 列出目录资源 |

## 使用示例

### 检查 VPK 内文件

```
inspect_file({
  "file_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::materials/metalness_metallic.vmat_c"
})
```

### 列出 VPK 内容

```
list_vpk_contents({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "extension_filter": "vmat_c"
})
```

### 导出 3D 模型

```
export_gltf({
  "model_path": "G:\\path\\to\\model.vmdl_c",
  "output_path": "G:\\Temp\\model.glb",
  "include_animations": true,
  "include_materials": true
})
```

### 验证 VPK

```
verify_vpk({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk"
})
```

## 路径格式

MCP 支持两种路径格式：

**普通路径**：
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\models\player\t_model.mdl
```

**VPK 内部路径**（格式：`vpk路径::内部路径`）：
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\pak01_dir.vpk::models/player/t_model.vmdl_c
```

## 系统要求

- Python 3.10+
- Windows/macOS/Linux
- ValveResourceFormat CLI