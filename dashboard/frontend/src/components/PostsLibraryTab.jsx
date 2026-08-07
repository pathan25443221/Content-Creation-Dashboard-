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
        <div style={{ display: 'flex', gap: '12px' }}>
          <select className="select-input" value={platformFilter} onChange={e => setPlatformFilter(e.target.value)}>
            <option value="all">All Platforms</option>
            <option value="youtube">YouTube</option>
            <option value="instagram">Instagram</option>
            <option value="tiktok">TikTok</option>
          </select>
          <select className="select-input" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="all">All Statuses</option>
            <option value="published">Published</option>
            <option value="queued">Queued</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </header>

      <div className="card-box glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
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
                  <td style={{ textTransform: 'capitalize' }}>{post.platform}</td>
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
