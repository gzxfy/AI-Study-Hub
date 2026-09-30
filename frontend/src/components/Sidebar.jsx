import { NavLink } from 'react-router';
import Icon from './Icon';

const links = [
  { to: '/app', label: 'Dashboard', icon: 'dashboard' },
  { to: '/app/notes', label: 'Notes', icon: 'notes' },
  { to: '/app/topics', label: 'Topics', icon: 'topics' },
  { to: '/app/flashcards', label: 'Flashcards', icon: 'flashcards' },
  { to: '/app/study', label: 'Study', icon: 'study' },
  { to: '/app/assistant', label: 'AI Assistant', icon: 'assistant' },
];

export default function Sidebar({ navigationOpen, onNavigate }) {
  return (
    <aside className="sidebar">
      <NavLink to="/app" className="brand" onClick={onNavigate} aria-label="AI Study Hub dashboard">
        <span className="brand-mark"><Icon name="book" size={22} /></span>
        <span>Study Hub<span className="brand-caption">A little more understanding.</span></span>
      </NavLink>
      <div id="workspace-navigation" className={`sidebar-body ${navigationOpen ? 'is-open' : ''}`}>
        <nav aria-label="Main navigation">
          <p className="nav-caption">Workspace</p>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === '/app'} onClick={onNavigate} className={({ isActive }) => `nav-link ${isActive ? 'is-active' : ''}`}>
              <Icon name={link.icon} /><span>{link.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="preview-label">Layout preview</span>
          <p>Account and logout will be available after authentication is connected.</p>
        </div>
      </div>
    </aside>
  );
}
