// Gate test 13 for issue #30: untested on purpose. Never merge.
export function toPercent(value) {
  const scaled = value * 100;
  return `${scaled.toFixed(1)}%`;
}
