"""Reference shot, end to end, every step verified on anicraft-cli 0.2.1 (Windows, 2026-11-13):
stage -> BG with parallax depth -> character symbols + bone arm wave -> mouth lip-sync from a voice wav
-> camera push-in -> stream dialogue -> save -> MP4 (AAC) -> loudness pass -> verify_frames gates.

python example_shot.py OUT_DIR [--voice voice.wav] [--seconds 3] [--fps 24]
Without --voice a synthetic talk-like test wav is generated. Copy this file per shot and replace the
primitive shapes with real character art (import SVG/PNG to the library, then library.place).
"""
import argparse, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acsession import AniCraft
from lipsync import cues_for, apply_cues, MOUTH3

FFMPEG = os.environ.get("ANICRAFT_FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("--voice"); ap.add_argument("--seconds", type=float, default=3)
ap.add_argument("--fps", type=int, default=24)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
N = int(a.seconds * a.fps)                    # shot length in frames
LAST = N - 1                                   # engine frames are 0-based
voice = a.voice or os.path.join(a.out, "voice_test.wav")
if not a.voice:
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency=220:duration={a.seconds}",
                    "-af", "volume='if(lt(mod(t,0.6),0.35),1,0.02)':eval=frame", voice], check=True)
voice_n = os.path.join(a.out, "voice_-16lufs.wav")   # pre-level dialogue so the mix lands near -14 LUFS
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", voice, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", voice_n], check=True)


def sym(ac, name, x, y, w, h, color, shape="draw.rect"):
    ac.run(shape, x=x, y=y, w=w, h=h, fill=color, object=True)
    ac.run("element.pick", x=x + w / 2, y=y + h / 2)
    return ac.run("modify.convert_to_symbol", name=name, kind="graphic")["instance"]


with AniCraft() as ac:
    ac.run("doc.set_stage", width=1920, height=1080, fps=a.fps, background="#cfe8ff")
    bg = ac.info()["layers"][0]["id"]
    ac.run("layer.rename", layer=bg, name="BG")
    ac.at(bg, 0)
    ac.run("draw.rect", x=0, y=820, w=1920, h=260, fill="#7cc35a", object=True)
    ac.fit(bg, N)

    body = ac.run("layer.new", name="Body")["layer"]; ac.fit(body, N); ac.at(body, 0)
    torso = sym(ac, "Torso", 880, 520, 160, 300, "#3a6fd8")
    upper = sym(ac, "UpperArm", 1040, 540, 130, 40, "#f2c19a")
    fore = sym(ac, "Forearm", 1170, 540, 120, 40, "#e9a97f")
    b1 = ac.run("bone.add", {"from": torso, "to": upper, "head": [1040, 560], "tail": [1170, 560], "name": "shoulder"})
    b2 = ac.run("bone.add", {"from": upper, "to": fore, "tail": [1290, 560], "name": "elbow"})
    arm = b1["layer"]; ac.fit(arm, N)
    ac.run("bone.set_limits", bone=b2["bone"], constrain=True, min=0, max=150)
    for f, s, e in ((0, 0, 0), (LAST // 2, -70, 40), (LAST, 0, 0)):   # wave: up at mid-shot, back down
        ac.run("bone.pose", bone=b1["bone"], angle=s, frame=f)
        ac.run("bone.pose", bone=b2["bone"], angle=e, frame=f)

    head = ac.run("layer.new", name="Head")["layer"]; ac.fit(head, N); ac.at(head, 0)
    sym(ac, "Head", 870, 300, 180, 200, "#f2c19a", "draw.ellipse")
    mouth = ac.run("layer.new", name="Mouth")["layer"]; ac.fit(mouth, N); ac.at(mouth, 0)
    sym(ac, "Mouth", 920, 440, 80, 12, "#5a1e1e", "draw.ellipse")      # frame 0 = rest (X)
    ac.run("symbol.edit")                                                # origin = centre of the art
    inner = ac.info()["layer"]
    ac.key(inner, 1, blank=True); ac.run("draw.ellipse", x=-35, y=-10, w=70, h=20, fill="#7a2020", object=True)  # mid
    ac.key(inner, 2, blank=True); ac.run("draw.ellipse", x=-40, y=-25, w=80, h=50, fill="#a02525", object=True)  # open
    ac.run("symbol.exit", all=True)
    cues = cues_for(voice_n, a.fps)
    print("lipsync keys:", apply_cues(ac, mouth, cues, MOUTH3))

    cam = ac.run("camera.add")["layer"]; ac.fit(cam, N)
    ac.key(cam, LAST)
    ac.run("camera.set", zoom=125, x=960, y=500, frame=LAST)
    ac.run("timeline.create_tween", layer=cam, frame=0, easing="Smooth")
    ac.run("layer.set_depth", layer=bg, depth=400)                       # BG drifts less than the character

    ac.at(cam, 0)
    snd = ac.run("file.import", path=voice_n)
    ac.run("sound.set", layer=snd["layer"], frame=0, sync="stream")      # stream = locked to frames (dialogue)
    ac.fit(snd["layer"], N)
    info = ac.info()
    assert info["movie_frames"] == N, f"movie is {info['movie_frames']} frames, wanted {N}"
    doc = os.path.join(a.out, "shot.anicraft")
    ac.run("file.save_as", path=doc, confirm=True)
    raw = os.path.join(a.out, "shot_raw.mp4")
    print("video:", {k: v for k, v in ac.run("file.export_video", path=raw, confirm=True).items() if k in ("frames", "audio", "bytes")})

final = os.path.join(a.out, "shot.mp4")
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", raw, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-ar", "48000", "-c:a", "aac", "-b:a", "192k", final], check=True)
qa = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_frames.py"), doc, "--video", final,
      "--expect-frames", str(N), "--expect-size", "1920x1080", "--expect-fps", str(a.fps)]
sys.exit(subprocess.run(qa).returncode)
