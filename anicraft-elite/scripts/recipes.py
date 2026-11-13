"""Reusable AniCraft animation recipes on top of acsession. Each is exercised by selftest.py.

camera_push(ac, n, zoom)                      camera layer, key at end, Smooth tween
blink(ac, eyes_layer, n, fps)                 Eyes symbol frames 0 open / 1 half / 2 closed, random 2-4.5 s
walk_across(ac, layer, n, stride_px, fps_step) loop a walk-cycle graphic and travel exactly stride/step (no foot slide)
breathe(ac, layer, n, fps, amount_pct)        motion tween on scale_y, one breath per `period_s`
All frames are 0-based. Each function leaves the layer exactly n frames long.
"""
import random


def camera_push(ac, n, zoom=115, x=960, y=540, easing="Smooth"):
    cam = ac.run("camera.add")["layer"]
    ac.fit(cam, n)
    ac.key(cam, n - 1)
    ac.run("camera.set", zoom=zoom, x=x, y=y, frame=n - 1)
    ac.run("timeline.create_tween", layer=cam, frame=0, easing=easing)
    return cam


def _pose(ac, layer, f, frame_in_symbol):
    ac.at(layer, f, select=True)
    ac.run("element.set_loop", loop="single_frame", first_frame=frame_in_symbol)


def blink(ac, layer, n, fps, every_s=(2.0, 4.5), closed=2, seed=7):
    """Layer holds one Eyes instance. Returns the keyed frames {frame: symbol_frame}."""
    ac.fit(layer, n)
    rng = random.Random(seed)
    keys, f = {0: 0}, int(fps * rng.uniform(*every_s))
    while f + closed + 2 < n:
        keys.update({f: 1, f + 1: 2, f + 1 + closed: 1, f + 2 + closed: 0})
        f += int(fps * rng.uniform(*every_s))
    have = {k["start"] for L in ac.info()["layers"] if L["id"] == layer for k in L["keyframes"]}
    for k in sorted(keys):
        if k not in have:
            ac.run("timeline.insert_keyframe", layer=layer, frame=k)
        _pose(ac, layer, k, keys[k])
    return keys


def walk_across(ac, layer, n, stride_px, frames_per_step, direction=1, easing="Linear"):
    """Layer holds one walk-cycle graphic instance at frame 0 (its own timeline = the cycle).
    Travel = (n-1)/frames_per_step * stride_px so feet do not slide. Returns dx."""
    ac.fit(layer, n)
    _pose(ac, layer, 0, 0)
    ac.run("element.set_loop", loop="loop", first_frame=0)
    dx = direction * (n - 1) / frames_per_step * stride_px
    ac.key(layer, n - 1)
    ac.at(layer, n - 1, select=True)
    ac.run("element.translate", dx=dx, dy=0)
    ac.run("timeline.create_tween", layer=layer, frame=0, easing=easing)
    return dx


def breathe(ac, layer, n, fps, period_s=3.0, amount_pct=1.5):
    """Idle breathing: motion tween on the layer's instance, scale_y 100 -> 100+amount -> 100 per period."""
    ac.fit(layer, n)
    ac.run("timeline.create_motion_tween", layer=layer, frame=0)
    half = max(1, int(fps * period_s / 2))
    f, up = 0, False
    while f < n:
        ac.run("motion.set_key", layer=layer, property="scale_y", value=100 + (amount_pct if up else 0), frame=f)
        f += half
        up = not up
    ac.run("motion.set_ease", layer=layer, easing="QuadInOut", frame=0)
    return half
