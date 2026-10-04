export default function FormField({ id, label, hint, error, ...props }) {
  const description = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(' ');

  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <input id={id} name={id} aria-describedby={description || undefined} aria-invalid={error ? true : undefined} {...props} />
      {hint && <p id={`${id}-hint`} className="field-hint">{hint}</p>}
      {error && <p id={`${id}-error`} className="field-error">{error}</p>}
    </div>
  );
}
