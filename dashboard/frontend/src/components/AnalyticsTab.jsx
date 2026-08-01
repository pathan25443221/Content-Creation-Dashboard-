import React from 'react';

export default function AnalyticsTab({ overview, fetchOverview }) {
  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Clip Performance Analytics</h1>
        <p className="page-subtitle">Historical performance data pulled from social platform APIs.</p>
      </header>

      <div className="stats-grid">
        <div className="stat-card glass-panel">
          <div className="stat-label">Total Views</div>
          <div className="stat-value">{overview.total_views.toLocaleString()}</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-label">Total Likes</div>
          <div className="stat-value" style={{ color: 'var(--accent-purple)' }}>{overview.total_likes.toLocaleString()}</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-label">Connected Platforms</div>
          <div className="stat-value">YouTube & IG</div>
        </div>
      </div>

      <div className="card-box glass-panel">
        <h3>Metrics Sync</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: '8px 0 16px' }}>
          Metrics are automatically polled every few hours on a schedule. You can also trigger an instant sync below:
        </p>
        <button 
          className="btn-secondary"
          onClick={async () => {
            await fetch('/api/analytics/poll', { method: 'POST' });
            fetchOverview();
            alert('Analytics poll completed!');
          }}
        >
          Poll Latest Metrics Now
        </button>
      </div>
    </div>
  );
}
