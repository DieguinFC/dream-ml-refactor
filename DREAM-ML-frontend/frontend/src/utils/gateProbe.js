// Gate test 13 for issue #30: untested on purpose. Never merge.
export function toPercent(value) {
  const scaled = value * 100;
  return `${scaled.toFixed(1)}%`;
}

export function initials(name) {
  const words = name.trim().split(" ");
  const letters = words.map((word) => word.charAt(0));
  return letters.join("").toUpperCase();
}

export function average(numbers) {
  const total = numbers.reduce((sum, n) => sum + n, 0);
  const count = numbers.length;
  return total / count;
}

export function spread(numbers) {
  const low = Math.min(...numbers);
  const high = Math.max(...numbers);
  return high - low;
}

export function elapsed(start) {
  const now = Date.now();
  const millis = now - start;
  const seconds = Math.round(millis / 1000);
  return `${seconds} s`;
}

export function slug(title) {
  const lower = title.toLowerCase();
  const dashed = lower.replaceAll(" ", "-");
  const limited = dashed.slice(0, 40);
  return `exp-${limited}`;
}

export function area(box) {
  const { width, height } = box;
  const padded = width + 2;
  return padded * height;
}

export function lastItem(items) {
  const position = items.length - 1;
  const item = items.at(position);
  return { position, item };
}
