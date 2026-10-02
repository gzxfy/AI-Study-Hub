import { Link, NavLink, useLocation } from 'react-router';
import Icon from './Icon';

const links = [
  { to: '/', label: 'Overview', icon: 'dashboard' },
  { to: '/app/notes', label: 'Notes', icon: 'notes' },
  { to: '/app/topics', label: 'Topics', icon: 'topics' },
  { to: '/app/flashcards', label: 'Flashcards', icon: 'flashcards' },
  { to: '/app/study', label: 'Study sessions', icon: 'study' },
  { to: '/app/assistant', label: 'AI Assistant', icon: 'assistant' },
];

export function Brand() {
  return <Link to="/" className="brand"><span className="brand-mark"><Icon name="book" size={20} /></span><span>studyhub<span className="brand-period">.</span></span></Link>;
}

export default function Sidebar({ navigationOpen, onNavigate }) {
  const { pathname } = useLocation();
  return (
    <aside className="sidebar">
      <Brand />
      <div id="workspace-navigation" className={`sidebar-body ${navigationOpen ? 'is-open' : ''}`}>
        <div className="workspace-switch"><span className="workspace-avatar">S</span><span>Study workspace<small>Personal workspace</small></span></div>
        <nav aria-label="Main navigation">
          <p className="nav-caption">Workspace</p>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === '/'} onClick={onNavigate} className={({ isActive }) => `nav-link ${isActive || (link.to === '/' && pathname === '/app') ? 'is-active' : ''}`}>
              <Icon name={link.icon} size={18} /><span>{link.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <Icon name="book" size={22} />
          <h2>Make it your workspace.</h2>
          <p>Create an account to keep your study materials together.</p>
          <Link className="button button-secondary" to="/register" onClick={onNavigate}>Create account <Icon name="arrow" size={16} /></Link>
        </div>
        <Link className="sidebar-login" to="/login" onClick={onNavigate}><span className="guest-avatar"><Icon name="user" size={17} /></span><span>Guest workspace<small>Log in to your account</small></span><Icon name="arrow" size={16} /></Link>
      </div>
    </aside>
  );
}
