import { ApiError, mutate, request } from './client.js';

export { listTopics } from './notes.js';

function readTopic(data) {
  if (data?.topic?.id == null || typeof data.topic.title !== 'string') {
    throw new ApiError('Unable to read this topic. Please reload your topics before trying again.');
  }
  return data.topic;
}

export async function getTopic(id, signal) {
  const data = await request(`/api/topics/${encodeURIComponent(id)}`, { signal });
  const topic = readTopic(data);
  if (!Array.isArray(data.notes)) throw new ApiError('Unable to read the notes in this topic.');
  return { topic, notes: data.notes };
}

export async function saveTopic(id, { title, description, color }) {
  const path = id == null ? '/api/topics' : `/api/topics/${encodeURIComponent(id)}`;
  return readTopic(await mutate(path, { title, description, color }, { method: id == null ? 'POST' : 'PATCH' }));
}

export function deleteTopic(id) {
  return mutate(`/api/topics/${encodeURIComponent(id)}`, undefined, { method: 'DELETE' });
}
