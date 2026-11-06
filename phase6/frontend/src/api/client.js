import axios from 'axios';

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function fetchCities() {
  const response = await apiClient.get('/api/cities');
  return response.data;
}

export async function fetchRecommendations({ city, price, preferences }) {
  const payload = {
    city,
    price,
    ...(preferences ? { preferences } : {}),
  };
  const response = await apiClient.post('/api/recommend', payload);
  return response.data;
}

export async function checkHealth() {
  const response = await apiClient.get('/health');
  return response.data;
}

