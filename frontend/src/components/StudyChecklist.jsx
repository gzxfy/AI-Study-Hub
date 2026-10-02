import { useState } from 'react';
import Icon from './Icon';

const initialTasks = [
  { id: 1, title: 'Review database normalization', done: true },
  { id: 2, title: 'Practice time complexity', done: false },
  { id: 3, title: 'Revisit HTTP status codes', done: false },
];

export default function StudyChecklist() {
  const [tasks, setTasks] = useState(initialTasks);
  const [adding, setAdding] = useState(false);
  const [title, setTitle] = useState('');
  const completed = tasks.filter((task) => task.done).length;

  function addTask(event) {
    event.preventDefault();
    if (!title.trim()) return;
    setTasks([...tasks, { id: crypto.randomUUID(), title: title.trim(), done: false }]);
    setTitle('');
    setAdding(false);
  }

  return (
    <section className="checklist" aria-labelledby="checklist-title">
      <div className="section-heading"><h2 id="checklist-title">Study checklist</h2><button className="text-button" aria-expanded={adding} onClick={() => setAdding(!adding)}>{adding ? 'Cancel' : <><Icon name="plus" size={14} /> Add</>}</button></div>
      <p className="checklist-progress" aria-live="polite">{completed} of {tasks.length} completed</p>
      <progress value={completed} max={tasks.length} aria-label="Study checklist completion" />
      <div className="task-list">
        {tasks.map((task) => <label key={task.id} className={`task ${task.done ? 'is-done' : ''}`}><input type="checkbox" checked={task.done} onChange={() => setTasks(tasks.map((item) => item.id === task.id ? { ...item, done: !item.done } : item))} /><span>{task.title}</span></label>)}
      </div>
      {adding && <form className="task-form" onSubmit={addTask}><label className="sr-only" htmlFor="task-title">New study task</label><input id="task-title" autoFocus maxLength={100} required value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Add a study task" /><button className="icon-button" aria-label="Save task" type="submit"><Icon name="check" size={18} /></button></form>}
      <p className="panel-footnote">Try it out. Changes last until you leave this page.</p>
    </section>
  );
}
