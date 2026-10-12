import { Link, useSearchParams } from 'react-router';
import { listNotes } from '../api/notes';
import ConversationPanel from '../assistant/ConversationPanel';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';

export default function AssistantPage() {
  const [params, setParams] = useSearchParams();
  const { data: notes, loading, error, reload } = useResource(listNotes);
  const selectedId = params.get('note');
  const selectedNote = notes?.find((note) => String(note.id) === selectedId);

  return (
    <div className="notes-workspace assistant-workspace">
      <PageHeader title="AI Assistant" description="Ask questions, connect ideas, and study with your notes beside you." />
      {loading ? <p className="page-status" role="status">Loading your notes…</p> : error ? (
        <RequestError error={error} onRetry={reload} />
      ) : notes.length === 0 ? (
        <section className="panel feature-state">
          <span className="empty-icon"><Icon name="notes" size={25} /></span>
          <h2>Start with a note</h2>
          <p>The assistant uses your study material as context. Create a note to begin.</p>
          <Link className="button button-primary" to="/app/notes/new">Create a note</Link>
        </section>
      ) : (
        <>
          <div className="assistant-note-picker">
            <label htmlFor="assistant-note">Study material</label>
            <select id="assistant-note" value={selectedNote ? selectedId : ''} onChange={(event) => setParams(event.target.value ? { note: event.target.value } : {})}>
              <option value="">Choose a note</option>
              {notes.map((note) => <option key={note.id} value={note.id}>{note.title}</option>)}
            </select>
            <span>Each note has its own saved conversation.</span>
          </div>
          {selectedNote ? <ConversationPanel key={selectedNote.id} note={selectedNote} /> : (
            <section className="panel feature-state">
              <span className="empty-icon"><Icon name="assistant" size={26} /></span>
              <h2>{selectedId ? 'This note is unavailable' : 'What are you studying?'}</h2>
              <p>{selectedId ? 'Choose another note from your workspace to continue.' : 'Select a note above to start a conversation or return to one you have saved.'}</p>
            </section>
          )}
        </>
      )}
    </div>
  );
}
