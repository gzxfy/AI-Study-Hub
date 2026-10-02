import { useEffect } from 'react';

export default function PageHeader({ title, description }) {
  useEffect(() => {
    document.title = `${title} · AI Study Hub`;
  }, [title]);

  return (
    <header className="page-header">
      <h1>{title}</h1>
      <p>{description}</p>
    </header>
  );
}
