import { useEffect, useRef } from 'react';

export default function UnsavedChangesDialog({ blocker, saving }) {
  const dialog = useRef(null);
  const open = blocker.state === 'blocked';

  useEffect(() => {
    if (open) dialog.current.showModal();
    else dialog.current.close();
  }, [open]);

  return (
    <dialog ref={dialog} className="note-dialog" aria-labelledby="discard-title" onCancel={(event) => {
      event.preventDefault();
      blocker.reset?.();
    }}>
      <h2 id="discard-title">Leave this note?</h2>
      <p>{saving ? 'Your note is being saved. Wait for it to finish before leaving.' : 'Your changes have not been saved. Keep writing, or discard this draft.'}</p>
      <div className="dialog-actions">
        <button className="button button-secondary" onClick={() => blocker.reset()}>Keep writing</button>
        <button className="button button-danger" disabled={saving} onClick={() => blocker.proceed()}>Discard draft</button>
      </div>
    </dialog>
  );
}
