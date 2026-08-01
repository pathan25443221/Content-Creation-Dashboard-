import React from 'react';
import GeneratorForm from './GeneratorForm';

export default function OverviewTab({ overview, generatorProps }) {
  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Operator Overview</h1>
        <p className="page-subtitle">Track your content pipeline generation, review queue, and performance at a glance.</p>
      </header>

      <div className="stats-grid">
        <div className="stat-card glass-panel">
          <div className="stat-label">Total Clips Generated</div>
          <div className="stat-value">{overview.total_clips}</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-label">Pending Review Queue</div>
          <div className="stat-value" style={{ color: 'var(--accent-blue)' }}>{overview.pending_review_count}</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-label">Published (Last 7 Days)</div>
          <div className="stat-value">{overview.recent_posts_count}</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-label">Total Reach / Views</div>
          <div className="stat-value" style={{ color: 'var(--badge-posted)' }}>{overview.total_views.toLocaleString()}</div>
        </div>
      </div>

      <GeneratorForm {...generatorProps} />
    </div>
  );
}
