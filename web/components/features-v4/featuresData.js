/*
 * featuresData.js
 * ----------------
 * The words for each chapter of the scroll film, and which frames belong to it.
 * Edit text here without touching any logic.
 *
 *   frames  [first, last] frame of this chapter in the rendered film (266 frames in total)
 *   refs    requirement numbers from our SRS
 *   labels  callouts pinned to real parts: key (from anchors.json), name, detail, and the
 *           frames in which the part is clearly visible
 *
 * Wording rule from the team: say "practice", "progress", "wellness".
 * Never "therapy", "treatment" or "medical-grade".
 */

export const FRAME_COUNT = 266;

export const CHAPTERS = [
  {
    id: "intro",
    frames: [1, 24],
    nav: "Dexteria",
    kicker: "Dexteria Smart Ball",
    title: "Hand practice you can measure.",
    body: "A soft ball for daily hand practice after a stroke. Scroll to see what it does.",
    labels: [],
  },
  {
    id: "grip",
    frames: [25, 62],
    nav: "Grip",
    refs: "FR2 · FR6 · FR7",
    kicker: "01  Grip strength and hold time",
    title: "Grip pressure and hold time, every session.",
    body: "An air bladder fills the core. Squeeze it and a pressure sensor reads the change.",
    labels: [
      { key: "bladder", name: "Air bladder", detail: "sealed TPU", from: 42, to: 62 },
      { key: "pressure", name: "Pressure sensor", detail: "reads the bladder", from: 46, to: 62 },
    ],
    squeeze: { start: 50, full: 56, end: 62, from: 46 }, // press and hold plays frames 50 to 56
  },
  {
    id: "move",
    frames: [63, 114],
    nav: "Movement",
    refs: "FR3 · FR4",
    kicker: "02  Movement and tremor",
    title: "Records movement and tremor.",
    body: "A 6-axis motion sensor follows how your hand moves the ball, and how steady it is.",
    labels: [{ key: "motion", name: "Motion sensor", detail: "6-axis, MPU-6050", from: 72, to: 85 }],
    trail: { steady: [98, 106], tremor: [106, 114] },
  },
  {
    id: "games",
    frames: [115, 150],
    nav: "Games",
    refs: "FR5 · FR18 · FR25",
    kicker: "03  Guided games",
    title: "Start with one tap. Follow spoken guidance.",
    body: "One press starts the session. A calm voice tells you what to do, and every squeeze moves the game.",
    labels: [{ key: "button", name: "Start button", detail: "one press", from: 125, to: 135 }],
    startFrame: 129, // the button is pressed in the film here
    squeeze: { start: 142, full: 146, end: 150, from: 140 },
  },
  {
    id: "progress",
    frames: [151, 184],
    nav: "Progress",
    refs: "FR20 · FR22",
    kicker: "04  Progress against your other hand",
    title: "See how close you are to your other hand.",
    body: "Your affected hand is compared with your own unaffected hand, so every goal is personal.",
    labels: [{ key: "dock", name: "Charging dock", detail: "syncs while it charges", from: 172, to: 184 }],
  },
  {
    id: "difficulty",
    frames: [185, 236],
    nav: "Difficulty",
    refs: "FR8 · FR10 · FR11",
    kicker: "05  Safe, clinician-led difficulty",
    title: "Your clinician sets the level. Caregivers can only make it easier.",
    body: "Firmness inserts sit under the shell and change how hard the ball is to squeeze.",
    labels: [{ key: "insert", name: "Firmness insert", detail: "swappable", from: 215, to: 226 }],
  },
  {
    id: "share",
    frames: [237, 266],
    nav: "Sharing",
    refs: "FR26 · FR27 · FR32",
    kicker: "06  Share with your clinician",
    title: "You choose who sees your progress.",
    body: "Turn sharing on and your clinician sees your report. Turn it off and their access stops.",
    labels: [],
  },
];

/* "Squeeze gently" in the three app languages.
   Please ask a teammate to double-check the Sinhala and Tamil lines. */
export const VOICE_LINES = [
  { lang: "EN", text: "Squeeze gently" },
  { lang: "සිං", text: "සෙමින් මිරිකන්න" },
  { lang: "தமி", text: "மெதுவாக அழுத்துங்கள்" },
];
