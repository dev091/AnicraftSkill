# HANDOFF (2026-11-13)
- Skill `anicraft-elite` installed on home-pc (`~\.claude\skills\anicraft-elite`, scripts `D:\youtube\anicraft\tools`);
  update with `D:\youtube\anicraft\tools\install_skill.ps1 -Branch <commit-sha>` (raw/API caches the branch name).
- MCP `anicraft` registered in Claude Desktop + Claude Code; restart the app to load it. `ANICRAFT_FFMPEG` user env set.
- Verified on anicraft-cli 0.2.1 (Windows): flipped talker upright (pixel check); selftest 6/6, example_shot ALL PASS, demo episode (3 shots) ALL PASS
  (-13.9 LUFS), walk_test ALL PASS (IK 0.01 px, slide 0.06 px).
- Intel (D:\youtube\anicraft\intel\intel.json): top 3 = Dream Toon, Gomu Toons, Hindi Kahaniya. Chhota Bheem links and
  ltglJxYbLmU are "not available" to yt-dlp (no cookies).
- Not verified: Linux run for Dot; Rhubarb lip-sync; talker + walker in one shot (walker has no mouth layer yet);
  arm swing direction sign by eye only.
- Next: (1) prep_parts.py: ChatGPT #00FF00 sheet -> cut parts -> align to rig.json -> caps; (2) walker head with
  eyes/mouth; (3) first real episode with ChatGPT art + TTS; (4) turn/3-4 view walk.

## SWOT gaps (P0 = do first)
P0 DONE: talker gesture rig (talker.py, verified 2026-11-13). TODO: script->shotlist generator; Hindi TTS lane + Rhubarb phonetic;
   automate the 3 hand-checked gates (static > 3 s, shot median, lip-sync coverage); prep_parts.py.
P1 head turns (front/3-4/side) + brows/expressions; props in hand + sit/stand; location bible with parallax layers;
   ambience/SFX library; intro sting + end screen; walk start/stop/turn.
P2 full-length ref benchmark (every shot, motion density, wpm, music %, thumbnails); Shorts cut-downs; Linux test.
Risk: YouTube inauthentic/repetitive-content policy -> original stories, recurring cast, human review per episode.
