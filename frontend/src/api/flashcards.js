import { ApiError, mutate, request } from './client.js';

function readCard(data) {
  const card = data?.flashcard;
  if (card?.id == null || typeof card.question !== 'string' || typeof card.answer !== 'string') {
    throw new ApiError('Unable to read this flashcard. Please reload and try again.');
  }
  return card;
}

export async function listFlashcards(signal) {
  const data = await request('/api/flashcards', { signal });
  if (!Array.isArray(data.flashcards)) throw new ApiError('Unable to read your flashcards.');
  return data.flashcards.map((card) => readCard({ flashcard: card }));
}

export async function getFlashcard(id, signal) {
  return readCard(await request(`/api/flashcards/${encodeURIComponent(id)}`, { signal }));
}

export async function saveFlashcard(id, payload) {
  // The current PATCH route cannot reassign a card's note or topic.
  const body = id == null ? payload : {
    question: payload.question, answer: payload.answer, difficulty: payload.difficulty,
  };
  return readCard(await mutate(id == null ? '/api/flashcards' : `/api/flashcards/${encodeURIComponent(id)}`, body, {
    method: id == null ? 'POST' : 'PATCH',
  }));
}

export function deleteFlashcard(id) {
  return mutate(`/api/flashcards/${encodeURIComponent(id)}`, undefined, { method: 'DELETE' });
}
