import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { Brand } from '../components/Sidebar';
import Icon from '../components/Icon';

export default function AuthPage({ mode }) {
  const registering = mode === 'register';
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('error');
  const [pending, setPending] = useState(false);
  const title = registering ? 'Create your account' : 'Welcome back';

  useEffect(() => { document.title = `${title} · AI Study Hub`; }, [title]);

  async function handleSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const password = formData.get('password');

    if (registering && password !== formData.get('confirm_password')) {
      setMessageType('error');
      setMessage('Passwords do not match.');
      return;
    }

    setPending(true);
    setMessage('');

    try {
      const csrfResponse = await fetch('/api/auth/csrf', {
        headers: { Accept: 'application/json' },
        credentials: 'same-origin',
      });
      const csrfData = await readJsonResponse(csrfResponse);
      const payload = registering
        ? {
            username: formData.get('username'),
            email: formData.get('email'),
            password,
            confirm_password: formData.get('confirm_password'),
          }
        : {
            email: formData.get('email'),
            password,
          };
      const response = await fetch(`/api/auth/${registering ? 'register' : 'login'}`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfData.csrf_token,
        },
        body: JSON.stringify(payload),
      });
      await readJsonResponse(response);

      setMessageType('success');
      setMessage(registering
        ? 'Your account was created. You can now log in.'
        : 'You are signed in. Your session is active.');
      form.reset();
    } catch (error) {
      setMessageType('error');
      setMessage(error.message || 'Unable to complete the request. Please try again.');
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="auth-page">
      <a className="skip-link" href="#auth-form">Skip to form</a>
      <section className="auth-main">
        <header className="auth-header"><Brand /><Link className="text-link" to="/">Back to workspace <Icon name="arrow" size={15} /></Link></header>
        <main id="auth-form" className="auth-content">
          <span className="auth-icon"><Icon name={registering ? 'book' : 'user'} size={23} /></span>
          <h1>{title}</h1>
          <p className="auth-description">{registering ? 'A dedicated space for your notes and revision.' : 'Log in to return to your study workspace.'}</p>
          <form className="auth-form" onSubmit={handleSubmit}>
            {registering && <FormField id="username" label="Username" autoComplete="username" placeholder="Enter a username" minLength={3} maxLength={50} required />}
            <FormField id="email" label="Email address" type="email" autoComplete="email" placeholder="you@example.com" maxLength={120} required />
            <div className="form-field">
              <label htmlFor="password">Password</label>
              <div className="password-input"><input id="password" name="password" type={showPassword ? 'text' : 'password'} autoComplete={registering ? 'new-password' : 'current-password'} minLength={registering ? 8 : undefined} required placeholder={registering ? 'Create a password' : 'Enter your password'} aria-describedby={registering ? 'password-hint' : undefined} /><button className="icon-button" type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)}><Icon name="eye" size={18} /></button></div>
              {registering && <p id="password-hint" className="field-hint">At least 8 characters, with uppercase and lowercase letters, a number, and a special character.</p>}
            </div>
            {registering && <FormField id="confirm_password" label="Confirm password" type="password" autoComplete="new-password" minLength={8} required />}
            <button className="button button-primary auth-submit" type="submit" disabled={pending}>{pending ? 'Please wait...' : registering ? 'Create account' : 'Log in'}<Icon name="arrow" size={17} /></button>
            {message && <div className="form-message" role={messageType === 'error' ? 'alert' : 'status'}>
              {message}
              {messageType === 'success' && <Link className="text-link" to={registering ? '/login' : '/app'}>{registering ? 'Go to login' : 'Continue to workspace'}<Icon name="arrow" size={14} /></Link>}
            </div>}
          </form>
          <p className="auth-switch">{registering ? 'Already have an account?' : 'New to Study Hub?'} <Link to={registering ? '/login' : '/register'}>{registering ? 'Log in' : 'Create an account'}</Link></p>
        </main>
        <footer className="auth-footer">AI Study Hub<span>Built for focused learning.</span></footer>
      </section>
      <aside className="auth-aside" aria-label="About Study Hub">
        <div className="auth-editorial">
          <p className="eyebrow">Your personal study workspace</p>
          <h2>Everything you learn.<br /><span>In one place.</span></h2>
          <p>Bring your notes together, organize by topic, and make revision part of your routine.</p>
          <div className="auth-product-card">
            <div className="section-heading"><span className="mini-brand"><Icon name="book" size={18} /> My workspace</span><span className="sample-badge">Example</span></div>
            <div className="mini-note"><span className="note-icon"><Icon name="notes" size={19} /></span><div><strong>Database normalization</strong><span>Databases · Study notes</span></div><Icon name="check" size={17} /></div>
            <div className="mini-note"><span className="note-icon"><Icon name="flashcards" size={19} /></span><div><strong>Turn understanding into recall</strong><span>Review with flashcards</span></div><Icon name="arrow" size={17} /></div>
            <div className="mini-session"><Icon name="study" size={17} /><span>A focused session starts here.</span></div>
          </div>
          <div className="auth-features"><span><Icon name="check" size={15} /> Organized notes</span><span><Icon name="check" size={15} /> Focused practice</span></div>
        </div>
        <span className="auth-aside-caption">Less searching. More studying.</span>
      </aside>
    </div>
  );
}

function FormField({ id, label, type = 'text', ...props }) {
  return <div className="form-field"><label htmlFor={id}>{label}</label><input id={id} name={id} type={type} {...props} /></div>;
}

async function readJsonResponse(response) {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(data?.error?.message || `Request failed (${response.status}).`);
  }
  return data;
}
