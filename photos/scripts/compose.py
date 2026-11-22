"""Make every team portrait look like it came from the same photo shoot.

The source photos were taken in different places (white wall, grey wall, a yellow sign),
at different distances and in different light. For each person this script:

  1. takes the cut-out mask and eye positions from cutout.swift (Apple Vision)
  2. frames them the same way: eyes 40% from the top, eye distance 15% of the width,
     so every head is the same size and sits at the same height
  3. puts them on one studio backdrop (soft light behind the head, darker edges)
  4. grades everyone to the same warm black and white, so different lighting and
     colour casts (like the yellow sign) disappear
  5. adds the same fine film grain to everything, so sharp and soft photos match

Usage (from the photos/ folder):  python scripts/compose.py
Output: ../web/demo/public/team/<name>.webp, placeholder.webp, and work/contact-sheet.jpg
"""
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # photos/
OUT = os.path.join(os.path.dirname(ROOT), "web", "demo", "public", "team")
os.makedirs(OUT, exist_ok=True)

# everyone who has sent a photo: name -> source file in photos/source/
PEOPLE = {"Zaina": "Zaina.jpeg", "Sima": "Sima.png", "Safiya": "Safiya.jpeg", "Raiqa": "Raiqa.jpeg", "Vinuri": "Vinuri.jpeg"}

# Vinuri's photo is a phone picture of a printed passport photo: the print is cropped tight
# at the shoulders, so at the normal framing her body would end in a hard line inside the frame.
# For her only: frame closer, so every edge of the frame stays inside the print.
# (Replace with a normal photo when she sends one, and delete this line.)
SPECIAL = {"Vinuri": {"gap": 0.23, "eye_line": 0.42}}

W, H = 720, 900          # 4:5 portrait, enough for a 360px wide card on a retina screen
EYE_LINE = 0.40          # eyes sit 40% down from the top
EYE_GAP = 0.15           # distance between the eyes, as a share of the width
SHADOW = np.array([0.115, 0.108, 0.098])    # warm black
HIGHLIGHT = np.array([0.968, 0.952, 0.928])  # warm paper white


def blur(a, r):
    """Fast soft blur: three box blurs in a row look like a gaussian blur."""
    for _ in range(3):
        for axis in (0, 1):
            pad = [(0, 0), (0, 0)]
            pad[axis] = (r + 1, r)
            c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis)
            if axis == 0:
                a = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
            else:
                a = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return a


def backdrop():
    """The shared studio backdrop, as brightness from 0 (black) to 1 (white)."""
    y, x = np.mgrid[0:H, 0:W] / np.array([H, W]).reshape(2, 1, 1)
    glow = np.exp(-(((x - 0.5) / 0.55) ** 2 + ((y - 0.34) / 0.5) ** 2))  # light behind the head
    edge = np.clip(np.hypot(x - 0.5, (y - 0.45) * 0.9) - 0.3, 0, None)    # darker corners
    return 0.835 + 0.06 * glow - 0.16 * edge - 0.035 * y


def tone(lum):
    """Brightness -> warm black and white RGB."""
    lum = np.clip(lum, 0, 1)[..., None]
    return SHADOW + (HIGHLIGHT - SHADOW) * lum


def finish(lum, seed):
    """Same grain on every image, then save-ready RGB."""
    rng = np.random.default_rng(seed)
    grain = blur(rng.normal(0, 1, lum.shape), 1) * 0.03
    rgb = tone(lum + grain)
    return Image.fromarray((rgb * 255 + 0.5).clip(0, 255).astype(np.uint8))


