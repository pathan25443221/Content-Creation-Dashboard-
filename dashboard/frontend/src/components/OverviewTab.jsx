import React from 'react';
import NumberFlow from '@number-flow/react';
import { motion } from 'motion/react';
import GeneratorForm from './GeneratorForm';

export default function OverviewTab({ overview, generatorProps, clips = [], posts = [] }) {
  const { videoInput, setVideoInput, handleGenerateSubmit, isGenerating } = generatorProps;

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Operator Overview</h1>
        <p className="page-subtitle">Track your content pipeline generation, review queue, and performance at a glance.</p>
      </header>

      <div className="stats-grid">
        <motion.div 
          className="stat-card glass-panel"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, delay: 0.05 }}
        >
          <div className="stat-label">Total Clips Generated</div>
          <div className="stat-value">
            <NumberFlow value={overview.total_clips || 0} />
          </div>
          <div className="stat-trend trend-up">+{overview.recent_posts_count || 12} this week</div>
        </motion.div>

        <motion.div 
          className="stat-card glass-panel"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, delay: 0.1 }}
        >
          <div className="stat-label">Pending Review Queue</div>
          <div className="stat-value" style={{ color: 'var(--accent-blue)' }}>
            <NumberFlow value={overview.pending_review_count || 0} />
          </div>
          <div className="stat-trend trend-neutral">Action required</div>
        </motion.div>

        <motion.div 
          className="stat-card glass-panel"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, delay: 0.15 }}
        >
          <div className="stat-label">Published (Last 7 Days)</div>
          <div className="stat-value">
            <NumberFlow value={overview.recent_posts_count || 0} />
          </div>
          <div className="stat-trend trend-up">On track</div>
        </motion.div>

        <motion.div 
          className="stat-card glass-panel"
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2, delay: 0.2 }}
        >
          <div className="stat-label">Total Reach / Views</div>
          <div className="stat-value" style={{ color: 'var(--badge-posted)' }}>
            <NumberFlow value={overview.total_views || 0} />
          </div>
          <div className="stat-trend trend-up">+450 this week</div>
        </motion.div>
      </div>

      <div style={{ display: 'flex', gap: '24px', marginTop: '32px' }}>
        {/* Left Column: Quick Generate */}
        <motion.div 
          className="glass-panel" 
          style={{ flex: 2, padding: '24px', display: 'flex', flexDirection: 'column' }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.25 }}
        >
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
              className="url-input" 
              placeholder="https://youtube.com/watch?v=..." 
              value={videoInput}
              onChange={(e) => setVideoInput(e.target.value)}
              style={{ flex: 1 }}
              required
            />
            <button type="submit" className="btn-primary" disabled={isGenerating}>
              {isGenerating ? 'Processing...' : 'Generate Magic'}
            </button>
          </form>
        </motion.div>

        {/* Right Column: Recent Activity */}
        <motion.div 
          className="glass-panel" 
          style={{ flex: 1, padding: '24px' }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.3 }}
        >
          <h2 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Recent Activity</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {overview.recent_activity && overview.recent_activity.length > 0 ? (
              overview.recent_activity.map(act => (
                <div key={act.id} style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.9rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
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
        </motion.div>
      </div>

      {/* Bottom Panoramic Video Carousel Reel */}
      <motion.div 
        className="glass-panel panoramic-reel-section"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.35 }}
      >
        <div className="panoramic-reel-header">
          <div>
            <h2 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
              Generated Videos Reel
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
              Panoramic reel of generated shorts across your content pipeline. Hover over any video to preview.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              className="theme-btn" 
              onClick={() => {
                const track = document.getElementById('panoramicTrack');
                if (track) track.scrollBy({ left: -320, behavior: 'smooth' });
              }}
              title="Scroll left"
            >
              ◀
            </button>
            <button 
              className="theme-btn" 
              onClick={() => {
                const track = document.getElementById('panoramicTrack');
                if (track) track.scrollBy({ left: 320, behavior: 'smooth' });
              }}
              title="Scroll right"
            >
              ▶
            </button>
          </div>
        </div>

        <div 
          className="panoramic-reel-track" 
          id="panoramicTrack"
          onMouseDown={(e) => {
            const track = e.currentTarget;
            track.isMouseDown = true;
            track.startX = e.clientX;
            track.scrollStart = track.scrollLeft;
            track.dragVelocity = 0;
            track.lastClientX = e.clientX;
            track.lastTime = performance.now();
            track.style.cursor = 'grabbing';
            if (track.animFrameId) cancelAnimationFrame(track.animFrameId);
          }}
          onMouseMove={(e) => {
            const track = e.currentTarget;
            if (!track.isMouseDown) return;
            e.preventDefault();
            const now = performance.now();
            const dt = Math.max(1, now - (track.lastTime || now));
            const dx = e.clientX - track.lastClientX;
            
            // Calculate instant velocity
            const currentVel = (dx / dt) * 16; 
            track.dragVelocity = track.dragVelocity ? (track.dragVelocity * 0.3 + currentVel * 0.7) : currentVel;
            
            track.lastClientX = e.clientX;
            track.lastTime = now;
            
            const totalDx = e.clientX - track.startX;
            track.scrollLeft = track.scrollStart - totalDx * 1.5;
          }}
          onMouseUp={(e) => {
            const track = e.currentTarget;
            if (!track.isMouseDown) return;
            track.isMouseDown = false;
            track.style.cursor = 'grab';

            let velocity = (track.dragVelocity || 0) * 3.2;
            const animateMomentum = () => {
              if (Math.abs(velocity) > 0.1 && !track.isMouseDown) {
                track.scrollLeft -= velocity;
                velocity *= 0.985;
                track.animFrameId = requestAnimationFrame(animateMomentum);
              }
            };
            track.animFrameId = requestAnimationFrame(animateMomentum);
          }}
          onMouseLeave={(e) => {
            const track = e.currentTarget;
            if (track.isMouseDown) {
              track.isMouseDown = false;
              track.style.cursor = 'grab';
            }
          }}
          onWheel={(e) => {
            if (e.deltaY !== 0) {
              e.preventDefault();
              e.currentTarget.scrollBy({ left: e.deltaY * 2.5, behavior: 'smooth' });
            }
          }}
          style={{ cursor: 'grab' }}
        >
          {clips && clips.filter(c => c.status !== 'rejected').length > 0 ? (
            clips.filter(c => c.status !== 'rejected').map((clip, idx) => {
              // Match with published post in posts list
              const matchedPost = posts && posts.find(p => p.clip_id === clip.id || p.clip_title === clip.title);
              const ytId = clip.youtube_id || (clip.youtube_url && clip.youtube_url.includes('v=') ? clip.youtube_url.split('v=')[1]?.split('&')[0] : null) || (matchedPost ? matchedPost.platform_post_id : null);

              return (
                <motion.div 
                  key={clip.id || idx} 
                  className="panoramic-card"
                  whileHover={{ scale: 1.04 }}
                  transition={{ duration: 0.2 }}
                >
                  {ytId && ytId !== 'Queued' ? (
                    <iframe
                      src={`https://www.youtube.com/embed/${ytId}?autoplay=0&controls=0&mute=1`}
                      className="panoramic-video"
                      title={clip.title}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      style={{ border: 'none', pointerEvents: 'none', width: '100%', height: '100%' }}
                    />
                  ) : clip.media_url ? (
                    <video 
                      src={clip.media_url} 
                      className="panoramic-video"
                      preload="metadata"
                      muted
                      onMouseEnter={(e) => e.currentTarget.play().catch(() => {})}
                      onMouseLeave={(e) => {
                        e.currentTarget.pause();
                        e.currentTarget.currentTime = 0;
                      }}
                    />
                  ) : (
                    <div style={{ width: '100%', height: '100%', background: 'linear-gradient(135deg, oklch(0.25 0.05 270), oklch(0.18 0.04 250))', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', padding: '16px', textAlign: 'center', gap: '8px' }}>
                      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" strokeWidth="2"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
                      <span>{clip.status === 'approved' || clip.status === 'published' ? 'Uploaded Video' : 'Processing Video'}</span>
                    </div>
                  )}

                  <div className="panoramic-card-overlay">
                    <div className="panoramic-card-title">{clip.title || `Clip #${clip.id}`}</div>
                    <div className="panoramic-card-meta">
                      <span>{clip.status || 'pending'}</span>
                      <span>★ {clip.virality_score || '8.5'}</span>
                    </div>
                  </div>
                </motion.div>
              );
            })
          ) : (
            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)', width: '100%', fontStyle: 'italic' }}>
              No videos generated yet. Use Quick Generate to produce your first clip reel!
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
