import { useCallback, useRef, useState } from 'react';
import { Link, useBeforeUnload, useBlocker, useNavigate, useParams } from 'react-router';
import { getTopic, saveTopic } from '../api/topics';
import FormField from '../components/FormField';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import UnsavedChangesDialog from '../notes/UnsavedChangesDialog';
import { topicColor } from '../topics/color';

export default function TopicEditorPage() {
  const { topicId } = useParams();
  const load = useCallback((signal) => topicId ? getTopic(topicId, signal) : Promise.resolve(null), [topicId]);
  const { data, loading, error, reload } = useResource(load);

  if (loading) return <p className="page-status" role="status">Opening topic editor…</p>;
  if (error) return <RequestError error={error} onRetry={reload} />;
  return <TopicForm key={topicId || 'new'} topic={data?.topic} />;
}

function TopicForm({ topic }) {
  const navigate = useNavigate();
  const initial = { title: topic?.title || '', description: topic?.description || '', color: topicColor(topic?.color) };
  const [draft, setDraft] = useState(initial);
  const [errors, setErrors] = useState({});
  const [failure, setFailure] = useState(null);
  const [saving, setSaving] = useState(false);
  const saved = useRef(false);
  const form = useRef(null);
  const dirty = Object.keys(initial).some((key) => draft[key] !== initial[key]);
  const backTo = topic ? `/app/topics/${topic.id}` : '/app/topics';
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
    const validation = {};
    if (!draft.title.trim() || draft.title.length > 100) validation.title = 'Enter a title between 1 and 100 characters.';
    if (!draft.description.trim() || draft.description.length > 1000) validation.description = 'Enter a description between 1 and 1,000 characters.';
    setErrors(validation);
    setFailure(null);
    if (Object.keys(validation).length) {
      form.current.elements[Object.keys(validation)[0]].focus();
      return;
    }
    setSaving(true);
    try {
      const result = await saveTopic(topic?.id, { ...draft, title: draft.title.trim(), description: draft.description.trim() });
      saved.current = true;
      navigate(`/app/topics/${result.id}`, { replace: true });
    } catch (error) {
      setFailure(error);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="notes-workspace">
      <Link className="text-link back-link" to={backTo}>Back to {topic ? 'topic' : 'topics'}</Link>
      <PageHeader title={topic ? 'Edit topic' : 'Create a topic'} description="Give related study materials a clear place to belong." />
      <form ref={form} className="topic-form" onSubmit={handleSave} noValidate aria-busy={saving}>
        <fieldset className="panel form-fields topic-form-fields" disabled={saving}>
          <FormField id="title" label="Topic name" value={draft.title} onChange={updateField} placeholder="e.g. Computer science" maxLength={100} error={errors.title} required />
          <div className="form-field">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={draft.description}
              onChange={updateField}
              placeholder="What will you study in this topic?"
              maxLength={1000}
              required
              aria-invalid={errors.description ? true : undefined}
              aria-describedby={errors.description ? 'description-error description-hint' : 'description-hint'}
            />
            {errors.description && <p className="field-error" id="description-error">{errors.description}</p>}
            <p className="field-hint" id="description-hint">{draft.description.length} / 1,000 characters</p>
          </div>
          <div className="form-field">
            <label htmlFor="color">Topic color</label>
            <div className="topic-color-control">
              <input type="color" id="color" name="color" value={draft.color} onChange={updateField} />
              <span>{draft.color.toUpperCase()}</span>
            </div>
            <p className="field-hint">A visual cue to help you recognize this topic.</p>
          </div>
        </fieldset>
        {failure && (
          <div className="form-message form-message-error" role="alert">
            <p>{failure.status === 401 ? 'Your session expired. Log in in a new tab, then return and save your changes.' : failure.message}</p>
            {failure.status === 401 && <Link className="text-link" to="/login" target="_blank" rel="noopener noreferrer">Log in in a new tab</Link>}
          </div>
        )}
        <div className="composer-actions">
          <p>{dirty ? 'You have unsaved changes.' : 'Changes are saved when you select Save topic.'}</p>
          <div><Link className="button button-secondary" to={backTo}>Cancel</Link><button className="button button-primary" disabled={saving}>{saving ? 'Saving…' : 'Save topic'}</button></div>
        </div>
      </form>
      <UnsavedChangesDialog blocker={blocker} saving={saving} subject="topic" />
    </div>
  );
}
