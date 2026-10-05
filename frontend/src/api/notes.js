import { ApiError, mutate, request } from './client.js';

function readNote(data) {
  if (data?.note?.id == null || typeof data.note.title !== 'string' || typeof data.note.content !== 'string') {
    throw new ApiError('Study Hub returned an unexpected note. Please reload your notes before trying again.');
  }
  return data.note;
}

export async function listNotes(signal) {
  const data = await request('/api/notes', { signal });
  if (!Array.isArray(data.notes)) throw new ApiError('Unable to read your notes. Please try again.');
  return data.notes;
}

export async function listTopics(signal) {
  const data = await request('/api/topics', { signal });
  if (!Array.isArray(data.topics)) throw new ApiError('Unable to read your topics. Please try again.');
  return data.topics;
}

export async function getNote(id, signal) {
  return readNote(await request(`/api/notes/${encodeURIComponent(id)}`, { signal }));
}

export async function createNote({ title, content, topic_id }) {
  return readNote(await mutate('/api/notes', { title, content, topic_id }));
}

export async function updateNote(id, { title, content, topic_id }) {
  return readNote(await mutate(`/api/notes/${encodeURIComponent(id)}`, { title, content, topic_id }, { method: 'PATCH' }));
}

export function deleteNote(id) {
  return mutate(`/api/notes/${encodeURIComponent(id)}`, undefined, { method: 'DELETE' });
}
