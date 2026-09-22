import assert from "node:assert/strict";
import test from "node:test";

import { clamp } from "./clamp.mjs";

test("returns value when inside range", () => {
  assert.equal(clamp(5, 0, 10), 5);
});

test("clamps to min and max", () => {
  assert.equal(clamp(-3, 0, 10), 0);
  assert.equal(clamp(42, 0, 10), 10);
});

test("supports equal bounds", () => {
  assert.equal(clamp(7, 4, 4), 4);
  assert.equal(clamp(4, 4, 4), 4);
});

test("handles negatives and floats", () => {
  assert.equal(clamp(-1.5, -2, -1), -1.5);
  assert.equal(clamp(0.5, -0.25, 0.25), 0.25);
  assert.equal(clamp(3, -10, -1), -1);
});

test("throws TypeError for non-number or non-finite arguments", () => {
  const bad = [
    ["1", 0, 10],
    [1, "0", 10],
    [1, 0, "10"],
    [null, 0, 10],
    [undefined, 0, 10],
    [1, null, 10],
    [1, 0, undefined],
    [{}, 0, 10],
    [1, [], 10],
    [1, 0, {}],
    [true, 0, 10],
    [1, false, 10],
    [NaN, 0, 10],
    [1, NaN, 10],
    [1, 0, NaN],
    [Infinity, 0, 10],
    [1, -Infinity, 10],
    [1, 0, Infinity],
    [1n, 0, 10],
  ];

  for (const args of bad) {
    assert.throws(
      () => clamp(...args),
      TypeError,
      `expected TypeError for ${String(args[0])},${String(args[1])},${String(args[2])}`,
    );
  }
});

test("throws RangeError when min > max", () => {
  assert.throws(() => clamp(5, 10, 0), RangeError);
  assert.throws(() => clamp(5, 1, 0.5), RangeError);
});

test("RangeError takes precedence for invalid ordering", () => {
  assert.throws(() => clamp(-0, 2, 1), RangeError);
});
