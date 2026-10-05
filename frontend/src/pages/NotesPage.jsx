import { useState } from 'react';
import { Link, useLocation } from 'react-router';
import { deleteNote, listNotes } from '../api/notes';
import DeleteDialog from '../components/DeleteDialog';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import { formatNoteDate } from '../notes/formatDate';

export default function NotesPage() {
  const { data: notes, error, loading, reload } = useResource(listNotes);
  const [query, setQuery] = useState('');
  const [deleting, setDeleting] = useState(null);
  const [deleted, setDeleted] = useState(false);
  const { state } = useLocation();
  const search = query.trim().toLowerCase();
  const visibleNotes = notes?.filter((note) => `${note.title} ${note.topic?.title || ''}`.toLowerCase().includes(search)) || [];

  return (
    <div className="notes-workspace">
      <div className="page-heading-row">
        <PageHeader title="Notes" description="Your study material, ready to revisit." />
        <Link className="button button-primary" to="/app/notes/new"><Icon name="plus" size={17} /> Create note</Link>
      </div>
      {(deleted || state?.deleted) && <p className="note-saved-message" role="status">Note deleted.</p>}
      <section className="panel notes-library" aria-label="Your notes">
        <div className="notes-toolbar">
          <h2>All notes {notes && <span className="note-count">{notes.length}</span>}</h2>
          <label className="notes-search">
            <span className="sr-only">Search notes</span>
            <input
              type="search"
              placeholder="Search by title or topic…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              disabled={loading || Boolean(error)}
            />
          </label>
        </div>

        {loading ? <p className="page-status" role="status">Loading your notes…</p> : error ? (
          <RequestError error={error} onRetry={reload} />
        ) : notes.length === 0 ? (
          <div className="notes-empty">
            <span className="empty-icon"><Icon name="notes" size={25} /></span>
            <h2>Your first note starts here</h2>
            <p>Add something you want to understand or remember.</p>
            <Link className="button button-primary" to="/app/notes/new"><Icon name="plus" size={16} /> Create a note</Link>
          </div>
        ) : visibleNotes.length === 0 ? (
          <div className="notes-empty" role="status">
            <h2>No matching notes</h2>
            <p>Try another title or topic.</p>
            <button className="text-button" onClick={() => setQuery('')}>Clear search</button>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="library-table">
              <thead><tr><th scope="col">Note</th><th scope="col">Topic</th><th scope="col">Last updated</th><th scope="col">Actions</th></tr></thead>
              <tbody>{visibleNotes.map((note) => (
                <tr key={note.id}>
                  <td>
                    <Link className="library-note-link" to={`/app/notes/${note.id}`}>
                      <span className="note-icon"><Icon name="notes" size={18} /></span>
                      <span>{note.title}<small>{note.excerpt || 'Open note'}</small></span>
                    </Link>
                  </td>
                  <td><span className="topic-tag topic-green">{note.topic?.title || 'No topic'}</span></td>
                  <td className="note-date">{formatNoteDate(note.updated_at)}</td>
                  <td>
                    <div className="record-actions">
                      <Link className="text-link" to={`/app/notes/${note.id}/edit`} aria-label={`Edit ${note.title}`}>Edit</Link>
                      <button className="text-button danger-text" onClick={() => setDeleting(note)} aria-label={`Delete ${note.title}`}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </section>
      {deleting && (
        <DeleteDialog
          title="Delete this note?"
          description={`“${deleting.title}” and its related flashcards and conversation will be permanently deleted. This cannot be undone.`}
          onDelete={() => deleteNote(deleting.id)}
          onDeleted={() => { setDeleting(null); setDeleted(true); reload(); }}
          onClose={() => setDeleting(null)}
        />
      )}
    </div>
  );
}
