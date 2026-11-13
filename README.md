# AniCraft elite skill

A Claude skill for [AniCraft](https://getartcraft.com/apps/anicraft) (ArtCraft's open-source 2D vector
animation studio): drive it from Claude Code / Claude Desktop through its MCP server, its `serve` JSON
session or its CLI, and produce toon shots with rigs, lip-sync, camera, sound and measured QA.

```
anicraft-elite/
  SKILL.md                         rules, setup, pipeline, quality bar (load this)
  references/recipes.md            verified code recipes
  references/commands-v0.2.1.md    upstream command reference (299 commands, MIT/Apache-2.0)
  scripts/acsession.py             Python driver for `anicraft-cli serve` (ids, at/key/fit helpers)
  scripts/recipes.py               camera push, blink, walk cycle, breathing
  scripts/lipsync.py               audio -> mouth cues (Rhubarb phonetic or amplitude) -> keys
  scripts/verify_frames.py         QA gates: frames, layers, size/fps, streams, LUFS, true peak, contact sheet
  scripts/example_shot.py          end-to-end reference shot
  scripts/selftest.py              regression check after AniCraft updates
  scripts/build_episode.py         episode.json -> dialogue shots -> final MP4 (lip-sync, blinks, camera, music, LUFS)
  scripts/rig.py                   joint-safe side rig + IK walk (planted feet) ; walk_test.py = gates
  scripts/make_demo_assets.py, make_demo_puppet.py   example inputs in the exact expected layout
  references/moral-toon-bible.md   niche numbers, look, story shape (Dream Toon / Gomu Toons / Hindi Kahaniya)
  references/asset-spec.md         joint rule, files, rig.json, image prompts
CHATGPT.md                         instructions for ChatGPT (art department)
DOT.md                             instructions for Dot (Linux pipeline)
```

## Setup scripts (Rahul PC)
- `setup/install_skill.ps1`: download/update the skill into `~\.claude\skills` + `D:\youtube\anicraft\tools`.
- `setup/connect_mcp.py`: register the MCP server in Claude Desktop + Claude Code (backs up configs).

## Install
- **Claude Code (PC):** copy `anicraft-elite` to `%USERPROFILE%\.claude\skills\anicraft-elite`.
- **claude.ai:** zip the `anicraft-elite` folder and upload it in Settings > Capabilities > Skills.
- MCP: `claude mcp add anicraft -- "C:\Program Files\ArtCraft\AniCraft\anicraft-cli.exe" mcp`
  (or add an `anicraft` entry with `command`/`args: ["mcp"]` to the Claude Desktop config).

Tested with anicraft-cli 0.2.1 on Windows 11. After an AniCraft update run `python scripts/selftest.py out`.
