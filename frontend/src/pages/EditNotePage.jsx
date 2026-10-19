import { useCallback } from 'react';
import { useParams } from 'react-router';
import { getNote } from '../api/notes';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import NoteEditor from '../notes/NoteEditor';

export default function EditNotePage() {
  const { noteId } = useParams();
  const load = useCallback((signal) => getNote(noteId, signal), [noteId]);
  const { data, loading, error, reload } = useResource(load);

  if (loading) return <p className="page-status" role="status">Loading your note…</p>;
  if (error) return <RequestError error={error} onRetry={reload} />;
  return <NoteEditor key={data.id} note={data} />;
}
