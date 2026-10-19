import { useState } from 'react';
import Icon from './Icon';

export default function PasswordField({ id = 'password', label = 'Password', hint, error, ...props }) {
  const [visible, setVisible] = useState(false);
  const description = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(' ');

  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <div className="password-input">
        <input id={id} name={id} type={visible ? 'text' : 'password'} aria-describedby={description || undefined} aria-invalid={error ? true : undefined} {...props} />
        <button className="icon-button" type="button" aria-label={`${visible ? 'Hide' : 'Show'} ${label.toLowerCase()}`} aria-pressed={visible} onClick={() => setVisible(!visible)}>
          <Icon name="eye" size={18} />
        </button>
      </div>
      {hint && <p id={`${id}-hint`} className="field-hint">{hint}</p>}
      {error && <p id={`${id}-error`} className="field-error">{error}</p>}
    </div>
  );
}
