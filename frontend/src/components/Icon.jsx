// Small, local SVGs keep navigation independent of an icon package.
const paths = {
  dashboard: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  notes: 'M6 3h9l4 4v14H6z M14 3v5h5 M9 12h7 M9 16h7',
  topics: 'M3 6h7l2 3h9v11H3z',
  flashcards: 'M7 7h14v14H7z M3 17V3h14',
  study: 'M9 5l11 7-11 7z',
  assistant: 'M4 4h16v12H9l-5 4z M8 9h8 M8 12h5',
  arrow: 'M5 12h14 M14 7l5 5-5 5',
  book: 'M12 5v15 M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1z',
};

export default function Icon({ name, size = 20 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name] || paths.notes} />
    </svg>
  );
}
