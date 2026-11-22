/* utils.js - tiny maths helpers for the Features section. */

/* Keep a number between min and max. */
export function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value));
}

/* Smooth 0..1 -> 0..1 (slow start, slow end). */
export function smooth(t) {
  t = clamp(t);
  return t * t * (3 - 2 * t);
}

/* Frame file name: f_0001.webp */
export function frameUrl(folder, n) {
  return `${folder}/f_${String(n).padStart(4, "0")}.webp`;
}

/* How squeezed the ball is in a given frame of the film (0 = relaxed, 1 = full),
   using the squeeze frames of a chapter: start -> full -> end. */
export function squeezeAt(frame, sq) {
  if (!sq || frame <= sq.start || frame >= sq.end) return 0;
  if (frame <= sq.full) return (frame - sq.start) / (sq.full - sq.start);
  return 1 - (frame - sq.full) / (sq.end - sq.full);
}
