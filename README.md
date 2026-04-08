# ValveResourceFormat MCP Server

|[中文版](./README_zh.md) | English

An MCP server that enables AI tools (Cursor / Claude Code) to interact with Valve Source 2 resource formats.

---

## Quick Start

### 1. Download CLI

Download the latest CLI from [ValveResourceFormat Releases](https://github.com/ValveResourceFormat/ValveResourceFormat/releases) (choose `Source2Viewer-CLI-win-x.x.zip`).

After extracting, place `Source2Viewer-CLI.exe` in your project directory, or remember the path for later configuration.

### 2. Configure Your AI Client

Edit the corresponding config file based on your AI tool:

**Cursor users** → Edit `C:\Users\Administrator\.cursor\mcp.json`

**Claude Code users** → Edit `C:\Users\Administrator\.mcp.json`

Add or append the following configuration (update paths to match your setup):

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

### 3. Restart Your AI Client

After saving, **fully quit and restart** your AI client to activate the MCP server.

---

## Key Concept: VPK Files

### What is VPK?

VPK (Valve Package) is a file format used by Steam games (like CS2, Dota 2) to package resources. All game assets (models, materials, sounds, etc.) are stored in VPK files.

### How to Find VPK Files?

For CS2, VPK files are located in the game directory:

```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\
```

You'll see multiple VPK files:
- `pak01_000.vpk`, `pak01_001.vpk`, ... → Distributed resource packages
- **`pak01_dir.vpk`** → Index package containing directory information for all resources

> **Important**: Most operations should use `pak01_dir.vpk`, not `pak01_000.vpk`.

### Path Formats

MCP supports two path formats:

**Regular path** (for files on disk):
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\models\player\t_model.mdl_c
```

**VPK internal path** (format: `VPKPath::InternalPath`, for files inside a VPK):
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\pak01_dir.vpk::models/player/t_model.vmdl_c
```

> Use `::` to separate the VPK path from the internal path.

---

## Supported Tools

| Tool | Description | Typical Use Case |
|------|-------------|-----------------|
| `get_file_info` | Get basic file information | Quick file size and type check |
| `list_directory_resources` | List resource files in a directory | Scan local directories for resources |
| `list_vpk_contents` | List files inside a VPK | Explore VPK package contents |
| `inspect_file` | Inspect resource file structure | Analyze model, material, texture details |
| `decompile_resource` | Decompile a single resource | Extract resource to readable format |
| `decompile_vpk` | Batch decompile VPK contents | Extract all resources from a VPK |
| `extract_texture` | Extract texture as image | Get game textures/maps |
| `export_gltf` | Export 3D model to glTF | View model in other software (Blender) |
| `export_gltf_advanced` | Advanced glTF export | Fine-grained control over export |
| `verify_vpk` | Verify VPK integrity | Check if VPK is corrupted |
| `collect_stats` | Collect resource statistics | Count resource types in VPK |

---

## Usage Examples

### Scenario 1: Get File Basic Information

```json
get_file_info({
  "file_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk"
})
```

**Returns**: File name, extension, size, full path.

---

### Scenario 2: List VPK Files in a Directory

```json
list_directory_resources({
  "directory": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo",
  "extension_filter": "vpk",
  "recursive": false
})
```

**Returns**: List of all .vpk files in the directory (425 files including pak01_xxx.vpk and shaders_xxx.vpk).

---

### Scenario 3: Understand a Model's Structure

```json
inspect_file({
  "file_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta.vmdl_c"
})
```

**Returns**: Model type, file size, skeleton count, vertex data, texture and material lists.

---

### Scenario 4: Find All Terrorist Models

```json
list_vpk_contents({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "extension_filter": "vmdl_c",
  "path_filter": "characters/models/tm_"
})
```

**Returns**: List of all terrorist model paths starting with `tm_`.

---

### Scenario 5: Extract Character Skin Texture

```json
extract_texture({
  "texture_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta/body_vmorf.vtex_c",
  "output_path": "C:\\temp\\texture.png"
})
```

**Returns**: PNG image file path of the texture.

---

### Scenario 6: Verify VPK File Integrity

```json
verify_vpk({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk"
})
```

**Returns**: VPK checksum verification results, whether it's corrupted or modified.

---

### Scenario 7: Count Particle Effects in VPK

```json
collect_stats({
  "input_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "particles": true,
  "include_files": true
})
```

**Returns**: Resource count statistics including detailed particle effect information.

---

### Scenario 8: Export a Game Model to Blender

```json
export_gltf({
  "model_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta.vmdl_c",
  "output_path": "C:\\temp\\csgo_model.glb",
  "include_animations": true,
  "include_materials": true
})
```

**Returns**: Export success info. Note: actual file will be saved to subdirectory `C:\temp\csgo_model.glb\characters\models\ctm_diver\`.

---

### Scenario 9: List All Shader Files

```json
list_vpk_contents({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\shaders_pc_dir.vpk"
})
```

**Returns**: 274 shader files including .vcs (compiled shader bytecode) and .ini (shader configuration).

---

### Scenario 10: Batch Decompile VPK Contents

```json
decompile_vpk({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\shaders_pc_dir.vpk",
  "output_path": "C:\\temp\\shaders_output",
  "extension_filter": "vcs",
  "recursive": false
})
```

**Returns**: Decompiled files to the specified output directory.

---

### Scenario 11: Advanced glTF Export with Animation Filtering

```json
export_gltf_advanced({
  "model_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta.vmdl_c",
  "output_path": "C:\\temp\\model_advanced.glb",
  "animation_list": "idle,walk",
  "mesh_list": "body,hands",
  "textures_adapt": true,
  "export_extras": true
})
```

**Returns**: Export success info with fine-grained control over animations, meshes, and texture adaptation.

---

## Tool Parameters Reference

### get_file_info

Get basic file information.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | ✅ | File path |

---

### list_directory_resources

List Source 2 resource files in a directory.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `directory` | string | ✅ | Directory path to scan |
| `extension_filter` | string | ❌ | Extension filter, e.g., `"vpk"` or `"vmdl,vmat"` |
| `recursive` | boolean | ❌ | Whether to scan subdirectories, default false |

---

### list_vpk_contents

List files in a VPK archive.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vpk_path` | string | ✅ | VPK file path |
| `extension_filter` | string | ❌ | Extension filter, e.g., `"vmdl_c,vmat_c"` |
| `path_filter` | string | ❌ | Path prefix filter, e.g., `"characters/models/"` |

---

### inspect_file

Inspect internal structure of a resource file.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | ✅ | File path (supports VPK internal paths) |

---

### decompile_resource

Decompile a single resource to readable format.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_path` | string | ✅ | Input file path (supports VPK internal paths) |
| `output_path` | string | ❌ | Output path, omit to output to stdout |

---

### decompile_vpk

Batch decompile all resources in a VPK to a directory.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vpk_path` | string | ✅ | VPK file path |
| `output_path` | string | ✅ | Output directory for decompiled files |
| `extension_filter` | string | ❌ | Extension filter, e.g., `"vmdl_c,vmat_c"` |
| `path_filter` | string | ❌ | Path prefix filter, e.g., `"characters/models/"` |
| `recursive` | boolean | ❌ | Whether to recurse into nested VPKs, default false |

---

### extract_texture

Extract texture as image file.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `texture_path` | string | ✅ | Texture path (supports VPK internal paths) |
| `output_path` | string | ✅ | Output image path (.png or .tga) |
| `decode_flags` | string | ❌ | Decode flags: `"none"`, `"auto"`, `"focused"`, default `"auto"` |

---

### export_gltf

Export 3D model to glTF/glb format.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_path` | string | ✅ | Model path (supports VPK internal paths) |
| `output_path` | string | ✅ | Output file path (.glb or .gltf) |
| `include_animations` | boolean | ❌ | Whether to include animations, default true |
| `include_materials` | boolean | ❌ | Whether to include materials, default true |

---

### export_gltf_advanced

Advanced glTF export with fine-grained control.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_path` | string | ✅ | Model path or VPK internal path |
| `output_path` | string | ✅ | Output file path (.glb or .gltf) |
| `vpk_path` | string | ❌ | If model_path is an internal path, specify VPK path |
| `include_animations` | boolean | ❌ | Whether to include animations, default true |
| `include_materials` | boolean | ❌ | Whether to include materials, default true |
| `animation_list` | string | ❌ | Comma-separated animation names to include |
| `mesh_list` | string | ❌ | Comma-separated mesh names to include |
| `textures_adapt` | boolean | ❌ | Perform glTF spec adaptations on textures, default false |
| `export_extras` | boolean | ❌ | Export extra mesh properties to glTF extras, default false |

---

### verify_vpk

Verify VPK integrity and signatures.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `vpk_path` | string | ✅ | VPK file path |

---

### collect_stats

Collect resource statistics.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_path` | string | ✅ | File/folder/VPK path, or `"steam"` to scan all Steam libraries |
| `include_files` | boolean | ❌ | Whether to print example file names, default false |
| `unique_deps` | boolean | ❌ | Whether to collect all unique dependencies, default false |
| `particles` | boolean | ❌ | Whether to collect particle stats, default false |
| `vbib` | boolean | ❌ | Whether to collect vertex attribute stats, default false |

---

## Notes

### About output_path

When exporting glTF, extracting textures, or decompiling resources, the CLI automatically creates subdirectories based on the resource path inside the VPK.

For example:
- Your specified `output_path`: `C:\temp\model.glb`
- Actual output location: `C:\temp\model.glb\characters\models\ctm_diver\ctm_diver_varianta.glb`

This is the CLI's built-in behavior, MCP cannot control it. Please consider this when specifying output_path.

### About VPK Selection

- **pak01_dir.vpk** → Contains directory index, used for listing contents and accessing any file
- **pak01_000.vpk etc** → Distributed resource packages, usually no need to use directly

In most cases, please use `pak01_dir.vpk`.

### About Return Results

All tools return a unified JSON format:
- Success: `{"success": true, ...other data}`
- Failure: `{"success": false, "error": "error message"}`

---

## System Requirements

- Python 3.10+
- Windows / macOS / Linux
- ValveResourceFormat CLI

---

## FAQ

### Q: Why does list_vpk_contents return empty?

A: Please confirm you are using `pak01_dir.vpk` instead of `pak01_000.vpk`. Only `pak01_dir.vpk` contains the complete directory index.

### Q: Why does inspect_file return "File not found"?

A: Check if the path format is correct. Files inside VPK need to use `VPKPath::InternalPath` format:
`G:\...\pak01_dir.vpk::models/player/model.vmdl_c`

### Q: Why is the exported file not in the specified directory?

A: This is the CLI's behavior - it creates subdirectories under output_path corresponding to the VPK internal path.

### Q: How to find resources of a specific type?

A: Use the `list_vpk_contents` tool with `extension_filter` and `path_filter` parameters for filtering.

### Q: How to scan all Steam libraries for resources?

A: Use `collect_stats` with `input_path: "steam"` to scan all Steam library directories.
