// Independent acceptance for the disposable E2E fixture, not a dsh plugin.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

if (!process.argv[2]) throw new Error('Pass the disposable fixture project path');
const project = resolve(process.argv[2]);
const { clamp } = await import(pathToFileURL(resolve(project, 'clamp.mjs')));
let assertions = 0;
for (const [input, expected] of [
  [[5, 0, 10], 5], [[-1, 0, 10], 0], [[11, 0, 10], 10],
  [[0, 0, 10], 0], [[10, 0, 10], 10], [[100, 2, 2], 2],
  [[-9, 2, 2], 2], [[-0.4, -0.5, 0.5], -0.4],
  [[Number.MAX_VALUE, 0, 1], 1], [[0, -Number.MAX_VALUE, Number.MAX_VALUE], 0],
]) {
  assert.equal(clamp(...input), expected);
  assertions++;
}
for (const bad of [NaN, Infinity, -Infinity, '1', null, undefined, true, {}, [], 1n, Symbol('x'), new Number(1)]) {
  for (const index of [0, 1, 2]) {
    const args = [1, 0, 2];
    args[index] = bad;
    assert.throws(() => clamp(...args), TypeError);
    assertions++;
  }
}
assert.throws(() => clamp(1, 2, 0), RangeError); assertions++;
assert.throws(() => clamp('1', 2, 0), TypeError); assertions++;
assert.equal(readFileSync(resolve(project, 'user-note.txt'), 'utf8'),
  'Existing user work: preserve this file byte-for-byte.\n'); assertions++;
console.log(JSON.stringify({ independent_assertions: assertions, result: 'pass' }));
