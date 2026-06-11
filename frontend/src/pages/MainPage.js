import React, { useState } from 'react';
import { signOut } from 'firebase/auth';
import { auth } from '../firebase';
import { getAIRecommend } from '../services/api';
import { searchAddressKakao } from '../services/kakao';
import ResultPage from './ResultPage';
import '../styles/MainPage.css';

function MainPage({ user }) {
  const [address, setAddress] = useState('');
  const [location, setLocation] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showResult, setShowResult] = useState(false);

  const handleSearch = async () => {
    if (!address.trim()) {
      alert('주소를 입력해주세요!');
      return;
    }
    try {
      setLoading(true);
      const locationData = await searchAddressKakao(address);
      setLocation(locationData);
    } catch (error) {
      alert('주소를 찾을 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleRecommend = async () => {
    if (!location) {
      alert('먼저 주소를 검색해주세요!');
      return;
    }
    try {
      setLoading(true);
      const res = await getAIRecommend(
        location.lat,
        location.lon,
        address
      );
      console.log('AI 결과:', res.data);
      setResult(res.data.recommendation);
      setShowResult(true);
    } catch (error) {
      if (error.response?.status === 429) {
        alert('이번 달 AI 추천 횟수를 초과했습니다. 유료 플랜으로 업그레이드하세요!');
      } else {
        alert('추천 중 오류가 발생했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await signOut(auth);
    localStorage.removeItem('token');
  };

  if (showResult) {
    return (
      <ResultPage
        result={result}
        location={address}
        onBack={() => setShowResult(false)}
        onSave={() => alert('저장됐어요!')}
      />
    );
  }

  return (
    <div className="main-container">
      <header className="header">
        <h1>🌾 팜맵 귀농 AI</h1>
        <div className="user-info">
          <img src={user.photoURL} alt="프로필" className="profile-img" />
          <span>{user.displayName}</span>
          <button onClick={handleLogout} className="logout-btn">로그아웃</button>
        </div>
      </header>

      <main className="main-content">
        <div className="search-section">
          <h2>내 농지 주소를 입력하세요</h2>
          <p>AI가 해당 지역의 날씨, 토양, 병해충 데이터를 분석해 작물을 추천해드려요!</p>
          <div className="search-box">
            <input
              type="text"
              placeholder="예: 전북 군산시 미룡동"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button onClick={handleSearch} disabled={loading}>
              {loading ? '검색 중...' : '검색'}
            </button>
          </div>
        </div>

        {location && (
          <div className="location-card">
            <h3>📍 {location.jibun_address}</h3>
            <p>위도: {location.lat} | 경도: {location.lon}</p>
            <button
              className="recommend-btn"
              onClick={handleRecommend}
              disabled={loading}
            >
              {loading ? '🤖 AI 분석 중...' : '🌱 작물 추천받기'}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default MainPage;