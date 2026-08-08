import React, { useState, useEffect } from 'react';

export default function ProgressOverlay({ progressMsg }) {
  const [pillState, setPillState] = useState('idle');

  useEffect(() => {
    if (!progressMsg) {
      setPillState('idle');
    } else if (progressMsg.toLowerCase().includes('complete') || progressMsg.toLowerCase().includes('done')) {
      setPillState('success');
    } else {
      setPillState('loading');
    }
  }, [progressMsg]);

  if (!progressMsg) return null;

  return (
    <div className="progress-overlay">
      <div className="progress-modal">
        <div className="status-pill" data-state={pillState}>
          <span className="icon">
            {pillState === 'loading' && (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="spin-icon">
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
            )}
            {pillState === 'success' && (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            )}
          </span>
          <span>{pillState === 'success' ? 'Generation Complete!' : 'Processing...'}</span>
        </div>

        <h3>{pillState === 'success' ? 'Ready for Review' : 'Generating AI Clips'}</h3>
        <p className="progress-text">{progressMsg}</p>
        
        {pillState === 'loading' && (
          <div className="progress-bar-container">
            <div className="progress-bar-fill"></div>
          </div>
        )}
      </div>
    </div>
  );
}
