import React, { useState, useEffect } from 'react';
import { getRecommendations, deleteRecommendation } from '../services/api';
import '../styles/HistoryPage.css';

function HistoryPage({ onBack }) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    try {
      const res = await getRecommendations();
      setRecords(res.data.data);
    } catch (error) {
      console.error('기록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('삭제할까요?')) return;
    try {
      await deleteRecommendation(id);
      setRecords(records.filter(r => r.id !== id));
    } catch (error) {
      alert('삭제 실패했습니다.');
    }
  };

  return (
    <div className="history-container">
      <div className="history-header">
        <button className="back-btn" onClick={onBack}>← 뒤로</button>
        <h2>📋 내 추천 기록</h2>
        <div></div>
      </div>

      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : records.length === 0 ? (
        <div className="empty">
          <p>아직 추천 기록이 없어요!</p>
          <p>작물 추천을 받아보세요 😊</p>
        </div>
      ) : (
        <div className="records-list">
          {records.map((record) => (
            <div key={record.id} className="record-card">
              <div className="record-info">
                <h3>📍 {record.location}</h3>
                <p>{record.created_at?.slice(0, 10)}</p>
              </div>
              <div className="record-preview">
                {record.result?.slice(0, 100)}...
              </div>
              <button
                className="delete-btn"
                onClick={() => handleDelete(record.id)}
              >
                삭제
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default HistoryPage;