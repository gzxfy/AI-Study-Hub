import { useCallback, useRef, useState } from 'react';
import { Link, useBeforeUnload, useBlocker, useNavigate } from 'react-router';
import { createNote, listTopics } from '../api/notes';
import FormField from '../components/FormField';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';
import useResource from '../hooks/useResource';
import { NOTE_LIMITS, notePayload, validateNote } from '../notes/validation';
import UnsavedChangesDialog from '../notes/UnsavedChangesDialog';

export default function CreateNotePage() {
  const navigate = useNavigate();
  const topics = useResource(listTopics);
  const [draft, setDraft] = useState({ title: '', content: '', topicId: '' });
  const [errors, setErrors] = useState({});
  const [saveError, setSaveError] = useState(null);
  const [saving, setSaving] = useState(false);
  const saved = useRef(false);
  const form = useRef(null);
  const dirty = Boolean(draft.title || draft.content || draft.topicId);
  const wordCount = draft.content.trim() ? draft.content.trim().split(/\s+/).length : 0;
  const blocker = useBlocker(({ currentLocation, nextLocation }) => (
    dirty && !saved.current && currentLocation.pathname !== nextLocation.pathname
  ));

  useBeforeUnload(useCallback((event) => {
    if (dirty && !saved.current) {
      event.preventDefault();
      event.returnValue = '';
    }
  }, [dirty]));

  function updateField(event) {
    const { name, value } = event.target;
    setDraft((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  async function handleSave(event) {
    event.preventDefault();
    if (saving) return;
    const validationErrors = validateNote(draft);
    setErrors(validationErrors);
    setSaveError(null);

    const firstError = Object.keys(validationErrors)[0];
    if (firstError) {
      form.current.elements[firstError].focus();
      return;
    }

    setSaving(true);
    try {
      const note = await createNote(notePayload(draft));
      // Only a confirmed server response can clear the unsaved-changes guard.
      saved.current = true;
      navigate(`/app/notes/${note.id}`, { replace: true, state: { created: true } });
    } catch (error) {
      setSaveError(error);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="notes-workspace">
      <Link className="text-link back-link" to="/app/notes"><span className="rotate"><Icon name="arrow" size={15} /></span> All notes</Link>
      <div className="page-heading-row">
        <PageHeader title="Create a note" description="Capture a concept, a lecture, or something worth revisiting." />
        <span className="draft-status"><span className="status-dot" />{saving ? 'Saving…' : 'Unsaved draft'}</span>
      </div>

      <form ref={form} className="note-composer" onSubmit={handleSave} noValidate aria-busy={saving}>
        <fieldset className="composer-fields" disabled={saving}>
          <section className="panel editor-panel" aria-label="Note content">
            <FormField
              id="title"
              label="Title"
              placeholder="Give your note a clear title"
              value={draft.title}
              onChange={updateField}
              maxLength={NOTE_LIMITS.title}
              error={errors.title}
              required
            />
            <div className="editor-divider" />
            <div className="form-field content-field">
              <label htmlFor="content">Content</label>
              <textarea
                id="content"
                name="content"
                placeholder="Start writing your notes here…"
                value={draft.content}
                onChange={updateField}
                maxLength={NOTE_LIMITS.content}
                aria-invalid={errors.content ? true : undefined}
                aria-describedby={errors.content ? 'content-error content-hint' : 'content-hint'}
                required
              />
              {errors.content && <p id="content-error" className="field-error">{errors.content}</p>}
            </div>
            <div className="editor-footer">
              <span>{wordCount} {wordCount === 1 ? 'word' : 'words'}</span>
              <span id="content-hint">{draft.content.length.toLocaleString()} / {NOTE_LIMITS.content.toLocaleString()} characters</span>
            </div>
          </section>

          <aside className="note-options">
            <section className="panel note-details">
              <h2>Note details</h2>
              <label htmlFor="topicId">Topic <span>optional</span></label>
              <select
                id="topicId"
                name="topicId"
                value={draft.topicId}
                onChange={updateField}
                disabled={topics.loading || Boolean(topics.error)}
                aria-describedby="topic-hint"
              >
                <option value="">No topic</option>
                {topics.data?.map((topic) => <option key={topic.id} value={topic.id}>{topic.title}</option>)}
              </select>
              <p id="topic-hint" className="field-hint">{topics.loading ? 'Loading your topics…' : 'Group this note with related study materials.'}</p>
              {topics.error && (
                <div className="topic-load-error" role="status">
                  <p>Topics could not be loaded. You can still save without a topic.</p>
                  <button className="text-button" type="button" onClick={topics.reload}>Retry topics</button>
                </div>
              )}
              {!topics.loading && !topics.error && topics.data?.length === 0 && <p className="field-hint">You have no topics yet. This note can be saved on its own.</p>}
              <div className="note-save-info"><Icon name="notes" size={16} /><p>Your note is saved when you select <strong>Save note</strong>.</p></div>
            </section>
            <div className="note-writing-tip"><Icon name="book" size={18} /><p>Use your own words. A short explanation can be easier to review than a full transcript.</p></div>
          </aside>
        </fieldset>

        {saveError && (
          <div className="form-message form-message-error" role="alert">
            <p>{saveError.status === 401
              ? 'Your session has expired. Log in in a new tab, then return here and save again. Your draft is still on this page.'
              : saveError.message}
            </p>
            {saveError.status === 401 && (
              <Link className="text-link" to="/login" target="_blank" rel="noopener noreferrer">
                Log in in a new tab <Icon name="arrow" size={14} />
              </Link>
            )}
          </div>
        )}
        <div className="composer-actions">
          <p>Plain text · Only visible to your account</p>
          <div>
            <Link className="button button-secondary" to="/app/notes">Cancel</Link>
            <button className="button button-primary" type="submit" disabled={saving}>
              {saving ? 'Saving…' : 'Save note'}<Icon name="check" size={16} />
            </button>
          </div>
        </div>
      </form>
      <UnsavedChangesDialog blocker={blocker} saving={saving} />
    </div>
  );
}
