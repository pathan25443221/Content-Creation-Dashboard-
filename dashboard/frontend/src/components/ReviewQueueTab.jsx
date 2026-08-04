import React, { useState } from 'react';

function ReviewCard({ clip, idx, handleApprove, handleReject }) {
  const initialTitle = clip.title ? (clip.hashtags ? `${clip.title} ${clip.hashtags}` : clip.title) : '';
  const [title, setTitle] = useState(initialTitle);
  const [description, setDescription] = useState(clip.description || '');

  const [publishToYT, setPublishToYT] = useState(true);
  const [publishToIG, setPublishToIG] = useState(true);

  return (
    <div className="vizard-card glass-panel">
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
          <h2 className="vizard-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%' }}>
            <span className="vizard-num">#{idx + 1}</span>
            <input 
              type="text" 
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="form-input"
              style={{ flex: 1, fontSize: '1.2rem', padding: '4px 8px' }}
              placeholder="Post Title..."
            />
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
              onClick={() => {
                const platforms = [];
                if (publishToYT) platforms.push('youtube');
                if (publishToIG) platforms.push('instagram');
                handleApprove(clip.id, title, description, '', platforms);
              }}
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

        {/* Editable Metadata Fields */}
        <div className="vizard-reason-card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div>
            <div className="vizard-reason-label" style={{ marginBottom: '4px' }}>Description</div>
            <textarea 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="form-input"
              style={{ width: '100%', minHeight: '60px', resize: 'vertical' }}
              placeholder="YouTube / Instagram Description..."
            />
          </div>
          <div style={{ marginTop: '5px' }}>
            <div className="vizard-reason-label" style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>Platforms</div>
            <div style={{ display: 'flex', gap: '16px', marginTop: '6px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem', color: '#0f172a', fontWeight: '600' }}>
                <input type="checkbox" checked={publishToYT} onChange={(e) => setPublishToYT(e.target.checked)} style={{ width: '16px', height: '16px', accentColor: 'var(--accent-blue)' }} />
                YouTube Shorts
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.85rem', color: '#0f172a', fontWeight: '600' }}>
                <input type="checkbox" checked={publishToIG} onChange={(e) => setPublishToIG(e.target.checked)} style={{ width: '16px', height: '16px', accentColor: 'var(--accent-purple)' }} />
                Instagram Reels
              </label>
            </div>
          </div>
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
  );
}

export default function ReviewQueueTab({ clips, handleApprove, handleReject }) {
  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Review Queue</h1>
        <p className="page-subtitle">Review candidate clips selected by local AI models before publishing.</p>
      </header>

      {clips.length === 0 ? (
        <div className="card-box glass-panel" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          No candidate clips awaiting review. Use "Generate Clip" to process a new video!
        </div>
      ) : (
        <div className="vizard-review-list">
          {clips.map((clip, idx) => (
            <ReviewCard 
              key={clip.id} 
              clip={clip} 
              idx={idx} 
              handleApprove={handleApprove} 
              handleReject={handleReject} 
            />
          ))}
        </div>
      )}
    </div>
  );
}
