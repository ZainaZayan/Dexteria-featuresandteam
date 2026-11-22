"""Post: lay a transparent render over the exact brand cream, add a soft lens vignette and fine grain.
Usage: post.py <in.png|dir> <out.png|dir> [width] [--webp quality] [--seed N]
Grain is added AFTER resizing, so every output size gets the same fine grain."""
import sys, os, glob
import numpy as np
from PIL import Image

CREAM = np.array([0xF0, 0xEB, 0xE4], np.float32) / 255.0


def process(src, dst, width=None, webp=None, seed=0, grain=0.009, vignette=0.035, falloff=True):
    im = Image.open(src).convert("RGBA")
    if width and im.size[0] != width:
        h = round(im.size[1] * width / im.size[0]); im = im.resize((width, h), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255.0
    rgb, al = a[..., :3], a[..., 3:4]
    H, W = al.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx - W / 2) / (W / 2); ny = (yy - H / 2) / (H / 2)
    r2 = nx * nx * 0.75 + ny * ny
    # background: cream with an extremely soft falloff (like a lit studio sweep), never a hard gradient
    bg = CREAM[None, None, :] * ((1.0 + 0.008 - 0.014 * np.clip(r2, 0, 2)[..., None]) if falloff else np.ones((H, W, 1), np.float32))
    out = rgb * al + bg * (1 - al)
    out *= (1.0 - vignette * np.clip(r2 - 0.35, 0, None) ** 1.6)[..., None]
    rs = np.random.RandomState(seed)
    g = rs.normal(0, 1, (H, W)).astype(np.float32)
    lum = out.mean(axis=2, keepdims=True)
    out = out + g[..., None] * grain * (0.6 + 0.6 * lum)   # film grain, slightly stronger in mids/highs
    out = np.clip(out, 0, 1)
    img = Image.fromarray((out * 255 + 0.5).astype(np.uint8))
    if webp:
        img.save(dst, "WEBP", quality=int(webp), method=6)
    else:
        img.save(dst, optimize=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    webp = None; seed = None; flat = False
    if "--flat" in args: args.remove("--flat"); flat = True
    if "--webp" in args: i = args.index("--webp"); webp = args[i + 1]; del args[i:i + 2]
    if "--seed" in args: i = args.index("--seed"); seed = int(args[i + 1]); del args[i:i + 2]
    src, dst = args[0], args[1]; width = int(args[2]) if len(args) > 2 else None
    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        files = sorted(glob.glob(os.path.join(src, "*.png")))
        for k, f in enumerate(files):
            name = os.path.splitext(os.path.basename(f))[0] + (".webp" if webp else ".png")
            process(f, os.path.join(dst, name), width, webp, seed=k, vignette=0.0 if flat else 0.035, falloff=not flat)
        print("POST", len(files), "->", dst)
    else:
        process(src, dst, width, webp, seed=seed or 0, vignette=0.0 if flat else 0.035, falloff=not flat); print("POST", dst)
