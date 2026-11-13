"""Episode builder: episode.json + character part PNGs + background PNGs + voice WAVs -> shots -> final MP4.

python build_episode.py episode.json [--only 3] [--skip-existing]
Layout (paths in episode.json are relative to it):
  characters/<Name>/body.png, eyes_0..2.png (open/half/closed), mouth_0..N.png (N=2: rest/mid/open, N=8: XABCDEFGH)
     -> every part PNG has the SAME canvas size with transparency, so parts align when centred on one point.
  backgrounds/<bg>.png at stage size (1920x1080).
episode.json:
{"title": "...", "fps": 24, "size": [1920, 1080], "music": "music/bed.mp3" (optional),
 "shots": [{"bg": "village", "chars": [{"name": "Ramu", "x": 600, "y": 620, "flip": false}],
            "lines": [{"who": "Ramu", "wav": "vo/001.wav"}], "hold": 0, "camera": {"zoom": 112, "x": 700, "y": 540}}]}
x,y = where the centre of the character canvas goes. A shot lasts its lines (+0.3 s head, +0.5 s tail) or `hold` s.
Per shot: BG, characters (body/eyes/mouth layers), lip-sync for each speaker, blinks, breathing idle, camera push,
dialogue as stream sound -> shots/sNN.mp4 + sNN.anicraft. Then concat -> music bed ducked -> -14 LUFS -> final.mp4.
"""
import argparse, json, os, shutil, subprocess, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acsession import AniCraft
from lipsync import MOUTH3, MOUTH9, apply_cues, cues_for
from recipes import blink, breathe, camera_push

FFMPEG = os.environ.get("ANICRAFT_FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
HEAD, TAIL = 0.3, 0.5


def wav_seconds(p):
    with wave.open(p) as w:
        return w.getnframes() / w.getframerate()


def to_wav(src, dst):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "48000", dst], check=True)
    return dst


def lib_bitmap(ac, path):
    r = ac.run("file.import_to_library", path=path)
    return r.get("bitmap") or r.get("id")


def part_symbol(ac, layer, name, pngs, x, y):
    """Graphic symbol whose frame i shows pngs[i]; one instance at (x, y) on `layer`. Returns instance id."""
    ac.at(layer, 0)
    ac.run("library.place", bitmap=lib_bitmap(ac, pngs[0]), x=x, y=y)
    inst = ac.run("modify.convert_to_symbol", name=name, kind="graphic")["instance"]
    if len(pngs) > 1:
        ac.run("symbol.edit")
        inner = ac.info()["layer"]
        for i, p in enumerate(pngs[1:], 1):
            ac.key(inner, i, blank=True)
            ac.run("library.place", bitmap=lib_bitmap(ac, p), x=0, y=0)
        ac.run("symbol.exit", all=True)
    return inst


