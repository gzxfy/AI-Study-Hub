import { useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { listNotes } from '../api/notes';
import ConversationPanel from '../assistant/ConversationPanel';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';

export default function AssistantPage() {
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState('');
  const { data: notes, loading, error, reload } = useResource(listNotes);
  const selectedId = params.get('note');
  const selectedNote = notes?.find((note) => String(note.id) === selectedId);
  const visible = notes?.filter((note) => `${note.title} ${note.topic?.title || ''}`.toLowerCase().includes(query.trim().toLowerCase())) || [];
  return (
    <div className="assistant-workspace">
      <PageHeader title="AI Assistant" description="Understand your notes. Work through a question. Make the next idea click." />
      {loading ? <p className="page-status" role="status">Loading your study material…</p> : error ? <RequestError error={error} onRetry={reload} /> : notes.length === 0 ? (
        <section className="panel assistant-welcome"><Icon name="book" size={32} /><h2>Your notes are the starting point.</h2><p>Add a note first. Then ask for an explanation, a summary, or a practice question based on your material.</p><Link className="button button-primary" to="/app/notes/new">Create your first note</Link></section>
      ) : (
        <div className="assistant-grid">
          <aside className="panel assistant-library" aria-label="Study material">
            <div className="assistant-library-header"><h2>Your study material</h2><p>Choose a note to open its saved conversation.</p><label htmlFor="assistant-search">Find a note</label><input id="assistant-search" type="search" placeholder="Search title or topic…" value={query} onChange={(event) => setQuery(event.target.value)} /></div>
            <nav className="assistant-note-list" aria-label="Note conversations">
              {visible.map((note) => <button key={note.id} type="button" aria-current={String(note.id) === selectedId ? 'page' : undefined} onClick={() => setParams({ note: String(note.id) })}><Icon name="notes" size={18} /><span><strong>{note.title}</strong><small>{note.topic?.title || 'No topic'}</small></span>{String(note.id) === selectedId && <Icon name="chevron" size={14} />}</button>)}
              {!visible.length && <div className="assistant-library-empty"><p>No matching notes.</p><button className="text-button" onClick={() => setQuery('')}>Clear search</button></div>}
            </nav>
            <Link className="text-link assistant-library-footer" to="/app/notes/new"><Icon name="plus" size={16} /> Create note</Link>
          </aside>
          {selectedNote ? <ConversationPanel key={selectedNote.id} note={selectedNote} /> : <section className="panel assistant-welcome"><span className="empty-icon"><Icon name="assistant" size={28} /></span><span className="assistant-eyebrow">Your study companion</span><h2>{selectedId ? 'This note is unavailable' : 'What would you like to understand?'}</h2><p>{selectedId ? 'The note may have been removed or is not available to your account. Choose another note to continue.' : 'Choose a note from your library. Its saved conversation will open here, ready to pick up where you left off.'}</p><ul className="assistant-capabilities"><li><strong>Understand</strong><span>Break a difficult concept into smaller steps.</span></li><li><strong>Review</strong><span>Pull out key ideas from your material.</span></li><li><strong>Practice</strong><span>Try a question and explain your reasoning.</span></li></ul><p className="assistant-privacy">Only notes available to your account appear here.</p></section>}
        </div>
      )}
    </div>
  );
}
