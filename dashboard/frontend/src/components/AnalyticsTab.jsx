import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

export default function AnalyticsTab({ overview, fetchOverview, posts, fetchPosts }) {
  // Sort posts by views descending for the leaderboard
  const topPosts = useMemo(() => {
    if (!posts) return [];
    return [...posts]
      .filter(p => p.latest_metrics)
      .sort((a, b) => b.latest_metrics.views - a.latest_metrics.views)
      .slice(0, 5);
  }, [posts]);

  // Format data for the chart (taking top 10 for chart readability)
  const chartData = useMemo(() => {
    if (!posts) return [];
    return [...posts]
      .filter(p => p.latest_metrics)
      .sort((a, b) => new Date(a.posted_at) - new Date(b.posted_at))
      .map(p => ({
        name: p.clip_title.substring(0, 15) + '...',
        views: p.latest_metrics.views,
        platform: p.platform
      }));
  }, [posts]);

  return (
    <div>
      <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 className="page-title">Clip Performance Analytics</h1>
          <p className="page-subtitle">Simulated historical performance data (mocked due to missing API keys).</p>
        </div>
        <button 
          className="btn-primary"
          style={{ padding: '10px 20px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))', color: 'white', border: 'none', boxShadow: '0 4px 15px rgba(139, 92, 246, 0.3)' }}
          onClick={async () => {
            const btn = document.getElementById('syncBtn');
            btn.innerText = 'Syncing...';
            await fetch('/api/poll', { method: 'POST' });
            await fetchOverview();
            if (fetchPosts) await fetchPosts();
            btn.innerText = 'Sync Latest Metrics';
          }}
          id="syncBtn"
        >
          Sync Latest Metrics
        </button>
      </header>

      <div className="stats-grid">
        <div className="stat-card glass-panel" style={{ background: 'linear-gradient(135deg, #ffffff 0%, #f8faff 100%)', border: '1px solid rgba(255,255,255,1)', boxShadow: '0 10px 25px rgba(0,0,0,0.05)' }}>
          <div className="stat-label" style={{ color: '#64748b', fontWeight: '600' }}>Total Views</div>
          <div className="stat-value" style={{ color: 'var(--accent-blue)', fontSize: '2.2rem', letterSpacing: '-1px' }}>{(overview.total_views || 0).toLocaleString()}</div>
        </div>
        <div className="stat-card glass-panel" style={{ background: 'linear-gradient(135deg, #ffffff 0%, #fcf8ff 100%)', border: '1px solid rgba(255,255,255,1)', boxShadow: '0 10px 25px rgba(0,0,0,0.05)' }}>
          <div className="stat-label" style={{ color: '#64748b', fontWeight: '600' }}>Total Likes</div>
          <div className="stat-value" style={{ color: 'var(--accent-purple)', fontSize: '2.2rem', letterSpacing: '-1px' }}>{(overview.total_likes || 0).toLocaleString()}</div>
        </div>
        <div className="stat-card glass-panel" style={{ background: 'linear-gradient(135deg, #ffffff 0%, #f0fdfa 100%)', border: '1px solid rgba(255,255,255,1)', boxShadow: '0 10px 25px rgba(0,0,0,0.05)' }}>
          <div className="stat-label" style={{ color: '#64748b', fontWeight: '600' }}>Total Comments</div>
          <div className="stat-value" style={{ color: '#0d9488', fontSize: '2.2rem', letterSpacing: '-1px' }}>{(overview.total_comments || 0).toLocaleString()}</div>
        </div>
      </div>

      <div className="grid-2col" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px', marginTop: '32px' }}>
        
        {/* Main Chart Section */}
        <div className="card-box glass-panel" style={{ background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(255,255,255,0.9)' }}>
          <h3 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a', fontWeight: '800' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', background: 'var(--accent-blue)' }}></span>
            Views Over Time
          </h3>
          
          {chartData.length > 0 ? (
            <div style={{ width: '100%', height: 350 }}>
              <ResponsiveContainer>
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" vertical={false} />
                  <XAxis dataKey="name" stroke="#64748b" tick={{fill: '#475569', fontSize: '0.85rem', fontWeight: 500}} axisLine={{stroke: 'rgba(0,0,0,0.1)'}} tickLine={false} />
                  <YAxis stroke="#64748b" tick={{fill: '#475569', fontSize: '0.85rem', fontWeight: 500}} axisLine={false} tickLine={false} />
                  <Tooltip 
                    cursor={{fill: 'rgba(0,0,0,0.03)'}}
                    contentStyle={{ backgroundColor: '#ffffff', border: 'none', borderRadius: '12px', color: '#0f172a', boxShadow: '0 10px 25px rgba(0,0,0,0.1)', fontWeight: '600' }}
                    itemStyle={{ color: 'var(--accent-blue)' }}
                  />
                  <Bar dataKey="views" radius={[6, 6, 0, 0]} maxBarSize={60}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.platform === 'youtube' ? '#ef4444' : 'var(--accent-blue)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontWeight: '500' }}>
              No data available yet. Publish some clips!
            </div>
          )}
        </div>

        {/* Top Performing Clips Leaderboard */}
        <div className="card-box glass-panel" style={{ background: 'rgba(255,255,255,0.7)', border: '1px solid rgba(255,255,255,0.9)' }}>
          <h3 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a', fontWeight: '800' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', background: 'var(--accent-purple)' }}></span>
            Top Performing Clips
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {topPosts.length > 0 ? topPosts.map((p, idx) => (
              <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '16px', background: 'rgba(255,255,255,0.9)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(0,0,0,0.03)', boxShadow: '0 4px 10px rgba(0,0,0,0.02)', transition: 'transform 0.2s', cursor: 'pointer' }} onMouseOver={e => e.currentTarget.style.transform = 'translateX(4px)'} onMouseOut={e => e.currentTarget.style.transform = 'translateX(0)'}>
                <div style={{ fontSize: '1.4rem', fontWeight: '900', color: idx === 0 ? 'var(--accent-purple)' : '#cbd5e1', width: '24px', textAlign: 'center' }}>
                  {idx + 1}
                </div>
                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <div style={{ fontWeight: '700', color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontSize: '0.95rem' }}>
                    {p.clip_title}
                  </div>
                  <div style={{ display: 'flex', gap: '16px', marginTop: '6px', fontSize: '0.8rem', color: '#64748b', fontWeight: '600' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                      {p.latest_metrics.views.toLocaleString()}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" strokeWidth="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                      {p.latest_metrics.likes.toLocaleString()}
                    </span>
                  </div>
                </div>
                <div style={{
                  background: p.platform === 'youtube' ? '#fef2f2' : '#eff6ff',
                  color: p.platform === 'youtube' ? '#ef4444' : '#3b82f6',
                  padding: '6px 10px',
                  borderRadius: '8px',
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  fontWeight: '800',
                  boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.05)'
                }}>
                  {p.platform === 'youtube' ? 'YT' : 'IG'}
                </div>
              </div>
            )) : (
               <div style={{ color: '#64748b', textAlign: 'center', padding: '30px 0', fontWeight: '500' }}>
                 No posts available.
               </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
