# Dot: AniCraft toon pipeline (Linux CPU cloud)

Goal: turn ChatGPT art + a script + voice lines into a finished episode in AniCraft whose characters walk and talk
naturally (no broken joints, no foot slide), at the level of Dream Toon / Gomu Toons / Hindi Kahaniya. Never upload
or publish; deliverables go to the Drive deliverables folder for Rahul.

## 1. Setup (once)
```bash
git clone -b claude/intelligent-archimedes-68cftw https://github.com/dev091/AnicraftSkill.git
cd AnicraftSkill/anicraft-elite/scripts
curl -LO https://github.com/storytold/anicraft/releases/download/v0.2.1/anicraft-0.2.1-linux-x86_64.tar.gz
mkdir -p ~/anicraft && tar -xzf anicraft-0.2.1-linux-x86_64.tar.gz -C ~/anicraft
export ANICRAFT_CLI=$(find ~/anicraft -name anicraft-cli -type f | head -1)
export ANICRAFT_FFMPEG=$(command -v ffmpeg)
pip install pillow yt-dlp
python selftest.py /tmp/st        # must print RESULT: ALL PASS before any real work
```
The scripts were verified on Windows with 0.2.1; on Linux run selftest first and report any FAIL instead of guessing.
Rules and pitfalls: read `../SKILL.md` section 2 (golden rules) and `../references/*.md`.

## 2. Assets from ChatGPT -> rig-ready parts
1. Remove the #00FF00 background (alpha), split sheets into one PNG per part (connected components), name them as in
   `references/asset-spec.md`.
2. Place each part on the character canvas in its neutral pose so joints coincide; write `rig.json` (joint = centre
   of the round cap). Talker parts: same canvas, eyes/mouth on top of the body.
3. `python -c "from rig import check_art; print(check_art('characters/<Name>_side'))"` -> must print `[]`. If a joint
   fails, paint a filled circle of the limb colour at the joint on both parts (radius = half limb width).
4. `python walk_test.py characters/<Name>_side out/<Name>_walk` -> ALL PASS, then look at ONE contact sheet.

## 3. Episode
1. Script -> lines `Speaker: text` -> TTS (natural Hindi voices) -> `vo/NNN.wav`, one file per line.
2. Write `episode.json` (see `build_episode.py` docstring): shots with bg, characters + x/y/flip, lines, camera.
   Walking shots: build with `rig.build` + `rig.walk` (see `walk_test.py`); dialogue shots: `build_episode.py`.
3. `python build_episode.py episode.json` -> shots/sNN.mp4 + final.mp4 (music ducked, -14 LUFS).
4. `python verify_frames.py shots/s01.anicraft --video shots/final.mp4 --expect-size 1920x1080 --expect-fps 24`
   -> every gate PASS. Report numbers, not adjectives.

## 4. Gates (fail = fix before delivery)
Automated (scripts print PASS/FAIL): joint caps; IK error <= 1.5 px; foot slide <= 2 px; knee bends forward; every
layer reaches the last frame; 1920x1080 @ 24 fps; audio present; -14 +/-1 LUFS; true peak <= -1 dBTP.
NOT automated yet (check by hand and say so in the report): no static stretch > 3 s; lip-sync keys on every voiced
line; shot median 4-8 s over the episode.

## 5. Report to Claude (STATUS.md, <= 30 lines)
Version of AniCraft, selftest result, gate table per shot, the one contact sheet path, open problems. No video files
over 10 MB in reports; finals only in deliverables.
