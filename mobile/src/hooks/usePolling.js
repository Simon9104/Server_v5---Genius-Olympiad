import { useState, useEffect, useCallback, useRef } from 'react';
import { AppState } from 'react-native';
import { fetchData, fetchAlerts, fetchStatus } from '../utils/api';

/**
 * usePolling — polls /data, /alerts, and /status on a fixed interval
 * while the app is in the foreground.
 *
 * @param {string|null} baseUrl   — full URL like "http://192.168.1.10:8080"; null disables polling
 * @param {number}      intervalMs — polling interval in milliseconds (default 5000)
 * @returns {{ data, alerts, status, error, loading, refetch }}
 */
export default function usePolling(baseUrl, intervalMs = 5000) {
  const [data, setData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const intervalRef = useRef(null);
  const appStateRef = useRef(AppState.currentState);
  const isMountedRef = useRef(true);

  const fetchAll = useCallback(async () => {
    if (!baseUrl) return;

    setLoading(true);
    setError(null);

    try {
      const [dataResult, alertsResult, statusResult] = await Promise.all([
        fetchData(baseUrl),
        fetchAlerts(baseUrl),
        fetchStatus(baseUrl),
      ]);

      if (!isMountedRef.current) return;

      setData(dataResult);
      setAlerts(Array.isArray(alertsResult) ? alertsResult : []);
      setStatus(statusResult);
    } catch (err) {
      if (!isMountedRef.current) return;
      setError(err.message || 'Failed to reach the server.');
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [baseUrl]);

  // Start / stop the polling interval
  const startPolling = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (!baseUrl) return;

    fetchAll(); // immediate first fetch
    intervalRef.current = setInterval(fetchAll, intervalMs);
  }, [baseUrl, intervalMs, fetchAll]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // React to app going to background / foreground
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState) => {
      if (
        appStateRef.current.match(/inactive|background/) &&
        nextState === 'active'
      ) {
        // App came to foreground — resume polling
        startPolling();
      } else if (nextState.match(/inactive|background/)) {
        // App went to background — pause polling
        stopPolling();
      }
      appStateRef.current = nextState;
    });

    return () => subscription.remove();
  }, [startPolling, stopPolling]);

  // Start polling when baseUrl or intervalMs changes
  useEffect(() => {
    isMountedRef.current = true;

    if (baseUrl) {
      startPolling();
    } else {
      stopPolling();
      // Reset state when disconnected
      setData(null);
      setAlerts([]);
      setStatus(null);
      setError(null);
    }

    return () => {
      stopPolling();
      isMountedRef.current = false;
    };
  }, [baseUrl, intervalMs]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    data,
    alerts,
    status,
    error,
    loading,
    refetch: fetchAll,
  };
}
