// Read-only local package check with synthetic strings; no adapter/model instance.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const root = process.argv[2];
assert(root, 'Pass the verified @deepseek-ai/dsh-llm package directory');
const metadata = JSON.parse(await readFile(resolve(root, 'package.json'), 'utf8'));
assert.equal(metadata.name, '@deepseek-ai/dsh-llm');
const llm = await import(pathToFileURL(resolve(root, 'lib/index.js')).href);
assert.equal(llm.CONTEXT_WINDOW_EXCEEDED_CODE, 'CONTEXT_WINDOW_EXCEEDED');
assert.equal(llm.QUOTA_EXCEEDED_CODE, 'QUOTA');
assert.equal(llm.isContextWindowExceededError('maximum context length exceeded'), true);
assert.equal(llm.isContextWindowExceededError('token 用完了'), false);
assert.equal(llm.isQuotaExceededError('insufficient_quota'), true);
assert.equal(llm.isQuotaExceededError('insufficient balance'), true);
assert.equal(llm.isQuotaExceededError('rate limit reached: tokens per minute'), false);
assert.equal(llm.isQuotaExceededError('token 用完了'), false);
console.log(JSON.stringify({package: metadata.name, version: metadata.version,
  classifierAssertions: 8, modelCalls: 0, liveRecovery: false}));
