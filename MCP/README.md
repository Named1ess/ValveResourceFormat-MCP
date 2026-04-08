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
| `decompile_resource` | 反编译单个资源（支持 VPK 内文件） |
| `decompile_vpk` | 批量反编译 VPK |
| `export_gltf` | 导出 glTF 模型（支持 VPK 内文件） |
| `export_gltf_advanced` | 高级 glTF 导出（支持 VPK 内模型） |
| `extract_texture` | 提取纹理图片（支持 VPK 内文件） |
| `verify_vpk` | 验证 VPK 完整性 |
| `collect_stats` | 收集资源统计 |
| `get_file_info` | 获取文件信息 |
| `list_directory_resources` | 列出目录资源 |

## 路径格式

MCP 支持两种路径格式：

**普通路径**：
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\models\player\t_model.mdl_c
```

**VPK 内部路径**（格式：`vpk路径::内部路径`）：
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\pak01_dir.vpk::models/player/t_model.vmdl_c
```

大多数工具都支持 VPK 内部路径格式。

## 使用示例

### 检查 VPK 内文件结构

```
inspect_file({
  "file_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/materials/ctm_diver_body_varianta.vmat_c"
})
```

### 列出 VPK 内容

```
list_vpk_contents({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "extension_filter": "vmdl_c,vmat_c",
  "path_filter": "characters/models/ctm_diver/"
})
```

### 反编译 VPK 内的资源

```
decompile_resource({
  "input_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/materials/ctm_diver_body_varianta.vmat_c",
  "output_path": "C:\\temp\\output.vmat"
})
```

### 导出 VPK 内的 3D 模型为 glTF

```
export_gltf({
  "model_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta.vmdl_c",
  "output_path": "C:\\temp\\model.glb",
  "include_animations": true,
  "include_materials": true
})
```

### 高级 glTF 导出（支持从 VPK 内部路径导出）

```
export_gltf_advanced({
  "model_path": "characters/models/ctm_diver/ctm_diver_varianta.vmdl_c",
  "output_path": "C:\\temp\\model_adv.glb",
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "include_animations": true,
  "include_materials": true,
  "animation_list": "idle,walk",
  "mesh_list": "body,default_gloves"
})
```

### 提取 VPK 内的纹理图片

```
extract_texture({
  "texture_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta/body_vmorf.vtex_c",
  "output_path": "C:\\temp\\texture.png",
  "decode_flags": "auto"
})
```

### 批量反编译 VPK

```
decompile_vpk({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "output_path": "C:\\temp\\decompiled",
  "extension_filter": "vmat_c",
  "path_filter": "characters/models/ctm_diver/",
  "recursive": false
})
```

### 验证 VPK 完整性

```
verify_vpk({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk"
})
```

### 收集资源统计

```
collect_stats({
  "input_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "include_files": false,
  "particles": true
})
```

### 列出目录中的资源文件

```
list_directory_resources({
  "directory": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo",
  "extension_filter": "vmdl_c,vmat_c",
  "recursive": true
})
```

## 注意事项

### CLI 输出目录

当导出 glTF、提取纹理或反编译资源时，CLI 会根据资源在 VPK 内的路径创建子目录结构。例如：

```
output_path: C:\temp\model.glb
实际输出: C:\temp\model.glb\characters\models\ctm_diver\ctm_diver_varianta.glb
```

这是 CLI 的内置行为，MCP 无法控制。请在使output_path 时考虑这一点。

## 系统要求

- Python 3.10+
- Windows/macOS/Linux
- ValveResourceFormat CLI
