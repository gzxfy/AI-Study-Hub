import { useEffect, useState } from 'react';
// A custom hook to load the data and tracks whether the request is loading, successful, or failed
export default function useResource(load) {
  const [result, setResult] = useState({ data: null, error: null, loading: true });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setResult({ data: null, error: null, loading: true });

    load(controller.signal).then((data) => {
      if (!controller.signal.aborted) setResult({ data, error: null, loading: false });
    }).catch((error) => {
      if (!controller.signal.aborted) setResult({ data: null, error, loading: false });
    });

    return () => controller.abort();
  }, [load, attempt]);

  return { ...result, reload: () => setAttempt((value) => value + 1) };
}
