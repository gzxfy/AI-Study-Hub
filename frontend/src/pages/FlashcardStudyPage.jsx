import { useCallback, useRef, useState } from 'react';
import { Link, useBeforeUnload, useBlocker, useSearchParams } from 'react-router';
import { listNotes } from '../api/notes';
import { finishStudy, reviewCard, startStudy } from '../api/study';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';

export default function FlashcardStudyPage() {
  const notes = useResource(listNotes);
  const [params] = useSearchParams();
  const [noteId, setNoteId] = useState(params.get('note') || '');
  const [difficulty, setDifficulty] = useState('');
  const [cards, setCards] = useState(null);
  const [results, setResults] = useState([]);
  const [revealed, setRevealed] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const [uncertain, setUncertain] = useState(false);
  const [summary, setSummary] = useState(null);
  const [ending, setEnding] = useState(false);
  const busy = useRef(false);
  const cardHeading = useRef(null);
  const active = cards !== null && !summary;
  const blocker = useBlocker(({ currentLocation, nextLocation }) => (active || pending) && currentLocation.pathname !== nextLocation.pathname);
  useBeforeUnload(useCallback((event) => { if (active || pending) { event.preventDefault(); event.returnValue = ''; } }, [active, pending]));

  async function start(event) {
    event.preventDefault();
    if (busy.current || !notes.data?.some((note) => String(note.id) === noteId)) return;
    busy.current = true; setPending(true); setError(null);
    try { setCards(await startStudy(noteId, difficulty)); setResults([]); setRevealed(false); setSummary(null); setUncertain(false); setEnding(false); }
    catch (failure) { setError(failure); }
    finally { busy.current = false; setPending(false); }
  }

  async function review(correct) {
    if (busy.current || uncertain || !revealed) return;
    busy.current = true; setPending(true); setError(null);
    const current = cards[results.length];
    try {
      await reviewCard(current.id, correct);
      setResults((previous) => [...previous, { flashcard_id: current.id, correct }]);
      setRevealed(false);
      cardHeading.current?.focus();
    } catch (failure) {
      setError(failure);
      // A lost response may still have committed. Never silently submit this review twice.
      setUncertain(true);
    } finally { busy.current = false; setPending(false); }
  }

  async function finish() {
    if (busy.current) return;
    busy.current = true; setPending(true); setError(null); setEnding(true);
    try { setSummary(await finishStudy(results)); }
    catch (failure) { setError(failure); }
    finally { busy.current = false; setPending(false); }
  }

  function reset() { setCards(null); setSummary(null); setResults([]); setError(null); setEnding(false); setUncertain(false); }
  const current = cards?.[results.length];
  const note = notes.data?.find((item) => String(item.id) === noteId);

  return (
    <div className="study-workspace flashcards-workspace">
      <Link className="text-link back-link" to="/app/flashcards">← Flashcard library</Link>
      <PageHeader title="Study session" description="Recall the answer first. Reveal it when you are ready." />
      {cards === null ? <section className="panel study-setup">
        <h2>What are you reviewing?</h2>
        {notes.loading ? <p className="page-status" role="status">Loading your notes…</p> : notes.error ? <RequestError error={notes.error} onRetry={notes.reload} /> : !notes.data.length ? <div className="notes-empty"><p>Create a note and add flashcards before starting.</p><Link className="button button-primary" to="/app/notes/new">Create note</Link></div> : <form onSubmit={start}>
          <div className="card-filters"><label>Note<select value={noteId} onChange={(event) => setNoteId(event.target.value)} required disabled={pending}><option value="">Choose a note</option>{noteId && !note && <option value={noteId}>Unavailable note</option>}{notes.data.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label>Difficulty<select value={difficulty} onChange={(event) => setDifficulty(event.target.value)} disabled={pending}><option value="">Any difficulty</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label></div>
          <p className="card-source">Review all matching cards from this note in a shuffled order.</p><button className="button button-primary" disabled={pending || !note}>{pending ? 'Loading cards…' : 'Start session'}</button>
        </form>}
      </section> : summary ? <section className="panel study-summary" aria-live="polite"><span className="card-difficulty">Session complete</span><h2>Time well spent.</h2><p>{summary.correct_count} correct out of {summary.reviewed_count} confirmed reviews · {summary.accuracy}% accuracy</p>{uncertain && <p className="card-source">An unconfirmed review is excluded from this summary; it may have reached the server.</p>}<div className="record-actions"><button className="button button-primary" onClick={reset}>Study again</button><Link className="button button-secondary" to="/app/flashcards">Back to flashcards</Link></div></section> : !cards.length ? <section className="panel notes-empty"><h2>No matching flashcards</h2><p>Add cards to this note, or choose a different difficulty.</p><div className="record-actions"><button className="button button-secondary" onClick={reset}>Change selection</button><Link className="button button-primary" to={`/app/flashcards/new?note=${noteId}`}>Create flashcard</Link></div></section> : (
        <section className="panel study-card-panel" aria-busy={pending}>
          <div className="section-heading"><span className="card-source">{note?.title || 'Selected note'}</span><span className="card-source" role="status">{results.length} / {cards.length} reviewed</span></div>
          <progress className="study-progress" max={cards.length} value={results.length} aria-label="Session progress" />
          {current && !ending ? <><span className="card-difficulty">{current.difficulty || 'Unrated'} · Question {results.length + 1}</span><h2 className="study-question" tabIndex={-1} ref={cardHeading}>{current.question}</h2>{revealed ? <div className="study-answer" aria-live="polite"><h3>Answer</h3><p>{current.answer}</p></div> : <button className="button button-primary reveal-button" onClick={() => setRevealed(true)} disabled={pending}>Reveal answer</button>}
            {revealed && <div className="study-review-actions"><button className="button button-secondary" disabled={pending || uncertain} onClick={() => review(false)}>Needs practice</button><button className="button button-primary" disabled={pending || uncertain} onClick={() => review(true)}>{pending ? 'Saving review…' : 'Got it'}</button></div>}
          </> : <div className="study-finished"><h2>{current ? 'Finish this session' : 'You have reviewed every card.'}</h2><p>Your confirmed reviews have been saved. Get your session summary below.</p></div>}
          {uncertain && <p className="form-message form-message-error" role="alert">We could not confirm the last review. It may already be saved, so this session will not submit that card again. Finish the session to see confirmed results.</p>}
          <div className="study-bottom"><span>Each confirmed answer is saved immediately.</span><button className="text-button" disabled={pending} onClick={finish}>{pending && ending ? 'Loading summary…' : ending ? 'Retry summary' : current ? 'Finish session' : 'View summary'}</button></div>
        </section>
      )}
      {error && <RequestError error={error} />}
      {blocker.state === 'blocked' && <StudyLeavePrompt pending={pending} onStay={() => blocker.reset()} onLeave={() => blocker.proceed()} />}
    </div>
  );
}

// A native dialog traps focus and supports Escape without a modal dependency.
function StudyLeavePrompt({ pending, onStay, onLeave }) {
  const open = useCallback((element) => { if (element && !element.open) element.showModal(); }, []);
  return <dialog ref={open} className="note-dialog" aria-labelledby="leave-study-title" onCancel={(event) => { event.preventDefault(); onStay(); }}><h2 id="leave-study-title">Leave this study session?</h2><p>{pending ? 'Wait for the current request to finish before leaving.' : 'Confirmed reviews are saved. Your place in this session will be lost.'}</p><div className="dialog-actions"><button className="button button-secondary" autoFocus onClick={onStay}>Keep studying</button><button className="button button-primary" disabled={pending} onClick={onLeave}>Leave session</button></div></dialog>;
}
