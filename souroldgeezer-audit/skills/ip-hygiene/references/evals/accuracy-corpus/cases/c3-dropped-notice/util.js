// adapted from a synthetic MIT-licensed snippet; upstream notice intentionally omitted for this corpus
function clampToRange(value, min, max) {
  if (value < min) return min;
  if (value > max) return max;
  return value;
}
