"""Regression test for this skill's assumptions. Run after every AniCraft update:
    python selftest.py OUT_DIR
Builds a tiny document with every recipe, renders frames with file.export_png and checks pixels. Prints PASS/FAIL.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from acsession import AniCraft
from recipes import blink, breathe, camera_push, walk_across

out = sys.argv[1] if len(sys.argv) > 1 else "selftest_out"
os.makedirs(out, exist_ok=True)
fails = []
RED, BLUE, WHITE, BLACK, GREEN = (220, 30, 30), (30, 30, 220), (250, 250, 250), (10, 10, 10), (30, 160, 60)


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (": " + detail if detail else ""))
    if not ok:
        fails.append(name)


def frame_png(ac, f):
    p = os.path.join(out, f"f{f:03d}.png")
    if os.path.exists(p):
        os.remove(p)
    ac.run("file.export_png", path=p, frame=f)
    return Image.open(p).convert("RGB")


def pixels(im, col, tol=40):
    px, w, h = im.load(), *im.size
    pts = [(x, y) for y in range(h) for x in range(w) if all(abs(px[x, y][i] - col[i]) <= tol for i in range(3))]
    if not pts:
        return 0, None, None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return len(pts), sum(xs) / len(xs), max(ys) - min(ys) + 1


def shape_symbol(ac, layer, name, frames, x, y, w, h, kind="draw.rect"):
    """Symbol whose frame i is a w*h shape of colour frames[i]; returns the instance id."""
    ac.at(layer, 0)
    ac.run(kind, x=x, y=y, w=w, h=h, fill="#%02x%02x%02x" % frames[0], object=True)
    ac.run("element.pick", x=x + w / 2, y=y + h / 2)
    inst = ac.run("modify.convert_to_symbol", name=name, kind="graphic")["instance"]
    if len(frames) > 1:
        ac.run("symbol.edit")
        inner = ac.info()["layer"]
        for i, c in enumerate(frames[1:], 1):
            ac.key(inner, i, blank=True)
            ac.run(kind, x=-w / 2, y=-h / 2, w=w, h=h, fill="#%02x%02x%02x" % c, object=True)
        ac.run("symbol.exit", all=True)
    return inst


N, FPS = 120, 24
with AniCraft() as ac:
    ac.run("doc.set_stage", width=480, height=270, fps=FPS, background="#808080")
    walk = ac.info()["layers"][0]["id"]
    ac.run("layer.rename", layer=walk, name="Walker")
    shape_symbol(ac, walk, "Cycle", [RED, BLUE], 20, 150, 40, 80)
    dx = walk_across(ac, walk, N, stride_px=8, frames_per_step=4)
    eyes = ac.run("layer.new", name="Eyes")["layer"]
    shape_symbol(ac, eyes, "Eyes", [WHITE, (128, 128, 250), BLACK], 300, 20, 60, 30, "draw.ellipse")
    keys = blink(ac, eyes, N, FPS)
    chest = ac.run("layer.new", name="Chest")["layer"]
    shape_symbol(ac, chest, "Chest", [GREEN], 400, 100, 40, 100)
    half = breathe(ac, chest, N, FPS, period_s=2.0, amount_pct=20)
    cam = camera_push(ac, N, zoom=120, x=240, y=135)
    info = ac.info()
    check("movie length", info["movie_frames"] == N, f"{info['movie_frames']} frames")
    zmid = ac.run("camera.info", frame=N // 2)["zoom"]
    check("camera push tweens", 100 < zmid < 120, f"zoom at mid {zmid:.1f}")
    ac.run("camera.set", reset=True, frame=0); ac.run("camera.set", reset=True, frame=N - 1)  # measure in stage space
    f0, f1, fl = frame_png(ac, 0), frame_png(ac, 1), frame_png(ac, N - 1)
    r0, b1 = pixels(f0, RED), pixels(f1, BLUE)
    check("walk cycle loops inside tween", r0[0] > 0 and b1[0] > 0, f"f0 red {r0[0]}px, f1 blue {b1[0]}px")
    last = pixels(fl, RED)[1] or pixels(fl, BLUE)[1]
    check("walk travel = stride/step (no slide)", last is not None and abs(last - (40 + dx)) <= 2,
          f"x {last and round(last)} vs {40 + dx:.0f}")
    closed = next(k for k, v in sorted(keys.items()) if v == 2)
    check("blink closes eyes", pixels(frame_png(ac, closed), BLACK)[0] > 0 and pixels(f0, WHITE)[0] > 0, f"closed at f{closed}")
    h0, hp = pixels(f0, GREEN)[2], pixels(frame_png(ac, half), GREEN)[2]
    check("breathing scales chest", h0 and hp and hp > h0 * 1.1, f"height {h0} -> {hp}")
    ac.run("file.save_as", path=os.path.join(out, "selftest.anicraft"), confirm=True)
print("RESULT:", "FAIL " + ", ".join(fails) if fails else "ALL PASS")
sys.exit(1 if fails else 0)
