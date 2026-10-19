// Keep the same ID for a manual retry of the same question and context.
// A new question needs a new ID, even if the previous attempt succeeded.
export function nextAttempt(previous, message, includeTopic, createId = () => crypto.randomUUID()) {
  if (previous?.message === message && previous.include_topic === includeTopic) return previous;
  return { message, include_topic: includeTopic, request_id: createId() };
}
