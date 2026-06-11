
// 백엔드 API 호출 모듈
import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
});

// 토큰 자동 추가
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 농업기상
export const getKoreaWeather = (date) => api.get('/api/weather/korea', { params: { date } });
export const getPointWeather = (lat, lon, date) => api.get('/api/weather/point', { params: { lat, lon, date } });

// 토양
export const getSoil = (lat, lon) => api.get('/api/soil/point', { params: { lat, lon } });

// AI 추천
export const getAIRecommend = (lat, lon, location, date) =>
  api.get('/api/ai/recommend', { params: { lat, lon, location, date } });
export const askQuestion = (question, location) =>
  api.get('/api/ai/question', { params: { question, location } });

// 카카오 주소검색
export const searchAddress = (address) => api.get('/api/kakao/address', { params: { address } });

// 인증
export const login = (token) => api.post('/api/auth/login', null, {
  headers: { Authorization: `Bearer ${token}` }
});

// 플랜
export const getPlans = () => api.get('/api/payment/plans');
export const getAIUsage = () => api.get('/api/payment/usage');

export default api;

// 추천 기록
export const getRecommendations = () => api.get('/api/user/recommendations');
export const deleteRecommendation = (id) => api.delete(`/api/user/recommendations/${id}`);

// 즐겨찾기
export const getFavorites = () => api.get('/api/user/favorites');
export const addFavorite = (crop_name, location) => api.post('/api/user/favorites', null, { params: { crop_name, location } });
export const deleteFavorite = (id) => api.delete(`/api/user/favorites/${id}`);