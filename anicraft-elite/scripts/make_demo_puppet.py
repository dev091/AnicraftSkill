"""Demo side-view puppet that follows the JOINT RULE (round caps centred on joints), for rig.py tests.
python make_demo_puppet.py OUT_DIR [--name Ramu_side]  -> OUT_DIR/<name>/{rig.json, <part>.png}
"""
import argparse, json, os
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--name", default="Ramu_side")
a = ap.parse_args()
W, H = 400, 720
J = {"neck": [200, 255], "head_top": [200, 95], "shoulder": [200, 285], "elbow_near": [200, 395], "wrist_near": [200, 495],
     "elbow_far": [200, 395], "wrist_far": [200, 495], "hip": [200, 465], "knee_near": [200, 570], "ankle_near": [200, 675],
     "toe_near": [250, 680], "knee_far": [200, 570], "ankle_far": [200, 675], "toe_far": [250, 680]}
SKIN, SKIN_D, SHIRT, PANT, PANT_D, SHOE = "#f2c19a", "#d9a47c", "#e53935", "#3949ab", "#283593", "#4e342e"
d = os.path.join(a.out, a.name); os.makedirs(d, exist_ok=True)


def seg(p, q, w, col, img=None):
    """Limb segment p->q, width w, ROUND CAPS of radius w/2 centred on both joints."""
    img = img or Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(img)
    g.line([tuple(p), tuple(q)], fill=col, width=w)
    for c in (p, q):
        g.ellipse([c[0] - w / 2, c[1] - w / 2, c[0] + w / 2, c[1] + w / 2], fill=col)
    return img


def save(img, name):
    img.save(os.path.join(d, name + ".png"))


for side, sk, pa in (("far", SKIN_D, PANT_D), ("near", SKIN, PANT)):
    save(seg(J["shoulder"], J[f"elbow_{side}"], 30, SHIRT if side == "near" else "#b71c1c"), f"arm_{side}_upper")
    lo = seg(J[f"elbow_{side}"], J[f"wrist_{side}"], 26, sk)
    ImageDraw.Draw(lo).ellipse([J[f"wrist_{side}"][0] - 18, J[f"wrist_{side}"][1] - 10, J[f"wrist_{side}"][0] + 18, J[f"wrist_{side}"][1] + 22], fill=sk)
    save(lo, f"arm_{side}_lower")
    save(seg(J["hip"], J[f"knee_{side}"], 40, pa), f"leg_{side}_thigh")
    save(seg(J[f"knee_{side}"], J[f"ankle_{side}"], 34, pa), f"leg_{side}_shin")
    ft = seg(J[f"ankle_{side}"], J[f"toe_{side}"], 26, SHOE)
    save(ft, f"foot_{side}")
t = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(t)
g.rounded_rectangle([160, 260, 240, 490], 36, fill=SHIRT)                 # torso incl. hips (covers hip + shoulder caps)
save(t, "torso")
h = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(h)
g.rectangle([188, 225, 212, 275], fill=SKIN)                               # neck overlaps torso
g.ellipse([125, 95, 275, 245], fill=SKIN); g.pieslice([120, 80, 280, 200], 180, 360, fill="#222222")
g.ellipse([228, 150, 246, 170], fill="white"); g.ellipse([236, 155, 245, 166], fill="black")   # eye (facing right)
g.arc([220, 190, 262, 215], 20, 120, fill="#6b1d1d", width=4)
save(h, "head")
json.dump({"canvas": [W, H], "joints": J}, open(os.path.join(d, "rig.json"), "w"), indent=1)
print("puppet:", d)
