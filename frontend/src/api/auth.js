import { ApiError, mutate, request } from './client.js';

function readUser(data) {
  if (!data?.user || data.user.id == null || typeof data.user.username !== 'string') {
    throw new ApiError('Study Hub could not load your account. Please try again.');
  }
  return data.user;
}

export async function getCurrentUser(signal) {
  try {
    return readUser(await request('/api/auth/me', { signal }));
  } catch (error) {
    if (error.status === 401) return null;
    throw error;
  }
}

export async function login({ email, password }) {
  return readUser(await mutate('/api/auth/login', { email, password }));
}

export async function register({ username, email, password, confirm_password }) {
  return readUser(await mutate('/api/auth/register', { username, email, password, confirm_password }));
}

export function logout() {
  return mutate('/api/auth/logout');
}
