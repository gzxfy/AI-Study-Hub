import { useCallback } from 'react';
import { getNote } from '../api/notes';
import useResource from '../hooks/useResource';
import RequestError from '../components/RequestError';

export default function SourcePreview({ noteId }) {
  const load = useCallback((signal) => getNote(noteId, signal), [noteId]);
  const { data, loading, error, reload } = useResource(load);
  return <div className="assistant-source">{loading ? <p role="status">Loading note…</p> : error ? <RequestError error={error} onRetry={reload} /> : <><p className="assistant-source-label">Your saved note · AI may use selected excerpts</p><div className="assistant-source-content" tabIndex={0} aria-label="Note content">{data.content}</div></>}</div>;
}
