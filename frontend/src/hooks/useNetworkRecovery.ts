import { useState, useEffect, useCallback, useRef } from 'react';

interface NetworkState {
  isOnline: boolean;
  isReconnecting: boolean;
  hasNetworkError: boolean;
  retryCount: number;
  lastErrorTime: number | null;
}

interface UseNetworkRecoveryOptions {
  maxRetries?: number;
  retryDelay?: number;
  exponentialBackoff?: boolean;
  onNetworkRestore?: () => void;
  onNetworkLost?: () => void;
}

interface NetworkRecoveryReturn extends NetworkState {
  retry: () => void;
  resetError: () => void;
  isRecovering: boolean;
}

const useNetworkRecovery = (options: UseNetworkRecoveryOptions = {}): NetworkRecoveryReturn => {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    exponentialBackoff = true,
    onNetworkRestore,
    onNetworkLost
  } = options;

  const [networkState, setNetworkState] = useState<NetworkState>({
    isOnline: navigator.onLine,
    isReconnecting: false,
    hasNetworkError: false,
    retryCount: 0,
    lastErrorTime: null
  });

  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastOnlineRef = useRef(navigator.onLine);

  const calculateDelay = useCallback((attempt: number): number => {
    if (!exponentialBackoff) return retryDelay;
    return Math.min(retryDelay * Math.pow(2, attempt), 30000); // Max 30 seconds
  }, [retryDelay, exponentialBackoff]);

  const resetError = useCallback(() => {
    setNetworkState(prev => ({
      ...prev,
      hasNetworkError: false,
      retryCount: 0,
      isReconnecting: false,
      lastErrorTime: null
    }));

    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = null;
    }
  }, []);

  const retry = useCallback(() => {
    if (networkState.retryCount >= maxRetries) {
      console.warn('Max retry attempts reached');
      return;
    }

    setNetworkState(prev => ({
      ...prev,
      isReconnecting: true,
      retryCount: prev.retryCount + 1
    }));

    const delay = calculateDelay(networkState.retryCount);

    retryTimeoutRef.current = setTimeout(() => {
      // Test network connectivity
      fetch('/api/health', { 
        method: 'HEAD',
        cache: 'no-cache',
        mode: 'no-cors'
      })
        .then(() => {
          setNetworkState(prev => ({
            ...prev,
            isReconnecting: false,
            hasNetworkError: false,
            retryCount: 0,
            lastErrorTime: null
          }));
          onNetworkRestore?.();
        })
        .catch(() => {
          setNetworkState(prev => ({
            ...prev,
            isReconnecting: false,
            lastErrorTime: Date.now()
          }));
          
          // Auto-retry if under max attempts
          if (networkState.retryCount + 1 < maxRetries) {
            setTimeout(() => retry(), calculateDelay(networkState.retryCount + 1));
          }
        });
    }, delay);
  }, [networkState.retryCount, maxRetries, calculateDelay, onNetworkRestore]);

  const handleOnline = useCallback(() => {
    const wasOffline = !lastOnlineRef.current;
    lastOnlineRef.current = true;

    setNetworkState(prev => ({
      ...prev,
      isOnline: true,
      hasNetworkError: false,
      isReconnecting: false,
      retryCount: 0,
      lastErrorTime: null
    }));

    if (wasOffline) {
      onNetworkRestore?.();
    }
  }, [onNetworkRestore]);

  const handleOffline = useCallback(() => {
    const wasOnline = lastOnlineRef.current;
    lastOnlineRef.current = false;

    setNetworkState(prev => ({
      ...prev,
      isOnline: false,
      hasNetworkError: true,
      lastErrorTime: Date.now()
    }));

    if (wasOnline) {
      onNetworkLost?.();
    }
  }, [onNetworkLost]);

  // Handle fetch errors and convert them to network errors
  const handleNetworkError = useCallback((error: Error) => {
    const isNetworkError = 
      error.name === 'TypeError' && error.message.includes('fetch') ||
      error.message.includes('NetworkError') ||
      error.message.includes('Failed to fetch') ||
      !navigator.onLine;

    if (isNetworkError) {
      setNetworkState(prev => ({
        ...prev,
        hasNetworkError: true,
        lastErrorTime: Date.now()
      }));
    }
  }, []);

  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [handleOnline, handleOffline]);

  // Attach global error handler for fetch errors
  useEffect(() => {
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);
        if (response.ok || response.status < 500) {
          // Reset network error on successful requests
          if (networkState.hasNetworkError && navigator.onLine) {
            resetError();
          }
        }
        return response;
      } catch (error) {
        handleNetworkError(error as Error);
        throw error;
      }
    };

    return () => {
      window.fetch = originalFetch;
    };
  }, [networkState.hasNetworkError, handleNetworkError, resetError]);

  return {
    ...networkState,
    retry,
    resetError,
    isRecovering: networkState.isReconnecting || 
                  (networkState.hasNetworkError && networkState.retryCount > 0)
  };
};

export default useNetworkRecovery;
