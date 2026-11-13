"""Front / 3-4 view TALKER rig with gestures. One graphic symbol per character per shot holds body + arm bones +
eyes + mouth, so breathing, moves and flips act on ONE instance and the parts never drift apart.

Character folder (all files one canvas size, transparent, drawn in place; l/r = SCREEN left/right):
  body.png (no arms) | arm_l_upper.png arm_l_lower.png (forearm incl. hand) | arm_r_upper.png arm_r_lower.png
  eyes_0..2.png | mouth_0..N.png | rig.json {"canvas": [W, H], "joints": {shoulder_l, elbow_l, wrist_l, shoulder_r,
  elbow_r, wrist_r, (optional) chest, head_side_l, head_side_r, hip_l, hip_r}}
  JOINT RULE: round caps centred on shoulder/elbow on both parts. Arms drawn hanging straight down.
Without arm files or rig.json the body is used as drawn (lip-sync + blinks only).

t = build_talker(ac, layer, "characters/Ramu", x, y, N, flip=False)  # on the main timeline, at frame 0
with_symbol(ac, t, lambda: gesture_track(ac, t, [(0, "rest"), (30, "explain"), (90, "namaste")], N, talking=[(30, 88)]))
"""
import json, math, os

GESTURES = {  # per arm: (anchor joint, dx, dy) in arm lengths, screen space (+x right, +y down); missing arm = hang
    "rest": {},
    "explain": {"l": ("shoulder_l", 0.40, 0.62), "r": ("shoulder_r", -0.40, 0.62)},
    "point_l": {"l": ("shoulder_l", -0.95, -0.10)},
    "point_r": {"r": ("shoulder_r", 0.95, -0.10)},
    "namaste": {"l": ("chest", -0.04, 0.0), "r": ("chest", 0.04, 0.0)},
    "worry": {"r": ("head_side_r", 0.02, 0.0)},          # hand on head
    "angry": {"l": ("hip_l", -0.05, 0.0), "r": ("hip_r", 0.05, 0.0)},   # hands on hips, elbows out
    "shrug": {"l": ("shoulder_l", -0.50, 0.50), "r": ("shoulder_r", 0.50, 0.50)},
    "wave_r": {"r": ("shoulder_r", 0.55, -0.80)},
}


def _mirror_files(d, names):
    from PIL import Image, ImageOps
    md = os.path.join(d, "_mirror"); os.makedirs(md, exist_ok=True)
    out = {}
    for n in names:
        src, dst = os.path.join(d, n), os.path.join(md, n)
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            ImageOps.mirror(Image.open(src)).save(dst)
        out[n] = dst
    return out


def _joints(spec, W, H, flip):
    J = {k: [float(v[0]), float(v[1])] for k, v in spec["joints"].items()}
    if flip:  # mirror x and swap screen sides
        J = {(k[:-1] + ("r" if k.endswith("_l") else "l") if k.endswith(("_l", "_r")) else k): [W - v[0], v[1]] for k, v in J.items()}
    L = math.dist(J["shoulder_l"], J["wrist_l"])
    J.setdefault("chest", [(J["shoulder_l"][0] + J["shoulder_r"][0]) / 2, J["shoulder_l"][1] + 0.35 * L])
    J.setdefault("hip_l", [J["shoulder_l"][0] - 0.05 * L, J["shoulder_l"][1] + 0.95 * L])
    J.setdefault("hip_r", [J["shoulder_r"][0] + 0.05 * L, J["shoulder_r"][1] + 0.95 * L])
    J.setdefault("head_side_r", [J["shoulder_r"][0] - 0.15 * L, J["shoulder_r"][1] - 0.75 * L])
    J.setdefault("head_side_l", [J["shoulder_l"][0] + 0.15 * L, J["shoulder_l"][1] - 0.75 * L])
    return {k: [v[0] - W / 2, v[1] - H / 2] for k, v in J.items()}, L     # symbol space: origin = canvas centre


def _bitmap(ac, path):
    r = ac.run("file.import_to_library", path=path)
    return r.get("bitmap") or r.get("id")


def _sym_from_bitmaps(ac, layer, name, paths, x, y):
    ac.at(layer, 0)
    ac.run("library.place", bitmap=_bitmap(ac, paths[0]), x=x, y=y)
    inst = ac.run("modify.convert_to_symbol", name=name, kind="graphic")["instance"]
    if len(paths) > 1:
        ac.run("symbol.edit")
        inner = ac.info()["layer"]
        for i, p in enumerate(paths[1:], 1):
            ac.key(inner, i, blank=True)
            ac.run("library.place", bitmap=_bitmap(ac, p), x=0, y=0)
        ac.run("symbol.exit")
    return inst


def with_symbol(ac, t, fn):
    """Run fn() inside this talker's symbol (commands then act on its timeline), then come back."""
    ac.run("symbol.edit", id=t["instance"])
    try:
        return fn()
    finally:
        ac.run("symbol.exit", all=True)


