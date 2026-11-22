"use client";
/*
 * Extras.jsx
 * -----------
 * The small interactive part under each chapter's text.
 * Plain text, thin lines and real buttons: no fake phones, no cards.
 *
 * Props from FeaturesSection:
 *   id      chapter id
 *   chapter the chapter's data from featuresData.js (frame numbers live there)
 *   t       how far through the chapter you have scrolled (0 to 1)
 *   frame   the frame chosen by the scroll
 *   level   how squeezed the ball is right now (0 to 1)
 *   hold    seconds you have been holding the ball
 *   pulses  number of finished squeezes
 *   canHold true when the ball can be squeezed in this part of the film
 *   pressHandlers  pointer/keyboard handlers for "press and hold"
 * All numbers are EXAMPLE values for the website, not patient data.
 */
import { useState } from "react";
import styles from "./FeaturesSection.module.css";
import { VOICE_LINES } from "./featuresData";
import { clamp, smooth } from "./utils";

const Tick = () => (
  <svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true">
    <path d="M3 8.5l3 3 7-7" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);
const Lock = () => (
  <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true">
    <rect x="3" y="7" width="10" height="7" rx="1.5" fill="currentColor" />
    <path d="M5.5 7V5a2.5 2.5 0 015 0v2" fill="none" stroke="currentColor" strokeWidth="1.6" />
  </svg>
);
const Wave = () => (
  <svg viewBox="0 0 20 14" width="18" height="13" aria-hidden="true">
    {[2, 6, 10, 14, 18].map((x, k) => (
      <line key={x} x1={x} x2={x} y1={7 - [2, 5, 6, 4, 2][k]} y2={7 + [2, 5, 6, 4, 2][k]} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    ))}
  </svg>
);

/* the "press and hold" button (the ball itself works the same way) */
function HoldButton({ canHold, pressHandlers, children }) {
  return (
    <button type="button" className={styles.hold} disabled={!canHold} {...pressHandlers}>
      <span className={styles.holdDot} />
      {canHold ? children : "Keep scrolling"}
    </button>
  );
}

/* ------------------------------------------------------------------ 1. grip */
function Grip({ level, hold, canHold, pressHandlers }) {
  return (
    <>
      <dl className={styles.readout}>
        <div>
          <dt>Grip pressure</dt>
          <dd>
            {Math.round(level * 64)}
            <small>rel.</small>
          </dd>
        </div>
        <div>
          <dt>Hold time</dt>
          <dd>
            {hold.toFixed(1)}
            <small>s</small>
          </dd>
        </div>
      </dl>
      <HoldButton canHold={canHold} pressHandlers={pressHandlers}>
        Press and hold the ball
      </HoldButton>
    </>
  );
}