def portrait(name, file):
    special = SPECIAL.get(name, {})
    src = np.asarray(Image.open(os.path.join(ROOT, "source", file)).convert("RGB"), dtype=np.float64) / 255
    mask = np.asarray(Image.open(os.path.join(ROOT, "work", name + "-mask.png")).convert("L"), dtype=np.float64) / 255
    face = json.load(open(os.path.join(ROOT, "work", name + "-face.json")))

    # black and white with a little more red, which keeps skin soft and even
    lum = src[..., 0] * 0.40 + src[..., 1] * 0.48 + src[..., 2] * 0.12

    # same contrast for everyone, measured on the person only
    person = mask > 0.5
    lo, hi = np.percentile(lum[person], [0.5, 99.7])
    lum = np.clip((lum - lo) / (hi - lo), 0, 1) * 0.93 + 0.02

    # same face brightness for everyone
    fx, fy, fw, fh = face["face"]
    inner = lum[int(fy + fh * 0.25):int(fy + fh * 0.8), int(fx + fw * 0.2):int(fx + fw * 0.8)]
    lum = lum ** (np.log(0.6) / np.log(inner.mean()))

    # clean edges: tighten the mask a little, and fill the soft edge with the person's
    # own nearby tones so no light from the old wall shows around the outline
    alpha = np.clip((mask - 0.12) / 0.8, 0, 1)
    solid = (alpha > 0.97).astype(float)
    spread = blur(lum * solid, 6) / np.maximum(blur(solid, 6), 1e-4)
    lum = np.where(alpha < 0.97, spread * (1 - alpha) + lum * alpha, lum)
    lum = np.where(solid > 0, lum, np.clip(spread, 0, 1))

    # framing: scale and position from the eyes
    (lx, ly), (rx, ry) = face["leftEye"], face["rightEye"]
    gap = np.hypot(rx - lx, ry - ly)
    crop_w = gap / special.get("gap", EYE_GAP)
    crop_h = crop_w * H / W
    cx, cy = (lx + rx) / 2, (ly + ry) / 2
    eye = special.get("eye_line", EYE_LINE)
    box = (cx - crop_w / 2, cy - eye * crop_h, cx + crop_w / 2, cy + (1 - eye) * crop_h)

    def place(a):  # outside the photo the mask is 0, so the backdrop shows there
        img = Image.fromarray(a.astype(np.float32))
        return np.asarray(img.transform((W, H), Image.Transform.EXTENT, box, Image.Resampling.BICUBIC), dtype=np.float64)

    lum_out, alpha_out = place(lum), np.clip(place(alpha), 0, 1)

    # smooth the outline: small photos get enlarged more, so their mask edges get
    # stair-stepped; soften in proportion to the enlargement, then firm it up again
    scale = W / crop_w
    alpha_out = blur(alpha_out, max(1, round(1.4 * scale)))
    alpha_out = np.clip((alpha_out - 0.2) / 0.6, 0, 1)
    alpha_out = alpha_out * alpha_out * (3 - 2 * alpha_out)

    # a little crispness after enlarging (only the person, not the backdrop)
    lum_out = lum_out + 0.5 * (lum_out - blur(lum_out, 1)) * alpha_out

    # soft shadow on the backdrop behind the shoulders, like a real studio light
    bg = backdrop()
    shade = blur(np.roll(np.roll(alpha_out, 14, axis=1), 10, axis=0), 28)
    bg = bg - 0.06 * shade

    out = lum_out * alpha_out + bg * (1 - alpha_out)
    print(f"{name}: source {crop_w:.0f}px wide -> {W}px ({scale:.2f}x)")
    return finish(out, seed=len(name))


sheet = []
for n, f in PEOPLE.items():
    im = portrait(n, f)
    im.save(os.path.join(OUT, n.lower() + ".webp"), "WEBP", quality=86, method=6)
    sheet.append(im)

blank = finish(backdrop(), seed=7)  # for people whose photo has not arrived yet
blank.save(os.path.join(OUT, "placeholder.webp"), "WEBP", quality=86, method=6)
sheet.append(blank)

contact = Image.new("RGB", (W * len(sheet) + 20 * (len(sheet) - 1), H), (240, 235, 228))
for k, im in enumerate(sheet):
    contact.paste(im, (k * (W + 20), 0))
contact.save(os.path.join(ROOT, "work", "contact-sheet.jpg"), quality=88)
print("saved to", OUT)
