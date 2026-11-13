---
name: anicraft-elite
description: Use when Rahul asks to make, rig, animate, lip-sync, render, export or fix a 2D animation, toon shot or episode in AniCraft (ArtCraft's open-source Rust 2D vector animation studio, Flash/Animate-style), to drive anicraft-cli, its `serve` JSON session or its MCP server (anicraft_* tools), to convert .fla/.xfl files, or to connect AniCraft to Claude on his PC.
---

# AniCraft elite (v0.2.1, verified on Rahul's PC 2026-11-13)

Reply to Rahul in short Hinglish: verdict, measured numbers, top 3 gaps, one question only if the decision is his.
He rates harshly: report only gates you measured; never call a shot done without `verify_frames.py` output.
Never upload or publish anything. Follow low-token-ops: read only what the step needs, view at most one contact sheet.

## 0. Setup facts (home-pc, Windows)
- App + CLI: `C:\Program Files\ArtCraft\AniCraft\anicraft.exe`, `...\anicraft-cli.exe` (NOT on PATH; installed by ArtCraft Launcher). Check `anicraft-cli --version`; if not 0.2.1, re-check commands with `anicraft-cli commands` before trusting `references/commands-v0.2.1.md`.
- MCP server `anicraft` is registered in Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`) and Claude Code (`~\.claude.json`), command `anicraft-cli mcp`, env `ANICRAFT_FFMPEG`. Re-register: `D:\youtube\anicraft\tools\connect_mcp.py` (backs up both files). Restart the Claude app after changes.
- ffmpeg: `D:\youtube\tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe` (user env `ANICRAFT_FFMPEG`, needed for MP4/WebM). Python: `D:\youtube\tools\studio-venv\Scripts\python.exe` (Pillow present).
- Work root `D:\youtube\anicraft\` (`tools\` = this skill's scripts, `test\`, one folder per job). From a cloud session use Rahul_Desktop_Command `run` (60 s cap): start long renders with `Start-Process` hidden + log file, then poll.

## 1. Pick the driver
| Need | Use |
|---|---|
| Interactive edit inside Claude Desktop/Code on the PC | MCP tools: `anicraft_commands` (filter words) -> `anicraft_run` / `anicraft_run_script`; `anicraft_document`; `anicraft_render` (PNG). The server edits its OWN copy: `file.save_as` to persist; the open app window does not update. |
| Build a shot/episode programmatically (default) | `scripts/acsession.py` (`anicraft-cli serve`): real ids back, helpers `at`, `key`, `fit`, `layer_id`. Template: `scripts/example_shot.py`. |
| One-off render/convert/batch | CLI: `info`, `render --frame N`, `render-seq`, `gif/apng/webp --overwrite yes`, `exec <doc> <cmd> '<json>' --save`, `run <doc> steps.json --save`, `new --out x.anicraft --width --height --fps`. In PowerShell put JSON in a file (`run`), not inline. |
| Animate files | `anicraft-cli exec --sample file.open '{"path":"in.fla"}' --save out.anicraft` (.fla/.xfl/XFL folder; read the import report). |

## 2. Golden rules (each one cost a real bug in testing)
1. **Commands act on the active layer at the playhead.** The `frame` param of `timeline.insert_keyframe` / `insert_blank_keyframe` does NOT move the playhead. Before any draw / translate / set_loop / transform: `ac.at(layer, frame)` (= `timeline.goto` + `layer.select`). Skipping it made a tween run backwards and drew all symbol frames onto frame 0.
2. **Pass explicit `layer` ids** to every timeline command. `layer.new` and `camera.add` create layers spanning the whole scene, so `insert_frame` on them grows the movie. Use `ac.fit(layer, N)` and assert `doc.info.movie_frames == N`.
3. **Select by layer, not by coordinates**, after a symbol swap or pose: `layer.select {layer, select:true}` (keep one instance per layer for mouths/eyes). `element.pick` misses once the shape changes.
4. **Symbol space origin = centre of the converted art.** Inside `symbol.edit`, draw around (0,0); `symbol.exit {all:true}` to return.
5. **Frames: engine/JSON/MCP are 0-based; CLI `--frame` is 1-based.**
6. **Camera:** `camera.set` on a frame with no camera keyframe edits the whole span. Key first (`ac.key(cam, f)`), set, then `timeline.create_tween {layer: cam, frame: 0, easing}`. Parallax: `layer.set_depth` (px behind stage, -500..10000; deeper moves less).
7. **Bones:** `bone.add {"from": inst, "to": inst, head:[x,y], tail:[x,y]}` (pass a dict: `from` is a Python keyword). Chains continue from the parent's end. `bone.pose {bone, angle, frame}` keys poses (tweened between), `bone.set_limits` clamps (200 deg -> 150 verified), `bone.solve` = IK drag (returns `reached`, `error`).
8. **Easing values:** `Linear, QuadIn|EaseIn, QuadOut|EaseOut, QuadInOut|EaseInOut, CubicIn, CubicOut, CubicInOut, Smooth`, or `{"classic": -100..100}`, or `{"bezier": [x1,y1,x2,y2]}`. Motion tweens: per-property `motion.set_key` / `motion.set_ease`.
9. **Overwrites:** exports and `save_as` refuse to replace files until `"confirm": true`; CLI `render` has no overwrite flag (delete first). Confirm only on files this job created; ask Rahul before replacing his files.
10. **Sound:** `file.import {path: wav|mp3|ogg}` puts it on a new layer at the playhead; then `sound.set {layer, frame, sync:"stream"}` for dialogue (frame-locked), `event` for SFX; envelope/fade via `sound.set`. `file.export_video` muxes audio (AAC in MP4) by default.
11. **Never `modify.flip_h` an instance that gets a motion tween** (breathing, property keys): the tween re-decomposes the flip as rotation 180 and the character turns upside down. Mirror the art instead (`build_episode.py` does this for `"flip": true`).
12. Every edit is undoable (`edit.undo`). Look up a command's exact params with `anicraft_commands {filter}` or grep `references/commands-v0.2.1.md` (299 commands) instead of guessing.

## 3. Shot pipeline (toon factory)
1. **Plan**: beat sheet -> shot list (length in frames at 24 fps, camera, who speaks). One `.anicraft` per shot in `D:\youtube\anicraft\<job>\shots\`.
2. **Assets**: characters as graphic symbols: body parts as separate symbols joined with bones; `Mouth` symbol with visemes on its frames (9-frame `XABCDEFGH` chart or 3-frame rest/mid/open); `Eyes` symbol (open/half/closed). Import art with `file.import_to_library` (SVG becomes a graphic symbol) and `library.place`.
3. **Build** with `acsession` following `scripts/example_shot.py` and `references/recipes.md` (walk cycle, blink, lip-sync, camera, parallax, sound).
4. **Lip-sync**: `scripts/lipsync.py voice.wav --fps 24` -> cues -> `apply_cues(ac, mouth_layer, cues, chart)`. Uses Rhubarb (`-r phonetic`, works for Hindi) if `rhubarb` is on PATH or passed, else amplitude fallback (X/B/C/D). Keep the mouth on its own main-timeline layer above a head that does not move during the line, or move both layers with identical tweens.
5. **Export**: `file.export_video {path: raw.mp4, confirm:true}` -> ffmpeg loudnorm pass (`-c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k`) -> episode concat outside AniCraft.
6. **Verify** (mandatory): `python scripts/verify_frames.py shot.anicraft --video shot.mp4 --expect-frames N --expect-size 1920x1080 --expect-fps 24`. Gates: frame count, every layer reaches the last frame, size/fps, video+audio streams, loudness -14 +/-1 LUFS, true peak <= -1 dBTP, motion between sampled frames (identical = frozen). Then look at `<shot>_qa/contact.jpg` once.
7. **Score** with the factory rubric (story 15, art 15, motion 20, voice 15, editing 15, sound 10, packaging 10); list measured gaps. Voice naturalness is Rahul's ear.

## 3b. Hindi moral-story lane (Dream Toon / Gomu Toons / Hindi Kahaniya format)
- Niche numbers, look, story shape, shot grammar: `references/moral-toon-bible.md`. Asset rules + prompts:
  `references/asset-spec.md`. Art comes from ChatGPT (`CHATGPT.md` in the repo root), pipeline runs on the PC or Dot (`DOT.md`).
- Dialogue shots: `scripts/build_episode.py episode.json` (BG, talkers, lip-sync per speaker, blinks, breathing,
  camera push, stream dialogue, concat, ducked music, -14 LUFS). Demo: `make_demo_assets.py` -> builder -> ALL PASS.
- Walking: `scripts/rig.py` (`build` = standard 11-bone side rig from part files + `rig.json`; `walk` = IK with
  planted feet, hip drop for reach, body bob, counter-swinging arms, keys on twos). Gate: `walk_test.py` (joint caps,
  IK error <= 1.5 px, foot slide <= 2 px, knee forward). Verified: 0.01 px IK error, 0.06 px slide.
- JOINT RULE: round caps centred on every joint on both parts. Most "joints break while walking" problems are art
  without caps or pivots not on the cap centre; `rig.check_art` catches them before building.

## 4. Quality bar for toons (beat Akku Toon / Dream Toon level)
- Limbs attached at joints (bone heads on the joint, limits on elbows/knees), no foot slide: travel per frame = stride px / frames per step.
- Lip-sync within +/-1 frame of the cue; mouth never frozen while the voice plays; blink every 2-5 s (2 frames closed).
- Camera never static for a whole long shot: slow push-in (100->110-125 %, Smooth) or pan; parallax depth on BG.
- Continuous idle (breathing: torso `scale_y` 100->101.5 % loop) so no frame is dead.
- Mix: dialogue stream, SFX event, music bed ducked under voice; master -14 LUFS / -1 dBTP.

## 5. Troubleshooting
- `nothing is selected` -> you are on the wrong frame/layer: `ac.at(layer, f, select=True)`.
- Movie longer than planned -> a layer was extended past N: `ac.fit(layer, N)` on every layer, re-check `movie_frames`.
- `Replace existing file?` -> add `"confirm": true` (only for this job's files).
- Video export fails -> `ANICRAFT_FFMPEG` unset in that process; pass `ffmpeg` param with the full path.
- PowerShell shows `NativeCommandError` for stderr output -> check exit code and output files, not the red text.
- Old app window shows old content -> the CLI/MCP work on copies; reopen the saved file.
