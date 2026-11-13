"""Lip-sync for AniCraft: audio -> mouth cues -> keys on a mouth layer (graphic symbol, one viseme per frame).

Cue source: Rhubarb Lip Sync (`--recognizer phonetic`, language-independent, good for Hindi) when found,
else an amplitude fallback (X/B/C/D only). Shapes follow Rhubarb: X rest, A closed MBP, B slight, C open,
D wide, E rounded, F puckered, G F/V, H L.

CLI:  python lipsync.py voice.wav --fps 24 [--rhubarb PATH] [--offset 0] > cues.json
Lib:  from lipsync import cues_for, apply_cues
      apply_cues(ac, mouth_layer, cues, chart=MOUTH9)   # ac = acsession.AniCraft, timeline holding the mouth layer
Tested (amplitude path) with anicraft-cli 0.2.1 on Windows (2026-11-13): 8/8 sampled frames showed the cued viseme.
"""
import argparse, array, json, math, os, shutil, subprocess, sys, tempfile, wave

MOUTH9 = {s: i for i, s in enumerate("XABCDEFGH")}          # 9-frame mouth symbol, frame i = shape
MOUTH3 = {"X": 0, "A": 0, "B": 1, "C": 1, "E": 1, "F": 1, "G": 1, "H": 1, "D": 2}  # rest / mid / open
FFMPEG = os.environ.get("ANICRAFT_FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"


def _pcm16_mono(path, rate=16000):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(rate), "-sample_fmt", "s16", tmp], check=True)
    with wave.open(tmp) as w:
        data = array.array("h", w.readframes(w.getnframes()))
    os.remove(tmp)
    return data, rate


def amplitude_cues(path, fps, hold=2):
    data, rate = _pcm16_mono(path)
    spf = rate / fps
    n = int(len(data) / spf)
    db = []
    for i in range(n):
        seg = data[int(i * spf):int((i + 1) * spf)]
        rms = math.sqrt(sum(s * s for s in seg) / max(1, len(seg))) or 1e-9
        db.append(20 * math.log10(rms / 32768))
    ref = sorted(db)[int(0.95 * (len(db) - 1))] if db else 0  # loud speech level of this clip
    shapes = []
    for d in db:
        rel = d - ref
        shapes.append("X" if rel < -30 else "B" if rel < -18 else "C" if rel < -9 else "D")
    out, last, since = [], None, hold
    for f, s in enumerate(shapes):  # hold each shape >= `hold` frames (no 1-frame flicker)
        if s != last and since >= hold:
            out.append({"frame": f, "shape": s}); last, since = s, 0
        since += 1
    return out


def rhubarb_cues(path, fps, exe, dialog=None):
    cmd = [exe, "-q", "-f", "json", "-r", "phonetic", "--extendedShapes", "GHX", path]
    if dialog:
        cmd += ["-d", dialog]
    res = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    out = []
    for c in res["mouthCues"]:
        f = round(c["start"] * fps)
        if out and out[-1]["frame"] == f:
            out[-1]["shape"] = c["value"]
        elif not out or out[-1]["shape"] != c["value"]:
            out.append({"frame": f, "shape": c["value"]})
    return out


def cues_for(path, fps, rhubarb=None, offset=0):
    exe = rhubarb or shutil.which("rhubarb")
    cues = rhubarb_cues(path, fps, exe) if exe and os.path.exists(exe if os.path.isabs(exe) else shutil.which(exe) or "") else amplitude_cues(path, fps)
    return [{"frame": c["frame"] + offset, "shape": c["shape"]} for c in cues if c["frame"] + offset >= 0]


def apply_cues(ac, layer, cues, chart=MOUTH9, reset=True):
    """Key the mouth layer: at each cue frame the mouth instance shows chart[shape] (single_frame)."""
    def starts():
        L = next(L for L in ac.info()["layers"] if L["id"] == layer)
        return [k["start"] for k in L["keyframes"]]
    if reset:
        for s in starts():
            if s:
                ac.run("timeline.clear_keyframe", layer=layer, frame=s)
    end = ac.layer_len(layer)
    have = set(starts())
    n = 0
    for c in cues:
        f = c["frame"]
        if f >= end:
            break
        if f not in have:
            ac.run("timeline.insert_keyframe", layer=layer, frame=f); have.add(f)
        ac.at(layer, f, select=True)
        ac.run("element.set_loop", loop="single_frame", first_frame=chart[c["shape"]])
        n += 1
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("audio"); ap.add_argument("--fps", type=float, default=24)
    ap.add_argument("--rhubarb"); ap.add_argument("--offset", type=int, default=0)
    a = ap.parse_args()
    json.dump(cues_for(a.audio, a.fps, a.rhubarb, a.offset), sys.stdout)
