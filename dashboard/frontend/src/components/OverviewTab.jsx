import React from 'react';
import GeneratorForm from './GeneratorForm';

export default function OverviewTab({ overview, generatorProps }) {
  const { videoInput, setVideoInput, handleGenerateSubmit, isGenerating } = generatorProps;

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
          <div className="stat-trend trend-up">+{overview.recent_posts_count || 12} this week</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-label">Pending Review Queue</div>
          <div className="stat-value" style={{ color: 'var(--accent-blue)' }}>{overview.pending_review_count}</div>
          <div className="stat-trend trend-neutral">Action required</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-label">Published (Last 7 Days)</div>
          <div className="stat-value">{overview.recent_posts_count}</div>
          <div className="stat-trend trend-up">On track</div>
        </div>
        <div className="stat-card glass-panel">
          <div className="stat-label">Total Reach / Views</div>
          <div className="stat-value" style={{ color: 'var(--badge-posted)' }}>{overview.total_views.toLocaleString()}</div>
          <div className="stat-trend trend-up">+450 this week</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '24px', marginTop: '32px' }}>
        {/* Left Column: Quick Generate */}
        <div className="glass-panel" style={{ flex: 2, padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            Quick Generate
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '16px' }}>
            Paste a YouTube URL to instantly generate shorts using your default preset. For advanced styling, use the Generate tab.
          </p>
          <form onSubmit={handleGenerateSubmit} style={{ display: 'flex', gap: '12px' }}>
            <input 
              type="text" 
              className="form-input" 
              placeholder="https://youtube.com/watch?v=..." 
              value={videoInput}
              onChange={(e) => setVideoInput(e.target.value)}
              style={{ flex: 1 }}
              required
            />
            <button type="submit" className="vizard-btn-publish" disabled={isGenerating}>
              {isGenerating ? 'Processing...' : 'Generate Magic'}
            </button>
          </form>
        </div>

        {/* Right Column: Recent Activity */}
        <div className="glass-panel" style={{ flex: 1, padding: '24px' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Recent Activity</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {overview.recent_activity && overview.recent_activity.length > 0 ? (
              overview.recent_activity.map(act => (
                <div key={act.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.9rem', borderBottom: '1px solid rgba(0,0,0,0.05)', paddingBottom: '8px' }}>
                  <div style={{
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: act.status === 'published' ? 'var(--badge-posted)' : (act.status === 'pending' ? 'var(--accent-blue)' : 'var(--badge-pending)')
                  }}></div>
                  <div style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {act.title}
                  </div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {act.status}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>No recent activity.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
