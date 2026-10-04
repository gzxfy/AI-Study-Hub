export class ApiError extends Error {
  constructor(message, status = 0, code = '') {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export async function request(path, { body, method = 'GET', signal, headers } = {}) {
  let response;

  try {
    response = await fetch(path, {
      method,
      signal,
      credentials: 'same-origin',
      headers: {
        Accept: 'application/json',
        ...(body !== undefined && { 'Content-Type': 'application/json' }),
        ...headers,
      },
      ...(body !== undefined && { body: JSON.stringify(body) }),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError('Unable to reach Study Hub. Check your connection and try again.');
  }

  if (response.status === 204) return null;
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const fallback = response.status >= 500
      ? 'Study Hub is temporarily unavailable. Please try again shortly.'
      : 'The request could not be completed. Please try again.';
    throw new ApiError(data?.error?.message || fallback, response.status, data?.error?.code);
  }

  if (!data || typeof data !== 'object') {
    throw new ApiError('Study Hub returned an unexpected response. Please try again.', response.status);
  }

  return data;
}

export async function mutate(path, body, { method = 'POST', signal } = {}) {
  // Fetch a fresh token: signing in or out may rotate the server session.
  const { csrf_token: csrfToken } = await request('/api/auth/csrf', { signal });
  if (typeof csrfToken !== 'string' || !csrfToken) {
    throw new ApiError('Unable to verify this request. Refresh the page and try again.');
  }

  return request(path, {
    method,
    body,
    signal,
    headers: { 'X-CSRFToken': csrfToken },
  });
}
