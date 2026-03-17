import { useState, useEffect, useRef, useCallback } from "react";

export default function usePolling(fetchFn, intervalMs = 30000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const timerRef = useRef(null);

  const load = useCallback(async () => {
    const result = await fetchFn();
    if (result !== null) setData(result);
    setLoading(false);
  }, [fetchFn]);

  useEffect(() => {
    load();
    timerRef.current = setInterval(load, intervalMs);
    return () => clearInterval(timerRef.current);
  }, [load, intervalMs]);

  return { data, loading };
}
