"""Make a tiny demo episode (placeholder art + synthetic voices) in the exact layout build_episode.py expects.
python make_demo_assets.py D:\\youtube\\anicraft\\demo_ep   ->  then: python build_episode.py D:\\youtube\\anicraft\\demo_ep\\episode.json
Replace the PNGs/WAVs with real art (same canvas size per character, transparent) and TTS lines for a real episode.
"""
import json, os, shutil, subprocess, sys
from PIL import Image, ImageDraw

out = sys.argv[1]
FF = os.environ.get("ANICRAFT_FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
CW, CH = 420, 640  # character canvas


def canvas():
    return Image.new("RGBA", (CW, CH), (0, 0, 0, 0))


def character(name, shirt, skin="#f2c19a"):
    d = os.path.join(out, "characters", name); os.makedirs(d, exist_ok=True)
    im = canvas(); g = ImageDraw.Draw(im)
    g.rectangle([150, 560, 190, 635], fill="#3b3b3b"); g.rectangle([230, 560, 270, 635], fill="#3b3b3b")  # legs
    g.rounded_rectangle([120, 300, 300, 570], 30, fill=shirt)                                               # torso
    g.ellipse([125, 70, 295, 290], fill=skin); g.pieslice([120, 50, 300, 200], 180, 360, fill="#222222")    # head + hair
    im.save(os.path.join(d, "body.png"))
    J = {"shoulder_l": [112, 322], "elbow_l": [108, 420], "wrist_l": [106, 515],
         "shoulder_r": [308, 322], "elbow_r": [312, 420], "wrist_r": [314, 515]}
    for s in "lr":                                                   # arms with ROUND CAPS on every joint
        for part, a, b, col in (("upper", "shoulder", "elbow", shirt), ("lower", "elbow", "wrist", skin)):
            im = canvas(); g = ImageDraw.Draw(im); p, q = J[f"{a}_{s}"], J[f"{b}_{s}"]
            g.line([tuple(p), tuple(q)], fill=col, width=30)
            for c in (p, q):
                g.ellipse([c[0] - 15, c[1] - 15, c[0] + 15, c[1] + 15], fill=col)
            if part == "lower":
                g.ellipse([q[0] - 17, q[1] - 6, q[0] + 17, q[1] + 30], fill=skin)   # hand
            im.save(os.path.join(d, f"arm_{s}_{part}.png"))
    json.dump({"canvas": [CW, CH], "joints": J}, open(os.path.join(d, "rig.json"), "w"), indent=1)
    for i, h in enumerate((24, 10, 2)):                                                                    # eyes open/half/closed
        im = canvas(); g = ImageDraw.Draw(im)
        for cx in (180, 240):
            g.ellipse([cx - 16, 175 - h, cx + 16, 175 + h], fill="white", outline="black", width=3)
            if h > 4:
                g.ellipse([cx - 6, 175 - min(h, 8), cx + 6, 175 + min(h, 8)], fill="black")
        im.save(os.path.join(d, f"eyes_{i}.png"))
    for i, h in enumerate((3, 12, 26)):                                                                    # mouth rest/mid/open
        im = canvas(); g = ImageDraw.Draw(im)
        g.ellipse([185, 240 - h / 2, 235, 240 + h / 2], fill="#6b1d1d")
        im.save(os.path.join(d, f"mouth_{i}.png"))


def background(name):
    d = os.path.join(out, "backgrounds"); os.makedirs(d, exist_ok=True)
    im = Image.new("RGB", (1920, 1080), "#9fd3ff"); g = ImageDraw.Draw(im)
    g.rectangle([0, 760, 1920, 1080], fill="#8bc34a")
    g.polygon([(1350, 520), (1550, 380), (1750, 520)], fill="#a0522d"); g.rectangle([1380, 520, 1720, 780], fill="#e0b97a")
    g.rectangle([1520, 640, 1580, 780], fill="#5d3a1a"); g.ellipse([160, 120, 300, 260], fill="#ffd54f")
    im.save(os.path.join(d, name + ".png"))


def voice(path, f0, secs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency={f0}:duration={secs}",
                    "-af", "volume='if(lt(mod(t,0.45),0.28),0.8,0.01)':eval=frame", "-ar", "48000", path], check=True)


character("Ramu", "#e53935"); character("Shyam", "#1e88e5"); background("village")
voice(os.path.join(out, "vo", "001.wav"), 180, 2.2); voice(os.path.join(out, "vo", "002.wav"), 260, 1.8)
voice(os.path.join(out, "vo", "003.wav"), 180, 2.0)
os.makedirs(os.path.join(out, "music"), exist_ok=True)
subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=330:duration=8", "-f", "lavfi", "-i",
                "sine=frequency=440:duration=8", "-filter_complex", "amix=inputs=2,volume=0.3", os.path.join(out, "music", "bed.wav")], check=True)
ep = {"title": "Demo", "fps": 24, "size": [1920, 1080], "music": "music/bed.wav", "shots": [
    {"bg": "village", "chars": [{"name": "Ramu", "x": 620, "y": 640}, {"name": "Shyam", "x": 1150, "y": 640, "flip": True}],
     "lines": [{"who": "Ramu", "wav": "vo/001.wav", "gesture": "explain"}, {"who": "Shyam", "wav": "vo/002.wav", "gesture": "point"}]},
    {"bg": "village", "chars": [{"name": "Ramu", "x": 900, "y": 640}], "lines": [{"who": "Ramu", "wav": "vo/003.wav", "gesture": "namaste"}],
     "camera": {"zoom": 135, "x": 900, "y": 450}},
    {"bg": "village", "chars": [], "hold": 2, "camera": {"zoom": 110, "x": 1500, "y": 600}}]}
json.dump(ep, open(os.path.join(out, "episode.json"), "w", encoding="utf-8"), indent=1)
print("demo episode ready:", os.path.join(out, "episode.json"))
