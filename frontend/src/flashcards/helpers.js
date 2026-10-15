export const CARD_LIMITS = { question: 500, answer: 2000 };

export function validateCard(draft) {
  const errors = {};
  for (const field of ['question', 'answer']) {
    if (!draft[field].trim()) errors[field] = `Enter a ${field === 'question' ? 'question' : 'response for the answer'}.`;
    else if (draft[field].length > CARD_LIMITS[field]) errors[field] = `Use ${CARD_LIMITS[field]} characters or fewer.`;
  }
  if (!/^\d+$/.test(String(draft.noteId)) || Number(draft.noteId) <= 0) errors.noteId = 'Choose a note for this card.';
  if (!['', 'easy', 'medium', 'hard'].includes(draft.difficulty)) errors.difficulty = 'Choose a supported difficulty.';
  return errors;
}

export function filterCards(cards, { query = '', noteId = '', topicId = '', difficulty = '' }) {
  const search = query.trim().toLowerCase();
  return cards.filter((card) => (
    (!search || `${card.question} ${card.answer}`.toLowerCase().includes(search)) &&
    (!noteId || String(card.note_id) === noteId) &&
    (!topicId || String(card.topic_id) === topicId) &&
    (!difficulty || card.difficulty === difficulty)
  ));
}
