import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';
import { register } from '../api/auth';
import { useAuth } from '../auth/AuthContext';
import AuthLayout from '../layouts/AuthLayout';
import FormField from '../components/FormField';
import PasswordField from '../components/PasswordField';
import Icon from '../components/Icon';

export default function AuthPage({ mode }) {
  const registering = mode === 'register';
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const { state } = useLocation();
  const [message, setMessage] = useState('');
  const [registered, setRegistered] = useState(false);
  const [confirmationError, setConfirmationError] = useState('');
  const [pending, setPending] = useState(false);
  const title = registering ? 'Create your account' : 'Welcome back';

  useEffect(() => { document.title = `${title} · AI Study Hub`; }, [title]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (pending) return;

    const form = event.currentTarget;
    const fields = new FormData(form);
    const password = fields.get('password');
    setMessage('');
    setConfirmationError('');

    if (registering && password !== fields.get('confirm_password')) {
      setConfirmationError('Passwords do not match.');
      form.elements.confirm_password.focus();
      return;
    }

    setPending(true);
    try {
      const credentials = { email: fields.get('email').trim(), password };
      if (registering) {
        await register({
          ...credentials,
          username: fields.get('username').trim(),
          confirm_password: fields.get('confirm_password'),
        });
        setRegistered(true);
        form.reset();
      } else {
        await signIn(credentials);
        const destination = /^\/app(?:\/|$)/.test(state?.returnTo) ? state.returnTo : '/app/notes';
        navigate(destination, { replace: true });
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <AuthLayout>
      <span className="auth-icon"><Icon name={registering ? 'book' : 'user'} size={23} /></span>
      <h1>{title}</h1>
      <p className="auth-description">
        {registering ? 'A dedicated space for your notes and revision.' : 'Log in to return to your study workspace.'}
      </p>

      {registered ? (
        <div className="form-message" role="status">
          Your account was created. You can now log in.
          <Link className="text-link" to="/login">Go to login <Icon name="arrow" size={14} /></Link>
        </div>
      ) : (
        <form className="auth-form" onSubmit={handleSubmit} aria-busy={pending}>
          <fieldset className="form-fields" disabled={pending}>
            {registering && (
              <FormField id="username" label="Username" autoComplete="username" placeholder="Enter a username" minLength={3} maxLength={50} required />
            )}
            <FormField id="email" label="Email address" type="email" autoComplete="email" placeholder="you@example.com" maxLength={120} required />
            <PasswordField
              autoComplete={registering ? 'new-password' : 'current-password'}
              minLength={registering ? 8 : undefined}
              placeholder={registering ? 'Create a password' : 'Enter your password'}
              hint={registering ? 'At least 8 characters, with uppercase and lowercase letters, a number, and a special character.' : undefined}
              required
            />
            {registering && (
              <PasswordField
                id="confirm_password"
                label="Confirm password"
                autoComplete="new-password"
                minLength={8}
                placeholder="Enter your password again"
                error={confirmationError}
                onChange={() => setConfirmationError('')}
                required
              />
            )}
            <button className="button button-primary auth-submit" type="submit">
              {pending ? 'Please wait…' : registering ? 'Create account' : 'Log in'}
              <Icon name="arrow" size={17} />
            </button>
          </fieldset>
          {message && <p className="form-message form-message-error" role="alert">{message}</p>}
        </form>
      )}

      <p className="auth-switch">
        {registering ? 'Already have an account?' : 'New to Study Hub?'}{' '}
        <Link to={registering ? '/login' : '/register'}>{registering ? 'Log in' : 'Create an account'}</Link>
      </p>
    </AuthLayout>
  );
}
