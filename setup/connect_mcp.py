"""Register the AniCraft MCP server with Claude Desktop and Claude Code (user scope).
Backs up each config first; only adds/replaces the "anicraft" entry. Prints server names only."""
import json, os, shutil, sys, time

CLI = r"C:\Program Files\ArtCraft\AniCraft\anicraft-cli.exe"
FF = r"D:\youtube\tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe"
for p in (CLI, FF):
    if not os.path.exists(p):
        sys.exit("MISSING " + p)

entry = {"command": CLI, "args": ["mcp"], "env": {"ANICRAFT_FFMPEG": FF}}
targets = [
    os.path.join(os.environ["APPDATA"], "Claude", "claude_desktop_config.json"),
    os.path.join(os.path.expanduser("~"), ".claude.json"),
]
stamp = time.strftime("%Y%m%d-%H%M%S")
for p in targets:
    if not os.path.exists(p):
        print("SKIP (not found)", p)
        continue
    with open(p, encoding="utf-8-sig") as f:
        data = json.load(f)
    shutil.copy2(p, p + ".bak-" + stamp)
    servers = data.setdefault("mcpServers", {})
    servers["anicraft"] = ({"type": "stdio", **entry} if p.endswith(".claude.json") else dict(entry))
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, p)
    with open(p, encoding="utf-8") as f:
        json.load(f)  # re-parse check
    print("OK", p, "servers:", sorted(servers))
