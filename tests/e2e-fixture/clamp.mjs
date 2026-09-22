/**
 * Clamp `value` into the inclusive range [min, max].
 *
 * @param {number} value
 * @param {number} min
 * @param {number} max
 * @returns {number}
 */
export function clamp(value, min, max) {
  if (
    typeof value !== "number" ||
    typeof min !== "number" ||
    typeof max !== "number" ||
    !Number.isFinite(value) ||
    !Number.isFinite(min) ||
    !Number.isFinite(max)
  ) {
    throw new TypeError("clamp requires finite numbers for value, min and max");
  }

  if (min > max) {
    throw new RangeError("min must be less than or equal to max");
  }

  return Math.min(max, Math.max(min, value));
}
