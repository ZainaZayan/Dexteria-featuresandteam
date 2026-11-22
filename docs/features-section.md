# Features section

Folder: `web/components/features-v4/`

| File | Responsibility |
|---|---|
| `FeaturesSection.jsx` | Scroll to frame, frame loading, drawing on the canvas, callouts, hold ring, motion trail, chapter timeline |
| `Extras.jsx` | The small interactive part under each chapter's text (readouts, chart, voice line, sliders, consent switch) |
| `featuresData.js` | All of the text, and the frame range of every chapter |
| `utils.js` | Small helpers: `clamp`, `smooth`, `frameUrl`, `squeezeAt` |
| `FeaturesSection.module.css` | All styles, including the type scale |

Props: `framesPath` (default `"/dexteria/v51"`), the folder that holds `d/`, `m/` and `anchors.json`.

## Chapters

The film has 266 frames. Each chapter owns a range of them, set in `featuresData.js`.

| Frames | Chapter | Requirements | On screen |
|---|---|---|---|
| 1 to 24 | Intro | | The closed ball on the floor, the camera moves in |
| 25 to 62 | Grip strength and hold time | FR2, FR6, FR7 | A quarter of the shell slides out; the soft layers squeeze and relax |
| 63 to 114 | Movement and tremor | FR3, FR4 | Close-up of the motion sensor, then a steady arc and a shaky arc |
| 115 to 150 | Guided games | FR5, FR18, FR25 | Start button pressed, LEDs light up, the ball squeezes |
| 151 to 184 | Progress against the other hand | FR20, FR22 | The dock slides in and the ball settles onto it |
| 185 to 236 | Clinician-led difficulty | FR8, FR10, FR11 | The ball opens on its mould line and the firmness insert is swapped |
| 237 to 266 | Sharing with the clinician | FR26, FR27, FR32 | The ball turns back, wide closing shot |

## From scroll to frame

1. The section is tall: 5% of the screen height per frame. Inside it, a `position: sticky` box
   holds the canvas and stays on screen while the section scrolls past.
2. Scroll position becomes `progress`, from 0 at the top of the section to 1 at the bottom.
3. A smoothed copy of `progress` follows it with a little inertia, so the film glides rather than
   jumps: `smooth += (progress - smooth) * min(1, dt * 7)`.
4. `frame = 1 + round(smooth * 265)`. Exactly one frame is drawn at a time; frames are never blended.
5. The current chapter is the one whose range contains that frame, so the text always matches the film.

## Callouts

`anchors.json` holds, for every frame, where each part of the ball sits on screen (as fractions of
the frame), plus the ball's centre and radius. The component converts those numbers to pixels with
the same scale and offset it uses to draw the frame, then places:

- a pin on the part,
- a thin SVG leader line,
- the part's name in empty space beside the ball, on whichever side has more room.

On close-ups, where there is no empty space, the label sits on a small flat plate. On phones the
pins are numbered and the names are listed under the chapter text.

## Interaction

| Chapter | What the visitor can do |
|---|---|
| Grip | Press and hold the ball (mouse, touch, Space or Enter). Holding plays the squeeze frames, fills a 5 second hold ring and updates the pressure and hold time readout |
| Movement | A dotted trail follows the ball through the steady pass and the pass with tremor |
| Games | Squeeze the ball to count squeezes; switch the voice line between English, Sinhala and Tamil |
| Progress | The chart draws itself while scrolling (example data, weeks 1 to 8) |
| Difficulty | The clinician slider moves with the film; "Make easier" works, "Make harder" is locked for caregivers |
| Sharing | The consent switch sends the report from phone to Supabase to clinician; switching it off removes access |

The timeline at the bottom shows the current chapter and jumps to any chapter on click.

## Loading and performance

- Frames are loaded rough first: every 8th frame, then every 4th, every 2nd, then the rest, six at
  a time. The film is usable almost immediately and gets smoother as more frames arrive. If a frame
  is not loaded yet, the nearest loaded frame is drawn.
- Every image is decoded (`img.decode()`) before it is used, so drawing never waits on decoding.
- One `requestAnimationFrame` loop does all drawing, and only when something has changed.
- The canvas is never more than twice the screen's pixel size. Drawing a frame takes about 1.6 ms.
- Phones load the square `m/` frames (1080 x 1080) instead of the wide desktop frames.
- Download size for the full film: about 18 MB on desktop and about 8 MB on phones.

## Layout on different screens

- Wide screens: chapter text on the left, the ball on the right, callouts in the space between.
- Portrait screens (taller than wide): the square frame on top with its edges faded into the page,
  the text underneath, numbered pins with a legend.

## Type scale

One family, Archivo, at three widths:

- wide (125) and light for headlines and numbers,
- normal (100) for running text,
- narrow (75) uppercase for small labels.

All sizes are defined once, as `--fs-*` variables at the top of `FeaturesSection.module.css`:
titles 28 to 38 px, body 17 px, captions 13 px, labels 11 px. Change sizes there only.

## Editing the text

Everything a visitor reads is in `featuresData.js`: each chapter has `kicker`, `title`, `body`,
`refs` and its `labels` (callouts, with the frames in which each part is clearly visible).
No other file needs to change for wording edits.

The Sinhala and Tamil versions of "Squeeze gently" (`VOICE_LINES`) should be checked by a native speaker.

## Accessibility

- All text is real HTML, not part of the image. The canvas is hidden from screen readers.
- The current chapter is announced through a polite live region.
- The ball's press and hold works from the keyboard (Space or Enter) and has a label.
- The timeline uses real buttons.
- With "reduce motion" turned on, fades and line drawing animations are switched off; the film
  still follows the scroll.
