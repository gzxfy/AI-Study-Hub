import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { useAuth } from '../auth/AuthContext';
import PageHeader from '../components/PageHeader';

export default function LogoutPage() {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const operation = useRef(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    // Reuse the operation when Strict Mode replays the effect.
    operation.current ??= signOut();
    operation.current.then(() => {
      if (active) navigate('/login', { replace: true });
    }).catch((failure) => {
      if (active) setError(failure.message);
    });
    return () => { active = false; };
  }, [signOut, navigate, attempt]);

  function retry() {
    operation.current = null;
    setError('');
    setAttempt((value) => value + 1);
  }

  return (
    <section className="panel feature-state">
      <PageHeader title={error ? 'Unable to log out' : 'Logging out…'} />
      {error ? (
        <>
          <p role="alert">{error}</p>
          <div className="dialog-actions">
            <Link className="button button-secondary" to="/app/notes">Back to notes</Link>
            <button className="button button-primary" onClick={retry}>Try again</button>
          </div>
        </>
      ) : <p role="status">Closing your session.</p>}
    </section>
  );
}
