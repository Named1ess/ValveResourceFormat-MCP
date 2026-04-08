import json
import subprocess
import sys
import time

VRF_CLI = r"C:\Users\Administrator\Documents\GitHub\ValveResourceFormat-MCP\cli-windows-x64\Source2Viewer-CLI.exe"
VPK = r"G:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\pak01_dir.vpk"

def send_request(request, timeout=60):
    proc = subprocess.Popen(
        [sys.executable, r"C:\Users\Administrator\Documents\GitHub\ValveResourceFormat-MCP\MCP\mcp_server.py"],
        env={**subprocess.os.environ, "VRF_CLI_PATH": VRF_CLI},
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=json.dumps(request) + "\n", timeout=timeout)
    return json.loads(stdout)

print("=" * 60)
print("VPK 完整测试 - CSGO pak01_dir.vpk")
print("=" * 60)

# Test: inspect_file on VPK internal file
print("\n[Test 1] inspect_file - VPK内文件")
start = time.time()
result = send_request({
    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
    "params": {"name": "inspect_file", "arguments": {"file_path": VPK + "::materials/metalness_metallic.vmat_c"}}
})
elapsed = time.time() - start
if result.get('result', {}).get('success'):
    output = result['result'].get('output', '')[:200]
    print(f"  Success: True")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Output (first 200 chars): {output}")
else:
    print(f"  Success: False")
    print(f"  Error: {result.get('result', {}).get('error', result.get('error'))}")

# Test: inspect_file on local file
print("\n[Test 2] inspect_file - 本地文件")
start = time.time()
result = send_request({
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {"name": "inspect_file", "arguments": {"file_path": VRF_CLI}}
})
elapsed = time.time() - start
if result.get('result', {}).get('success'):
    output = result['result'].get('output', '')[:200]
    print(f"  Success: True")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Output (first 200 chars): {output}")
else:
    print(f"  Success: False")
    print(f"  Error: {result.get('result', {}).get('error', result.get('error'))}")

# Test: list_vpk_contents with filter
print("\n[Test 3] list_vpk_contents - 按扩展名过滤 (vmat_c)")
start = time.time()
result = send_request({
    "jsonrpc": "2.0", "id": 3, "method": "tools/call",
    "params": {"name": "list_vpk_contents", "arguments": {"vpk_path": VPK, "extension_filter": "vmat_c"}}
})
elapsed = time.time() - start
if result.get('result', {}).get('success'):
    files = result['result'].get('files', [])
    print(f"  Success: True")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Total: {result['result'].get('file_count')}")
    print(f"  First 5: {files[:5]}")
else:
    print(f"  Success: False")
    print(f"  Error: {result.get('result', {}).get('error')}")

# Test: list_vpk_contents with path filter
print("\n[Test 4] list_vpk_contents - 按路径过滤 (materials/)")
start = time.time()
result = send_request({
    "jsonrpc": "2.0", "id": 4, "method": "tools/call",
    "params": {"name": "list_vpk_contents", "arguments": {"vpk_path": VPK, "path_filter": "materials/"}}
})
elapsed = time.time() - start
if result.get('result', {}).get('success'):
    print(f"  Success: True")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Total: {result['result'].get('file_count')}")
    files = result['result'].get('files', [])
    print(f"  First 5: {files[:5]}")
else:
    print(f"  Success: False")
    print(f"  Error: {result.get('result', {}).get('error')}")

# Test: verify_vpk
print("\n[Test 5] verify_vpk - 验证VPK完整性 (可能需要较长时间)")
start = time.time()
result = send_request({
    "jsonrpc": "2.0", "id": 5, "method": "tools/call",
    "params": {"name": "verify_vpk", "arguments": {"vpk_path": VPK}}
}, timeout=300)
elapsed = time.time() - start
if result.get('result', {}).get('success'):
    output = result['result'].get('output', '')
    lines = output.strip().split('\n')
    last_line = lines[-1] if lines else ""
    print(f"  Success: True")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Result: {last_line}")
else:
    print(f"  Success: False")
    print(f"  Error: {result.get('result', {}).get('error')}")

# Test: collect_stats
print("\n[Test 6] collect_stats - 统计资源")
start = time.time()
result = send_request({
    "jsonrpc": "2.0", "id": 6, "method": "tools/call",
    "params": {"name": "collect_stats", "arguments": {"input_path": VPK}}
}, timeout=300)
elapsed = time.time() - start
if result.get('result', {}).get('success'):
    output = result['result'].get('output', '')
    print(f"  Success: True")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Output (first 500 chars):\n{output[:500]}")
else:
    print(f"  Success: False")
    print(f"  Error: {result.get('result', {}).get('error')}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)