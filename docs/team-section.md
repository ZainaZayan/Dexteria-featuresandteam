# Team section

Folder: `web/components/team-v3/`

A server component with no JavaScript: portraits and type straight on the page, no cards or shadows,
in the same palette and type scale as the Features section.

Props: `photosPath` (default `"/team"`), the folder that holds the portraits.

## Editing team details

Everything is in the `TEAM` list at the top of `TeamSection.jsx`:

| Field | Meaning |
|---|---|
| `name` | Full name as it should appear |
| `role` | One line. While it is empty the card shows "Role to be confirmed" |
| `photo` | File name inside `photosPath`. While it is empty the card shows the backdrop with initials |
| `linkedin`, `github`, `email` | Leave empty to hide that link |

Phone numbers are not shown, because the page is public.

## Layout

- Wide screens: five portraits in a row.
- Tablets: three per row.
- Phones: one row that swipes sideways, so every portrait stays large.
- Role lines reserve two lines of height, so every row of links lines up.

## How the portraits are made

The photos were taken in different places, at different distances and in different light (a white
wall, a grey wall, a yellow sign, a printed passport photo). To make them read as one set, every
portrait goes through the same two steps.

**1. Cut-out and face detection** (`photos/scripts/cutout.swift`). Uses Apple's Vision framework,
which is built into macOS and runs offline:

- `VNGenerateForegroundInstanceMaskRequest` separates the person from the background,
- `VNDetectFaceLandmarksRequest` finds the face and the centre of each eye.

**2. Composition** (`photos/scripts/compose.py`, NumPy and Pillow):

- **Framing from the eyes.** Each photo is scaled so the distance between the eyes is 15% of the
  frame width, and moved so the eyes sit 40% from the top. Every head ends up the same size and at
  the same height.
- **One backdrop.** Everyone is placed on the same studio backdrop: soft light behind the head,
  slightly darker edges, a faint shadow behind the shoulders.
- **One grade.** Warm black and white. Contrast is measured on the person only and set to the same
  range, and face brightness is matched, so different lighting and colour casts disappear.
- **Clean edges.** The mask is tightened slightly, and the soft edge is filled with the person's own
  nearby tones so no light from the old background shows around the outline. Photos that were
  enlarged more get a proportionally softer edge, which hides stair-stepping.
- **Same grain.** The same fine grain on every portrait, so sharper and softer photos match.

Output: 720 x 900 WebP in `web/demo/public/team/`, plus `placeholder.webp` (the empty backdrop).

One exception is set in `compose.py`: Vinuri's source is a photo of a printed passport photo,
cropped tight at the shoulders, so her portrait is framed slightly closer to keep every edge inside
the print. Remove that line when a normal photo is available.

## Adding or replacing a portrait

Requirements: macOS 14 or newer (for Vision), Python 3 with NumPy and Pillow.

1. Put the photo in `photos/source/`, named after the person (for example `Sima.png`). Source photos
   are kept out of the repository.
2. Cut it out:
   ```bash
   cd photos
   swift scripts/cutout.swift source/Sima.png work/Sima-mask.png work/Sima-face.json
   ```
3. Add the person to `PEOPLE` in `scripts/compose.py`, then run `python scripts/compose.py`.
4. Check `work/contact-sheet.jpg`, then set `photo` in `TeamSection.jsx`.

A good source photo: shoulders visible, plain wall, phone at eye level about one metre away,
soft daylight from the front.
