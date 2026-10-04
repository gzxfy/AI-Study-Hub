import { Link, useLocation } from 'react-router';

export default function RequestError({ error, onRetry }) {
  const { pathname } = useLocation();

  return (
    <div className="request-error" role="alert">
      <p>{error.status === 401 ? 'Your session has expired. Log in to continue.' : error.message}</p>
      {error.status === 401 ? (
        <Link className="text-link" to="/login" state={{ returnTo: pathname }}>Log in</Link>
      ) : onRetry && (
        <button className="text-button" onClick={onRetry}>Try again</button>
      )}
    </div>
  );
}
