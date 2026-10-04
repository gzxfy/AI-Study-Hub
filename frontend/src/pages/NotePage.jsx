import { useCallback } from 'react';
import { Link, useLocation, useParams } from 'react-router';
import { getNote } from '../api/notes';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import { formatNoteDate } from '../notes/formatDate';

export default function NotePage() {
  const { noteId } = useParams();
  const { state } = useLocation();
  const loadNote = useCallback((signal) => getNote(noteId, signal), [noteId]);
  const { data: note, error, loading, reload } = useResource(loadNote);

  return (
    <div className="notes-workspace">
      <Link className="text-link back-link" to="/app/notes"><span className="rotate"><Icon name="arrow" size={15} /></span> All notes</Link>
      {state?.created && <p className="note-saved-message" role="status"><Icon name="check" size={16} /> Your note has been saved.</p>}
      {loading ? <p className="page-status" role="status">Loading your note…</p> : error ? (
        <section className="panel note-details">
          <PageHeader title={error.status === 404 ? 'Note not found' : 'Unable to open this note'} />
          <RequestError error={error} onRetry={reload} />
        </section>
      ) : (
        <>
          <PageHeader title={note.title} />
          <div className="note-metadata">
            <span className="topic-tag topic-green">{note.topic?.title || 'No topic'}</span>
            <span>Updated {formatNoteDate(note.updated_at)}</span>
          </div>
          <article className="panel saved-note" aria-label="Note content">{note.content}</article>
        </>
      )}
    </div>
  );
}
