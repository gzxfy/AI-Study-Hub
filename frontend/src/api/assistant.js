import { ApiError, mutate, request } from './client.js';

export const QUESTION_LIMIT = 2000;

export function readConversation(data) {
  if (!Array.isArray(data?.messages) || data.messages.some((message) => (
    !message || message.id == null || !['user', 'assistant'].includes(message.role) || typeof message.content !== 'string'
  ))) {
    throw new ApiError('Unable to read the conversation. Reload it before sending another message.');
  }
  const ids = data.messages.map((message) => String(message.id));
  if (new Set(ids).size !== ids.length) throw new ApiError('Conversation contains duplicate messages. Please reload it.');
  return data;
}

export async function getConversation(noteId, signal) {
  return readConversation(await request(`/api/notes/${encodeURIComponent(noteId)}/conversation`, { signal }));
}

export async function sendMessage(noteId, payload, signal) {
  return readConversation(await mutate(`/api/notes/${encodeURIComponent(noteId)}/messages`, payload, { signal }));
}
