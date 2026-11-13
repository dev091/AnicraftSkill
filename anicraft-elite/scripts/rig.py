"""Joint-safe cut-out character rig + natural IK walk for AniCraft.

Character folder (side view, facing right):
  rig.json  {"canvas": [W, H], "joints": {name: [x, y]}, "limits": {bone: [min, max]} (optional)}
  <part>.png or <part>.svg for each PART below, every file the SAME canvas size (transparent), so they align.
Joint names: neck, head_top, shoulder, elbow_near, wrist_near, elbow_far, wrist_far, hip, knee_near, ankle_near,
toe_near, knee_far, ankle_far, toe_far.
JOINT RULE (why limbs never break): every limb segment ends in a round cap whose centre IS the joint, radius >= half
the limb width, on BOTH parts of the joint. `check_art()` measures it before anything is built.

from rig import build, walk, foot_slide
r = build(ac, "characters/Ramu_side", x=400, y=600, n=N)       # x,y = where the canvas centre goes
walk(ac, r, 0, N, step_px=110, frames_per_step=12)               # 2 steps/s at 24 fps, feet planted (IK)
foot_slide(ac, r, range(N))  -> max px a planted foot moves (gate <= 2)
"""
import json, math, os

PARTS = ["arm_far_upper", "arm_far_lower", "leg_far_thigh", "leg_far_shin", "foot_far",      # back to front
         "torso", "head", "leg_near_thigh", "leg_near_shin", "foot_near", "arm_near_upper", "arm_near_lower"]
BONES = [  # name, from part, to part, head joint, tail joint (parents first)
    ("neck", "torso", "head", "neck", "head_top"),
    ("shoulder_near", "torso", "arm_near_upper", "shoulder", "elbow_near"),
    ("elbow_near", "arm_near_upper", "arm_near_lower", "elbow_near", "wrist_near"),
    ("shoulder_far", "torso", "arm_far_upper", "shoulder", "elbow_far"),
    ("elbow_far", "arm_far_upper", "arm_far_lower", "elbow_far", "wrist_far"),
    ("hip_near", "torso", "leg_near_thigh", "hip", "knee_near"),
    ("knee_near", "leg_near_thigh", "leg_near_shin", "knee_near", "ankle_near"),
    ("ankle_near", "leg_near_shin", "foot_near", "ankle_near", "toe_near"),
    ("hip_far", "torso", "leg_far_thigh", "hip", "knee_far"),
    ("knee_far", "leg_far_thigh", "leg_far_shin", "knee_far", "ankle_far"),
    ("ankle_far", "leg_far_shin", "foot_far", "ankle_far", "toe_far"),
]
CAPS = {"elbow_near": ("arm_near_upper", "arm_near_lower"), "elbow_far": ("arm_far_upper", "arm_far_lower"),
        "knee_near": ("leg_near_thigh", "leg_near_shin"), "knee_far": ("leg_far_thigh", "leg_far_shin"),
        "shoulder": ("arm_near_upper", "arm_far_upper"), "hip": ("leg_near_thigh", "leg_far_thigh"),
        "ankle_near": ("leg_near_shin", "foot_near"), "ankle_far": ("leg_far_shin", "foot_far")}


def _file(d, part):
    for ext in (".svg", ".png"):
        if os.path.exists(os.path.join(d, part + ext)):
            return os.path.join(d, part + ext)
    raise FileNotFoundError(f"{d}: missing {part}.png/.svg")


def check_art(d, min_r=6):
    """Joint-cap test on PNG parts: each part touching a joint must be opaque in a disc of radius min_r around it."""
    from PIL import Image
    spec = json.load(open(os.path.join(d, "rig.json"), encoding="utf-8"))
    J, fails = spec["joints"], []
    for joint, parts in CAPS.items():
        x0, y0 = J[joint]
        for p in parts:
            f = _file(d, p)
            if f.endswith(".svg"):
                continue
            a = Image.open(f).convert("RGBA").split()[-1]
            holes = sum(1 for dy in range(-min_r, min_r + 1) for dx in range(-min_r, min_r + 1)
                        if dx * dx + dy * dy <= min_r * min_r and a.getpixel((int(x0 + dx), int(y0 + dy))) < 200)
            if holes:
                fails.append(f"{p} has {holes} transparent px within {min_r}px of joint {joint}")
    return fails


