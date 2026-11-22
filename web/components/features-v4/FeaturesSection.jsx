"use client";
/*
 * FeaturesSection.jsx (v4)
 * -------------------------
 * One continuous 3D film of the Dexteria ball, played by scrolling.
 *
 * How it works, in short:
 *  1. Blender rendered the film as 266 still images (frames).
 *  2. This section is very tall. Inside it, a "sticky" box stays on screen while you scroll.
 *  3. Scroll position -> a number from 0 to 1 (progress) -> a frame number.
 *     We draw that frame on a <canvas>. Scrolling down plays the film, scrolling up rewinds it.
 *  4. The film is split into chapters (featuresData.js). The text of the current chapter
 *     sits on the left, the ball on the right.
 *  5. Callouts follow the real parts: Blender exported where each part is on screen in every
 *     frame (anchors.json), so a pin sits exactly on the part and a thin line leads to its name.
 *  6. In some chapters you can press and hold the ball: it plays the squeeze frames.
 *
 * Feel:
 *  - inertia: the film glides towards your scroll position instead of jumping
 *  - exactly ONE real frame is on screen at any time (no mixing of frames), like a video
 *
 * Performance:
 *  - ONE requestAnimationFrame loop does all the drawing, only when something changed
 *  - every image is decoded before it is used (img.decode), so scrolling never waits
 *  - frames load "rough first": every 8th frame, then every 4th, then the rest
 *  - the canvas is never bigger than 2x the screen pixels
 *
 * Props (optional):
 *   framesPath  folder with d/ (desktop) and m/ (phone) frames and anchors.json
 */
import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import styles from "./FeaturesSection.module.css";
import { CHAPTERS, FRAME_COUNT } from "./featuresData";
import { clamp, frameUrl, squeezeAt } from "./utils";
import Extras from "./Extras";

const VH_PER_FRAME = 5; // scroll length: 5% of the screen height per frame

/* Which chapter a frame belongs to. */
function chapterOf(frame) {
  const i = CHAPTERS.findIndex((c) => frame >= c.frames[0] && frame <= c.frames[1]);
  return i < 0 ? 0 : i;
}

/* Where the picture sits inside the canvas (pixels).
   Desktop: the 16:9 frame covers the whole screen, like CSS "background-size: cover".
   Phone:   the square phone frame sits at the top, full width, the text goes underneath. */
function layoutBox(cw, ch, mobile) {
  if (!mobile) {
    const s = Math.max(cw / 16, ch / 9);
    return { x: (cw - 16 * s) / 2, y: (ch - 9 * s) / 2, w: 16 * s, h: 9 * s };
  }
  const size = Math.min(cw, ch * 0.52);
  return { x: (cw - size) / 2, y: ch * 0.04, w: size, h: size };
}

/* The image for frame n, or the nearest frame that has loaded so far. */
function pick(images, n) {
  for (let d = 0; d < images.length; d++) {
    if (images[n - d]) return images[n - d];
    if (images[n + d]) return images[n + d];
  }
  return null;
}

/* Callouts: where each label's text goes.
   Desktop: in the empty cream space beside the ball, joined to the part by a thin line,
   so text never sits on top of the picture. Close-ups (no empty space): next to the part,
   on a small cream plate. Labels are spread out so they never overlap. */
function layoutCallouts(items, ball, radius, w) {
  if (!items.length) return [];
  const captionRight = Math.min(104, Math.max(20, w * 0.06)) + Math.min(440, w * 0.38) + 32;
  const right = ball ? ball.x + radius + 40 : w;
  const left = ball ? ball.x - radius - 40 : 0;
  let side = 1;
  let x = right;
  let plate = false;
  if (right > w - 190) {
    if (left - 170 >= captionRight) {
      side = -1; // room between the text column and the ball
      x = left;
    } else {
      plate = true; // close-up: the ball fills the screen, the label goes up and away from the part
      x = Math.min(w - 190, Math.max(...items.map((it) => it.p.x)) + 70);
    }
  }
  let lastY = -Infinity;
  return [...items]
    .sort((a, b) => a.p.y - b.p.y)
    .map((it) => {
      const y = Math.max(plate ? it.p.y - 90 : it.p.y, lastY + 52);
      lastY = y;
      return { ...it, x, y, side, plate };
    });
}

