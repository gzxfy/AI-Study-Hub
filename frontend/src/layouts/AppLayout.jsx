import { useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router';
import Sidebar from '../components/Sidebar';

export default function AppLayout() {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const location = useLocation();
  const mainRef = useRef(null);
  const menuRef = useRef(null);

  // Client-side navigation doesn't reload the document. Move focus to its new content.
  useEffect(() => {
    mainRef.current?.focus();
  }, [location.pathname]);

  function closeNavigation() {
    setNavigationOpen(false);
  }

  function handleEscape(event) {
    if (event.key === 'Escape' && navigationOpen) {
      closeNavigation();
      menuRef.current?.focus();
    }
  }

  return (
    <div className="app-shell" onKeyDown={handleEscape}>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <Sidebar navigationOpen={navigationOpen} onNavigate={closeNavigation} />
      <div className="workspace">
        <header className="topbar">
          <button ref={menuRef} className="menu-button" aria-expanded={navigationOpen} aria-controls="workspace-navigation" onClick={() => setNavigationOpen(!navigationOpen)}>
            {navigationOpen ? 'Close menu' : 'Menu'}
          </button>
          <span className="workspace-label">Your learning workspace</span>
          <span className="stage-label">Stage 2 · Layout preview</span>
        </header>
        <main id="main-content" className="main-content" tabIndex={-1} ref={mainRef}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
