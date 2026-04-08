# ValveResourceFormat MCP Server

|[English](./README.md) | 中文版

一个让 AI 工具（Cursor / Claude Code）能够与 Valve Source 2 资源格式交互的 MCP 服务器。

---

## 快速开始

### 1. 下载 CLI

前往 [ValveResourceFormat Releases](https://github.com/ValveResourceFormat/ValveResourceFormat/releases) 下载最新版 CLI（选择 `Source2Viewer-CLI-win-x.x.zip`）。

解压后将 `Source2Viewer-CLI.exe` 放到项目目录，或者记住路径稍后配置。

### 2. 配置 AI 客户端

根据你使用的 AI 工具，编辑对应的配置文件：

**Cursor 用户** → 编辑 `C:\Users\Administrator\.cursor\mcp.json`

**Claude Code 用户** → 编辑 `C:\Users\Administrator\.claude\mcp.json`

添加或追加以下配置（将路径改为你的实际路径）：

```json
{
  "mcpServers": {
    "vrf": {
      "command": "python",
      "args": ["C:\\Users\\Administrator\\Documents\\GitHub\\ValveResourceFormat-MCP\\mcp_server.py"],
      "env": {
        "VRF_CLI_PATH": "C:\\Users\\Administrator\\Documents\\GitHub\\ValveResourceFormat-MCP\\cli-windows-x64\\Source2Viewer-CLI.exe"
      }
    }
  }
}
```

### 3. 重启 AI 客户端

保存配置后，**完全退出并重新启动** AI 客户端，使 MCP 服务器生效。

---

## 重要概念：VPK 文件

### 什么是 VPK？

VPK（Valve Package）是 Steam 游戏（如 CS2、Dota 2）用于打包资源的文件格式。游戏的所有资源（模型、材质、声音等）都存储在 VPK 文件中。

### 如何找到 VPK 文件？

以 CS2 为例，VPK 文件位于游戏目录：

```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\
```

你会看到多个 VPK 文件：
- `pak01_000.vpk`, `pak01_001.vpk`, ... → 分散存储的资源包
- **`pak01_dir.vpk`** → 索引包，包含所有资源的目录信息

⚠️ **重要**：大多数操作应该使用 `pak01_dir.vpk`，而不是 `pak01_000.vpk`。

### 路径格式

MCP 支持两种路径格式：

**普通路径**（用于磁盘上的文件）：
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\models\player\t_model.mdl_c
```

**VPK 内部路径**（格式：`VPK路径::内部路径`，用于 VPK 内的文件）：
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\pak01_dir.vpk::models/player/t_model.vmdl_c
```

⚠️ 使用 `::` 分隔 VPK 路径和内部路径。

---

## 支持的工具

| 工具 | 功能 | 典型用途 |
|------|------|----------|
| `get_file_info` | 获取文件基本信息 | 快速查看文件大小、类型 |
| `list_directory_resources` | 列出目录中的资源文件 | 扫描本地目录查找资源 |
| `list_vpk_contents` | 列出 VPK 内的文件 | 探索 VPK 包内容 |
| `inspect_file` | 检查资源文件结构 | 分析模型、材质、纹理详情 |
| `decompile_resource` | 反编译单个资源 | 提取资源为可读格式 |
| `decompile_vpk` | 批量反编译 VPK | 批量导出 VPK 内资源 |
| `extract_texture` | 提取纹理为图片 | 获取游戏纹理/贴图 |
| `export_gltf` | 导出 3D 模型为 glTF | 在其他软件中查看模型 |
| `export_gltf_advanced` | 高级模型导出 | 精细控制导出的动画、网格 |
| `verify_vpk` | 验证 VPK 完整性 | 检查 VPK 文件是否损坏 |
| `collect_stats` | 收集资源统计 | 统计 VPK 中各类资源数量 |

---

## 使用示例

### 场景 1：了解某个模型长什么样

```json
inspect_file({
  "file_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta.vmdl_c"
})
```

**返回内容**：模型类型、文件大小、骨骼数量、顶点数据、使用的纹理和材质列表。

---

### 场景 2：找到所有的恐怖分子模型

```json
list_vpk_contents({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "extension_filter": "vmdl_c",
  "path_filter": "characters/models/tm_"
})
```

**返回内容**：所有以 `tm_` 开头的恐怖分子模型路径列表。

---

### 场景 3：把游戏模型导出到 Blender 查看

```json
export_gltf({
  "model_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta.vmdl_c",
  "output_path": "C:\\temp\\csgo_model.glb",
  "include_animations": true,
  "include_materials": true
})
```

**返回内容**：导出成功信息。注意：实际文件会保存在子目录 `C:\temp\csgo_model.glb\characters\models\ctm_diver\` 下。

---

### 场景 4：提取游戏角色的皮肤贴图

```json
extract_texture({
  "texture_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta/body_vmorf.vtex_c",
  "output_path": "C:\\temp\\texture.png",
  "decode_flags": "auto"
})
```

**返回内容**：PNG 格式的纹理图片文件路径。

---

### 场景 5：批量反编译某个目录下的所有材质

```json
decompile_vpk({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "output_path": "C:\\temp\\decompiled_materials",
  "extension_filter": "vmat_c",
  "path_filter": "materials/",
  "recursive": false
})
```

**返回内容**：批量反编译的统计信息，包括处理了多少文件。

---

### 场景 6：验证 VPK 文件是否完整

```json
verify_vpk({
  "vpk_path": "G:\\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\\pak01_dir.vpk"
})
```

**返回内容**：VPK 的校验和验证结果，是否有损坏或被修改。

---

### 场景 7：统计 VPK 中有多少粒子特效

```json
collect_stats({
  "input_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "particles": true,
  "include_files": true
})
```

**返回内容**：各类资源的数量统计，包括粒子特效的详细信息。

---

### 场景 8：列出本地目录的所有 .mdl 文件

```json
list_directory_resources({
  "directory": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\models",
  "extension_filter": "mdl,mdl_c",
  "recursive": true
})
```

**返回内容**：本地目录中所有模型文件的列表。

---

## 各工具详细参数

### inspect_file

检查资源文件的内部结构。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_path` | string | ✅ | 文件路径（支持 VPK 内路径） |

---

### list_vpk_contents

列出 VPK 存档中的文件。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `vpk_path` | string | ✅ | VPK 文件路径 |
| `extension_filter` | string | ❌ | 扩展名过滤器，如 `"vmdl_c,vmat_c"` |
| `path_filter` | string | ❌ | 路径前缀过滤器，如 `"characters/models/"` |

---

### decompile_resource

反编译单个资源文件为可读格式。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `input_path` | string | ✅ | 输入文件路径（支持 VPK 内路径） |
| `output_path` | string | ❌ | 输出路径，不填则输出到 stdout |

---

### decompile_vpk

批量反编译 VPK 中的资源。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `vpk_path` | string | ✅ | VPK 文件路径 |
| `output_path` | string | ✅ | 输出目录 |
| `extension_filter` | string | ❌ | 扩展名过滤器 |
| `path_filter` | string | ❌ | 路径前缀过滤器 |
| `recursive` | boolean | ❌ | 是否递归处理嵌套 VPK，默认 false |

---

### export_gltf

导出 3D 模型为 glTF/glb 格式。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model_path` | string | ✅ | 模型路径（支持 VPK 内路径） |
| `output_path` | string | ✅ | 输出文件路径（.glb 或 .gltf） |
| `include_animations` | boolean | ❌ | 是否包含动画，默认 true |
| `include_materials` | boolean | ❌ | 是否包含材质，默认 true |

---

### export_gltf_advanced

高级 glTF 导出，支持细粒度控制。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model_path` | string | ✅ | 模型路径或 VPK 内部路径 |
| `output_path` | string | ✅ | 输出文件路径 |
| `vpk_path` | string | ❌ | 如果 model_path 是内部路径，需要提供此参数 |
| `include_animations` | boolean | ❌ | 是否包含动画 |
| `include_materials` | boolean | ❌ | 是否包含材质 |
| `animation_list` | string | ❌ | 要包含的动画名称列表，逗号分隔 |
| `mesh_list` | string | ❌ | 要包含的网格名称列表，逗号分隔 |
| `textures_adapt` | boolean | ❌ | 是否执行 glTF 规范适配 |
| `export_extras` | boolean | ❌ | 是否导出额外网格属性 |

---

### extract_texture

提取纹理为图片文件。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `texture_path` | string | ✅ | 纹理路径（支持 VPK 内路径） |
| `output_path` | string | ✅ | 输出图片路径（.png 或 .tga） |
| `decode_flags` | string | ❌ | 解码标志：`none`、`auto`、`focused`，默认 `auto` |

---

### verify_vpk

验证 VPK 完整性和签名。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `vpk_path` | string | ✅ | VPK 文件路径 |

---

### collect_stats

收集资源统计信息。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `input_path` | string | ✅ | 文件/文件夹/VPK 路径，或 `"steam"` 扫描所有 Steam 库 |
| `include_files` | boolean | ❌ | 是否打印示例文件名 |
| `unique_deps` | boolean | ❌ | 是否收集唯一依赖 |
| `particles` | boolean | ❌ | 是否收集粒子特效统计 |
| `vbib` | boolean | ❌ | 是否收集顶点属性统计 |

---

### list_directory_resources

列出目录中的 Source 2 资源文件。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `directory` | string | ✅ | 要扫描的目录路径 |
| `extension_filter` | string | ❌ | 扩展名过滤器，如 `"vmdl,vmat"` |
| `recursive` | boolean | ❌ | 是否递归扫描子目录，默认 false |

---

### get_file_info

获取文件基本信息。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file_path` | string | ✅ | 文件路径 |

---

## 注意事项

### 关于 output_path

当导出 glTF、提取纹理或反编译资源时，CLI 会根据资源在 VPK 内的路径自动创建子目录结构。

例如：
- 你指定的 `output_path`: `C:\temp\model.glb`
- 实际输出位置: `C:\temp\model.glb\characters\models\ctm_diver\ctm_diver_varianta.glb`

这是 CLI 的内置行为，MCP 无法控制。请在指定 output_path 时考虑这一点。

### 关于 VPK 选择

- **pak01_dir.vpk** → 包含目录索引，用于列出内容和访问任何文件
- **pak01_000.vpk 等** → 分散存储的资源包，通常不需要直接使用

大多数情况下，请使用 `pak01_dir.vpk`。

### 关于返回结果

所有工具返回统一的 JSON 格式：
- 成功时：`{"success": true, ...其他数据}`
- 失败时：`{"success": false, "error": "错误信息"}`

---

## 系统要求

- Python 3.10+
- Windows / macOS / Linux
- ValveResourceFormat CLI

---

## 常见问题

### Q: 为什么 list_vpk_contents 返回空？

A: 请确认使用的是 `pak01_dir.vpk` 而不是 `pak01_000.vpk`。只有 `pak01_dir.vpk` 包含完整的目录索引。

### Q: 为什么 inspect_file 返回 "File not found"？

A: 检查路径格式是否正确。VPK 内文件需要使用 `VPK路径::内部路径` 格式，如：
`G:\...\pak01_dir.vpk::models/player/model.vmdl_c`

### Q: 为什么导出的文件不在指定目录？

A: 这是 CLI 的行为，会在 output_path 下创建与 VPK 内部路径对应的子目录。

### Q: 如何查找特定类型的资源？

A: 使用 `list_vpk_contents` 工具，结合 `extension_filter` 和 `path_filter` 参数进行过滤。
