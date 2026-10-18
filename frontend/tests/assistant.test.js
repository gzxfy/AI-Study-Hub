import test from 'node:test';
import assert from 'node:assert/strict';
import { readConversation, getConversation, sendMessage } from '../src/api/assistant.js';
import { nextAttempt } from '../src/assistant/requestAttempt.js';
import { messageBlocks, messageTime } from '../src/assistant/messageFormat.js';

test('invalid histories fail explicitly, including null messages and duplicate IDs', () => {
  for (const data of [null, {}, { messages: [null] }, { messages: [{ id: 1, role: 'system', content: 'secret' }] }, { messages: [{ id: 1, role: 'user', content: 'a' }, { id: '1', role: 'assistant', content: 'b' }] }]) {
    assert.throws(() => readConversation(data), { name: 'ApiError' });
  }
  assert.deepEqual(readConversation({ messages: [] }), { messages: [] });
});

test('uncertain retries preserve ID; edited questions or context create a new attempt', () => {
  const first = nextAttempt(null, 'Explain', false, () => 'first');
  assert.equal(nextAttempt(first, 'Explain', false, () => assert.fail('ID regenerated')), first);
  assert.equal(nextAttempt(first, 'Explain', true, () => 'topic').request_id, 'topic');
  assert.equal(nextAttempt(first, 'Explain more', false, () => 'edited').request_id, 'edited');
});

test('formatter preserves code, lists and raw HTML as text', () => {
  assert.deepEqual(messageBlocks('# Heading\n\n- One\n- Two\n```js\n<script>alert(1)</script>\n```'), [
    { type: 'heading', text: 'Heading' },
    { type: 'list', ordered: false, items: ['One', 'Two'] },
    { type: 'code', language: 'js', text: '<script>alert(1)</script>' },
  ]);
  assert.deepEqual(messageBlocks('<img src=x onerror=alert(1)>'), [{ type: 'paragraph', text: '<img src=x onerror=alert(1)>' }]);
  assert.deepEqual(messageBlocks('```\nunclosed'), [{ type: 'code', language: '', text: 'unclosed' }]);
  assert.equal(messageTime('invalid date'), '');
  assert.equal(messageTime(null), '');
});

test('assistant calls send session credentials, fresh CSRF and exact payload', async (t) => {
  const calls = [];
  t.mock.method(globalThis, 'fetch', async (path, options) => {
    calls.push({ path, options });
    return Response.json(path === '/api/auth/csrf' ? { csrf_token: 'test-token' } : { messages: [] });
  });
  await getConversation(12);
  const payload = { message: 'Explain', include_topic: true, request_id: 'test-attempt' };
  await sendMessage(12, payload);
  assert.deepEqual(calls.map(({ path }) => path), ['/api/notes/12/conversation', '/api/auth/csrf', '/api/notes/12/messages']);
  assert.ok(calls.every(({ options }) => options.credentials === 'same-origin'));
  assert.equal(calls[2].options.method, 'POST');
  assert.equal(calls[2].options.headers['X-CSRFToken'], 'test-token');
  assert.deepEqual(JSON.parse(calls[2].options.body), payload);
});

test('expired session and network failures are surfaced without automatic resubmission', async (t) => {
  let count = 0;
  t.mock.method(globalThis, 'fetch', async () => {
    count += 1;
    return Response.json({ error: { code: 'unauthorized', message: 'Log in' } }, { status: 401 });
  });
  await assert.rejects(sendMessage(12, { message: 'Explain' }), { name: 'ApiError', status: 401 });
  assert.equal(count, 1);
  globalThis.fetch = async () => { throw new TypeError('Network error'); };
  await assert.rejects(getConversation(12), { name: 'ApiError', status: 0 });
});

test('aborted requests stay aborted instead of appearing as server errors', async (t) => {
  t.mock.method(globalThis, 'fetch', async () => { throw new DOMException('Aborted', 'AbortError'); });
  await assert.rejects(getConversation(12), { name: 'AbortError' });
});
