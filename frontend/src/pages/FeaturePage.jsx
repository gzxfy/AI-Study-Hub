import { Link } from 'react-router';
import PageHeader from '../components/PageHeader';
import Icon from '../components/Icon';

export default function FeaturePage({ title, description, stage, detail }) {
  return (
    <>
      <PageHeader title={title} description={description} />
      <section className="feature-state" aria-label={`${title} implementation status`}>
        <span className="preview-label">Planned for stage {stage}</span>
        <h2>This space is ready for the next step.</h2>
        <p>{detail}</p>
        <p className="feature-note">This page is not connected to Flask yet. It does not read or change your saved data.</p>
        <Link className="text-link" to="/app">Back to dashboard <Icon name="arrow" size={16} /></Link>
      </section>
    </>
  );
}
