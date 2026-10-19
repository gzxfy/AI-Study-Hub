import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useBeforeUnload, useBlocker } from 'react-router';
import { getConversation, QUESTION_LIMIT, sendMessage } from '../api/assistant';
import Icon from '../components/Icon';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import UnsavedChangesDialog from '../notes/UnsavedChangesDialog';
import ConversationMessages from './ConversationMessages';
import SourcePreview from './SourcePreview';
import { nextAttempt } from './requestAttempt';

const suggestions = [
  { title: 'Summarize', detail: 'Find the ideas that matter.', prompt: 'Summarize the main ideas in this note with a short list of key takeaways.' },
  { title: 'Explain simply', detail: 'Break it down, step by step.', prompt: 'Explain the most important concept in this note in simple terms, with a concrete example.' },
  { title: 'Quiz me', detail: 'Check what you understand.', prompt: 'Quiz me on this note. Ask one question at a time and wait for my answer before explaining.' },
];
const EMPTY_MESSAGES = [];

export default function ConversationPanel({ note }) {
  const load = useCallback((signal) => getConversation(note.id, signal), [note.id]);
  const history = useResource(load);
  const [reply, setReply] = useState(null);
  const [question, setQuestion] = useState('');
  const [includeTopic, setIncludeTopic] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const [showSource, setShowSource] = useState(false);
  const [slow, setSlow] = useState(false);
  const [announcement, setAnnouncement] = useState('');
  const busy = useRef(false);
  const title = useRef(null);
  const requestController = useRef(null);
  const lastAttempt = useRef(null);
  const composer = useRef(null);
  const messages = reply?.messages ?? history.data?.messages ?? EMPTY_MESSAGES;
  const ready = !history.loading && !history.error;
  const dirty = question.length > 0 || pending;
  const blocker = useBlocker(({ currentLocation, nextLocation }) => (
    dirty && (currentLocation.pathname !== nextLocation.pathname || currentLocation.search !== nextLocation.search)
  ));

  useEffect(() => () => requestController.current?.abort(), []);
  useEffect(() => { title.current?.focus(); }, [note.id]);
  useEffect(() => {
    setSlow(false);
    if (!pending) return;
    const timer = setTimeout(() => setSlow(true), 15000);
    return () => clearTimeout(timer);
  }, [pending]);
  useBeforeUnload(useCallback((event) => {
    if (dirty) {
      event.preventDefault();
      event.returnValue = '';
    }
  }, [dirty]));

  async function handleSubmit(event) {
    event.preventDefault();
    const message = question.trim();
    if (!message || message.length > QUESTION_LIMIT || busy.current || !ready) return;

    // Reuse the request ID so Flask can recognize a previously saved exchange.
    const payload = nextAttempt(lastAttempt.current, message, includeTopic);
    lastAttempt.current = payload;
    requestController.current = new AbortController();
    busy.current = true;
    setPending(true);
    setError(null);
    setAnnouncement('Sending your question. The assistant is preparing a response.');

    try {
      const result = await sendMessage(note.id, payload, requestController.current.signal);
      setReply(result);
      setQuestion('');
      lastAttempt.current = null;
      setAnnouncement('Response received and conversation saved. The latest response is in the conversation history.');
    } catch (failure) {
      if (failure.name !== 'AbortError') setError(failure);
    } finally {
      busy.current = false;
      if (!requestController.current.signal.aborted) {
        setPending(false);
      }
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
        <div><span className="conversation-label">Studying · saved conversation</span><h2 ref={title} tabIndex={-1}>{note.title}</h2></div>
        <div className="record-actions">
          <button className="text-button" aria-expanded={showSource} aria-controls="assistant-source-preview" onClick={() => setShowSource(!showSource)}>{showSource ? 'Hide note' : 'View note'}</button>
          <button className="text-button" disabled={pending || history.loading} onClick={reloadConversation}>Reload history</button>
        </div>
      </header>
      <div id="assistant-source-preview" hidden={!showSource}>{showSource && <SourcePreview noteId={note.id} />}</div>
      <div className="conversation-context">
        <Icon name="notes" size={16} />
        <span>{includeTopic ? `Next question: this note and related notes in ${note.topic?.title || 'its topic'}` : 'Next question: this note'}</span>
        <label>
          <input type="checkbox" checked={includeTopic} onChange={(event) => setIncludeTopic(event.target.checked)} disabled={!note.topic_id || pending} />
          Include topic notes
        </label>
      </div>
      {!note.topic_id && <p className="context-hint">Assign this note to a topic to include related notes.</p>}
      <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">{announcement}</p>

      {history.loading ? <p className="page-status" role="status">Loading conversation…</p> : history.error ? (
        <RequestError error={history.error} onRetry={history.reload} />
      ) : messages.length === 0 && !pending ? (
        <div className="conversation-empty">
          <span className="empty-icon"><Icon name="assistant" size={25} /></span>
          <h2>Work through your notes.</h2>
          <p>Ask for an explanation, review the main ideas, or check what you understand.</p>
          <div className="question-suggestions">
            {suggestions.map((suggestion) => <button key={suggestion.title} onClick={() => useSuggestion(suggestion.prompt)}><span><strong>{suggestion.title}</strong><small>{suggestion.detail}</small></span><Icon name="arrow" size={16} /></button>)}
          </div>
        </div>
      ) : <ConversationMessages messages={messages} pending={pending} pendingQuestion={lastAttempt.current?.message} />}

      <form className="message-composer" onSubmit={handleSubmit} aria-busy={pending}>
        <label className="composer-label" htmlFor="assistant-question">Your question</label>
        <textarea
          ref={composer}
          id="assistant-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about your notes…"
          maxLength={QUESTION_LIMIT}
          readOnly={pending}
          disabled={!ready}
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
        {slow && pending && <p className="assistant-slow" role="status">This is taking longer than usual. You can keep reading above while the response is prepared.</p>}
        <p className="assistant-footnote">Enter adds a new line. AI can make mistakes; check answers against your material.</p>
      </form>
      <UnsavedChangesDialog blocker={blocker} saving={pending} subject="conversation" />
    </section>
  );
}
