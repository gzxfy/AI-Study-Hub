// Match validate_note_data in the backend service, not the wider database column.
export const NOTE_LIMITS = { title: 100, content: 5000 };

export function validateNote({ title, content }) {
  const errors = {};
  if (!title.trim()) errors.title = 'Give your note a title.';
  else if (title.length > NOTE_LIMITS.title) errors.title = `Keep the title under ${NOTE_LIMITS.title + 1} characters.`;
  if (!content.trim()) errors.content = 'Add some content before saving your note.';
  else if (content.length > NOTE_LIMITS.content) errors.content = `Keep the content under ${NOTE_LIMITS.content + 1} characters.`;
  return errors;
}

export function notePayload({ title, content, topicId }) {
  return { title: title.trim(), content: content.trim(), topic_id: topicId ? Number(topicId) : null };
}
