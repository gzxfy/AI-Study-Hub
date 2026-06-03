/* =============================================================
   register.js — AI StudyHub Register Page Validation
   =============================================================

   WHAT THIS FILE DOES:
   1. Validates password requirements in real time as the user
      types — flipping rules from red ✗ to green ✓.
   2. Updates a visual strength meter bar below the rules.
   3. Toggles password field visibility (👁 button).
   4. Prevents form submission if any requirement is not met
      and shows inline error messages for empty fields.

   WHAT THIS FILE DOES NOT DO:
   - It does NOT send any data to a server.
   - It does NOT replace server-side validation.
   When you build your Flask auth route, you MUST also validate
   on the backend. This JS is purely a UX layer — a user can
   bypass it by disabling JavaScript or using DevTools.

   STRUCTURE:
   A. DOM references — grab elements once, reuse everywhere
   B. Validation checks — pure functions, easy to test
   C. updateRules() — runs on every keystroke in password fields
   D. updateStrengthMeter() — called from updateRules()
   E. Toggle password visibility
   F. Form submit guard
   G. Event listeners — wire everything together
============================================================= */


/* =============================================================
   A. DOM REFERENCES
   We grab every element we need once at the top.
   Storing them in variables is faster than calling
   document.getElementById() repeatedly inside event handlers.
============================================================= */

// Form and inputs
const registerForm    = document.getElementById('registerForm');
const usernameInput   = document.getElementById('username');
const emailInput      = document.getElementById('email');
const passwordInput   = document.getElementById('password');
const confirmInput    = document.getElementById('confirmPassword');

// Error message spans (one per field)
const errorUsername   = document.getElementById('error-username');
const errorEmail      = document.getElementById('error-email');
const errorPassword   = document.getElementById('error-password');
const errorConfirm    = document.getElementById('error-confirm');

// Rule <li> elements — JS will add/remove .rule--pass / .rule--fail
const ruleLength      = document.getElementById('rule-length');
const ruleUpper       = document.getElementById('rule-upper');
const ruleLower       = document.getElementById('rule-lower');
const ruleNumber      = document.getElementById('rule-number');
const ruleSpecial     = document.getElementById('rule-special');
const ruleMatch       = document.getElementById('rule-match');

// Strength meter elements
const strengthFill    = document.getElementById('strengthFill');
const strengthLabel   = document.getElementById('strengthLabel');

// Password toggle buttons
const togglePassword  = document.getElementById('togglePassword');
const toggleConfirm   = document.getElementById('toggleConfirm');


