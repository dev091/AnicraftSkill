# Asset spec (what ChatGPT / Dot must deliver so AniCraft animates it without broken joints)

## Folder per character
```
characters/<Name>/            front 3/4 "talker" (dialogue shots, build_episode.py)
  body.png, eyes_0.png (open), eyes_1.png (half), eyes_2.png (closed), mouth_0..2.png (rest/mid/open)
  or mouth_0..8.png (X A B C D E F G H, Rhubarb chart)
characters/<Name>_side/       side "walker" (rig.py), facing RIGHT
  rig.json + torso, head, arm_near_upper, arm_near_lower (incl. hand), arm_far_upper, arm_far_lower,
  leg_near_thigh, leg_near_shin, foot_near, leg_far_thigh, leg_far_shin, foot_far  (.png or .svg)
backgrounds/<place>.png      1920x1080, no characters, horizon/ground line around y 760-900
```
- Every part file of one character has the SAME canvas size (e.g. 800x1400 talker, 400x720 walker), transparent,
  drawn in its final place, so all parts line up when centred on one point. Far limbs one shade darker.
- Talker eyes/mouth PNGs contain only the eyes/mouth plus a small skin-coloured patch that hides the body's own.

## JOINT RULE (the reason Dot/ChatGPT rigs broke while walking)
1. Every limb segment ends in a ROUND CAP: a circle centred exactly on the joint, radius >= half the limb width.
2. BOTH parts at a joint carry the cap (thigh bottom AND shin top), so any rotation keeps the joint closed.
3. The joint point in `rig.json` is the centre of that circle, in canvas pixels.
4. The torso covers the shoulder and hip caps; the neck extends into the torso.
5. Sleeves/dhoti edges: draw cloth folds on the upper part only; never a straight cut at a joint.
6. Limbs drawn straight and vertical (arms hanging, legs straight) in the neutral pose; feet flat, toes to the right.
`rig.check_art(dir)` measures rule 1-2 on PNGs (opaque disc of 6 px around every joint on both parts).
Then `walk_test.py <dir> <out>` must print ALL PASS (IK reach, foot slide <= 2 px, knee forward, length).

## rig.json
```json
{"canvas": [400, 720],
 "joints": {"neck": [200, 255], "head_top": [200, 95], "shoulder": [200, 285],
            "elbow_near": [200, 395], "wrist_near": [200, 495], "elbow_far": [200, 395], "wrist_far": [200, 495],
            "hip": [200, 465], "knee_near": [200, 570], "ankle_near": [200, 675], "toe_near": [250, 680],
            "knee_far": [200, 570], "ankle_far": [200, 675], "toe_far": [250, 680]},
 "limits": {"knee_near": [0, 150], "knee_far": [0, 150], "elbow_near": [-150, 0], "elbow_far": [-150, 0]}}
```
Thigh and shin about equal length; upper arm and forearm about equal. `make_demo_puppet.py` is a working example.

## Style lock (paste into every image prompt)
"2D Indian village cartoon, clean thin dark-brown outline, flat colours with one soft cel-shadow tone, warm saturated
palette, realistic adult toon proportions (6.5 heads tall), simple friendly faces, no gradients on characters,
no text, no watermark, original character (not based on any existing show)."

## Prompts
- Character sheet (consistency anchor): "Character model sheet of <Name>, <age/role/clothes/colours>, front, 3/4 and
  side view, neutral pose, arms down, full body, plain white background, <style lock>."
- Talker base: "<Name> full body 3/4 front view, arms relaxed, mouth closed, eyes open, transparent or flat #00FF00
  background, centred, 800x1400, <style lock>."
- Mouth / eyes sheet: "Mouth shapes for <Name> in a row on #00FF00: closed, slightly open, open, wide, rounded O,
  puckered U, teeth on lip F, tongue L, rest; same size and position each, <style lock>." (eyes: open, half, closed)
- Walker parts: "Cut-out puppet parts of <Name> side view facing right, each part separate with a gap between parts on
  #00FF00: head with neck, torso with hips, upper arm, forearm with hand, thigh, shin, foot; every limb end is a full
  round circle (rounded joint ends), straight limbs, <style lock>." Then Dot cuts, aligns to rig.json and caps
  anything that fails `check_art`.
- Background: "<place> in an Indian village, <time of day>, wide establishing view, empty of people, ground plane
  in the lower third, 16:9 1920x1080, painted detailed background, <style lock>."
- Thumbnail (1280x720): big emotional face of the hero + the object of the story + high contrast, no small text.
