import { useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router';
import AccountControls from '../components/AccountControls';
import Sidebar from '../components/Sidebar';
import Icon from '../components/Icon';

export default function AppLayout() {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const { pathname } = useLocation();
  const mainRef = useRef(null);
  const menuRef = useRef(null);

  useEffect(() => {
    mainRef.current?.focus();
    window.scrollTo(0, 0);
  }, [pathname]);

  function handleEscape(event) {
    if (event.key === 'Escape' && navigationOpen) {
      setNavigationOpen(false);
      menuRef.current?.focus();
    }
  }

  return (
    <div className="app-shell" onKeyDown={handleEscape}>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <Sidebar navigationOpen={navigationOpen} onNavigate={() => setNavigationOpen(false)} />
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb"><button ref={menuRef} className="icon-button menu-button" aria-label={navigationOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={navigationOpen} aria-controls="workspace-navigation" onClick={() => setNavigationOpen(!navigationOpen)}><Icon name="menu" /></button><Icon name="book" size={16} /><span>Workspace</span><span className="breadcrumb-divider">/</span><strong>Study Hub</strong></div>
          <AccountControls />
        </header>
        <main id="main-content" className="main-content" tabIndex={-1} ref={mainRef}><Outlet /></main>
      </div>
    </div>
  );
}
