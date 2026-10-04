import { Link } from 'react-router';
import { Brand } from '../components/Sidebar';
import Icon from '../components/Icon';

export default function AuthLayout({ children }) {
  return (
    <div className="auth-page">
      <a className="skip-link" href="#auth-form">Skip to form</a>
      <section className="auth-main">
        <header className="auth-header">
          <Brand />
          <Link className="text-link" to="/">Back to workspace <Icon name="arrow" size={15} /></Link>
        </header>
        <main id="auth-form" className="auth-content">{children}</main>
        <footer className="auth-footer">AI Study Hub<span>Built for focused learning.</span></footer>
      </section>
      <aside className="auth-aside" aria-label="About Study Hub">
        <div className="auth-editorial">
          <p className="eyebrow">Your personal study workspace</p>
          <h2>Everything you learn.<br /><span>In one place.</span></h2>
          <p>Bring your notes together, organize by topic, and make revision part of your routine.</p>
          <div className="auth-product-card">
            <div className="section-heading">
              <span className="mini-brand"><Icon name="book" size={18} /> My workspace</span>
              <span className="sample-badge">Example</span>
            </div>
            <div className="mini-note">
              <span className="note-icon"><Icon name="notes" size={19} /></span>
              <div><strong>Database normalization</strong><span>Databases · Study notes</span></div>
              <Icon name="check" size={17} />
            </div>
            <div className="mini-note">
              <span className="note-icon"><Icon name="flashcards" size={19} /></span>
              <div><strong>Turn understanding into recall</strong><span>Review with flashcards</span></div>
              <Icon name="arrow" size={17} />
            </div>
            <div className="mini-session"><Icon name="study" size={17} /><span>A focused session starts here.</span></div>
          </div>
          <div className="auth-features">
            <span><Icon name="check" size={15} /> Organized notes</span>
            <span><Icon name="check" size={15} /> Focused practice</span>
          </div>
        </div>
        <span className="auth-aside-caption">Less searching. More studying.</span>
      </aside>
    </div>
  );
}
