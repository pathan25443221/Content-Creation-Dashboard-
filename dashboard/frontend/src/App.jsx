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
  const [burnCaptions, setBurnCaptions] = useState(true);
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
        body: JSON.stringify({ video_input: videoInput, video_type: videoType, burn_captions: burnCaptions })
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
                  <option value="speech">Podcast / Talking Head (AI finds best quotes)</option>
                  <option value="visual">Action / Gaming (AI finds exciting moments)</option>
                  <option value="visual_split">Gaming with Facecam (Split Screen)</option>
                </select>
                <div style={{ display: 'flex', alignItems: 'center', marginLeft: '12px' }}>
                  <input 
                    type="checkbox" 
                    id="burnCaptionsOverview" 
                    checked={burnCaptions} 
                    onChange={(e) => setBurnCaptions(e.target.checked)} 
                    style={{ marginRight: '6px' }}
                  />
                  <label htmlFor="burnCaptionsOverview" style={{ fontSize: '0.85rem' }}>Burn Captions</label>
                </div>
                <button type="submit" className="btn-primary" disabled={isGenerating} style={{ marginLeft: '12px' }}>
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
                    <option value="speech">Podcast / Talking Head (AI finds best quotes)</option>
                    <option value="visual">Action / Gaming (AI finds exciting moments)</option>
                    <option value="visual_split">Gaming with Facecam (Split Screen)</option>
                  </select>
                </div>

                <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center' }}>
                  <input 
                    type="checkbox" 
                    id="burnCaptionsGenerate" 
                    checked={burnCaptions} 
                    onChange={(e) => setBurnCaptions(e.target.checked)} 
                    style={{ marginRight: '8px', width: '18px', height: '18px' }}
                  />
                  <label htmlFor="burnCaptionsGenerate" style={{ fontWeight: 500 }}>Burn Captions (Overlay subtitles on video)</label>
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
              <p className="page-subtitle">Review candidate clips selected by local AI models before publishing.</p>
            </header>

            {clips.length === 0 ? (
              <div className="card-box" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                No candidate clips awaiting review. Use "Generate Clip" to process a new video!
              </div>
            ) : (
              <div className="vizard-review-list">
                {clips.map((clip, idx) => (
                  <div key={clip.id} className="vizard-card">
                    {/* Left Column: 9:16 Vertical Video Player */}
                    <div className="vizard-media-col">
                      {clip.media_url && (
                        <div className="vizard-player-container">
                          <video 
                            src={clip.media_url} 
                            controls 
                            preload="metadata"
                            className="vizard-video"
                          />
                        </div>
                      )}
                    </div>

                    {/* Right Column: Vizard Card Details */}
                    <div className="vizard-details-col">
                      <div className="vizard-header-row">
                        <h2 className="vizard-title">
                          <span className="vizard-num">#{idx + 1}</span> {clip.title}
                        </h2>
                      </div>

                      {/* Virality Score and Actions Bar */}
                      <div className="vizard-score-actions-row">
                        <div className="vizard-virality-badge">
                          <span className="vizard-score-val">{clip.virality_score || 8.5}</span>
                          <span className="vizard-score-lbl">VIRALITY</span>
                        </div>

                        <div className="vizard-action-group">
                          <button 
                            className="vizard-btn-publish" 
                            onClick={() => handleApprove(clip.id, clip.title)}
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
                            Publish
                          </button>
                          <button 
                            className="vizard-btn-reject"
                            onClick={() => handleReject(clip.id)}
                            title="Reject clip"
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                          </button>
                        </div>
                      </div>

                      {/* Viral Reason Callout Container */}
                      <div className="vizard-reason-card">
                        <div className="vizard-reason-label">Viral reason</div>
                        <div className="vizard-reason-text">{clip.reason}</div>
                      </div>

                      {/* Timestamped Subtitle Transcript Preview */}
                      {clip.transcript_lines && clip.transcript_lines.length > 0 && (
                        <div className="vizard-transcript-container">
                          {clip.transcript_lines.map((line, lIdx) => (
                            <div key={lIdx} className="vizard-transcript-line">
                              <span className="vizard-ts">{line.timestamp}</span>
                              <span className="vizard-txt">{line.text}</span>
                            </div>
                          ))}
                        </div>
                      )}
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
