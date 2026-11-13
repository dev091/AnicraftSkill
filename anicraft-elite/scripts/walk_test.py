"""Gate test for natural walking: joint caps, IK reach, foot slide, layer order, contact sheet.
python walk_test.py CHAR_DIR OUT_DIR [--seconds 3] [--step 110] [--fps 24]
"""
import argparse, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acsession import AniCraft
from rig import build, check_art, foot_slide, walk

ap = argparse.ArgumentParser(); ap.add_argument("char"); ap.add_argument("out")
ap.add_argument("--seconds", type=float, default=3); ap.add_argument("--step", type=float, default=110)
ap.add_argument("--fps", type=int, default=24); ap.add_argument("--arm-sign", type=int, default=1)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
fails = []


def gate(name, ok, detail):
    print(("PASS " if ok else "FAIL ") + f"{name}: {detail}")
    fails.append(name) if not ok else None


caps = check_art(a.char)
gate("joint caps", not caps, "; ".join(caps[:4]) or "every joint has a round cap on both parts")
N = int(a.seconds * a.fps)
with AniCraft() as ac:
    ac.run("doc.set_stage", width=1920, height=1080, fps=a.fps, background="#cfe8ff")
    bg = ac.info()["layers"][0]["id"]; ac.at(bg, 0)
    ac.run("draw.rect", x=0, y=900, w=1920, h=180, fill="#7cc35a", object=True); ac.fit(bg, N)
    r = build(ac, a.char, x=300, y=572, n=N)                  # demo puppet: ankle (canvas y 675) lands at y 887, sole on 900
    w = walk(ac, r, 0, N, step_px=a.step, frames_per_step=12, arm_sign=a.arm_sign)
    gate("IK reaches targets", w["ik_error_max"] <= 1.5, f"max error {w['ik_error_max']:.2f} px")
    s = foot_slide(ac, r, w)
    gate("no foot slide", s <= 2.0, f"planted foot drifts {s:.2f} px max over every stance frame")
    e = ac.run("bone.info", frame=6, layer=r["layer"])
    knees = {b["name"]: b for arm in e["armatures"] for b in arm["bones"] if b["name"].startswith(("hip_", "knee_"))}
    hx, kx = knees["hip_near"]["head"][0], knees["hip_near"]["tail"][0]
    ax = knees["knee_near"]["tail"][0]
    gate("knee bends forward", kx >= (hx + ax) / 2 - 1, f"knee x {kx:.0f} vs hip/ankle mid {(hx + ax) / 2:.0f}")
    gate("movie length", ac.info()["movie_frames"] == N, str(ac.info()["movie_frames"]))
    doc = os.path.join(a.out, "walk.anicraft")
    ac.run("file.save_as", path=doc, confirm=True)
qa = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_frames.py")
step = max(1, N // 8)
subprocess.run([sys.executable, qa, doc, "--frames", ",".join(str(f) for f in range(1, N + 1, step))], check=False)
print("RESULT:", "FAIL " + ", ".join(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
