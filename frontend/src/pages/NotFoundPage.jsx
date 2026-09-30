import { Link } from 'react-router';
import PageHeader from '../components/PageHeader';

export default function NotFoundPage() {
  return (
    <div className="not-found">
      <PageHeader title="Page not found" description="This address does not match a page in your workspace." />
      <Link className="text-link" to="/app">Return to dashboard</Link>
    </div>
  );
}
