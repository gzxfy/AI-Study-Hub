import { Link } from 'react-router';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';

const destinations = [
  { to: 'notes', title: 'Notes', detail: 'Keep your learning material together.', icon: 'notes' },
  { to: 'topics', title: 'Topics', detail: 'Organize by subject or course.', icon: 'topics' },
  { to: 'study', title: 'Study', detail: 'Return to a focused review session.', icon: 'study' },
  { to: 'assistant', title: 'AI Assistant', detail: 'Explore a question in your notes.', icon: 'assistant' },
];

export default function DashboardPage() {
  return (
    <>
      <PageHeader title="A place to focus." description="Bring your notes, practice, and questions into one workspace." />
      <div className="connection-notice"><span className="status-dot" /><p><strong>Your workspace is taking shape.</strong> This is a layout preview. Sign-in and your saved materials are not connected yet.</p></div>
      <section className="dashboard-section" aria-labelledby="workspace-heading">
        <div className="section-heading"><h2 id="workspace-heading">Explore your workspace</h2><span>Find your next step</span></div>
        <div className="destination-list">
          {destinations.map((item) => (
            <Link className="destination-row" to={`/app/${item.to}`} key={item.to}>
              <span className="destination-icon"><Icon name={item.icon} /></span>
              <span className="destination-copy"><strong>{item.title}</strong><span>{item.detail}</span></span>
              <Icon name="arrow" size={18} />
            </Link>
          ))}
        </div>
      </section>
      <section className="dashboard-section" aria-labelledby="recent-heading">
        <div className="section-heading"><h2 id="recent-heading">Recent notes</h2><span className="muted-label">Not connected</span></div>
        <div className="unconnected-state">
          <Icon name="notes" size={28} />
          <h3>Your study materials will live here</h3>
          <p>Once the notes API is connected, this area will show your actual recent notes. No sample notes or statistics are displayed.</p>
        </div>
      </section>
    </>
  );
}
