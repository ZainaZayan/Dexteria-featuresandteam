# The 3D film

The film is a pre-rendered sequence, not live 3D in the browser. Cycles is a path tracer, so soft
shadows, the soft-touch shell, the foam and the translucent air bladder look photographic, which a
real-time browser renderer cannot match on an ordinary laptop. The website then only has to draw
pictures, which keeps it simple and fast. The trade-off is that the visitor cannot spin the ball
freely, so the interaction is built on top instead (press and hold, the switches, the timeline).

## Files

| File | Purpose |
|---|---|
| `3d/v3/dexteria-ball-v3.blend` | The finished model. All textures are packed inside the file |
| `3d/v3/scripts/studio.py` | Shared set-up: render engine settings, lighting, the studio floor and the camera |
| `3d/v5/scripts/film51.py` | The film: story, camera, every movement, and the anchor export |
| `3d/v4/scripts/render4.py` | Renders a range of frames on the GPU |
| `3d/v5/scripts/post5.py` | Turns rendered frames into website frames (uses `3d/v3/scripts/post.py`) |
| `3d/v5/scripts/run51.sh` | Runs rendering and export unattended, in passes |
| `3d/v5/anchors51.json` | Screen positions of each part, for every frame |

The folder names (`v3`, `v4`, `v5`) are the iteration in which each piece was finalised.

## The model

Built in Blender with Python (`bpy`) rather than by hand, so every dimension and change is written
down and the model can be rebuilt exactly. It contains:

- the shell: a sphere with two raised logo panels, the start button and its LED ring, and the mould
  parting line,
- three foam layers and the swappable firmness insert,
- the sealed air bladder,
- a clear chassis with the electronics: ESP32-C3 board, 6-axis motion sensor (MPU-6050), pressure
  sensor and ADC, charger and protection boards, battery, wiring and pogo pins,
- the charging dock.

The circuit boards are drawn with Python (copper, pads, silkscreen) and used as textures. A realism
pass adds the soft-touch surface, light wear and open-cell foam.

## The film

`film51.py` opens the model, builds the whole animation and saves `3d/v5/film51.blend`.

Techniques used:

- **Keyframes with eased curves.** Each moving part has a few keyframes; Blender fills the frames in
  between with Bezier curves, so every move starts and ends softly. The camera starts its next move
  before the previous action has ended, and drifts slowly during holds, so the picture is never
  completely still.
- **Nothing passes through anything.** The cutaway quarter only slides in directions that keep it
  inside its own quarter. When the ball opens, the halves lift only along the parting-line axis and
  outer layers always stay above inner ones.
- **Opening on the real parting line.** The shell and foam are cut with a Boolean modifier on the
  same plane as the mould line, so the top lifts off the way a moulded part would.
- **Squeeze rig.** The soft parts are parented to an empty whose scale is animated (narrower and
  slightly taller). The electronics are not parented to it, because hard parts do not squeeze.
- **Hiding what cannot be seen.** Parts inside the closed ball are switched off for rendering in
  the frames where they are hidden. Rendering is faster and nothing can show through by accident.
- **Anchors.** For every frame, `world_to_camera_view` gives the on-screen position of each part.
  These go into `anchors51.json`, which the website uses to pin the labels and overlays.

## Rendering

- Cycles on the GPU (Metal on Apple silicon), 1920 x 1080, 48 samples with adaptive sampling,
  denoised with OpenImageDenoise.
- Light bounces are limited to what the scene needs, and motion blur is off, because the frames are
  shown one at a time while scrolling.
- The background is transparent, with a shadow catcher floor that keeps only the shadow.
- Frames render in passes: every 4th frame, then every 2nd, then the rest. Frames that already exist
  are skipped, so a pass can be stopped and resumed.

## Export for the web

`post5.py` processes every new frame:

1. lays it on the page colour `#F0EBE4` with a fine film grain, so the frames blend into the page,
2. saves a 1920 px wide WebP (quality 86) to `d/`,
3. saves a 1080 x 1080 square crop around the ball (quality 84) to `m/`, so phones get a sharp ball
   instead of a shrunken wide frame,
4. copies the anchors next to the frames, with the position of the square crop added.

## Re-rendering

Requirements: Blender 5.3 and Python 3 with NumPy and Pillow (`pip install -r 3d/requirements.txt`).

```bash
cd 3d/v5
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/film51.py   # builds film51.blend
mkdir -p logs
zsh scripts/run51.sh                                                            # renders and exports
```

`run51.sh` expects the Python environment at `3d/v3/.venv` (change `PY=` at the top to use another).
A full render of 266 frames takes several hours on an M4 MacBook.
