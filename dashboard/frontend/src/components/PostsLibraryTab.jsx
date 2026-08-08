import React, { useState } from 'react';

export default function PostsLibraryTab({ posts }) {
  const [statusFilter, setStatusFilter] = useState('all');
  const [platformFilter, setPlatformFilter] = useState('all');

  const filteredPosts = posts.filter(post => {
    if (statusFilter !== 'all' && post.status !== statusFilter) return false;
    if (platformFilter !== 'all' && post.platform !== platformFilter) return false;
    return true;
  });

  return (
    <div>
      <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Posts Library</h1>
          <p className="page-subtitle">All generated clips and their publishing status across connected social platforms.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button 
            type="button" 
            className={`platform-toggle-btn ${platformFilter === 'all' ? 'active' : ''}`}
            onClick={() => setPlatformFilter('all')}
          >
            All Platforms
          </button>
          <button 
            type="button" 
            className={`platform-toggle-btn youtube ${platformFilter === 'youtube' ? 'active' : ''}`}
            onClick={() => setPlatformFilter(platformFilter === 'youtube' ? 'all' : 'youtube')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
            YouTube Shorts
          </button>
          <button 
            type="button" 
            className={`platform-toggle-btn instagram ${platformFilter === 'instagram' ? 'active' : ''}`}
            onClick={() => setPlatformFilter(platformFilter === 'instagram' ? 'all' : 'instagram')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>
            Instagram Reels
          </button>
          
          <select className="select-input" value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ marginLeft: '6px' }}>
            <option value="all">All Statuses</option>
            <option value="published">Published</option>
            <option value="queued">Queued</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </header>

      <div className="data-table-container">
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
            {filteredPosts.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>
                  No posts found matching the filters.
                </td>
              </tr>
            ) : (
              filteredPosts.map((post) => (
                <tr key={post.id}>
                  <td><strong>{post.clip_title}</strong></td>
                  <td>
                    <span style={{ 
                      display: 'inline-flex', 
                      alignItems: 'center', 
                      gap: '6px', 
                      padding: '4px 10px', 
                      borderRadius: '12px', 
                      fontSize: '0.8rem', 
                      fontWeight: 600,
                      background: post.platform === 'youtube' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(217, 70, 239, 0.1)',
                      color: post.platform === 'youtube' ? '#ef4444' : '#d946ef',
                      border: `1px solid ${post.platform === 'youtube' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(217, 70, 239, 0.3)'}`
                    }}>
                      {post.platform === 'youtube' ? (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                      ) : (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>
                      )}
                      {post.platform === 'youtube' ? 'YouTube' : 'Instagram'}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{post.platform_post_id || 'Queued'}</td>
                  <td>{post.posted_at ? new Date(post.posted_at).toLocaleDateString() : '-'}</td>
                  <td>
                    <span className={`badge badge-${post.status}`}>
                      {post.status}
                    </span>
                  </td>
                  <td>
                    {post.latest_metrics && (post.latest_metrics.views > 0 || post.latest_metrics.likes > 0) ? (
                      <span>{post.latest_metrics.views} views / {post.latest_metrics.likes} likes</span>
                    ) : (
                      <span className="badge badge-pending">Syncing...</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
