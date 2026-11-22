"""Render frames of one v4 feature blend.
Usage: Blender -b <feature>.blend --python render4.py -- <outdir> <W> <H> <samples> <frames "1-24" or "1,12"> [skip]

Speed settings (same look, less waste):
  - adaptive sampling stops early on clean pixels, OpenImageDenoise cleans the rest
  - fewer light bounces: a soft studio does not need 10+ bounces
  - no motion blur: the website scrubs frame by frame, blur would only cost time
"""
import bpy, sys, os, time
a = sys.argv[sys.argv.index("--") + 1:]
out, W, H, S, spec = a[0], int(a[1]), int(a[2]), int(a[3]), a[4]
skip = len(a) > 5 and a[5] == "skip"
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.cycles.samples = S
sc.cycles.adaptive_threshold = 0.02
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 3
sc.cycles.transmission_bounces = 6; sc.cycles.transparent_max_bounces = 10
sc.render.use_motion_blur = False
sc.render.use_persistent_data = True
sc.render.image_settings.color_depth = '8'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'; prefs.get_devices()
for d in prefs.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
frames = []
for part in spec.split(","):
    step = 1
    if ":" in part: part, st = part.split(":"); step = int(st)
    if "-" in part:
        x, y = part.split("-"); frames += list(range(int(x), int(y) + 1, step))
    else: frames.append(int(part))
os.makedirs(out, exist_ok=True)
t_all = time.time()
for f in frames:
    path = os.path.join(out, f"f_{f:04d}.png")
    if skip and os.path.exists(path): continue
    t0 = time.time(); sc.frame_set(f); sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"FRAME {f} {time.time() - t0:.1f}s", flush=True)
print(f"ALL DONE {len(frames)} frames {time.time() - t_all:.0f}s", flush=True)
