import React from 'react';

export default function PostsLibraryTab({ posts }) {
  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Posts Library</h1>
        <p className="page-subtitle">All generated clips and their publishing status across connected social platforms.</p>
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
  );
}
