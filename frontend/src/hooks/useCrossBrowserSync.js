import { useEffect, useCallback } from 'react';

/**
 * Hook for cross-tab/cross-window synchronization using BroadcastChannel API
 * @param {string} channelName - Name of the broadcast channel
 * @param {function} onMessage - Callback when message is received
 * @returns {object} - { broadcast } function to send messages
 */
export const useCrossBrowserSync = (channelName, onMessage) => {
  useEffect(() => {
    // Check if BroadcastChannel is supported
    if (typeof BroadcastChannel === 'undefined') {
      console.warn('BroadcastChannel API is not supported in this browser');
      return;
    }

    const channel = new BroadcastChannel(channelName);
    
    channel.onmessage = (event) => {
      if (onMessage) {
        onMessage(event.data);
      }
    };

    return () => {
      channel.close();
    };
  }, [channelName, onMessage]);

  const broadcast = useCallback((data) => {
    // Check if BroadcastChannel is supported
    if (typeof BroadcastChannel === 'undefined') {
      return;
    }

    const channel = new BroadcastChannel(channelName);
    channel.postMessage(data);
    channel.close();
  }, [channelName]);

  return { broadcast };
};
