import React from 'react';

export default function ProgressOverlay({ progressMsg }) {
  if (!progressMsg) return null;

  return (
    <div className="progress-overlay">
      <div className="progress-modal">
        <div className="spinner"></div>
        <h3>Generating Magic ✨</h3>
        <p className="progress-text">{progressMsg}</p>
        <div className="progress-bar-container">
           <div className="progress-bar-fill"></div>
        </div>
      </div>
    </div>
  );
}
