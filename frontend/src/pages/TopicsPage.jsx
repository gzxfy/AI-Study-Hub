import { useState } from 'react';
import { Link, useLocation } from 'react-router';
import { listTopics } from '../api/topics';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import { topicColor } from '../topics/color';

export default function TopicsPage() {
  const { data: topics, loading, error, reload } = useResource(listTopics);
  const [query, setQuery] = useState('');
  const { state } = useLocation();
  const visible = topics?.filter((topic) => topic.title.toLowerCase().includes(query.trim().toLowerCase())) || [];

  return (
    <div className="notes-workspace">
      <div className="page-heading-row">
        <PageHeader title="Topics" description="Organize your notes by subject, course, or project." />
        <Link className="button button-primary" to="/app/topics/new"><Icon name="plus" size={17} /> Create topic</Link>
      </div>
      {state?.deleted && <p className="note-saved-message" role="status">Topic deleted.</p>}
      <section className="panel notes-library" aria-label="Your topics">
        <div className="notes-toolbar">
          <h2>All topics {topics && <span className="note-count">{topics.length}</span>}</h2>
          <label className="notes-search">
            <span className="sr-only">Search topics</span>
            <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search topics…" />
          </label>
        </div>
        {loading ? <p className="page-status" role="status">Loading your topics…</p> : error ? (
          <RequestError error={error} onRetry={reload} />
        ) : visible.length === 0 ? (
          <div className="notes-empty">
            <span className="empty-icon"><Icon name="topics" size={25} /></span>
            <h2>{topics.length ? 'No matching topics' : 'Give your notes a home'}</h2>
            <p>{topics.length ? 'Try another title.' : 'Create a topic to keep related study materials together.'}</p>
            {topics.length ? <button className="text-button" onClick={() => setQuery('')}>Clear search</button> : <Link className="button button-primary" to="/app/topics/new">Create your first topic</Link>}
          </div>
        ) : (
          <div className="topic-grid">
            {visible.map((topic) => (
              <Link className="topic-card" to={`/app/topics/${topic.id}`} key={topic.id}>
                <span className="topic-symbol" style={{ color: topicColor(topic.color) }}><Icon name="topics" size={24} /></span>
                <h2>{topic.title}</h2>
                <p>{topic.description || 'Open this topic to view its notes.'}</p>
                <span className="topic-card-footer">
                  <span>{Number.isInteger(topic.note_count) ? `${topic.note_count} ${topic.note_count === 1 ? 'note' : 'notes'}` : 'View notes'}</span>
                  <Icon name="arrow" size={16} />
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
