import { ApiError, mutate, request } from './client.js';

export async function startStudy(noteId, difficulty, signal) {
  const query = new URLSearchParams({ note_id: String(noteId) });
  if (difficulty) query.set('difficulty', difficulty);
  const cards = await request(`/study_mode/start?${query}`, { signal });
  if (!Array.isArray(cards) || cards.some((card) => card.id == null || typeof card.question !== 'string' || typeof card.answer !== 'string')) {
    throw new ApiError('Study Hub returned an unexpected study session.');
  }
  return cards;
}

export async function reviewCard(id, correct) {
  const data = await mutate('/study_mode/review', { flashcard_id: id, marked_correctly: correct });
  if (data.flashcard_id !== id || !Number.isInteger(data.times_seen)) {
    throw new ApiError('The review response could not be verified.');
  }
  return data;
}

export async function finishStudy(results) {
  const data = await mutate('/study_mode/end', { reviewed_results: results });
  if (!Number.isInteger(data.reviewed_count) || !Number.isInteger(data.correct_count) || !Number.isFinite(data.accuracy)) {
    throw new ApiError('The study summary could not be read.');
  }
  return data;
}
