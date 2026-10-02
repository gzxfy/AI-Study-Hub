import { useRef, useState } from 'react';
import { Link } from 'react-router';
import Icon from '../components/Icon';
import PageHeader from '../components/PageHeader';
import StudyCalendar from '../components/StudyCalendar';
import StudyChecklist from '../components/StudyChecklist';
import { sampleNotes, sampleTopics } from '../sampleWorkspace';

export default function DashboardPage() {
  const [topic, setTopic] = useState('All topics');
  const [selectedNote, setSelectedNote] = useState(null);
  const noteDialog = useRef(null);
  const notes = topic === 'All topics' ? sampleNotes : sampleNotes.filter((note) => note.topic === topic);

  function openNote(note) {
    setSelectedNote(note);
    noteDialog.current.showModal();
  }

  return (
    <>
      <div className="page-heading-row">
        <PageHeader title="Overview" description="Keep your notes, topics, and revision in one place." />
        <Link className="button button-primary" to="/register"><Icon name="plus" size={17} /> Create your workspace</Link>
      </div>
      <div className="preview-banner"><span className="sample-badge"><span className="status-dot" /> Sample workspace</span><p>A look at how your study materials come together. The content below is an example.</p></div>
      <div className="dashboard-grid">
        <div className="dashboard-primary">
          <section className="summary-grid" aria-label="Sample workspace summary">
            <SummaryCard title="Notes" count={sampleNotes.length} icon="notes" detail="Your reading, all together" to="/app/notes" />
            <SummaryCard title="Topics" count={sampleTopics.length} icon="topics" detail="Organized by subject" to="/app/topics" />
            <SummaryCard title="Flashcards" count={24} icon="flashcards" detail="Ready for a quick review" to="/app/flashcards" />
            <div className="study-card"><span className="study-card-icon"><Icon name="study" size={19} /></span><h2>A little practice goes a long way.</h2><p>Make time to review what you know.</p><Link to="/app/study">Start studying <Icon name="arrow" size={16} /></Link></div>
          </section>
          <section className="panel notes-panel" aria-labelledby="notes-title">
            <div className="panel-heading"><div><h2 id="notes-title">Recent notes</h2><p>Pick up where you left off.</p></div><label className="topic-filter"><span className="sr-only">Filter notes by topic</span><select value={topic} onChange={(event) => setTopic(event.target.value)}><option>All topics</option>{sampleTopics.map((name) => <option key={name}>{name}</option>)}</select></label></div>
            <div className="table-scroll"><table><thead><tr><th scope="col">Name</th><th scope="col">Topic</th><th scope="col">Updated</th><th scope="col"><span className="sr-only">Open note</span></th></tr></thead><tbody>{notes.map((note) => <tr key={note.id}><td><button className="note-link" onClick={() => openNote(note)}><span className="note-icon"><Icon name="notes" size={17} /></span>{note.title}</button></td><td><span className={`topic-tag topic-${note.color}`}>{note.topic}</span></td><td className="note-date">{note.updated}</td><td><button className="icon-button" aria-label={`Preview ${note.title}`} onClick={() => openNote(note)}><Icon name="chevron" size={15} /></button></td></tr>)}</tbody></table></div>
            <div className="table-footer"><span>{notes.length} sample notes</span><Link className="text-link" to="/app/notes">View all notes <Icon name="arrow" size={14} /></Link></div>
          </section>
          <div className="workspace-tip"><span className="tip-icon"><Icon name="assistant" size={20} /></span><div><h2>Work through the difficult parts.</h2><p>Ask questions about your notes with the AI Assistant.</p></div><Link className="icon-button" to="/app/assistant" aria-label="Explore AI Assistant"><Icon name="arrow" size={18} /></Link></div>
        </div>
        <aside className="panel planning-panel" aria-label="Study planning"><StudyCalendar /><StudyChecklist /></aside>
      </div>
      <footer className="workspace-footer"><span>Study Hub</span><span>One place for your next study session.</span></footer>
      <dialog ref={noteDialog} className="note-dialog" aria-labelledby="note-dialog-title">
        <div className="section-heading"><span className="sample-badge">Sample note</span><button className="text-button" onClick={() => noteDialog.current.close()}>Close</button></div>
        <h2 id="note-dialog-title">{selectedNote?.title}</h2><span className="dialog-topic">{selectedNote?.topic}</span><p>{selectedNote?.body}</p><p className="panel-footnote">This is example content, not a saved note.</p>
      </dialog>
    </>
  );
}

function SummaryCard({ title, count, icon, detail, to }) {
  return <div className="panel summary-card"><div className="section-heading"><span className="summary-label"><Icon name={icon} size={16} />{title}</span><Link className="text-link" to={to} aria-label={`Open ${title.toLowerCase()}`}>Open <Icon name="arrow" size={13} /></Link></div><strong className="summary-number">{String(count).padStart(2, '0')}</strong><p>{detail}</p></div>;
}
