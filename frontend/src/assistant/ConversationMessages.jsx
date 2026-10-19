import { useEffect, useRef, useState } from 'react';
import Icon from '../components/Icon';
import MessageContent from './MessageContent';
import { messageTime } from './messageFormat';

export default function ConversationMessages({ messages, pending, pendingQuestion }) {
  const scroll = useRef(null);
  const atBottom = useRef(true);
  const [newMessages, setNewMessages] = useState(false);
  function jumpToLatest() {
    const element = scroll.current;
    if (element) element.scrollTop = element.scrollHeight;
    atBottom.current = true;
    setNewMessages(false);
  }
  useEffect(() => {
    if (atBottom.current) jumpToLatest();
    else setNewMessages(true);
  }, [messages, pending]);
  return <div className="conversation-transcript">
    <div ref={scroll} className="conversation-messages" role="region" aria-label="Conversation history" tabIndex={0} onScroll={() => {
      const element = scroll.current;
      atBottom.current = element.scrollHeight - element.scrollTop - element.clientHeight < 60;
      if (atBottom.current) setNewMessages(false);
    }}>
      {messages.map((message) => <Message key={message.id} message={message} />)}
      {pending && <><article className="chat-message chat-message-user"><span className="chat-avatar"><Icon name="user" size={17} /></span><div className="chat-message-body"><h3>You <span className="message-status">Sending · not saved yet</span></h3><p className="pending-question">{pendingQuestion}</p></div></article><div className="chat-pending"><span className="status-dot" /> Working through your notes…</div></>}
    </div>
    {newMessages && <button className="assistant-jump" onClick={jumpToLatest}>Jump to latest message ↓</button>}
  </div>;
}

function Message({ message }) {
  const [copyStatus, setCopyStatus] = useState('');
  async function copy() {
    try { await navigator.clipboard.writeText(message.content); setCopyStatus('Copied'); }
    catch { setCopyStatus('Copy unavailable. Select the message text to copy it.'); }
  }
  const timestamp = messageTime(message.timestamp);
  return <article className={`chat-message chat-message-${message.role}`}>
    <span className="chat-avatar"><Icon name={message.role === 'user' ? 'user' : 'assistant'} size={17} /></span>
    <div className="chat-message-body"><div className="chat-message-meta"><h3>{message.role === 'user' ? 'You' : 'Study assistant'}</h3>{timestamp && <time dateTime={message.timestamp}>{timestamp}</time>}</div>
      {message.role === 'assistant' ? <MessageContent content={message.content} /> : <p className="pending-question">{message.content}</p>}
      {message.role === 'assistant' && <div className="message-copy"><button className="text-button" onClick={copy} aria-label="Copy assistant response">Copy response</button><span role="status">{copyStatus}</span></div>}
    </div>
  </article>;
}
