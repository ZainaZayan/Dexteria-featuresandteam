"""Turn the raw film renders into website frames.

Usage: post5.py [raw_dir] [anchors file name] [web folder name]   (defaults: raw anchors.json v5)
For every raw transparent PNG (skips frames already done):
  1. lay it on the brand cream #F0EBE4 with fine film grain (post.py from v3)
  2. desktop frame: 1920 wide WebP, quality 86            -> .../v5/d/f_0001.webp
  3. phone frame: a 1080x1080 square cut around the ball,  -> .../v5/m/f_0001.webp
     full detail, so phones get a sharp ball instead of a shrunk wide frame
Also copies anchors.json next to the frames, adding "mobileX0"/"mobileW"
(where the square cut starts and how wide it is, as fractions of the frame width).
"""
import sys, os, glob, json
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(V5), "v3", "scripts"))
from post import process

raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(V5, "raw")
ANCH_NAME = sys.argv[2] if len(sys.argv) > 2 else "anchors.json"
WEB_NAME = sys.argv[3] if len(sys.argv) > 3 else "v5"
web = os.path.join(os.path.dirname(os.path.dirname(V5)), "web", "demo", "public", "dexteria", WEB_NAME)
os.makedirs(os.path.join(web, "d"), exist_ok=True); os.makedirs(os.path.join(web, "m"), exist_ok=True)
full_dir = os.path.join(V5, "out_" + WEB_NAME); os.makedirs(full_dir, exist_ok=True)

anch = json.load(open(os.path.join(V5, ANCH_NAME)))
W, H = anch["width"], anch["height"]
CX = 0.60                                   # the ball sits a little right of centre in most shots
x0 = int(round(min(max(CX * W - H / 2, 0), W - H)))

done = 0
for k, f in enumerate(sorted(glob.glob(os.path.join(raw, "*.png")))):
    name = os.path.splitext(os.path.basename(f))[0]
    d_out = os.path.join(web, "d", name + ".webp")
    if os.path.exists(d_out) and os.path.getmtime(d_out) > os.path.getmtime(f):
        continue                            # already up to date
    full = os.path.join(full_dir, name + ".png")
    process(f, full, None, None, seed=k, vignette=0.0, falloff=False)   # flat cream, same as the page
    im = Image.open(full).convert("RGB")
    im.save(d_out, "WEBP", quality=86, method=6)
    im.crop((x0, 0, x0 + H, H)).save(os.path.join(web, "m", name + ".webp"), "WEBP", quality=84, method=6)
    done += 1

anch["mobileX0"] = round(x0 / W, 4)
anch["mobileW"] = round(H / W, 4)
json.dump(anch, open(os.path.join(web, "anchors.json"), "w"))
print("POST5", done, "new frames ->", web, flush=True)
