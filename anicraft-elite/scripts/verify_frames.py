"""Measured QA for an AniCraft shot: structure, sampled frames, contact sheet, video + loudness gates.

python verify_frames.py shot.anicraft [--frames 1,24,48] [--scale 0.25] [--video shot.mp4]
  [--expect-frames N] [--expect-size 1920x1080] [--expect-fps 24] [--lufs -14] [--tp -1]
Prints one line per check, PASS/FAIL, and writes <shot>_qa/contact.jpg (view ONE image, not every frame).
Exit 1 if any gate FAILS. CLI frames here are 1-based (as on the timeline). Needs Pillow; ffmpeg via ANICRAFT_FFMPEG.
"""
import argparse, json, os, re, shutil, subprocess, sys
from PIL import Image, ImageChops, ImageDraw, ImageStat

CLI = os.environ.get("ANICRAFT_CLI", r"C:\Program Files\ArtCraft\AniCraft\anicraft-cli.exe")
FFMPEG = os.environ.get("ANICRAFT_FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
fails = []


def gate(name, ok, detail):
    print(("PASS " if ok else "FAIL ") + name + ": " + detail)
    if not ok:
        fails.append(name)


ap = argparse.ArgumentParser()
ap.add_argument("doc"); ap.add_argument("--frames"); ap.add_argument("--scale", type=float, default=0.25)
ap.add_argument("--video"); ap.add_argument("--expect-frames", type=int); ap.add_argument("--expect-size")
ap.add_argument("--expect-fps", type=float); ap.add_argument("--lufs", type=float, default=-14.0)
ap.add_argument("--tp", type=float, default=-1.0)
a = ap.parse_args()

info = json.loads(subprocess.run([CLI, "info", a.doc], capture_output=True, text=True, check=True).stdout)
st = info.get("stage", info)
w, h, fps = st.get("width"), st.get("height"), st.get("fps")
total = info.get("movie_frames") or info.get("frames")
print(f"doc: {w}x{h} @ {fps} fps, {total} frames, layers: " + ", ".join(
    f"{L['name']}[{sum(k['duration'] for k in L['keyframes'])}f/{len(L['keyframes'])}k]" for L in info.get("layers", [])))
if a.expect_frames:
    gate("frame count", total == a.expect_frames, f"{total} vs {a.expect_frames}")
if a.expect_size:
    gate("stage size", f"{w}x{h}" == a.expect_size, f"{w}x{h}")
if a.expect_fps:
    gate("fps", abs((fps or 0) - a.expect_fps) < 0.01, str(fps))
lens = {L["name"]: sum(k["duration"] for k in L["keyframes"]) for L in info.get("layers", [])}
short = {n: l for n, l in lens.items() if total and l < total}
gate("layers cover the shot", not short, "short: " + json.dumps(short) if short else "all layers reach the last frame")

frames = [int(x) for x in a.frames.split(",")] if a.frames else sorted({1, max(1, (total or 1) // 2), total or 1})
out = os.path.splitext(a.doc)[0] + "_qa"
os.makedirs(out, exist_ok=True)
ims = []
for f in frames:
    png = os.path.join(out, f"f{f:04d}.png")
    if os.path.exists(png):
        os.remove(png)
    r = subprocess.run([CLI, "render", a.doc, "--frame", str(f), "--scale", str(a.scale), "--out", png], capture_output=True, text=True)
    if r.returncode:
        gate(f"render f{f}", False, r.stderr.strip()[:200]); continue
    ims.append((f, Image.open(png).convert("RGB")))
for (f0, i0), (f1, i1) in zip(ims, ims[1:]):
    d = sum(ImageStat.Stat(ImageChops.difference(i0, i1)).mean) / 3
    print(f"motion f{f0}->f{f1}: mean abs diff {d:.2f}" + ("  (identical: a hold or nothing moves)" if d < 0.05 else ""))
if ims:
    tw, th = ims[0][1].size
    sheet = Image.new("RGB", ((tw + 8) * min(4, len(ims)), (th + 8) * ((len(ims) + 3) // 4)), "white")
    for i, (f, im) in enumerate(ims):
        x, y = (i % 4) * (tw + 8), (i // 4) * (th + 8)
        sheet.paste(im, (x, y)); ImageDraw.Draw(sheet).text((x + 4, y + 4), f"f{f}", fill="black")
    sheet.save(os.path.join(out, "contact.jpg"), quality=80)
    print("contact sheet:", os.path.join(out, "contact.jpg"))

if a.video:
    probe = subprocess.run([FFMPEG, "-hide_banner", "-i", a.video, "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True, errors="replace").stderr
    vs = re.search(r"Video: (\w+).*?, (\d+)x(\d+).*?, ([\d.]+) fps", probe)
    has_audio = "Audio:" in probe
    gate("video stream", bool(vs), f"{vs.group(1)} {vs.group(2)}x{vs.group(3)} {vs.group(4)} fps" if vs else "none")
    if vs and a.expect_size:
        gate("video size", f"{vs.group(2)}x{vs.group(3)}" == a.expect_size, f"{vs.group(2)}x{vs.group(3)}")
    gate("audio stream", has_audio, "present" if has_audio else "missing")
    if has_audio:
        I = re.findall(r"I:\s+(-?[\d.]+|-inf) LUFS", probe)
        P = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", probe)
        lufs = float(I[-1]) if I and I[-1] != "-inf" else None
        tp = float(P[-1]) if P and P[-1] != "-inf" else None
        gate("loudness", lufs is not None and abs(lufs - a.lufs) <= 1.0, f"{lufs} LUFS (target {a.lufs} +/-1)")
        gate("true peak", tp is not None and tp <= a.tp, f"{tp} dBTP (max {a.tp})")

print("RESULT:", "FAIL " + ", ".join(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
