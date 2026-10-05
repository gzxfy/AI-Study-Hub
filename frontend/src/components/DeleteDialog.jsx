import { useEffect, useId, useRef, useState } from 'react';

export default function DeleteDialog({ title, description, onDelete, onDeleted, onClose }) {
  const dialog = useRef(null);
  const titleId = useId();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { dialog.current.showModal(); }, []);

  async function handleDelete() {
    if (pending) return;
    setPending(true);
    setError('');
    try {
      await onDelete();
      onDeleted();
    } catch (failure) {
      setError(failure.message);
      setPending(false);
    }
  }

  return (
    <dialog ref={dialog} className="note-dialog" aria-labelledby={titleId} onCancel={(event) => {
      event.preventDefault();
      if (!pending) onClose();
    }}>
      <h2 id={titleId}>{title}</h2>
      <p>{description}</p>
      {error && <p className="field-error" role="alert">{error}</p>}
      <div className="dialog-actions">
        <button className="button button-secondary" disabled={pending} onClick={onClose} autoFocus>Cancel</button>
        <button className="button button-danger" disabled={pending} onClick={handleDelete}>
          {pending ? 'Deleting…' : 'Delete permanently'}
        </button>
      </div>
    </dialog>
  );
}
