# ValveResourceFormat MCP Server

[中文版](./README_zh.md) | English

An MCP server that enables AI tools (like Cursor) to interact with Valve Source 2 resource formats.

## Quick Start

### 1. Download CLI

Download the latest CLI from [ValveResourceFormat Releases](https://github.com/ValveResourceFormat/ValveResourceFormat/releases) (choose `Source2Viewer-CLI-win-x.x.zip`).

### 2. Configure Cursor

Edit `C:\Users\Administrator\.cursor\mcp.json` (Cursor) or `C:\Users\Administrator\.claude\mcp.json` (Claude Code) and add the following configuration (update paths to match your setup):

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

### 3. Restart Cursor

After saving the configuration, restart Cursor to activate the MCP server.

## Supported Tools

| Tool | Description |
|------|-------------|
| `inspect_file` | Inspect resource file structure (supports VPK internal files) |
| `list_vpk_contents` | List VPK archive contents |
| `decompile_resource` | Decompile a single resource (supports VPK internal files) |
| `decompile_vpk` | Batch decompile VPK archive |
| `export_gltf` | Export 3D model to glTF (supports VPK internal files) |
| `export_gltf_advanced` | Advanced glTF export with filtering options |
| `extract_texture` | Extract texture to image (supports VPK internal files) |
| `verify_vpk` | Verify VPK integrity and signatures |
| `collect_stats` | Collect resource statistics |
| `get_file_info` | Get file information |
| `list_directory_resources` | List resource files in a directory |

## Path Formats

MCP supports two path formats:

**Regular path**:
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\models\player\t_model.mdl_c
```

**VPK internal path** (format: `vpk_path::internal_path`):
```
G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\pak01_dir.vpk::models/player/t_model.vmdl_c
```

Most tools support the VPK internal path format.

## Usage Examples

### Inspect a file inside a VPK

```
inspect_file({
  "file_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/materials/ctm_diver_body_varianta.vmat_c"
})
```

### List VPK contents

```
list_vpk_contents({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "extension_filter": "vmdl_c,vmat_c",
  "path_filter": "characters/models/ctm_diver/"
})
```

### Decompile a resource from VPK

```
decompile_resource({
  "input_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/materials/ctm_diver_body_varianta.vmat_c",
  "output_path": "C:\\temp\\output.vmat"
})
```

### Export a model from VPK to glTF

```
export_gltf({
  "model_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta.vmdl_c",
  "output_path": "C:\\temp\\model.glb",
  "include_animations": true,
  "include_materials": true
})
```

### Advanced glTF export

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

### Extract texture from VPK

```
extract_texture({
  "texture_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk::characters/models/ctm_diver/ctm_diver_varianta/body_vmorf.vtex_c",
  "output_path": "C:\\temp\\texture.png",
  "decode_flags": "auto"
})
```

### Batch decompile VPK

```
decompile_vpk({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "output_path": "C:\\temp\\decompiled",
  "extension_filter": "vmat_c",
  "path_filter": "characters/models/ctm_diver/",
  "recursive": false
})
```

### Verify VPK integrity

```
verify_vpk({
  "vpk_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk"
})
```

### Collect resource statistics

```
collect_stats({
  "input_path": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\pak01_dir.vpk",
  "include_files": false,
  "particles": true
})
```

### List resource files in directory

```
list_directory_resources({
  "directory": "G:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo",
  "extension_filter": "vmdl_c,vmat_c",
  "recursive": true
})
```

## Notes

### CLI Output Directory

When exporting glTF, extracting textures, or decompiling resources, the CLI creates subdirectories based on the resource path inside the VPK. For example:

```
output_path: C:\temp\model.glb
actual output: C:\temp\model.glb\characters\models\ctm_diver\ctm_diver_varianta.glb
```

This is the CLI's built-in behavior and cannot be controlled by MCP. Please keep this in mind when specifying output_path.

## System Requirements

- Python 3.10+
- Windows/macOS/Linux
- ValveResourceFormat CLI
