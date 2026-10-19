import { useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router';
import { deleteFlashcard, listFlashcards } from '../api/flashcards';
import { listNotes, listTopics } from '../api/notes';
import DeleteDialog from '../components/DeleteDialog';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import Icon from '../components/Icon';
import useResource from '../hooks/useResource';
import { filterCards } from '../flashcards/helpers';

export default function FlashcardsPage() {
  const cards = useResource(listFlashcards);
  const notes = useResource(listNotes);
  const topics = useResource(listTopics);
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState('');
  const [deleting, setDeleting] = useState(null);
  const [deleted, setDeleted] = useState(false);
  const { state } = useLocation();
  const noteId = params.get('note') || '';
  const topicId = params.get('topic') || '';
  const difficulty = params.get('difficulty') || '';
  const visible = filterCards(cards.data || [], { query, noteId, topicId, difficulty });

  function changeFilter(key, value) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    setParams(next, { replace: true });
  }

  return (
    <div className="notes-workspace flashcards-workspace">
      <div className="page-heading-row">
        <PageHeader title="Flashcards" description="Small questions. Stronger recall. Build a collection from your notes." />
        <div className="record-actions">
          <Link className="button button-secondary" to={`/app/study${noteId ? `?note=${encodeURIComponent(noteId)}` : ''}`}>Study cards</Link>
          <Link className="button button-primary" to={`/app/flashcards/new${noteId ? `?note=${encodeURIComponent(noteId)}` : ''}`}><Icon name="plus" size={16} /> Create flashcard</Link>
        </div>
      </div>
      {(state?.saved || deleted) && <p className="note-saved-message" role="status">{deleted ? 'Flashcard deleted.' : 'Flashcard saved.'}</p>}
      <section className="panel notes-library">
        <div className="notes-toolbar"><h2>Your flashcards {cards.data && <span className="note-count">{cards.data.length}</span>}</h2><label className="notes-search"><span className="sr-only">Search questions and answers</span><input type="search" placeholder="Search questions and answers…" value={query} onChange={(event) => setQuery(event.target.value)} /></label></div>
        <div className="card-filters">
          <label>Note<select value={noteId} onChange={(event) => changeFilter('note', event.target.value)} disabled={notes.loading || Boolean(notes.error)}><option value="">All notes</option>{noteId && !notes.data?.some((note) => String(note.id) === noteId) && <option value={noteId}>Selected note (unavailable)</option>}{notes.data?.map((note) => <option key={note.id} value={note.id}>{note.title}</option>)}</select></label>
          <label>Topic<select value={topicId} onChange={(event) => changeFilter('topic', event.target.value)} disabled={topics.loading || Boolean(topics.error)}><option value="">All topics</option>{topicId && !topics.data?.some((topic) => String(topic.id) === topicId) && <option value={topicId}>Selected topic (unavailable)</option>}{topics.data?.map((topic) => <option key={topic.id} value={topic.id}>{topic.title}</option>)}</select></label>
          <label>Difficulty<select value={difficulty} onChange={(event) => changeFilter('difficulty', event.target.value)}><option value="">Any difficulty</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
          {(query || noteId || topicId || difficulty) && <button className="text-button" onClick={() => { setQuery(''); setParams({}); }}>Clear filters</button>}
        </div>
        {notes.error && <RequestError error={notes.error} onRetry={notes.reload} />}
        {topics.error && <RequestError error={topics.error} onRetry={topics.reload} />}
        {cards.loading ? <p className="page-status" role="status">Loading your flashcards…</p> : cards.error ? <RequestError error={cards.error} onRetry={cards.reload} /> : visible.length === 0 ? (
          <div className="notes-empty"><span className="empty-icon"><Icon name="flashcards" size={25} /></span><h2>{cards.data.length ? 'No matching flashcards' : 'Make your first flashcard'}</h2><p>{cards.data.length ? 'Try a different search or clear your filters.' : 'Choose a note, write a question, and add the answer you want to remember.'}</p>{!cards.data.length && <Link className="button button-primary" to="/app/flashcards/new">Create flashcard</Link>}</div>
        ) : <ul className="flashcard-list">{visible.map((card) => (
          <li key={card.id} className="flashcard-row">
            <div className="flashcard-copy"><span className="card-difficulty">{card.difficulty || 'Unrated'}</span><h2>{card.question}</h2><p className="card-source">{notes.data?.find((note) => note.id === card.note_id)?.title || `Note #${card.note_id}`} · {topics.data?.find((topic) => topic.id === card.topic_id)?.title || (card.topic_id ? `Topic #${card.topic_id}` : 'No topic')}</p><details><summary>Show answer</summary><p className="card-answer">{card.answer}</p></details></div>
            <div className="record-actions"><Link className="text-link" to={`/app/flashcards/${card.id}/edit`} aria-label={`Edit ${card.question}`}>Edit</Link><button className="text-button danger-text" onClick={() => setDeleting(card)} aria-label={`Delete ${card.question}`}>Delete</button></div>
          </li>
        ))}</ul>}
        {cards.data && <div className="table-footer" role="status">{visible.length} of {cards.data.length} flashcards</div>}
      </section>
      {deleting && <DeleteDialog title="Delete this flashcard?" description={`“${deleting.question}” will be permanently deleted. This cannot be undone.`} onDelete={() => deleteFlashcard(deleting.id)} onDeleted={() => { setDeleting(null); setDeleted(true); cards.reload(); }} onClose={() => setDeleting(null)} />}
    </div>
  );
}
