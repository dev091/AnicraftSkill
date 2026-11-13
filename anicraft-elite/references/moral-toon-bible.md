# Hindi moral-story toon bible (measured 2026-11-13, yt-dlp public data)

## Top 3 competitors for this exact format (village / garib / food-vendor kahani)
| channel | subs | median views (last 30) | typical length | what wins |
|---|---|---|---|---|
| Dream Toon | 1.88M | 343K | 20-27 min | village mystery (`Gaon Ka Rahasya`, `Rahasyamayi Dhaba`), night/horror grading |
| Gomu Toons | 67K | 290K | 20-28 min | `garib <food> wala` at a place (railway station, rain): 9.3x outlier `Gaon Mein Bread Pizza Wala` |
| Hindi Kahaniya | 11.4M | 227K | 13-14 min | `Gaon Me <dish>` series (Dosa, Chole Kulche, Paneer Roll), fast cutting |
Adjacent formats with higher medians: Riya Jungle Tv (animals/Panchatantra, 1.5M median), PunToon Kids (kids/school,
418K), Spicy Sas Bahu (family drama, 276K, outliers to 16x). Breakouts: Modern Toonss `Baarish Mein Garib Ke Ghar
Mehmaan` 52x; Apno Tak Toons `Garib Parivar Ki Anokhi Diwali` 118x (festival timing).
Chhota Bheem (Green Gold) links could not be measured (yt-dlp: not available): style class = fully animated 2D
Flash; study only, never use its characters, names, designs or music.

## Craft numbers (first 180 s of 5 refs)
| ref | shot median | shot p90 | LUFS |
|---|---|---|---|
| Apno Tak Toons | 11.5 s | 15.0 s | -20.6 |
| Dream Toon | 11.6 s | 33.1 s | -11.7 |
| Hindi Kahaniya (2) | 3.9 / 4.0 s | 13.9 / 10.9 s | -15.7 / -13.7 |
| Gomu Toons | 10.6 s | 21.0 s | -23.9 |
Targets for us: shot median 4-8 s (beat the slow ones, match Hindi Kahaniya), never a static frame > 3 s (camera
drift, blink, idle, lip-sync always running), master -14 LUFS / -1 dBTP (refs are inconsistent: we win on sound).

## Look (from stills)
- Adults in realistic toon proportions (6-7 heads), 3/4 front view for dialogue, side view for walking.
- Clean thin dark outline, flat colour + one shadow tone (cel), warm saturated palette; night = blue grade + moon.
- Indian village/town: thatch or tile huts, mud courtyards, charpai, handpump, food carts, police station, railway
  platform, kitchens with steel utensils. Clothing: saree, dhoti-kurta, gamchha, lungi, school uniform, khaki police.
- Backgrounds are detailed painted plates (where AI images shine); characters are clean flat cut-outs on top.
- Opening: channel logo sting (2-3 s) then an establishing wide (aerial village or location), then medium two-shots.

## Story shape (12-25 min)
1. Hook 0-15 s: the garib hero's problem in one line + a visual of the place.
2. Setup: family, the craft or stall, a mean rich neighbour or official.
3. Escalation x3: humiliation, loss, a test of honesty; each re-hook <= 60 s (a question or a reveal).
4. Turn: kindness or a clever idea (often magical or a stranger's reward).
5. Payoff: success; the greedy one is punished or learns.
6. Moral line spoken in the last 30 % (`Seekh: ...`), CTA to the next episode.
Title shape: `<Devanagari hook> | <Roman transliteration> | Hindi Kahaniya | Moral Stories` with a place + garib/food
/ weather / festival word. Score titles with `yt-intel-analyst` before locking.

## Shot grammar for our builder
- Dialogue: medium two-shot (both characters full body or knee-up), slow push-in 100->106-112 %, cut to a single
  close-up (135 %) on the emotional line. Speaker lip-syncs, listener blinks and breathes.
- Movement: side-view walk with `rig.walk` (planted feet), camera follows or the character crosses frame.
- Insert shots: food, object, reaction (2-3 s) to keep the shot median down.
- Transitions: hard cuts in scenes; dip-to-black or a whoosh between locations.
