# Adding the sections to the main landing page

Both sections are React components with CSS Modules. They need React 18 or newer and nothing else,
so they work in Next.js and in Vite + React.

Tested in the team's Vite project (Vite 5.4, React 18.3) by following the steps below exactly:
the production build passes with no warnings, and both sections work on desktop and phone,
including press and hold, callouts, the chapter timeline and the team links.

## 1. Copy the files

| From this repository | To the main site |
|---|---|
| `web/components/features-v3/` | components folder |
| `web/components/team-v3/` | components folder |
| `web/demo/public/dexteria/v51/` | `public/dexteria/v51/` |
| `web/demo/public/team/` | `public/team/` |

## 2. Load the font

Both sections use Archivo with its width axis, read from the CSS variable `--font-archivo`.
Without it they fall back to Helvetica Neue or Arial and lose their character.

**Next.js** (in the root layout):

```jsx
import { Archivo } from "next/font/google";

const archivo = Archivo({ subsets: ["latin"], axes: ["wdth"], variable: "--font-archivo", display: "swap" });

// <html lang="en" className={archivo.variable}>
```

**Vite or plain HTML** (in `index.html`, then set the variable once in the global CSS):

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap" />
```

```css
:root { --font-archivo: "Archivo"; }
```

## 3. Render them

```jsx
import FeaturesSection from "./components/features-v3/FeaturesSection";
import TeamSection from "./components/team-v3/TeamSection";

<FeaturesSection framesPath="/dexteria/v51" />
<TeamSection photosPath="/team" />
```

The Team section has `id="team"`, so a nav link to `#team` scrolls to it.

## 4. Check after merging

- **Global styles.** If the main site styles bare elements globally (for example `header`, `nav` or
  `h2`), check that they do not change these sections. The Features timeline already resets the
  `height` a global `nav` rule might set.
- **A sticky site header.** The film fills the full screen height. A sticky header of the main site
  will sit over the top of it, which is fine, but check that it does not cover the chapter text on
  short laptop screens.
- **Dark mode.** Both sections are always cream. If the main site switches to a dark theme, decide
  whether these sections should stay light.
- **Wording.** "Practice", "progress", "wellness"; never "therapy", "treatment" or "medical-grade".
- **Production build.** Run `npm run build` once after merging.