export default function FeaturesSection({ framesPath = "/dexteria/v51" }) {
  const sectionRef = useRef(null);
  const canvasRef = useRef(null);
  const imagesRef = useRef(new Array(FRAME_COUNT + 1)); // index 1..FRAME_COUNT
  // values that change many times a second live in a ref (no React re-render needed)
  const live = useRef({ progress: 0, smooth: 0, holding: false, holdStart: 0, squeeze: 0, canHold: false, dirty: true, mobile: false });

  const [frame, setFrame] = useState(1); // frame on screen
  const [scrollFrame, setScrollFrame] = useState(1); // frame chosen by the scroll alone
  const [squeeze, setSqueeze] = useState(0); // 0 = relaxed, 1 = fully squeezed (by you)
  const [hold, setHold] = useState(0); // seconds you have been holding
  const [pulses, setPulses] = useState(0); // finished squeezes (games)
  const [anchors, setAnchors] = useState(null);
  const [mobile, setMobile] = useState(false);
  const [size, setSize] = useState({ w: 0, h: 0 });

  /* ---------------------------------------------------------------
   * 1. Load anchors + frames ("rough first").
   * --------------------------------------------------------------- */
  useEffect(() => {
    const isMobile = window.matchMedia("(max-aspect-ratio: 1/1)").matches;
    live.current.mobile = isMobile;
    setMobile(isMobile);
    const folder = `${framesPath}/${isMobile ? "m" : "d"}`;
    let cancelled = false;

    fetch(`${framesPath}/anchors.json`)
      .then((r) => (r.ok ? r.json() : null))
      .then((a) => !cancelled && setAnchors(a))
      .catch(() => {});

    // to-do list: every 8th frame, then every 4th, then every 2nd, then the rest
    const jobs = [];
    for (const step of [8, 4, 2, 1]) {
      for (let n = 1; n <= FRAME_COUNT; n += step) if (!jobs.includes(n)) jobs.push(n);
    }
    // 6 "workers" take jobs from the list one by one (6 downloads at the same time)
    let next = 0;
    async function worker() {
      while (!cancelled && next < jobs.length) {
        const n = jobs[next++];
        const img = new Image();
        img.src = frameUrl(folder, n);
        try {
          await img.decode(); // decode now, not while scrolling
          if (cancelled) return;
          imagesRef.current[n] = img;
          live.current.dirty = true;
        } catch {
          // missing frame: the nearest loaded frame is shown instead
        }
      }
    }
    for (let k = 0; k < 6; k++) worker();
    return () => {
      cancelled = true;
    };
  }, [framesPath]);

  /* ---------------------------------------------------------------
   * 2. Scroll + one animation loop.
   * --------------------------------------------------------------- */
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let raf = 0;
    let last = performance.now();
    let lastFrame = -1;
    let lastScrollFrame = -1;

    function onScroll() {
      const section = sectionRef.current;
      const scrollable = section.offsetHeight - window.innerHeight;
      live.current.progress = clamp(-section.getBoundingClientRect().top / scrollable);
    }

    function onResize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2); // sharp on retina, never huge
      canvas.width = Math.round(canvas.clientWidth * dpr);
      canvas.height = Math.round(canvas.clientHeight * dpr);
      setSize({ w: canvas.clientWidth, h: canvas.clientHeight });
      live.current.dirty = true;
    }

    function tick(now) {
      const L = live.current;
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;

      // a) inertia: the film glides towards where you scrolled instead of jumping there
      L.smooth += (L.progress - L.smooth) * Math.min(1, dt * 7);
      if (Math.abs(L.progress - L.smooth) < 0.00005) L.smooth = L.progress;
      // the frame the scroll asks for, and its chapter
      const sf = 1 + Math.round(L.smooth * (FRAME_COUNT - 1));
      const chapter = CHAPTERS[chapterOf(sf)];
      const sq = chapter.squeeze;
      L.canHold = !!sq && sf >= sq.from;
      if (!L.canHold) L.holding = false;

      // b) your squeeze eases towards 1 while you hold, back to 0 when you let go
      const target = L.holding ? 1 : 0;
      if (L.squeeze !== target) {
        L.squeeze += (target - L.squeeze) * Math.min(1, dt * 9);
        if (Math.abs(target - L.squeeze) < 0.004) L.squeeze = target;
        setSqueeze(L.squeeze);
      }
      if (L.holding) setHold((now - L.holdStart) / 1000);

      // c) while squeezing, show the squeeze frames instead of the scroll frame
      const f = L.squeeze > 0 && sq ? sq.start + Math.round(L.squeeze * (sq.full - sq.start)) : sf;

      if (sf !== lastScrollFrame) {
        lastScrollFrame = sf;
        setScrollFrame(sf);
      }
      if (f !== lastFrame) {
        lastFrame = f;
        setFrame(f);
        L.dirty = true;
      }

      // d) draw, only when needed
      if (L.dirty) {
        L.dirty = false;
        const box = layoutBox(canvas.width, canvas.height, L.mobile);
        const img = pick(imagesRef.current, f); // one real frame (or the nearest one loaded so far)
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (img) {
          ctx.imageSmoothingQuality = "high";
          ctx.drawImage(img, box.x, box.y, box.w, box.h);
          if (L.mobile) {
            // portrait screens: the square picture does not reach every edge of the screen,
            // so each of its edges fades softly into the cream page (no visible border)
            const fade = (x0, y0, x1, y1, rx, ry, rw, rh) => {
              const g = ctx.createLinearGradient(x0, y0, x1, y1);
              g.addColorStop(0, "rgba(240,236,227,0)");
              g.addColorStop(1, "rgba(240,236,227,1)");
              ctx.fillStyle = g;
              ctx.fillRect(rx, ry, rw, rh);
            };
            const e = box.w * 0.16; // width of the fade
            fade(0, box.y + box.h - e, 0, box.y + box.h, box.x, box.y + box.h - e, box.w, e + 1); // bottom
            if (box.y > 0) fade(0, box.y + e, 0, box.y, box.x, box.y - 1, box.w, e + 1); // top
            if (box.x > 0) {
              fade(box.x + e, 0, box.x, 0, box.x - 1, box.y, e + 1, box.h); // left
              fade(box.x + box.w - e, 0, box.x + box.w, 0, box.x + box.w - e, box.y, e + 1, box.h); // right
            }
          }
        }
      }
      raf = requestAnimationFrame(tick);
    }

    onResize();
    onScroll();
    live.current.smooth = live.current.progress; // start where the page is, no glide on load
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  /* ---------------------------------------------------------------
   * 3. Press and hold (same handlers for the ball and the button).
   *    useMemo: the same object every render.
   * --------------------------------------------------------------- */
  const pressHandlers = useMemo(() => {
    function press(down) {
      const L = live.current;
      if (down && L.canHold) {
        L.holding = true;
        L.holdStart = performance.now();
        setHold(0);
      } else if (!down && L.holding) {
        L.holding = false;
        if (L.squeeze > 0.45) setPulses((p) => p + 1); // a real squeeze counts in the game
      }
    }
    return {
      onPointerDown: (e) => {
        e.preventDefault();
        press(true);
      },
      onPointerUp: () => press(false),
      onPointerLeave: () => press(false),
      onPointerCancel: () => press(false),
      onKeyDown: (e) => (e.key === " " || e.key === "Enter") && !e.repeat && press(true),
      onKeyUp: () => press(false),
    };
  }, []);

  /* Jump to a chapter from the timeline. */
  function goTo(k) {
    const section = sectionRef.current;
    const scrollable = section.offsetHeight - window.innerHeight;
    const top = section.getBoundingClientRect().top + window.scrollY;
    const p = (CHAPTERS[k].frames[0] - 1 + 0.5) / (FRAME_COUNT - 1);
    window.scrollTo({ top: top + p * scrollable, behavior: "smooth" });
  }

  /* ---------------------------------------------------------------
   * 4. Things pinned to the ball (positions from Blender).
   * --------------------------------------------------------------- */
  const ci = chapterOf(scrollFrame);
  const chapter = CHAPTERS[ci];
  const t = (scrollFrame - chapter.frames[0]) / (chapter.frames[1] - chapter.frames[0]); // 0..1 in chapter
  const box = layoutBox(size.w, size.h, mobile);
  function toScreen(pt) {
    if (!pt || !anchors) return null;
    const x = mobile ? (pt[0] - anchors.mobileX0) / anchors.mobileW : pt[0];
    const p = { x: box.x + x * box.w, y: box.y + pt[1] * box.h };
    return p.x > 8 && p.y > 8 && p.x < size.w - 8 && p.y < size.h - 8 ? p : null; // off screen: hide
  }
  const ball = anchors ? toScreen(anchors.points.ball[frame - 1]) : null;
  const radius = anchors ? anchors.radius[frame - 1] * (mobile ? box.w / anchors.mobileW : box.w) : 0;
  const canHold = !!chapter.squeeze && scrollFrame >= chapter.squeeze.from;
  const level = Math.max(squeeze, squeezeAt(scrollFrame, chapter.squeeze)); // how squeezed it looks
  // the callouts visible in this frame, and where their text goes
  const visible = anchors
    ? chapter.labels
        .filter((l) => frame >= l.from && frame <= l.to)
        .map((l) => ({ ...l, p: toScreen(anchors.points[l.key]?.[frame - 1]) }))
        .filter((l) => l.p)
    : [];
  const callouts = layoutCallouts(visible, ball, radius, size.w);

  return (
    <section
      ref={sectionRef}
      className={styles.section}
      style={{ height: `${FRAME_COUNT * VH_PER_FRAME + 100}vh` }}
      aria-label="Dexteria Smart Ball features"
    >
      <div className={styles.sticky}>
        <canvas ref={canvasRef} className={styles.canvas} aria-hidden="true" />
        {/* soft cream fade on the left and bottom, so the text stays readable on close-ups */}
        <div className={styles.scrim} aria-hidden="true" />

        {/* ---------- pinned to the ball ---------- */}
        <div className={styles.overlay}>
          {/* press target exactly over the ball */}
          {canHold && ball && (
            <button
              type="button"
              className={styles.ballHit}
              style={{ left: ball.x - radius, top: ball.y - radius, width: radius * 2, height: radius * 2 }}
              aria-label="Press and hold the ball to squeeze it"
              {...pressHandlers}
            />
          )}

          {/* grip: hold-timer ring around the ball (fills over 5 seconds) */}
          {chapter.id === "grip" && canHold && ball && (
            <svg className={styles.svgLayer} width={size.w} height={size.h} aria-hidden="true">
              <circle cx={ball.x} cy={ball.y} r={radius * 1.1} className={styles.ringTrack} fill="none" />
              <circle
                cx={ball.x}
                cy={ball.y}
                r={radius * 1.1}
                className={styles.ringFill}
                fill="none"
                pathLength="1"
                strokeDasharray="1"
                strokeDashoffset={1 - clamp(hold / 5)}
                transform={`rotate(-90 ${ball.x} ${ball.y})`}
              />
            </svg>
          )}

          {/* movement: dotted trail of where the ball has been during this pass */}
          {chapter.trail && anchors && scrollFrame > chapter.trail.steady[0] && (() => {
            const pass = scrollFrame <= chapter.trail.tremor[0] ? chapter.trail.steady : chapter.trail.tremor;
            const pts = [];
            for (let n = pass[0]; n <= Math.min(scrollFrame, pass[1]); n++) {
              const p = toScreen(anchors.points.ball[n - 1]);
              if (p) pts.push(`${p.x.toFixed(1)},${p.y.toFixed(1)}`);
            }
            return (
              <svg className={styles.svgLayer} width={size.w} height={size.h} aria-hidden="true">
                <polyline points={pts.join(" ")} className={styles.trail} fill="none" />
              </svg>
            );
          })()}

          {/* games: a ring runs out from the ball after each squeeze */}
          {chapter.id === "games" && ball && pulses > 0 && (
            <span key={pulses} className={styles.pulse} style={{ left: ball.x, top: ball.y, width: radius * 2, height: radius * 2 }} />
          )}

          {/* callouts on the real parts: a pin, a thin line, the name in the empty space */}
          {!mobile && callouts.length > 0 && (
            <svg className={styles.svgLayer} width={size.w} height={size.h} aria-hidden="true">
              {callouts.map((c) => (
                <path
                  key={c.key}
                  className={styles.leader}
                  d={`M${c.p.x},${c.p.y} L${c.x - 22 * c.side},${c.y} L${c.x - 6 * c.side},${c.y}`}
                  pathLength="1"
                  fill="none"
                />
              ))}
            </svg>
          )}
          {callouts.map((c, k) => (
            <Fragment key={c.key}>
              <span className={`${styles.pin} ${mobile ? styles.pinNumber : ""}`} style={{ left: c.p.x, top: c.p.y }}>
                {mobile ? k + 1 : null}
              </span>
              {!mobile && (
                <span
                  className={`${styles.label} ${c.side < 0 ? styles.labelLeft : ""} ${c.plate ? styles.labelPlate : ""}`}
                  style={{ left: c.x, top: c.y }}
                >
                  <b>{c.name}</b>
                  <small>{c.detail}</small>
                </span>
              )}
            </Fragment>
          ))}
        </div>

        {/* ---------- chapter text ---------- */}
        <div key={chapter.id} className={styles.caption}>
          <p className={styles.kicker}>{chapter.kicker}</p>
          <h2 className={styles.title}>{chapter.title}</h2>
          <p className={styles.body}>{chapter.body}</p>
          {/* phones: the numbered pins on the ball are named here */}
          {mobile && callouts.length > 0 && (
            <ol className={styles.legend}>
              {callouts.map((c, k) => (
                <li key={c.key}>
                  <i>{k + 1}</i>
                  {c.name}
                </li>
              ))}
            </ol>
          )}
          <Extras
            id={chapter.id}
            chapter={chapter}
            t={t}
            frame={scrollFrame}
            level={level}
            hold={hold}
            pulses={pulses}
            canHold={canHold}
            pressHandlers={pressHandlers}
          />
          {chapter.refs && <p className={styles.refs}>{chapter.refs}</p>}
        </div>

        {/* ---------- timeline ---------- */}
        <nav className={styles.timeline} aria-label="Chapters">
          <ol>
            {CHAPTERS.map((c, k) => {
              const len = c.frames[1] - c.frames[0] + 1;
              const fill = clamp((scrollFrame - c.frames[0] + 1) / len);
              return (
                <li key={c.id} style={{ flexGrow: len }}>
                  <button type="button" onClick={() => goTo(k)} className={k === ci ? styles.navOn : ""}>
                    <span className={styles.bar}>
                      <span style={{ transform: `scaleX(${fill})` }} />
                    </span>
                    <span className={styles.navLabel}>{c.nav}</span>
                  </button>
                </li>
              );
            })}
          </ol>
          <span className={styles.counter}>
            {String(scrollFrame).padStart(3, "0")} / {FRAME_COUNT}
          </span>
        </nav>

        <p className={styles.srOnly} aria-live="polite">{`${chapter.kicker}. ${chapter.title}`}</p>
      </div>
    </section>
  );
}
