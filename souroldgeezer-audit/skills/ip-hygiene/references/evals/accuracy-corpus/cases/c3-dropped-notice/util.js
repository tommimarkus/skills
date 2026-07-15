// Synthetic corpus fixture. This helper plays the role of code adapted
// from ExampleLib, a fictional MIT-licensed third-party library invented
// for this corpus; the upstream MIT copyright/licence notice is
// intentionally omitted here — that omission is the planted defect.
function clamp(value, lo, hi) {
  if (value < lo) return lo;
  if (value > hi) return hi;
  return value;
}
