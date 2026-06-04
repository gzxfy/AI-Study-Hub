const loginForm = document.getElementById('loginForm');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const errorEmail = document.getElementById('error-email');
const errorPassword = document.getElementById('error-password');
const togglePassword = document.getElementById('togglePassword');

function setError(input, errorElement, message) {
  input.classList.add('is-invalid');
  errorElement.textContent = message;
}

function clearError(input, errorElement) {
  input.classList.remove('is-invalid');
  errorElement.textContent = '';
}

function makeToggle(button, input) {
  return function () {
    const isShowing = input.type === 'text';

    if (isShowing) {
      input.type = 'password';
      button.setAttribute('aria-label', 'Show password');
      button.setAttribute('aria-pressed', 'false');
    } else {
      input.type = 'text';
      button.setAttribute('aria-label', 'Hide password');
      button.setAttribute('aria-pressed', 'true');
    }
  };
}

function handleSubmit(event) {
  let hasError = false;

  clearError(emailInput, errorEmail);
  clearError(passwordInput, errorPassword);

  if (!emailInput.value.trim()) {
    setError(emailInput, errorEmail, 'Email is required.');
    hasError = true;
  }

  if (!passwordInput.value.trim()) {
    setError(passwordInput, errorPassword, 'Password is required.');
    hasError = true;
  }

  if (hasError) {
    event.preventDefault();
  }
}

emailInput.addEventListener('input', function () {
  if (emailInput.value.trim()) {
    clearError(emailInput, errorEmail);
  }
});

passwordInput.addEventListener('input', function () {
  if (passwordInput.value.trim()) {
    clearError(passwordInput, errorPassword);
  }
});

togglePassword.addEventListener('click', makeToggle(togglePassword, passwordInput));
loginForm.addEventListener('submit', handleSubmit);