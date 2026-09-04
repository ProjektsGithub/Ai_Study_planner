import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

// Module-level shared state for unified health checking
let sharedHealth = {
  ok: null, // null = initial/unknown, true = connected, false = disconnected
  backend: 'colab',
  configured: true,
  url: null,
  latency_ms: null,
  model: null,
  gpu: null,
  device: null,
  error: null,
  lastChecked: null,
};
let isFetching = false;
const subscribers = new Set();

const notifySubscribers = () => {
  subscribers.forEach((callback) => callback({ ...sharedHealth, isFetching }));
};

export const checkColabHealth = async (force = false) => {
  // Prevent duplicate concurrent requests
  if (isFetching) return sharedHealth;

  // Don't refetch if checked within the last 15 seconds unless forced
  const now = Date.now();
  if (!force && sharedHealth.lastChecked && now - sharedHealth.lastChecked.getTime() < 15000) {
    return sharedHealth;
  }

  isFetching = true;
  notifySubscribers();

  try {
    const res = await apiClient.get('/api/v1/chat/health', { timeout: 10000 });
    const data = res.data || {};

    sharedHealth = {
      ok: Boolean(data.ok),
      backend: data.backend || 'colab',
      configured: data.configured !== false,
      url: data.url || null,
      latency_ms: typeof data.latency_ms === 'number' ? data.latency_ms : null,
      model: data.model || null,
      gpu: data.gpu || null,
      device: data.device || null,
      error: data.error || null,
      lastChecked: new Date(),
    };
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.error || err.message;
    sharedHealth = {
      ok: false,
      backend: 'colab',
      configured: true,
      url: null,
      latency_ms: null,
      model: null,
      gpu: null,
      device: null,
      error: detail || 'Impossible de joindre le serveur backend ou Colab',
      lastChecked: new Date(),
    };
  } finally {
    isFetching = false;
    notifySubscribers();
  }

  return sharedHealth;
};

/**
 * Custom hook providing live AI backend (Colab / Ollama) health status.
 * Automatically synchronizes across all components that use it.
 */
export const useColabStatus = (autoRefreshInterval = 60000) => {
  const [state, setState] = useState(() => ({
    ...sharedHealth,
    isFetching,
  }));

  useEffect(() => {
    // Subscribe to state updates
    const handleUpdate = (updatedState) => setState(updatedState);
    subscribers.add(handleUpdate);

    // Initial check if never checked
    if (!sharedHealth.lastChecked) {
      checkColabHealth();
    }

    // Auto-polling interval
    let intervalId = null;
    if (autoRefreshInterval > 0) {
      intervalId = setInterval(() => {
        checkColabHealth(true);
      }, autoRefreshInterval);
    }

    return () => {
      subscribers.delete(handleUpdate);
      if (intervalId) clearInterval(intervalId);
    };
  }, [autoRefreshInterval]);

  const refresh = useCallback(() => checkColabHealth(true), []);

  return {
    ...state,
    refresh,
  };
};

export default useColabStatus;