def build_talker(ac, layer, d, x, y, n, flip=False, name=None):
    name = name or os.path.basename(d.rstrip("/\\"))
    files = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    mouths = sorted(f for f in files if f.startswith("mouth_"))
    has_arms = os.path.exists(os.path.join(d, "rig.json")) and all(
        f"arm_{s}_{p}.png" in files for s in "lr" for p in ("upper", "lower"))
    names = ["body.png"] + [f"eyes_{i}.png" for i in range(3)] + mouths + (
        [f"arm_{s}_{p}.png" for s in "lr" for p in ("upper", "lower")] if has_arms else [])
    path = _mirror_files(d, names) if flip else {k: os.path.join(d, k) for k in names}
    if flip:  # mirrored screen-left arm art now sits on screen right: swap the names
        path = {k.replace("arm_l_", "arm_X_").replace("arm_r_", "arm_l_").replace("arm_X_", "arm_r_"): v for k, v in path.items()}
    ac.at(layer, 0)
    ac.run("library.place", bitmap=_bitmap(ac, path["body.png"]), x=x, y=y)
    inst = ac.run("modify.convert_to_symbol", name=f"{name}_char", kind="graphic")["instance"]
    t = {"instance": inst, "layer": layer, "name": name, "has_arms": has_arms, "bones": {}, "chart_n": len(mouths)}
    ac.run("symbol.edit", id=inst)
    try:
        body_layer = ac.info()["layer"]
        ac.fit(body_layer, n)
        if has_arms:
            spec = json.load(open(os.path.join(d, "rig.json"), encoding="utf-8"))
            W, H = spec["canvas"]
            J, L = _joints(spec, W, H, flip)
            t["J"], t["L"] = J, L
            body_inst = ac.at(body_layer, 0, select=True)["selected"][0]
            arm = {}
            for s in "lr":
                for p in ("upper", "lower"):
                    ac.at(body_layer, 0)
                    ac.run("library.place", bitmap=_bitmap(ac, path[f"arm_{s}_{p}.png"]), x=0, y=0)
                    arm[s, p] = ac.run("modify.convert_to_symbol", name=f"{name}_arm_{s}_{p}", kind="graphic")["instance"]
            for s in "lr":
                b1 = ac.run("bone.add", {"from": body_inst, "to": arm[s, "upper"], "head": J[f"shoulder_{s}"],
                                         "tail": J[f"elbow_{s}"], "name": f"shoulder_{s}"})
                b2 = ac.run("bone.add", {"from": arm[s, "upper"], "to": arm[s, "lower"], "tail": J[f"wrist_{s}"],
                                         "name": f"elbow_{s}"})
                t["bones"][f"shoulder_{s}"], t["bones"][f"elbow_{s}"], t["arm_layer"] = b1["bone"], b2["bone"], b1["layer"]
            ac.fit(t["arm_layer"], n)
            _set_elbow_side(ac, t)
        for part, files_ in (("eyes", [path[f"eyes_{i}.png"] for i in range(3)]), ("mouth", [path[m] for m in mouths])):
            t[f"{part}_layer"] = ac.run("layer.new", name=f"{name}_{part}")["layer"]
            ac.fit(t[f"{part}_layer"], n)
            _sym_from_bitmaps(ac, t[f"{part}_layer"], f"{name}_{part}", files_, 0, 0)
    finally:
        ac.run("symbol.exit", all=True)
    return t


def _elbow_out(ac, t, s, f=0):
    bi = ac.run("bone.info", frame=f, layer=t["arm_layer"])
    b = {x["name"]: x for a in bi["armatures"] for x in a["bones"]}
    sh, el, wr = b[f"shoulder_{s}"]["head"], b[f"shoulder_{s}"]["tail"], b[f"elbow_{s}"]["tail"]
    out_x = el[0] - (sh[0] + wr[0]) / 2
    return out_x < 0 if s == "l" else out_x > 0


def _set_elbow_side(ac, t):
    """Pick elbow limits so IK bends elbows outward/down (natural), whatever the engine's sign convention."""
    for s in "lr":
        for lo, hi in ((0, 150), (-150, 0)):
            ac.run("bone.set_limits", bone=t["bones"][f"elbow_{s}"], constrain=True, min=lo, max=hi)
            _solve(ac, t, s, "explain", 0)
            ok = _elbow_out(ac, t, s)
            _hang(ac, t, s, 0)
            if ok:
                t[f"elbow_limits_{s}"] = (lo, hi)
                break


def _hang(ac, t, s, f):
    ac.run("bone.pose", bone=t["bones"][f"shoulder_{s}"], angle=0, frame=f)
    ac.run("bone.pose", bone=t["bones"][f"elbow_{s}"], angle=0, frame=f)


def _solve(ac, t, s, gesture, f, jitter=(0.0, 0.0)):
    g = GESTURES[gesture].get(s)
    if not g:
        return _hang(ac, t, s, f)
    anchor, dx, dy = g
    ax, ay = t["J"][anchor]
    return ac.run("bone.solve", bone=t["bones"][f"elbow_{s}"], x=ax + (dx + jitter[0]) * t["L"],
                  y=ay + (dy + jitter[1]) * t["L"], frame=f)


def pose(ac, t, gesture, f, jitter=(0.0, 0.0)):
    """Key both arms in `gesture` at frame f (call inside with_symbol)."""
    for s in "lr":
        _solve(ac, t, s, gesture, f, jitter)


def gesture_track(ac, t, events, n, talking=(), blend=5, beat=12):
    """events: [(frame, gesture)] sorted. Holds each gesture, blends over `blend` frames into the next,
    and while talking (list of (start, end) frames) adds small hand beats every `beat` frames."""
    if not t.get("has_arms"):
        return 0
    keys = {}
    ev = sorted(events) or [(0, "rest")]
    if ev[0][0] > 0:
        ev.insert(0, (0, "rest"))
    for i, (f, g) in enumerate(ev):
        keys[f] = (g, (0.0, 0.0))
        nxt = ev[i + 1][0] if i + 1 < len(ev) else n
        if nxt - blend > f:
            keys[nxt - blend] = (g, (0.0, 0.0))              # hold until the blend starts
        for a, b in talking:
            k = 0
            for bf in range(max(a, f) + beat, min(b, nxt - blend) - 2, beat):
                k += 1
                keys[bf] = (g, (0.03 * (-1) ** k, -0.04 * (k % 2)))
    for f in sorted(k for k in keys if k < n):
        g, j = keys[f]
        pose(ac, t, g, f, j)
    return len(keys)
