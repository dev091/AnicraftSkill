# AniCraft recipes (verified on 0.2.1 unless marked)

All code uses `acsession.AniCraft` (`ac`) and 0-based frames. `scripts/recipes.py` holds the reusable
versions; `scripts/selftest.py` re-checks them after an AniCraft update.

## Symbol with poses (mouth, eyes, hands)
```python
ac.at(layer, 0)
ac.run("draw.ellipse", x=920, y=440, w=80, h=12, fill="#5a1e1e", object=True)  # frame 0 art
ac.run("element.pick", x=960, y=446)
ac.run("modify.convert_to_symbol", name="Mouth", kind="graphic")
ac.run("symbol.edit")                       # origin (0,0) = centre of that art
inner = ac.info()["layer"]
ac.key(inner, 1, blank=True); ac.run("draw.ellipse", x=-35, y=-10, w=70, h=20, fill="#7a2020", object=True)
ac.run("symbol.exit", all=True)
# show pose k from frame f on:
ac.run("timeline.insert_keyframe", layer=layer, frame=f); ac.at(layer, f, select=True)
ac.run("element.set_loop", loop="single_frame", first_frame=k)
```
Real art: `file.import_to_library {path: x.svg}` (a graphic symbol named after the file) or a PNG,
then `library.place {symbol: id, x, y}` at the playhead of the active layer. `element.swap_symbol {symbol}`
swaps the selected instance keeping its transform (pose libraries: Hand_open, Hand_point, ...).

## Lip-sync
`lipsync.cues_for(wav, fps)` -> `[{"frame", "shape"}]`; `apply_cues(ac, mouth_layer, cues, MOUTH9|MOUTH3)`.
Rhubarb: install the Windows release, pass `rhubarb=` path or put it on PATH; `-r phonetic` handles Hindi.
If the voice starts later in the shot, `offset=` the start frame. Check 3 cue frames on the contact sheet.

## Bones (arm, leg, tail)
```python
b1 = ac.run("bone.add", {"from": torso, "to": upper, "head": [1040, 560], "tail": [1170, 560], "name": "shoulder"})
b2 = ac.run("bone.add", {"from": upper, "to": fore, "tail": [1290, 560], "name": "elbow"})  # head = b1 end
ac.fit(b1["layer"], N)
ac.run("bone.set_limits", bone=b2["bone"], constrain=True, min=0, max=150)
ac.run("bone.pose", bone=b1["bone"], angle=-70, frame=12)        # keyed, tweened between keys
ac.run("bone.solve", bone=b2["bone"], x=1100, y=650, frame=6)    # IK: hand to a point
ac.run("bone.info", frame=12)                                      # angles per bone, to verify
```
Shapes can bend too (`bone.add_in_shape`, `bone.bind`) for tails and cloth (not tested here).

## Camera and parallax
`recipes.camera_push(ac, N, zoom=115, x, y)`; pans: same with x/y changes. `layer.set_depth {layer, depth}`:
BG 300-800, far sky 2000+, foreground negative. `camera.info {frame}` to verify.

## Walk cycle without foot slide
Make a `Cycle` graphic symbol whose own timeline is one cycle (2 steps). `recipes.walk_across(ac, layer, N,
stride_px, frames_per_step)` loops it and travels exactly `(N-1)/frames_per_step*stride_px`. Measure the
stride on the art (heel to heel of one step) before choosing it.

## Blink and idle
`recipes.blink(ac, eyes_layer, N, fps)` (Eyes frames 0 open, 1 half, 2 closed).
`recipes.breathe(ac, layer, N, fps, period_s=3, amount_pct=1.5)` on a layer holding the character symbol
(not on an armature layer).

## Sound
```python
snd = ac.run("file.import", path=r"D:\...\line01.wav")             # new layer at the playhead
ac.run("sound.set", layer=snd["layer"], frame=0, sync="stream")     # dialogue; "event" for SFX
ac.run("sound.set", layer=music, frame=0, effect="fade_out")        # or envelope=[{at, left, right}, ...]
ac.run("layer.set_volume", ...)                                     # check params with anicraft_commands
```
Pre-level dialogue to about -16 LUFS before import, master the exported MP4 to -14 LUFS / -1.5 dBTP with
ffmpeg loudnorm (AniCraft has no loudness tool).

## Export
- MP4/WebM: `file.export_video {path, from?, to?, scale?, audio?: true, confirm}` (needs ffmpeg).
- PNG sequence: `file.export_png_sequence {dir, from?, to?, scale?}`; still: `file.export_png {path, frame}`.
- GIF/APNG/WebP/Lottie/SVG/sprite sheet/HTML canvas: see `commands-v0.2.1.md` (File section).
- Publish all formats saved in the document: `exec doc.anicraft file.publish '{"confirm": true}'`.
- Renders are deterministic: same document + flags = same pixels.

## Batch (PowerShell)
```powershell
$c='C:\Program Files\ArtCraft\AniCraft\anicraft-cli.exe'
Get-ChildItem shots\*.anicraft | % { & $c exec $_.FullName file.export_video "{`"path`":`"out\\$($_.BaseName).mp4`",`"confirm`":true}" }
```
Prefer a Python loop over `acsession` when quoting gets ugly.
