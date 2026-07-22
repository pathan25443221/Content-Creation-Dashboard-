import React, { useState, useEffect } from 'react';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState({
    total_clips: 0,
    pending_review_count: 0,
    recent_posts_count: 0,
    total_views: 0,
    total_likes: 0,
    recent_activity: []
  });

  const [clips, setClips] = useState([]);
  const [posts, setPosts] = useState([]);
  const [videoInput, setVideoInput] = useState('');
  const [videoType, setVideoType] = useState('speech');
  const [isGenerating, setIsGenerating] = useState(false);
  const [genMessage, setGenMessage] = useState('');

  // Fetch overview data
  const fetchOverview = async () => {
    try {
      const res = await fetch('/api/overview');
      if (res.ok) {
        const data = await res.json();
        setOverview(data);
      }
    } catch (e) {
      console.error("Failed to fetch overview:", e);
    }
  };

  // Fetch clips
  const fetchClips = async (status = '') => {
    try {
      const url = status ? `/api/clips?status=${status}` : '/api/clips';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setClips(data);
      }
    } catch (e) {
      console.error("Failed to fetch clips:", e);
    }
  };

  // Fetch posts
  const fetchPosts = async () => {
    try {
      const res = await fetch('/api/posts');
      if (res.ok) {
        const data = await res.json();
        setPosts(data);
      }
    } catch (e) {
      console.error("Failed to fetch posts:", e);
    }
  };

  useEffect(() => {
    fetchOverview();
    if (activeTab === 'review') fetchClips('pending');
    if (activeTab === 'posts') fetchPosts();
    if (activeTab === 'clips') fetchClips();

    // Auto-poll overview and pending clips every 5 seconds to catch completed background generations
    const interval = setInterval(() => {
      fetchOverview();
      if (activeTab === 'review') fetchClips('pending');
    }, 5000);

    return () => clearInterval(interval);
  }, [activeTab]);

  const handleGenerateSubmit = async (e) => {
    e.preventDefault();
    if (!videoInput) return;

    setIsGenerating(true);
    setGenMessage('🚀 Generation started in background! Downloading, transcribing with Whisper, & selecting clips via Ollama...');

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_input: videoInput, video_type: videoType })
      });

      const data = await res.json();
      if (res.ok || res.status === 202) {
        setGenMessage('⚡ Processing active in background! Clips will automatically land in the Review Queue when rendered.');
        setVideoInput('');
        setTimeout(() => {
          setIsGenerating(false);
          setActiveTab('review');
        }, 1500);
      } else {
        setGenMessage(`Error: ${data.detail || 'Generation failed'}`);
        setIsGenerating(false);
      }
    } catch (err) {
      setGenMessage(`Network Error: ${err.message}`);
      setIsGenerating(false);
    }
  };

  const handleApprove = async (clipId, customTitle) => {
    try {
      const res = await fetch(`/api/clips/${clipId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: customTitle, platforms: ['youtube', 'instagram'] })
      });
      if (res.ok) {
        fetchClips('pending');
        fetchOverview();
      }
    } catch (e) {
      console.error("Approve failed:", e);
    }
  };

  const handleReject = async (clipId) => {
    try {
      const res = await fetch(`/api/clips/${clipId}/reject`, {
        method: 'POST'
      });
      if (res.ok) {
        fetchClips('pending');
        fetchOverview();
      }
    } catch (e) {
      console.error("Reject failed:", e);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-brand">Content Dashboard</div>
        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={`nav-item ${activeTab === 'generate' ? 'active' : ''}`}
            onClick={() => setActiveTab('generate')}
          >
            Generate Clip
          </button>
          <button 
            className={`nav-item ${activeTab === 'review' ? 'active' : ''}`}
            onClick={() => setActiveTab('review')}
          >
            Review Queue ({overview.pending_review_count})
          </button>
          <button 
            className={`nav-item ${activeTab === 'posts' ? 'active' : ''}`}
            onClick={() => setActiveTab('posts')}
          >
            Posts / Library
          </button>
          <button 
            className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            Analytics
          </button>
        </nav>
      </aside>

      {/* Main Screen Content */}
      <main className="main-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div>
            <header className="page-header">
              <h1 className="page-title">Operator Overview</h1>
              <p className="page-subtitle">Track your content pipeline generation, review queue, and performance at a glance.</p>
            </header>

            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Clips Generated</div>
                <div className="stat-value">{overview.total_clips}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Pending Review Queue</div>
                <div className="stat-value" style={{ color: 'var(--accent-blue)' }}>{overview.pending_review_count}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Published (Last 7 Days)</div>
                <div className="stat-value">{overview.recent_posts_count}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Reach / Views</div>
                <div className="stat-value" style={{ color: 'var(--badge-posted)' }}>{overview.total_views.toLocaleString()}</div>
              </div>
            </div>

            {/* Quick Generator Box */}
            <div className="card-box">
              <h3>Quick Generate Short Clips</h3>
              <form onSubmit={handleGenerateSubmit} className="input-group">
                <input 
                  type="text" 
                  className="url-input" 
                  placeholder="Paste YouTube Video URL or local path..."
                  value={videoInput}
                  onChange={(e) => setVideoInput(e.target.value)}
                />
                <select 
                  className="select-input"
                  value={videoType}
                  onChange={(e) => setVideoType(e.target.value)}
                >
                  <option value="speech">Speech-based (Talking head/Podcast)</option>
                  <option value="visual">Visual-based (Sports/Gameplay)</option>
                </select>
                <button type="submit" className="btn-primary" disabled={isGenerating}>
                  {isGenerating ? 'Processing...' : 'Generate Shorts'}
                </button>
              </form>
              {genMessage && <p style={{ marginTop: '12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{genMessage}</p>}
            </div>
          </div>
        )}

        {/* Generate Tab */}
        {activeTab === 'generate' && (
          <div>
            <header className="page-header">
              <h1 className="page-title">Generate Shorts</h1>
              <p className="page-subtitle">Paste a YouTube URL or file path to produce vertical 9:16 short-form clips.</p>
            </header>

            <div className="card-box">
              <form onSubmit={handleGenerateSubmit}>
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Source Video URL / Local Path</label>
                  <input 
                    type="text" 
                    className="url-input" 
                    style={{ width: '100%' }}
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={videoInput}
                    onChange={(e) => setVideoInput(e.target.value)}
                  />
                </div>

                <div style={{ marginBottom: '24px' }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Content Pipeline Router Path</label>
                  <select 
                    className="select-input"
                    style={{ width: '100%' }}
                    value={videoType}
                    onChange={(e) => setVideoType(e.target.value)}
                  >
                    <option value="speech">Speech-based — Local Whisper transcription + Ollama LLM clip reasoning</option>
                    <option value="visual">Visual-based — Librosa audio energy volume spikes + PySceneDetect motion cuts</option>
                  </select>
                </div>

                <button type="submit" className="btn-primary" disabled={isGenerating}>
                  {isGenerating ? 'Running Pipeline...' : 'Start Clip Generation'}
                </button>
              </form>
              {genMessage && <p style={{ marginTop: '16px', color: 'var(--accent-blue)' }}>{genMessage}</p>}
            </div>
          </div>
        )}

        {/* Review Queue Tab */}
        {activeTab === 'review' && (
          <div>
            <header className="page-header">
              <h1 className="page-title">Review Queue</h1>
              <p className="page-subtitle">Review candidate clips selected by local models before publishing.</p>
            </header>

            {clips.length === 0 ? (
              <div className="card-box" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                No candidate clips awaiting review. Use "Generate Clip" to process a new video!
              </div>
            ) : (
              <div className="review-grid">
                {clips.map((clip) => (
                  <div key={clip.id} className="review-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="badge badge-pending">Pending Review</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{clip.duration}s clip ({clip.start_time}s - {clip.end_time}s)</span>
                    </div>

                    {clip.media_url && (
                      <div style={{ borderRadius: '8px', overflow: 'hidden', backgroundColor: '#000', display: 'flex', justifyContent: 'center' }}>
                        <video 
                          src={clip.media_url} 
                          controls 
                          preload="metadata"
                          style={{ width: '100%', maxHeight: '320px', objectFit: 'contain' }} 
                        />
                      </div>
                    )}

                    <div>
                      <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Title / Caption</label>
                      <input 
                        type="text" 
                        className="url-input" 
                        defaultValue={clip.title}
                        onBlur={(e) => clip.title = e.target.value}
                        style={{ width: '100%', marginTop: '4px' }}
                      />
                    </div>

                    <div className="reason-box">
                      <strong>AI Reasoning:</strong> {clip.reason}
                    </div>

                    <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
                      <button 
                        className="btn-primary" 
                        style={{ flex: 1 }}
                        onClick={() => handleApprove(clip.id, clip.title)}
                      >
                        Approve & Queue
                      </button>
                      <button 
                        className="btn-danger"
                        onClick={() => handleReject(clip.id)}
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Posts Library Tab */}
        {activeTab === 'posts' && (
          <div>
            <header className="page-header">
              <h1 className="page-title">Posts Library</h1>
              <p className="page-subtitle">All generated clips and their publishing status across connected social platforms.</p>
            </header>

            <div className="card-box" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Clip Title</th>
                    <th>Platform</th>
                    <th>Post ID</th>
                    <th>Posted Date</th>
                    <th>Status</th>
                    <th>Views / Likes</th>
                  </tr>
                </thead>
                <tbody>
                  {posts.length === 0 ? (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>
                        No published posts found. Approve clips in the Review Queue to queue posts.
                      </td>
                    </tr>
                  ) : (
                    posts.map((post) => (
                      <tr key={post.id}>
                        <td><strong>{post.clip_title}</strong></td>
                        <td style={{ textTransform: 'capitalize' }}>{post.platform}</td>
                        <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{post.platform_post_id || 'Queued'}</td>
                        <td>{post.posted_at ? new Date(post.posted_at).toLocaleDateString() : '-'}</td>
                        <td>
                          <span className={`badge badge-${post.status}`}>
                            {post.status}
                          </span>
                        </td>
                        <td>
                          {post.latest_metrics ? (
                            <span>{post.latest_metrics.views} views / {post.latest_metrics.likes} likes</span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>Pending sync</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div>
            <header className="page-header">
              <h1 className="page-title">Clip Performance Analytics</h1>
              <p className="page-subtitle">Historical performance data pulled from social platform APIs.</p>
            </header>

            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Views</div>
                <div className="stat-value">{overview.total_views.toLocaleString()}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Likes</div>
                <div className="stat-value" style={{ color: 'var(--accent-purple)' }}>{overview.total_likes.toLocaleString()}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Connected Platforms</div>
                <div className="stat-value">YouTube & IG</div>
              </div>
            </div>

            <div className="card-box">
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
        )}
      </main>
    </div>
  );
}
