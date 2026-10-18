import { ApiError, request } from './client.js';

const progressFields = [
  'total_cards',
  'total_reviewed',
  'average_accuracy',
  'cards_mastered',
  'cards_needing_reviewing',
  'cards_studied_today',
  'current_streak',
];

export async function getProgress(signal) {
  const data = await request('/api/progress', { signal });
  if (!data.progress || progressFields.some((field) => !Number.isFinite(data.progress[field]))) {
    throw new ApiError('Unable to read your study progress. Please try again.');
  }
  return data.progress;
}