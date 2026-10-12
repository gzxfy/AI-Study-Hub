import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useBeforeUnload, useBlocker } from 'react-router';
import { getConversation, QUESTION_LIMIT, sendMessage } from '../api/assistant';
import Icon from '../components/Icon';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import UnsavedChangesDialog from '../notes/UnsavedChangesDialog';
import ConversationMessages from './ConversationMessages';

const suggestions = [
  'Summarize the main ideas in this note.',
  'Explain the most important concept with an example.',
  'Ask me a question to check my understanding.',
];

export default function ConversationPanel({ note }) {
  const load = useCallback((signal) => getConversation(note.id, signal), [note.id]);
  const history = useResource(load);
  const [reply, setReply] = useState(null);
  const [question, setQuestion] = useState('');
  const [includeTopic, setIncludeTopic] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const requestController = useRef(null);
  const lastAttempt = useRef(null);
  const composer = useRef(null);
  const messages = reply?.messages ?? history.data?.messages ?? [];
  const ready = !history.loading && !history.error;
  const dirty = question.length > 0 || pending;
  const blocker = useBlocker(({ currentLocation, nextLocation }) => (
    dirty && (currentLocation.pathname !== nextLocation.pathname || currentLocation.search !== nextLocation.search)
  ));

  useEffect(() => () => requestController.current?.abort(), []);
  useBeforeUnload(useCallback((event) => {
    if (dirty) {
      event.preventDefault();
      event.returnValue = '';
    }
  }, [dirty]));

  async function handleSubmit(event) {
    event.preventDefault();
    const message = question.trim();
    if (!message || message.length > QUESTION_LIMIT || pending || !ready) return;

    // Reuse the request ID after an uncertain response to avoid duplicate AI calls.
    const previous = lastAttempt.current;
    const payload = previous?.message === message && previous.include_topic === includeTopic
      ? previous
      : { message, include_topic: includeTopic, request_id: crypto.randomUUID() };
    lastAttempt.current = payload;
    requestController.current = new AbortController();
    setPending(true);
    setError(null);

    try {
      const result = await sendMessage(note.id, payload, requestController.current.signal);
      setReply(result);
      setQuestion('');
      lastAttempt.current = null;
    } catch (failure) {
      if (failure.name !== 'AbortError') setError(failure);
    } finally {
      setPending(false);
      composer.current?.focus();
    }
  }

  function reloadConversation() {
    setReply(null);
    setError(null);
    history.reload();
  }

  function useSuggestion(value) {
    setQuestion(value);
    composer.current?.focus();
  }

  return (
    <section className="panel conversation-panel" aria-label={`Assistant for ${note.title}`}>
      <header className="conversation-header">
        <div><span className="conversation-label">Studying</span><h2>{note.title}</h2></div>
        <div className="record-actions">
          <Link className="text-link" to={`/app/notes/${note.id}`}>Open note <Icon name="arrow" size={14} /></Link>
          <button className="text-button" disabled={pending || history.loading} onClick={reloadConversation}>Reload history</button>
        </div>
      </header>
      <div className="conversation-context">
        <Icon name="notes" size={16} />
        <span>{includeTopic ? `Next question: this note and related notes in ${note.topic?.title || 'its topic'}` : 'Next question: this note'}</span>
        <label>
          <input type="checkbox" checked={includeTopic} onChange={(event) => setIncludeTopic(event.target.checked)} disabled={!note.topic_id || pending} />
          Include topic notes
        </label>
      </div>
      {!note.topic_id && <p className="context-hint">Assign this note to a topic to include related notes.</p>}

      {history.loading ? <p className="page-status" role="status">Loading conversation…</p> : history.error ? (
        <RequestError error={history.error} onRetry={history.reload} />
      ) : messages.length === 0 && !pending ? (
        <div className="conversation-empty">
          <span className="empty-icon"><Icon name="assistant" size={25} /></span>
          <h2>Work through your notes.</h2>
          <p>Ask for an explanation, review the main ideas, or check what you understand.</p>
          <div className="question-suggestions">
            {suggestions.map((suggestion) => <button key={suggestion} onClick={() => useSuggestion(suggestion)}>{suggestion}<Icon name="arrow" size={14} /></button>)}
          </div>
        </div>
      ) : <ConversationMessages messages={messages} pending={pending} />}

      <form className="message-composer" onSubmit={handleSubmit} aria-busy={pending}>
        <label className="sr-only" htmlFor="assistant-question">Your question</label>
        <textarea
          ref={composer}
          id="assistant-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about your notes…"
          maxLength={QUESTION_LIMIT}
          disabled={pending || !ready}
          aria-describedby="question-hint"
          onKeyDown={(event) => {
            if (event.key === 'Enter' && (event.ctrlKey || event.metaKey) && !event.nativeEvent.isComposing) {
              event.preventDefault();
              event.currentTarget.form.requestSubmit();
            }
          }}
        />
        <div className="composer-bottom">
          <span id="question-hint">{question.length.toLocaleString()} / {QUESTION_LIMIT.toLocaleString()} · Ctrl/⌘ + Enter to send</span>
          <button className="button button-primary" disabled={pending || !ready || !question.trim()}>
            {pending ? 'Sending…' : error ? 'Try sending again' : 'Send message'}<Icon name="arrow" size={16} />
          </button>
        </div>
        {error && (
          <div className="form-message form-message-error" role="alert">
            <p>{error.status === 401 ? 'Your session expired. Log in in a new tab, then return to send your question.' : error.message}</p>
            {error.status === 401 && <Link className="text-link" to="/login" target="_blank" rel="noopener noreferrer">Log in in a new tab</Link>}
          </div>
        )}
        <p className="assistant-footnote">Responses can contain mistakes. Check important details against your notes.</p>
      </form>
      <UnsavedChangesDialog blocker={blocker} saving={pending} subject="conversation" />
    </section>
  );
}
