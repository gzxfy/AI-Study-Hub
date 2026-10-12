import { useEffect, useRef } from 'react';
import Icon from '../components/Icon';

export default function ConversationMessages({ messages, pending }) {
  const end = useRef(null);

  useEffect(() => {
    end.current?.scrollIntoView({ block: 'nearest' });
  }, [messages.length, pending]);

  return (
    <div className="conversation-messages" role="log" aria-label="Conversation" aria-live="polite" aria-relevant="additions text">
      {messages.map((message) => (
        <article className={`chat-message chat-message-${message.role}`} key={message.id}>
          <span className="chat-avatar"><Icon name={message.role === 'user' ? 'user' : 'assistant'} size={17} /></span>
          <div className="chat-message-body">
            <h3>{message.role === 'user' ? 'You' : 'Study assistant'}</h3>
            {/* Render model output as text; never interpret generated HTML. */}
            <p>{message.content}</p>
          </div>
        </article>
      ))}
      {pending && (
        <div className="chat-pending" role="status"><span className="status-dot" /> Working through your question…</div>
      )}
      <div ref={end} />
    </div>
  );
}