def build_shot(ep, base, k, shot, out):
    fps = ep.get("fps", 24); W, H = ep.get("size", [1920, 1080])
    lines, t, starts = shot.get("lines", []), HEAD, []
    tmpwav = []
    for ln in lines:
        w = to_wav(os.path.join(base, ln["wav"]), os.path.join(out, f"s{k:02d}_l{len(tmpwav)}.wav")); tmpwav.append(w)
        starts.append(round(t * fps)); t += wav_seconds(w) + 0.15
    secs = (t - 0.15 + TAIL) if lines else shot.get("hold", 3)
    N = max(int(round(secs * fps)), fps)
    with AniCraft() as ac:
        ac.run("doc.set_stage", width=W, height=H, fps=fps, background="#000000")
        bg = ac.info()["layers"][0]["id"]
        ac.run("layer.rename", layer=bg, name="BG"); ac.at(bg, 0)
        ac.run("library.place", bitmap=lib_bitmap(ac, os.path.join(base, "backgrounds", shot["bg"] + ".png")), x=W / 2, y=H / 2)
        ac.fit(bg, N)
        mouths, eye_layers, char_layers = {}, [], []
        for c in shot.get("chars", []):
            d = os.path.join(base, "characters", c["name"])
            mouth_pngs = sorted(p for p in os.listdir(d) if p.startswith("mouth_"))
            lay = {}
            for part, pngs in (("body", ["body.png"]), ("eyes", [f"eyes_{i}.png" for i in range(3)]), ("mouth", mouth_pngs)):
                lay[part] = ac.run("layer.new", name=f"{c['name']}_{part}")["layer"]
                ac.fit(lay[part], N)
                part_symbol(ac, lay[part], f"{c['name']}_{part}", [os.path.join(d, p) for p in pngs], c["x"], c["y"])
                if c.get("flip"):
                    ac.at(lay[part], 0, select=True); ac.run("modify.flip_h")
            mouths[c["name"]] = (lay["mouth"], MOUTH9 if len(mouth_pngs) >= 9 else MOUTH3)
            eye_layers.append(lay["eyes"]); char_layers += list(lay.values())
        for who in {ln["who"] for ln in lines}:
            cues = []
            for ln, s, w in zip(lines, starts, tmpwav):
                if ln["who"] == who:
                    cues += [c for c in cues_for(w, fps, offset=s)] + [{"frame": s + round(wav_seconds(w) * fps), "shape": "X"}]
            layer, chart = mouths[who]
            apply_cues(ac, layer, sorted(cues, key=lambda c: c["frame"]), chart)
        for i, el in enumerate(eye_layers):
            blink(ac, el, N, fps, seed=7 + 13 * i + k)
        for L in char_layers:                       # same breathing on every part keeps them aligned
            if L not in eye_layers and L not in [m[0] for m in mouths.values()]:
                breathe(ac, L, N, fps, period_s=3.2, amount_pct=1.2)
        cam = shot.get("camera", {"zoom": 106, "x": W / 2, "y": H / 2})
        camera_push(ac, N, zoom=cam.get("zoom", 106), x=cam.get("x", W / 2), y=cam.get("y", H / 2))
        for s, w in zip(starts, tmpwav):
            ac.at(bg, s)
            snd = ac.run("file.import", path=w)
            ac.run("sound.set", layer=snd["layer"], frame=s, sync="stream")
            ac.fit(snd["layer"], N)
        assert ac.info()["movie_frames"] == N, "movie length drifted"
        doc = os.path.join(out, f"s{k:02d}.anicraft")
        ac.run("file.save_as", path=doc, confirm=True)
        mp4 = os.path.join(out, f"s{k:02d}.mp4")
        ac.run("file.export_video", path=mp4, confirm=True)
    for w in tmpwav:
        os.remove(w)
    return mp4, N


def finish(ep, base, shots, out):
    lst = os.path.join(out, "concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        f.writelines(f"file '{os.path.basename(p)}'\n" for p in shots)
    cat = os.path.join(out, "cat.mp4")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", cat], check=True, cwd=out)
    final = os.path.join(out, "final.mp4")
    if ep.get("music"):
        flt = ("[1:a]volume=0.35,aloop=loop=-1:size=2e9[m];[m][0:a]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[d];"
               "[0:a][d]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", cat, "-i", os.path.join(base, ep["music"]), "-filter_complex", flt,
               "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", final]
    else:
        cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", cat, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", final]
    subprocess.run(cmd, check=True)
    os.remove(cat)
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("episode"); ap.add_argument("--only", type=int); ap.add_argument("--skip-existing", action="store_true")
    a = ap.parse_args()
    base = os.path.dirname(os.path.abspath(a.episode))
    ep = json.load(open(a.episode, encoding="utf-8"))
    out = os.path.join(base, "shots"); os.makedirs(out, exist_ok=True)
    mp4s = []
    for k, shot in enumerate(ep["shots"], 1):
        mp4 = os.path.join(out, f"s{k:02d}.mp4")
        if (a.only and k != a.only) or (a.skip_existing and os.path.exists(mp4)):
            mp4s.append(mp4); continue
        mp4, n = build_shot(ep, base, k, shot, out)
        print(f"shot {k}: {n} frames -> {mp4}", flush=True)
        mp4s.append(mp4)
    if not a.only:
        print("final:", finish(ep, base, mp4s, out), flush=True)
