import React from 'react';

export default function Sidebar({ activeTab, setActiveTab, pendingReviewCount }) {
  return (
    <aside className="sidebar glass-panel" style={{ borderRadius: '24px', borderRight: '1px solid rgba(255,255,255,0.4)', margin: '16px' }}>
      <div className="sidebar-brand" style={{ textAlign: 'center', marginTop: '-20px', marginBottom: '2px' }}>
        <img src="/Assets/LOGO_Website.png" alt="ClipForge" style={{ width: '100%', maxWidth: '240px', objectFit: 'contain', transform: 'scale(1.2)' }} />
      </div>
      <nav className="sidebar-nav">
        <button
          className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <img src="/Assets/Overview_logo.png" alt="Overview" className="nav-icon" />
          <span>Overview</span>
        </button>
        <button
          className={`nav-item ${activeTab === 'generate' ? 'active' : ''}`}
          onClick={() => setActiveTab('generate')}
        >
          <img src="/Assets/Generate_clip_logo.png" alt="Generate" className="nav-icon" />
          <span>Generate Clip</span>
        </button>
        <button
          className={`nav-item ${activeTab === 'review' ? 'active' : ''}`}
          onClick={() => setActiveTab('review')}
        >
          <img src="/Assets/Review_queue.png" alt="Review Queue" className="nav-icon" />
          <span>Review Queue ({pendingReviewCount})</span>
        </button>
        <button
          className={`nav-item ${activeTab === 'posts' ? 'active' : ''}`}
          onClick={() => setActiveTab('posts')}
        >
          <img src="/Assets/posts_library.png" alt="Posts" className="nav-icon" />
          <span>Posts / Library</span>
        </button>
        <button
          className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          <img src="/Assets/Analytics.png" alt="Analytics" className="nav-icon" />
          <span>Analytics</span>
        </button>
      </nav>
    </aside>
  );
}
