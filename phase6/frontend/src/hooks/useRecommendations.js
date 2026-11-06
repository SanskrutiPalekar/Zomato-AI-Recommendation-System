import { useState, useEffect, useCallback } from 'react';
import { fetchCities, fetchRecommendations } from '../api/client';

export function useRecommendations() {
  const [cities, setCities] = useState([]);
  const [status, setStatus] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    fetchCities()
      .then((res) => {
        if (mounted && res?.cities) {
          setCities(res.cities);
        }
      })
      .catch(() => {
        // Fallback default cities if backend isn't reachable yet on mount
        if (mounted) {
          setCities([
            'Banashankari',
            'Basavanagudi',
            'BTM',
            'Indiranagar',
            'Jayanagar',
            'JP Nagar',
            'Koramangala',
          ]);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  const search = useCallback(async ({ city, price, preferences }) => {
    setStatus('loading');
    setError(null);
    try {
      const result = await fetchRecommendations({ city, price, preferences });
      setData(result);
      setStatus('success');
      return result;
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        'Unable to fetch restaurant recommendations. Please try again.';
      setError(detail);
      setStatus('error');
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setStatus('idle');
    setData(null);
    setError(null);
  }, []);

  return {
    cities,
    status,
    data,
    error,
    search,
    reset,
  };
}

