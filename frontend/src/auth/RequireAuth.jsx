import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from './AuthContext';

export default function RequireAuth() {
  const { status, error, retrySession } = useAuth();
  const location = useLocation();

  if (status === 'loading') return <p className="page-status" role="status">Opening your workspace…</p>;

  if (status === 'error') {
    return (
      <section className="panel feature-state">
        <h1>Unable to open your workspace</h1>
        <p role="alert">{error}</p>
        <button className="button button-secondary" onClick={retrySession}>Try again</button>
      </section>
    );
  }

  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ returnTo: location.pathname }} />;
  }

  return <Outlet />;
}
