import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import * as auth from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const sessionRequest = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    sessionRequest.current = controller;
    setStatus('loading');
    setError('');

    auth.getCurrentUser(controller.signal).then((account) => {
      if (controller.signal.aborted) return;
      setUser(account);
      setStatus(account ? 'authenticated' : 'anonymous');
    }).catch((failure) => {
      if (controller.signal.aborted) return;
      setError(failure.message);
      setStatus('error');
    });

    return () => controller.abort();
  }, [retry]);

  const signIn = useCallback(async (credentials) => {
    const account = await auth.login(credentials);
    sessionRequest.current?.abort();
    setUser(account);
    setError('');
    setStatus('authenticated');
  }, []);

  const signOut = useCallback(async () => {
    await auth.logout();
    sessionRequest.current?.abort();
    setUser(null);
    setStatus('anonymous');
  }, []);

  return (
    <AuthContext.Provider value={{ user, status, error, signIn, signOut, retrySession: () => setRetry((value) => value + 1) }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider.');
  return context;
}
