import { useCallback, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router';
import { deleteTopic, getTopic } from '../api/topics';
import DeleteDialog from '../components/DeleteDialog';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';
import RequestError from '../components/RequestError';
import useResource from '../hooks/useResource';
import { formatNoteDate } from '../notes/formatDate';
import { topicColor } from '../topics/color';

export default function TopicPage() {
  const { topicId } = useParams();
  const navigate = useNavigate();
  const [deleting, setDeleting] = useState(false);
  const load = useCallback((signal) => getTopic(topicId, signal), [topicId]);
  const { data, loading, error, reload } = useResource(load);

  if (loading) return <p className="page-status" role="status">Loading your topic…</p>;
  if (error) return <RequestError error={error} onRetry={reload} />;
  const { topic, notes } = data;

  return (
    <div className="notes-workspace">
      <Link className="text-link back-link" to="/app/topics">All topics</Link>
      <div className="page-heading-row">
        <div className="topic-title">
          <span className="topic-symbol" style={{ color: topicColor(topic.color) }}><Icon name="topics" size={26} /></span>
          <PageHeader title={topic.title} description={topic.description} />
        </div>
        <div className="record-actions">
          <Link className="button button-secondary" to={`/app/topics/${topic.id}/edit`}>Edit topic</Link>
          <button className="button button-danger-outline" onClick={() => setDeleting(true)}>Delete topic</button>
        </div>
      </div>
      <section className="panel notes-library" aria-label="Topic notes">
        <div className="notes-toolbar"><h2>Notes <span className="note-count">{notes.length}</span></h2><Link className="button button-primary" to={`/app/notes/new?topic=${topic.id}`}>Create note</Link></div>
        {notes.length === 0 ? (
          <div className="notes-empty"><h2>No notes in this topic yet</h2><p>Create a note here, or assign an existing note using Edit note.</p></div>
        ) : (
          <ul className="topic-notes">
            {notes.map((note) => (
              <li key={note.id}>
                <Link to={`/app/notes/${note.id}`}><Icon name="notes" size={18} /><span>{note.title}</span><small>{formatNoteDate(note.updated_at)}</small><Icon name="chevron" size={16} /></Link>
              </li>
            ))}
          </ul>
        )}
      </section>
      {deleting && (
        <DeleteDialog
          title="Delete this topic?"
          description={`“${topic.title}” can only be deleted when it has no linked notes or other study data. Move its notes to another topic first. This cannot be undone.`}
          onDelete={() => deleteTopic(topic.id)}
          onDeleted={() => navigate('/app/topics', { replace: true, state: { deleted: true } })}
          onClose={() => setDeleting(false)}
        />
      )}
    </div>
  );
}
