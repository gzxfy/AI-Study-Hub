import { Link } from 'react-router';
import PageHeader from '../components/PageHeader';
import Icon from '../components/Icon';

export default function FeaturePage({ title, description }) {
  return (
    <>
      <PageHeader title={title} description={description} />
      <section className="panel feature-state">
        <span className="empty-icon"><Icon name="topics" size={26} /></span>
        <h2>{title} is coming next</h2>
        <p>This section is not available yet. You can explore the sample workspace in the meantime.</p>
        <Link className="button button-secondary" to="/">Back to overview <Icon name="arrow" size={16} /></Link>
      </section>
    </>
  );
}
