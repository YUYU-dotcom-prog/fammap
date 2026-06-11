import React from 'react';
import '../styles/ResultPage.css';

function ResultPage({ result, location, onBack, onSave }) {
  if (!result) return null;

  // AI 결과 텍스트를 섹션별로 나누기
  const sections = result.split('\n\n').filter(s => s.trim());

  return (
    <div className="result-container">
      {/* 헤더 */}
      <div className="result-header">
        <button className="back-btn" onClick={onBack}>← 뒤로</button>
        <h2>🌾 AI 작물 추천 결과</h2>
        <button className="save-btn" onClick={onSave}>💾 저장</button>
      </div>

      {/* 지역 정보 */}
      <div className="location-info">
        <span>📍 {location}</span>
      </div>

      {/* AI 결과 */}
      <div className="result-content">
        {sections.map((section, i) => (
          <div key={i} className="result-section">
            {section.split('\n').map((line, j) => (
              <p key={j} className={line.startsWith('1.') || line.startsWith('2.') || line.startsWith('3.') || line.startsWith('4.') ? 'section-title' : 'section-text'}>
                {line}
              </p>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ResultPage;