/* =============================================================
   B. VALIDATION CHECKS
   Each property is a function that returns true (pass) or
   false (fail). They are pure functions — they only read their
   arguments and return a boolean, no side effects.

   WHY THIS STRUCTURE?
   Keeping checks as named functions in an object makes the
   code easy to read, easy to extend (add a new rule = add one
   line here), and easy to unit-test later.
============================================================= */
const checks = {

  // Minimum 8 characters
  length: function(pw) {
    return pw.length >= 8;
  },

  // At least one uppercase letter A–Z
  upper: function(pw) {
    return /[A-Z]/.test(pw);
  },

  // At least one lowercase letter a–z
  lower: function(pw) {
    return /[a-z]/.test(pw);
  },

  // At least one digit 0–9
  number: function(pw) {
    return /[0-9]/.test(pw);
  },

  // At least one special character from a common set
  // The backslash escapes inside the character class are intentional:
  //   \-  → literal hyphen (must be escaped or placed at end)
  //   \/  → literal forward slash
  special: function(pw) {
    return /[!@#$%^&*()\-_=+[\]{}|;:'",.<>?/\\`~]/.test(pw);
  },

  // Both fields are non-empty AND they contain the same value.
  // We pass the confirm value as a second argument.
  match: function(pw, confirm) {
    return pw.length > 0 && pw === confirm;
  },

};


/* =============================================================
   C. UPDATE RULES
   Reads the current password and confirm values, runs all six
   checks, and updates the CSS classes on each rule <li>.

   Called by:
   - passwordInput 'input' event listener
   - confirmInput  'input' event listener
============================================================= */
function updateRules() {
  const pw      = passwordInput.value;
  const confirm = confirmInput.value;

  // Map each rule element to its corresponding check function.
  // Array of [element, boolean result] pairs.
  const results = [
    [ruleLength,  checks.length(pw)],
    [ruleUpper,   checks.upper(pw)],
    [ruleLower,   checks.lower(pw)],
    [ruleNumber,  checks.number(pw)],
    [ruleSpecial, checks.special(pw)],
    [ruleMatch,   checks.match(pw, confirm)],
  ];

  results.forEach(function(pair) {
    const element = pair[0];
    const passed  = pair[1];

    if (passed) {
      // Rule satisfied — green ✓
      element.classList.add('rule--pass');
      element.classList.remove('rule--fail');
    } else {
      // Rule not satisfied — red ✗
      element.classList.add('rule--fail');
      element.classList.remove('rule--pass');
    }
  });

  // Count how many of the 6 rules are passing
  const passCount = results.filter(function(pair) {
    return pair[1] === true;
  }).length;

  // Update the strength bar based on pass count
  updateStrengthMeter(passCount);
}


/* =============================================================
   D. UPDATE STRENGTH METER
   Takes the count of passing rules (0–6) and:
   1. Sets the fill bar's width as a percentage.
   2. Adds the correct color class to the fill element.
   3. Updates the label text.

   Strength levels:
     0–1 rules passing → Weak   (red)
     2–3 rules passing → Fair   (orange)
     4   rules passing → Good   (yellow)
     5–6 rules passing → Strong (green)
============================================================= */
function updateStrengthMeter(passCount) {
  // Width as a fraction of 6 total rules (expressed as %)
  const widthPct = Math.round((passCount / 6) * 100);
  strengthFill.style.width = widthPct + '%';

  // Remove all existing strength classes before adding the new one.
  // This prevents multiple classes stacking up.
  strengthFill.classList.remove(
    'strength--weak',
    'strength--fair',
    'strength--good',
    'strength--strong'
  );

  // Determine the level and apply the right class + label
  if (passCount === 0) {
    // Password field is empty — reset to neutral state
    strengthFill.style.width = '0%';
    strengthLabel.textContent = 'Enter a password to see strength';

  } else if (passCount <= 1) {
    strengthFill.classList.add('strength--weak');
    strengthLabel.textContent = 'Weak — keep going';

  } else if (passCount <= 3) {
    strengthFill.classList.add('strength--fair');
    strengthLabel.textContent = 'Fair — almost there';

  } else if (passCount === 4) {
    strengthFill.classList.add('strength--good');
    strengthLabel.textContent = 'Good — one more';

  } else {
    // 5 or 6 — all or nearly all rules passing
    strengthFill.classList.add('strength--strong');
    strengthLabel.textContent = 'Strong password!';
  }
}


/* =============================================================
   E. TOGGLE PASSWORD VISIBILITY
   makeToggle() is a factory function — it creates a click
   handler for a given (button, input) pair.
   This avoids writing the same handler twice.

   A "factory function" is just a function that returns another
   function. It's a common pattern when you need the same logic
   for multiple elements.
============================================================= */
function makeToggle(button, input) {
  return function() {
    const isShowing = input.type === 'text';

    if (isShowing) {
      // Currently showing → hide it
      input.type = 'password';
      button.setAttribute('aria-label', 'Show password');
      button.setAttribute('aria-pressed', 'false');
    } else {
      // Currently hidden → show it
      input.type = 'text';
      button.setAttribute('aria-label', 'Hide password');
      button.setAttribute('aria-pressed', 'true');
    }
  };
}


/* =============================================================
   F. FORM SUBMIT GUARD
   Runs when the user clicks "Create Account".
   Checks for empty required fields and whether any password
   rule is still failing.

   If validation fails:
   - e.preventDefault() stops the form from submitting.
   - Inline error messages are shown in the .form-error spans.
   - The relevant input gets the .is-invalid CSS class.

   If all checks pass, the form submits normally (to action="#"
   while frontend-only; to "/register" once Flask is added).

   IMPORTANT:
   This is client-side only. Your Flask route must re-validate
   everything on the server. Never trust the browser alone.
============================================================= */
function handleSubmit(e) {
  let hasError = false;

  // Helper — shows an error and marks the input invalid
  function showError(input, span, message) {
    span.textContent = message;
    input.classList.add('is-invalid');
    hasError = true;
  }

  // Helper — clears an error on a field that is now valid
  function clearError(input, span) {
    span.textContent = '';
    input.classList.remove('is-invalid');
  }

  // Reset all errors first so stale messages don't show
  clearError(usernameInput, errorUsername);
  clearError(emailInput,    errorEmail);
  clearError(passwordInput, errorPassword);
  clearError(confirmInput,  errorConfirm);

  // --- Check username ---
  if (usernameInput.value.trim() === '') {
    showError(usernameInput, errorUsername, 'Username is required.');
  }

  // --- Check email ---
  if (emailInput.value.trim() === '') {
    showError(emailInput, errorEmail, 'Email address is required.');
  } else if (!emailInput.value.includes('@')) {
    // Basic format check — Flask will do proper validation on the backend
    showError(emailInput, errorEmail, 'Please enter a valid email address.');
  }

  // --- Check password rules ---
  // If any rule still has .rule--fail, the password is not acceptable.
  const failingRules = [ruleLength, ruleUpper, ruleLower, ruleNumber, ruleSpecial, ruleMatch]
    .filter(function(rule) {
      return rule.classList.contains('rule--fail');
    });

  if (passwordInput.value === '') {
    showError(passwordInput, errorPassword, 'Password is required.');
  } else if (failingRules.length > 0) {
    showError(
      passwordInput,
      errorPassword,
      'Please meet all password requirements above.'
    );
  }

  // --- Check confirm password ---
  if (confirmInput.value === '') {
    showError(confirmInput, errorConfirm, 'Please confirm your password.');
  } else if (passwordInput.value !== confirmInput.value) {
    showError(confirmInput, errorConfirm, 'Passwords do not match.');
  }

  // If any check failed, stop the form from submitting
  if (hasError) {
    e.preventDefault();
    // Scroll to the first error so the user sees it
    const firstError = registerForm.querySelector('.is-invalid');
    if (firstError) {
      firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
      firstError.focus();
    }
  }
}


/* =============================================================
   G. EVENT LISTENERS
   Wire all the handlers defined above to their DOM events.
   This section is kept short and simple — all the logic lives
   in the named functions above.
============================================================= */

// Real-time password validation — fires on every keystroke in either field
passwordInput.addEventListener('input', updateRules);
confirmInput.addEventListener('input', updateRules);

// Password visibility toggles
togglePassword.addEventListener('click', makeToggle(togglePassword, passwordInput));
toggleConfirm.addEventListener('click',  makeToggle(toggleConfirm,  confirmInput));

// Form submit guard
registerForm.addEventListener('submit', handleSubmit);

// Clear field-level errors as the user corrects them
// This gives immediate positive feedback when a user fixes a mistake.
usernameInput.addEventListener('input', function() {
  errorUsername.textContent = '';
  usernameInput.classList.remove('is-invalid');
});

emailInput.addEventListener('input', function() {
  errorEmail.textContent = '';
  emailInput.classList.remove('is-invalid');
});
