import { Link } from 'react-router';
import { useAuth } from '../auth/AuthContext';
import Icon from './Icon';

export default function AccountControls() {
  const { user, status } = useAuth();

  if (status === 'loading') return <span className="account-status">Checking session…</span>;

  if (user) {
    return (
      <div className="topbar-actions">
        <span className="account-name">{user.username}</span>
        <Link className="login-link" to="/logout">Log out</Link>
      </div>
    );
  }

  return (
    <div className="topbar-actions">
      <Link className="login-link" to="/login">Log in</Link>
      <Link className="button button-primary button-small" to="/register">Get started <Icon name="arrow" size={15} /></Link>
    </div>
  );
}
