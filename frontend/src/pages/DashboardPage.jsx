import { useState } from 'react';
import { Link } from 'react-router';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import { listFlashcards } from '../api/flashcards';
import { listNotes } from '../api/notes';
import { getProgress } from '../api/progress';
import { listTopics } from '../api/topics';
import { useAuth } from '../auth/AuthContext';

async function loadOverview(signal) {
  const [notes, topics, flashcards, progress] = await Promise.all([
    listNotes(signal),
    listTopics(signal),
    listFlashcards(signal),
    getProgress(signal),
  ]);
  return { notes, topics, flashcards, progress };
}

function loadEmptyOverview() {
  return Promise.resolve(null);
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: '2-digit' }).format(date);
}

export default function DashboardPage() {
  const { user } = useAuth();
  const overview = useResource(user ? loadOverview : loadEmptyOverview);

  return (
    <>
      <div className="page-heading-row">
        <PageHeader title="Overview" description="Keep your notes, topics, and revision in one place." />
        <Link className="button button-primary" to={user ? '/app/notes/new' : '/register'}><Icon name="plus" size={17} /> {user ? 'Create a note' : 'Create your workspace'}</Link>
      </div>
      <div className="preview-banner">
        {user ? <span className="sample-badge"><span className="status-dot" /> Your workspace</span> : null}
        <p>{user ? 'Your saved study materials and review activity.' : 'Sign in to see your saved study materials and progress.'}</p>
      </div>
      {user && overview.loading && <p className="page-status" role="status">Loading your workspace…</p>}
      {user && overview.error && <RequestError error={overview.error} onRetry={overview.reload} />}
      {!user && (
        <section className="panel notes-empty dashboard-signin">
          <h2>Your study workspace</h2>
          <p>Sign in to see your notes, topics, flashcards, and study progress.</p>
          <Link className="button button-primary" to="/login">Sign in</Link>
        </section>
      )}
      {user && overview.data && <DashboardContent data={overview.data} />}
      <footer className="workspace-footer"><span>Study Hub</span><span>One place for your next study session.</span></footer>
    </>
  );
}

function DashboardContent({ data }) {
  const [topic, setTopic] = useState('all');
  const notes = topic === 'all'
    ? data.notes
    : data.notes.filter((note) => String(note.topic_id) === topic);

  return (
    <div className="dashboard-grid">
      <div className="dashboard-primary">
        <section className="summary-grid" aria-label="Workspace summary">
          <SummaryCard title="Notes" count={data.notes.length} icon="notes" detail="Saved study notes" to="/app/notes" />
          <SummaryCard title="Topics" count={data.topics.length} icon="topics" detail="Your study subjects" to="/app/topics" />
          <SummaryCard title="Flashcards" count={data.flashcards.length} icon="flashcards" detail="Ready for a quick review" to="/app/flashcards" />
          <div className="study-card">
            <span className="study-card-icon"><Icon name="study" size={19} /></span>
            <h2>{data.progress.current_streak} day study streak</h2>
            <p>{data.progress.cards_studied_today} flashcards studied today</p>
            <Link to="/app/study">Start studying <Icon name="arrow" size={16} /></Link>
          </div>
        </section>

        <section className="panel notes-panel" aria-labelledby="notes-title">
          <div className="panel-heading">
            <div><h2 id="notes-title">Recent notes</h2><p>Pick up where you left off.</p></div>
            <label className="topic-filter">
              <span className="sr-only">Filter notes by topic</span>
              <select value={topic} onChange={(event) => setTopic(event.target.value)}>
                <option value="all">All topics</option>
                {data.topics.map((item) => <option key={item.id} value={String(item.id)}>{item.title}</option>)}
              </select>
            </label>
          </div>
          <div className="table-scroll">
            <table>
              <thead><tr><th scope="col">Name</th><th scope="col">Topic</th><th scope="col">Updated</th></tr></thead>
              <tbody>
                {notes.slice(0, 6).map((note) => (
                  <tr key={note.id}>
                    <td><Link className="note-link" to={`/app/notes/${note.id}`}><span className="note-icon"><Icon name="notes" size={17} /></span>{note.title}</Link></td>
                    <td><span className="topic-tag">{note.topic?.title || 'Unassigned'}</span></td>
                    <td className="note-date">{formatDate(note.updated_at)}</td>
                  </tr>
                ))}
                {notes.length === 0 && <tr><td className="dashboard-empty-row" colSpan="3">{data.notes.length ? 'No notes in this topic yet.' : 'Your notes will appear here when you create one.'}</td></tr>}
              </tbody>
            </table>
          </div>
          <div className="table-footer"><span>{data.notes.length} {data.notes.length === 1 ? 'note' : 'notes'}</span><Link className="text-link" to="/app/notes">View all notes <Icon name="arrow" size={14} /></Link></div>
        </section>
        <div className="workspace-tip"><span className="tip-icon"><Icon name="assistant" size={20} /></span><div><h2>Work through the difficult parts.</h2><p>Ask questions about your notes with the AI Assistant.</p></div><Link className="icon-button" to="/app/assistant" aria-label="Explore AI Assistant"><Icon name="arrow" size={18} /></Link></div>
      </div>

      <aside className="panel planning-panel progress-panel" aria-labelledby="progress-title">
        <div className="section-heading"><h2 id="progress-title">Study progress</h2><Icon name="study" size={17} /></div>
        <ProgressMetric label="Reviews completed" value={data.progress.total_reviewed} />
        <ProgressMetric label="Average accuracy" value={`${data.progress.average_accuracy}%`} />
        <ProgressMetric label="Cards mastered" value={data.progress.cards_mastered} />
        <ProgressMetric label="Need review" value={data.progress.cards_needing_reviewing} />
        <p className="panel-footnote">Progress updates as you review flashcards.</p>
      </aside>
    </div>
  );
}

function SummaryCard({ title, count, icon, detail, to }) {
  return <div className="panel summary-card"><div className="section-heading"><span className="summary-label"><Icon name={icon} size={16} />{title}</span><Link className="text-link" to={to} aria-label={`Open ${title.toLowerCase()}`}>Open <Icon name="arrow" size={13} /></Link></div><strong className="summary-number">{count.toLocaleString()}</strong><p>{detail}</p></div>;
}

function ProgressMetric({ label, value }) {
  return <div className="progress-metric"><span>{label}</span><strong>{typeof value === 'number' ? value.toLocaleString() : value}</strong></div>;
}
