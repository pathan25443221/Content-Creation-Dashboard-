import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';

function ReviewCard({ clip, idx, handleApprove, onRejectRequest }) {
  const initialTitle = clip.title ? (clip.hashtags ? `${clip.title} ${clip.hashtags}` : clip.title) : '';
  const [title, setTitle] = useState(initialTitle);
  const [description, setDescription] = useState(clip.description || '');

  const [publishToYT, setPublishToYT] = useState(true);
  const [publishToIG, setPublishToIG] = useState(true);
  
  const [isPublishing, setIsPublishing] = useState(false);

  const onPublishClick = async () => {
    const platforms = [];
    if (publishToYT) platforms.push('youtube');
    if (publishToIG) platforms.push('instagram');
    
    if (platforms.length === 0) {
      toast.error('Please select at least one platform to publish to.');
      return;
    }

    setIsPublishing(true);
    const result = await handleApprove(clip.id, title, description, '', platforms);
    if (result && !result.success) {
      toast.error(`Publishing Failed: ${result.message}`);
      setIsPublishing(false);
    } else {
      toast.success('Clip successfully approved and published!');
    }
  };

  return (
    <motion.div 
      className="vizard-card glass-panel"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.25, delay: idx * 0.05 }}
    >
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

      {/* Right Column: Details */}
      <div className="vizard-details-col">
        {/* Top Header Row with Title input & Action buttons */}
        <div className="vizard-header-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
          <div style={{ flex: 1 }}>
            <div className="vizard-reason-label" style={{ marginBottom: '4px', color: 'var(--text-muted)' }}>Clip Title</div>
            <input 
              type="text" 
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="form-input"
              style={{ width: '100%', fontSize: '1.05rem', fontWeight: 600 }}
              placeholder="Post Title..."
              disabled={isPublishing}
            />
          </div>

          <div className="vizard-action-group" style={{ paddingTop: '16px' }}>
            <button 
              className="vizard-btn-publish" 
              onClick={onPublishClick}
              disabled={isPublishing}
              style={{ opacity: isPublishing ? 0.7 : 1, cursor: isPublishing ? 'not-allowed' : 'pointer' }}
            >
              {isPublishing ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="spin-icon"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
              )}
              {isPublishing ? 'Publishing...' : 'Publish'}
            </button>
            <button 
              className="vizard-btn-reject"
              onClick={() => onRejectRequest(clip)}
              disabled={isPublishing}
              title="Reject clip"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
        </div>

        {/* Big Virality Score Banner */}
        <div className="vizard-score-actions-row" style={{ marginTop: '14px', marginBottom: '14px', padding: '12px 18px', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div className="vizard-virality-badge">
            <span className="vizard-score-val-hero">{clip.virality_score || 8.5}</span>
            <span className="vizard-score-lbl">AI Virality & Quality Score</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--badge-posted)', fontSize: '0.85rem', fontWeight: 600 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            High Retention Potential
          </div>
        </div>

        {/* Editable Metadata Fields */}
        <div className="vizard-reason-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <div className="vizard-reason-label" style={{ marginBottom: '6px', color: 'var(--text-muted)' }}>Description</div>
            <textarea 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="form-input"
              style={{ width: '100%', minHeight: '70px', resize: 'vertical' }}
              placeholder="YouTube / Instagram Description..."
            />
          </div>
          <div>
            <div className="vizard-reason-label" style={{ color: 'var(--text-muted)', marginBottom: '8px' }}>Target Platforms</div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                type="button"
                className={`platform-toggle-btn youtube ${publishToYT ? 'active' : ''}`}
                onClick={() => setPublishToYT(!publishToYT)}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                YouTube Shorts
              </button>
              <button 
                type="button"
                className={`platform-toggle-btn instagram ${publishToIG ? 'active' : ''}`}
                onClick={() => setPublishToIG(!publishToIG)}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>
                Instagram Reels
              </button>
            </div>
          </div>
        </div>

        {/* Transcript Preview */}
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
    </motion.div>
  );
}

export default function ReviewQueueTab({ clips, handleApprove, handleReject }) {
  const [pendingRejections, setPendingRejections] = useState({});

  const onRejectRequest = (clip) => {
    // Set a 3-second deferral timer
    const timerId = setTimeout(() => {
      handleReject(clip.id);
      setPendingRejections(prev => {
        const next = { ...prev };
        delete next[clip.id];
        return next;
      });
    }, 3000);

    setPendingRejections(prev => ({
      ...prev,
      [clip.id]: { clip, timerId }
    }));
  };

  const handleUndo = (clipId) => {
    const item = pendingRejections[clipId];
    if (item) {
      clearTimeout(item.timerId);
      setPendingRejections(prev => {
        const next = { ...prev };
        delete next[clipId];
        return next;
      });
      toast.info('Rejection undone');
    }
  };

  const visibleClips = clips.filter(c => !pendingRejections[c.id]);
  const activeRejectionList = Object.values(pendingRejections);

  return (
    <div>
      <header className="page-header">
        <h1 className="page-title">Review Queue</h1>
        <p className="page-subtitle">Review candidate clips selected by local AI models before publishing.</p>
      </header>

      {visibleClips.length === 0 ? (
        <div className="card-box glass-panel" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          No candidate clips awaiting review. Use "Generate Clip" to process a new video!
        </div>
      ) : (
        <div className="vizard-review-list">
          <AnimatePresence>
            {visibleClips.map((clip, idx) => (
              <ReviewCard 
                key={clip.id} 
                clip={clip} 
                idx={idx} 
                handleApprove={handleApprove} 
                onRejectRequest={onRejectRequest} 
              />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Kinetics UndoSnackbar */}
      {activeRejectionList.length > 0 && (
        <div className="snackbar-container">
          {activeRejectionList.map(({ clip }) => (
            <div key={clip.id} className="snackbar">
              <span>Clip #{clip.id} marked as rejected</span>
              <button className="snackbar-undo-btn" onClick={() => handleUndo(clip.id)}>
                Undo
              </button>
              <div className="snackbar-progress" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
