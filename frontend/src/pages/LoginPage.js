//로그인
import React from 'react';
import { getAuth, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { login } from '../services/api';
import '../styles/LoginPage.css';

function LoginPage({ onLogin }) {
  const handleGoogleLogin = async () => {
    try {
      const auth = getAuth();
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      const token = await result.user.getIdToken();

      // 백엔드에 토큰 전달
      await login(token);
      localStorage.setItem('token', token);
      onLogin();
    } catch (error) {
      console.error('로그인 실패:', error);
      alert('로그인에 실패했습니다. 다시 시도해주세요.');
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-logo">🌾</div>
        <h1>팜맵 귀농 AI</h1>
        <p>AI가 추천하는 나만의 작물을 찾아보세요!</p>
        <button className="google-btn" onClick={handleGoogleLogin}>
          <img src="https://www.google.com/favicon.ico" alt="google" />
          구글로 시작하기
        </button>
      </div>
    </div>
  );
}

export default LoginPage;