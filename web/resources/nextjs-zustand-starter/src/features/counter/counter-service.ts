export function addToCount(current: number, delta: number): number {
  if (!Number.isFinite(current) || !Number.isFinite(delta)) {
    throw new TypeError('Counter values must be finite numbers.');
  }

  return current + delta;
}
