import { useCallback, useRef, useState } from 'react';
import { Link, useBeforeUnload, useBlocker, useNavigate, useParams, useSearchParams } from 'react-router';
import { getFlashcard, saveFlashcard } from '../api/flashcards';
import { listNotes } from '../api/notes';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import UnsavedChangesDialog from '../notes/UnsavedChangesDialog';
import { CARD_LIMITS, validateCard } from '../flashcards/helpers';

export default function FlashcardEditorPage() {
  const { cardId } = useParams();
  const load = useCallback((signal) => cardId ? getFlashcard(cardId, signal) : Promise.resolve(null), [cardId]);
  const card = useResource(load);
  if (card.loading) return <p className="page-status" role="status">Loading flashcard…</p>;
  if (card.error) return <RequestError error={card.error} onRetry={card.reload} />;
  return <CardEditor key={cardId || 'new'} card={card.data} />;
}

function CardEditor({ card }) {
  const notes = useResource(listNotes);
  const [params] = useSearchParams();
  const initial = { question: card?.question || '', answer: card?.answer || '', difficulty: card?.difficulty || '', noteId: String(card?.note_id || params.get('note') || '') };
  const [draft, setDraft] = useState(initial);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const saved = useRef(false);
  const form = useRef(null);
  const navigate = useNavigate();
  const dirty = Object.keys(initial).some((key) => initial[key] !== draft[key]);
  const blocker = useBlocker(({ currentLocation, nextLocation }) => !saved.current && (dirty || saving) && currentLocation.pathname !== nextLocation.pathname);
  useBeforeUnload(useCallback((event) => { if (!saved.current && (dirty || saving)) { event.preventDefault(); event.returnValue = ''; } }, [dirty, saving]));
  const selected = notes.data?.find((note) => String(note.id) === draft.noteId);

  function update(event) {
    setDraft({ ...draft, [event.target.name]: event.target.value });
    setErrors({ ...errors, [event.target.name]: undefined });
  }

  async function submit(event) {
    event.preventDefault();
    if (saving) return;
    const nextErrors = validateCard(draft);
    if (!card && !selected) nextErrors.noteId = 'Choose an available note.';
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) { form.current.elements[Object.keys(nextErrors)[0]]?.focus(); return; }
    setSaving(true); setError(null);
    try {
      await saveFlashcard(card?.id, { question: draft.question, answer: draft.answer, difficulty: draft.difficulty, note_id: Number(draft.noteId), topic_id: selected?.topic_id ?? null });
      saved.current = true;
      navigate(`/app/flashcards?note=${draft.noteId}`, { replace: true, state: { saved: true } });
    } catch (failure) { setError(failure); } finally { setSaving(false); }
  }

  return (
    <div className="notes-workspace flashcards-workspace">
      <Link className="text-link back-link" to="/app/flashcards">← All flashcards</Link>
      <PageHeader title={card ? 'Edit flashcard' : 'Create a flashcard'} description="One clear question, one useful answer. Keep each card focused." />
      <form ref={form} className="panel flashcard-editor" onSubmit={submit} noValidate aria-busy={saving}>
        <fieldset className="form-fields" disabled={saving}>
          <div className="card-filters">
            <label>Source note<select name="noteId" value={draft.noteId} onChange={update} disabled={Boolean(card) || notes.loading || Boolean(notes.error)} aria-invalid={Boolean(errors.noteId)} aria-describedby={errors.noteId ? 'noteId-error' : undefined}><option value="">Choose a note</option>{draft.noteId && !selected && <option value={draft.noteId}>{card ? `Note #${card.note_id}` : 'Unavailable note'}</option>}{notes.data?.map((note) => <option key={note.id} value={note.id}>{note.title}</option>)}</select></label>
            <label>Difficulty<select name="difficulty" value={draft.difficulty} onChange={update}><option value="">Not set</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
          </div>
          {errors.noteId && <p id="noteId-error" className="field-error">{errors.noteId}</p>}
          <p className="card-source">{card ? 'The source note and topic cannot be changed on an existing card.' : `Topic follows the selected note${selected ? `: ${selected.topic?.title || 'No topic'}` : '.'}`}</p>
          {notes.error && <RequestError error={notes.error} onRetry={notes.reload} />}
          {!card && notes.data?.length === 0 && <p className="card-source">Create a note before adding flashcards. <Link className="text-link" to="/app/notes/new">Create note</Link></p>}
          {['question', 'answer'].map((field) => <div className="form-field" key={field}><label htmlFor={field}>{field === 'question' ? 'Question' : 'Answer'}</label><textarea id={field} name={field} value={draft[field]} onChange={update} maxLength={CARD_LIMITS[field]} rows={field === 'question' ? 3 : 6} required aria-invalid={Boolean(errors[field])} aria-describedby={`${field}-hint${errors[field] ? ` ${field}-error` : ''}`} placeholder={field === 'question' ? 'What do you want to recall?' : 'Write the explanation you want to remember.'} /><span className="card-source" id={`${field}-hint`}>{draft[field].length} / {CARD_LIMITS[field]} characters</span>{errors[field] && <p id={`${field}-error`} className="field-error">{errors[field]}</p>}</div>)}
        </fieldset>
        {error && <div role="alert" className="form-message form-message-error"><p>{error.status === 401 ? 'Your session expired. Log in in another tab, then save again. Your draft remains here.' : error.message}</p>{error.status === 401 && <Link className="text-link" to="/login" target="_blank" rel="noopener noreferrer">Log in</Link>}</div>}
        <div className="composer-actions"><p>Saved only when you select Save flashcard.</p><div><Link className="button button-secondary" to="/app/flashcards">Cancel</Link><button className="button button-primary" disabled={saving || (!card && (!selected || notes.loading))}>{saving ? 'Saving…' : 'Save flashcard'}</button></div></div>
      </form>
      <UnsavedChangesDialog blocker={blocker} saving={saving} subject="flashcard" />
    </div>
  );
}