def build(ac, d, x, y, n, layer=None):
    """Place the parts (z-ordered) on one layer, convert to symbols, join with bones. Returns the rig dict."""
    spec = json.load(open(os.path.join(d, "rig.json"), encoding="utf-8"))
    W, H = spec["canvas"]
    ox, oy = x - W / 2, y - H / 2                       # canvas -> stage offset
    J = {k: [v[0] + ox, v[1] + oy] for k, v in spec["joints"].items()}
    if layer is None:
        layer = ac.run("layer.new", name=os.path.basename(d.rstrip("/\\")))["layer"]
    ac.fit(layer, n)
    ac.at(layer, 0)
    inst = {}
    for p in PARTS:
        f = _file(d, p)
        r = ac.run("file.import_to_library", path=f)
        item = {k: r[k] for k in ("symbol", "bitmap") if r.get(k) is not None}
        placed = ac.run("library.place", **item, x=x, y=y)
        ac.run("element.select", ids=[placed["element"]])
        inst[p] = placed["element"] if "symbol" in item else ac.run("modify.convert_to_symbol", name=f"{os.path.basename(d)}_{p}")["instance"]
    bones, arm_layer = {}, None
    for name, a, b, hj, tj in BONES:
        r = ac.run("bone.add", {"from": inst[a], "to": inst[b], "head": J[hj], "tail": J[tj], "name": name})
        bones[name], arm_layer = r["bone"], r["layer"]
    ac.fit(arm_layer, n)
    for name, (lo, hi) in spec.get("limits", {"knee_near": [0, 150], "knee_far": [0, 150],
                                              "elbow_near": [-150, 0], "elbow_far": [-150, 0]}).items():
        ac.run("bone.set_limits", bone=bones[name], constrain=True, min=lo, max=hi)
    return {"bones": bones, "layer": arm_layer, "joints": J, "dir": d, "x": x, "y": y}


def _ends(ac, r, f):
    """{bone name: (joint xy, end xy, angle)} at frame f, for this rig's armature layer."""
    info = ac.run("bone.info", frame=f, layer=r["layer"])
    out = {}
    for arm in info.get("armatures", []):
        for b in arm.get("bones", []):
            out[b.get("name")] = (b.get("head"), b.get("tail"), b.get("angle", 0.0))
    return out


def _plant(w, side, t):
    """(stance?, target x, target y) of one foot at walk time t (frames since start)."""
    ph = 0.0 if side == "near" else 0.5
    T, S = w["T"], w["step"]
    u = t / T + ph
    k, p = math.floor(u), u % 1.0
    plant = w["hip0"] + S / 2 + 2 * S * k - ph * 2 * S
    if p < 0.5:
        return True, plant, w["ground"]
    s = (p - 0.5) / 0.5
    s2 = s * s * (3 - 2 * s)
    return False, plant + 2 * S * s2, w["ground"] - w["lift"] * math.sin(math.pi * s)


def walk(ac, r, start, n, step_px=110, frames_per_step=12, lift_px=None, bob_px=None, arm_swing=22, key_every=2, arm_sign=1):
    """IK walk to the right: stance foot locked to the ground, swing foot arcs, body bobs, arms counter-swing.
    Travel = step_px per frames_per_step exactly, so planted feet do not slide. Keys every `key_every` frames.
    Returns the walk spec for foot_slide()."""
    J0 = r["joints"]
    leg = J0["ankle_near"][1] - J0["hip"][1]
    w = {"start": start, "n": n, "T": 2 * frames_per_step, "step": step_px, "hip0": J0["hip"][0],
         "ground": J0["ankle_near"][1], "lift": lift_px if lift_px is not None else 0.12 * leg}
    bob = bob_px if bob_px is not None else 0.035 * leg
    # a straight leg cannot reach a foot step/2 ahead: lower the hip by the reach deficit (+2 px) for the whole walk
    drop = leg - math.sqrt(max(leg * leg - (step_px / 2) ** 2, 1.0)) + 2.0
    v = step_px / frames_per_step
    frames = list(range(start, start + n, key_every))
    if frames[-1] != start + n - 1:
        frames.append(start + n - 1)
    cx = cy = 0.0
    errs = []
    for f in frames:
        t = f - start
        bx, by = v * t, drop + bob * (1 + math.cos(4 * math.pi * t / w["T"])) / 2   # lowest at contacts, highest at passing
        ac.run("bone.pose", layer=r["layer"], dx=bx - cx, dy=by - cy, frame=f)
        cx, cy = bx, by
        for side in ("near", "far"):
            _, ax, ay = _plant(w, side, t)
            res = ac.run("bone.solve", bone=r["bones"][f"knee_{side}"], x=ax, y=ay, frame=f)
            errs.append(res.get("error", 0.0))
        e = _ends(ac, r, f)
        for side in ("near", "far"):
            ac.run("bone.pose", bone=r["bones"][f"ankle_{side}"], angle=-(e[f"hip_{side}"][2] + e[f"knee_{side}"][2]), frame=f)
            ph = 0.0 if side == "near" else 0.5
            fwd = math.cos(2 * math.pi * (t / w["T"] + ph))          # +1 when this leg is forward
            ac.run("bone.pose", bone=r["bones"][f"shoulder_{side}"], angle=-arm_sign * arm_swing * fwd, frame=f)
            ac.run("bone.pose", bone=r["bones"][f"elbow_{side}"], angle=-arm_sign * (12 + 8 * (1 - fwd) / 2), frame=f)
    w["ik_error_max"] = max(errs) if errs else 0.0
    return w


def foot_slide(ac, r, w):
    """Max |ankle x - planted x| over EVERY stance frame (tweened ones too). Gate: <= 2 px."""
    worst = 0.0
    for f in range(w["start"], w["start"] + w["n"]):
        e = _ends(ac, r, f)
        for side in ("near", "far"):
            stance, x, _ = _plant(w, side, f - w["start"])
            if stance:
                worst = max(worst, abs(e[f"knee_{side}"][1][0] - x))
    return worst
