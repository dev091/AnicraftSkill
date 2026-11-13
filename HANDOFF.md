# HANDOFF (2026-11-13)
- Skill `anicraft-elite` installed on home-pc (`~\.claude\skills\anicraft-elite`, scripts `D:\youtube\anicraft\tools`);
  update with `D:\youtube\anicraft\tools\install_skill.ps1 -Branch <commit-sha>` (raw/API caches the branch name).
- MCP `anicraft` registered in Claude Desktop + Claude Code; restart the app to load it. `ANICRAFT_FFMPEG` user env set.
- Verified on anicraft-cli 0.2.1 (Windows): selftest 6/6, example_shot ALL PASS, demo episode (3 shots) ALL PASS
  (-13.9 LUFS), walk_test ALL PASS (IK 0.01 px, slide 0.06 px).
- Intel (D:\youtube\anicraft\intel\intel.json): top 3 = Dream Toon, Gomu Toons, Hindi Kahaniya. Chhota Bheem links and
  ltglJxYbLmU are "not available" to yt-dlp (no cookies).
- Not verified: Linux run for Dot; Rhubarb lip-sync; talker + walker in one shot (walker has no mouth layer yet);
  flipped (mirrored) talker after the fix was rebuilt but not re-checked by pixels; arm swing direction sign by eye only.
- Next: (1) prep_parts.py: ChatGPT #00FF00 sheet -> cut parts -> align to rig.json -> caps; (2) walker head with
  eyes/mouth; (3) first real episode with ChatGPT art + TTS; (4) turn/3-4 view walk.