/* ------------------------------------------------------------------ 2. movement */
function line(wobble) {
  let d = "";
  for (let k = 0; k <= 60; k++) {
    const x = (k / 60) * 200;
    const y = 18 - 12 * Math.sin((k / 60) * Math.PI) + wobble * Math.sin(k * 1.9) * (0.6 + 0.4 * Math.sin(k * 0.37));
    d += `${k ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
  }
  return d;
}
const STEADY = line(0);
const SHAKY = line(2.2);

function Move({ frame, chapter }) {
  const [s0, s1] = chapter.trail.steady; // frames of the steady pass
  const [t0, t1] = chapter.trail.tremor; // frames of the pass with tremor
  const steady = clamp((frame - s0) / (s1 - s0));
  const tremor = clamp((frame - t0) / (t1 - t0));
  return (
    <>
      <div className={styles.lines}>
        {[
          ["Steady pass", STEADY, steady, frame <= t0],
          ["Pass with tremor", SHAKY, tremor, frame > t0],
        ].map(([label, d, drawn, on]) => (
          <div key={label} className={on ? styles.lineOn : ""}>
            <span>{label}</span>
            <svg viewBox="0 0 200 30" aria-hidden="true">
              <path d={d} pathLength="1" strokeDasharray="1" strokeDashoffset={1 - drawn} fill="none" />
            </svg>
          </div>
        ))}
      </div>
      <p className={styles.note}>Movement and tremor only. Lift height is not measured.</p>
    </>
  );
}

/* ------------------------------------------------------------------ 3. games */
function Games({ frame, chapter, pulses, canHold, pressHandlers }) {
  const [lang, setLang] = useState(0);
  const started = frame >= chapter.startFrame; // the frame where the start button is pressed in the film
  return (
    <>
      <p className={styles.voice}>
        <Wave /> {started ? VOICE_LINES[lang].text : "Press the button to start"}
      </p>
      <div className={styles.langs} role="group" aria-label="Voice language">
        {VOICE_LINES.map((v, k) => (
          <button key={v.lang} type="button" className={k === lang ? styles.langOn : ""} onClick={() => setLang(k)}>
            {v.lang}
          </button>
        ))}
        <span className={styles.note}>In Sinhala, Tamil, English.</span>
      </div>
      <dl className={styles.readout}>
        <div>
          <dt>Squeezes this session</dt>
          <dd>{pulses}</dd>
        </div>
      </dl>
      <HoldButton canHold={canHold} pressHandlers={pressHandlers}>
        Squeeze the ball
      </HoldButton>
    </>
  );
}

/* ------------------------------------------------------------------ 4. progress */
const WEEKS = [38, 45, 49, 57, 61, 68, 72, 78]; // EXAMPLE: % of the unaffected hand, weeks 1 to 8
const X = (k) => 4 + k * 44;
const Y = (v) => 100 - v;
const PATH = WEEKS.map((v, k) => `${k ? "L" : "M"}${X(k)},${Y(v)}`).join("");

function Progress({ t }) {
  const p = smooth(t / 0.8); // the line draws itself while you scroll
  return (
    <>
      <div className={styles.chartHead}>
        <span className={styles.bigNum}>{Math.round(WEEKS[WEEKS.length - 1] * p)}%</span>
        <span>of your other hand, week 8</span>
      </div>
      <svg className={styles.chart} viewBox="0 -16 316 126" aria-hidden="true">
        <line x1="0" x2="316" y1={Y(100)} y2={Y(100)} className={styles.goal} />
        <text x="316" y={Y(100) - 4} textAnchor="end" className={styles.goalText}>
          Unaffected hand
        </text>
        <path d={PATH} pathLength="1" strokeDasharray="1" strokeDashoffset={1 - p} className={styles.handLine} fill="none" />
        {WEEKS.map((v, k) => (k / (WEEKS.length - 1) <= p + 0.001 ? <circle key={k} cx={X(k)} cy={Y(v)} r="2.6" className={styles.dot} /> : null))}
      </svg>
      <p className={styles.note}>Weeks 1 to 8. Example data.</p>
    </>
  );
}

/* ------------------------------------------------------------------ 5. difficulty */
function Difficulty({ t }) {
  const [note, setNote] = useState("");
  const knob = 0.3 + 0.4 * smooth((t - 0.08) / 0.3); // no numbers on purpose: the grades are not labelled
  const fitted = t > 0.78; // the new insert is in place in the film
  return (
    <div className={styles.roles}>
      <div>
        <span className={styles.role}>Clinician</span>
        <div className={styles.slider}>
          <span style={{ left: `${knob * 100}%` }} />
        </div>
        <div className={styles.ends}>
          <span>Softer</span>
          <span>Firmer</span>
        </div>
        <p className={`${styles.check} ${fitted ? styles.checkOn : ""}`}>
          <Tick /> Matching insert fitted
        </p>
      </div>
      <div>
        <span className={styles.role}>Caregiver</span>
        <div className={styles.pair}>
          <button type="button" className={styles.textBtn} onClick={() => setNote("Made easier. Your clinician will see this.")}>
            Make easier
          </button>
          <button type="button" className={styles.locked} aria-disabled="true" onClick={() => setNote("Only your clinician can make it harder.")}>
            <Lock /> Make harder
          </button>
        </div>
        <p className={styles.note} aria-live="polite">
          {note || "Harder is locked. Only the clinician can raise it."}
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ 6. sharing */
function Share({ t }) {
  const [choice, setChoice] = useState(null); // null = follow the scroll story, true/false = your click
  const on = choice ?? (t > 0.08 && t < 0.85);
  const travel = clamp((t - 0.15) / 0.45); // the report: phone -> Supabase -> clinician
  const arrived = on && travel >= 1;
  return (
    <>
      <div className={styles.switchRow}>
        <span>Share with my clinician</span>
        <button type="button" role="switch" aria-checked={on} className={`${styles.switch} ${on ? styles.switchOn : ""}`} onClick={() => setChoice(!on)}>
          <span />
        </button>
      </div>
      <div className={`${styles.flow} ${on ? "" : styles.flowOff}`}>
        <span>Phone</span>
        <span className={styles.flowLine}>
          <i style={{ left: `${clamp(travel * 2) * 100}%`, opacity: on && travel > 0 && travel < 0.5 ? 1 : 0 }} />
        </span>
        <span>Supabase</span>
        <span className={styles.flowLine}>
          <i style={{ left: `${clamp(travel * 2 - 1) * 100}%`, opacity: on && travel >= 0.5 && travel < 1 ? 1 : 0 }} />
        </span>
        <span>Clinician</span>
      </div>
      <p className={styles.note}>
        {!on ? "Sharing is off. Your clinician no longer has access." : arrived ? "Your clinician can see this week's report." : "Sending this week's report..."}
      </p>
    </>
  );
}

export default function Extras(props) {
  switch (props.id) {
    case "grip":
      return <Grip {...props} />;
    case "move":
      return <Move {...props} />;
    case "games":
      return <Games {...props} />;
    case "progress":
      return <Progress {...props} />;
    case "difficulty":
      return <Difficulty {...props} />;
    case "share":
      return <Share {...props} />;
    default:
      return null;
  }
}
