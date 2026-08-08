import React from 'react';

export default function GeneratorForm({
  videoInput,
  setVideoInput,
  videoType,
  setVideoType,
  quantity,
  setQuantity,
  quality,
  setQuality,
  burnCaptions,
  setBurnCaptions,
  captionColor,
  setCaptionColor,
  captionAnimation,
  setCaptionAnimation,
  isGenerating,
  handleGenerateSubmit,
  genMessage
}) {
  return (
    <div className="card-box">
      <h3 style={{ marginBottom: '16px', color: '#0f172a' }}>Generate New AI Clip</h3>
      <form onSubmit={handleGenerateSubmit}>

        <div className="input-group" style={{ marginBottom: '24px', width: '100%', display: 'flex', alignItems: 'center' }}>
          <div style={{ position: 'relative', width: '100%', display: 'flex', alignItems: 'center' }}>
            <span style={{
              position: 'absolute',
              left: '14px',
              display: 'flex',
              alignItems: 'center',
              pointerEvents: 'none',
              zIndex: 2
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
            </span>
            <input
              type="text"
              className="url-input"
              style={{ width: '100%', paddingLeft: '44px', paddingRight: '16px' }}
              placeholder="Enter YouTube / Twitch URL..."
              value={videoInput}
              onChange={(e) => setVideoInput(e.target.value)}
            />
          </div>
        </div>

        <div style={{ marginBottom: '32px' }}>
          <h4 style={{ color: 'var(--text-main)', marginBottom: '16px' }}>AI Styles</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px' }}>
            <div 
              className={`style-card glass-panel ${videoType === 'speech' ? 'active' : ''}`} 
              onClick={() => setVideoType('speech')}
            >
              <img src="/Assets/Podcast_mic.png" alt="Podcast" />
              <div className="style-card-title">Podcast</div>
              <div className="style-card-desc">Ideal for conversations</div>
            </div>

            <div 
              className={`style-card glass-panel ${videoType === 'center' ? 'active' : ''}`} 
              onClick={() => setVideoType('center')}
            >
              <img src="/Assets/Center focus.png" alt="Center" />
              <div className="style-card-title">Center Focus</div>
              <div className="style-card-desc">Keeps speaker centered</div>
            </div>

            <div 
              className={`style-card glass-panel ${videoType === 'visual' ? 'active' : ''}`} 
              onClick={() => setVideoType('visual')}
            >
              <img src="/Assets/Gaming_controller.png" alt="Gaming" />
              <div className="style-card-title">Gaming</div>
              <div className="style-card-desc">Highlights action scenes</div>
            </div>

            <div 
              className={`style-card glass-panel ${videoType === 'vlog' ? 'active' : ''}`} 
              onClick={() => setVideoType('vlog')}
            >
              <img src="/Assets/Vlog_logo.png" alt="Vlog" />
              <div className="style-card-title">Vlog</div>
              <div className="style-card-desc">Dynamic camera angles</div>
            </div>

            <div 
              className={`style-card glass-panel ${videoType === 'visual_split' ? 'active' : ''}`} 
              onClick={() => setVideoType('visual_split')}
            >
              <img src="/Assets/ChatGPT Image Aug 1, 2026, 01_39_02 PM.png" alt="Split Screen" />
              <div className="style-card-title">Faszy (Split)</div>
              <div className="style-card-desc">Split screen gameplay</div>
            </div>
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.4)', borderRadius: '24px', padding: '24px', marginBottom: '32px' }}>
          <h4 style={{ color: '#0f172a', marginBottom: '20px', fontSize: '1.2rem', fontWeight: 800 }}>Render Settings</h4>
          <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <label style={{ fontSize: '0.9rem', marginBottom: '8px', color: '#0f172a', fontWeight: 700 }}>Quantity</label>
              <input
                type="number"
                className="select-input"
                style={{ width: '100px' }}
                min="1" max="10"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value))}
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <label style={{ fontSize: '0.9rem', marginBottom: '8px', color: '#0f172a', fontWeight: 700 }}>Quality</label>
              <select
                className="select-input"
                value={quality}
                onChange={(e) => setQuality(e.target.value)}
              >
                <option value="high">High (4K/1080p)</option>
                <option value="medium">Medium (1080p)</option>
                <option value="low">Low (720p)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', marginTop: '28px', background: 'rgba(255,255,255,0.7)', padding: '12px 20px', borderRadius: '16px' }}>
              <input
                type="checkbox"
                id="burnCaptionsGenerator"
                checked={burnCaptions}
                onChange={(e) => setBurnCaptions(e.target.checked)}
                style={{ marginRight: '12px', width: '20px', height: '20px', cursor: 'pointer' }}
              />
              <label htmlFor="burnCaptionsGenerator" style={{ fontSize: '1rem', color: '#0f172a', fontWeight: 700, cursor: 'pointer' }}>
                Enable Captions
              </label>
            </div>
          </div>

          {burnCaptions && (
            <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap', marginTop: '24px', paddingTop: '24px', borderTop: '2px dashed rgba(255,255,255,0.6)' }}>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label style={{ fontSize: '0.9rem', marginBottom: '8px', color: '#0f172a', fontWeight: 700 }}>Caption Color</label>
                <select className="select-input" value={captionColor} onChange={(e) => setCaptionColor(e.target.value)}>
                  <option value="white">⚪ White</option>
                  <option value="yellow">🟡 Yellow</option>
                  <option value="green">🟢 Green</option>
                  <option value="cyan">🔵 Cyan</option>
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <label style={{ fontSize: '0.9rem', marginBottom: '8px', color: '#0f172a', fontWeight: 700 }}>Caption Animation</label>
                <select className="select-input" value={captionAnimation} onChange={(e) => setCaptionAnimation(e.target.value)}>
                  <option value="none">Standard</option>
                  <option value="pop">🔥 Pop (TikTok Style)</option>
                  <option value="fade">✨ Fade In</option>
                </select>
              </div>
            </div>
          )}
        </div>

        <button type="submit" className="btn-primary" disabled={isGenerating} style={{ width: '100%' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          {isGenerating ? 'Processing...' : 'Generate Clips'}
        </button>
      </form>
      {genMessage && <p style={{ marginTop: '12px', fontSize: '0.85rem', color: '#475569', textAlign: 'center' }}>{genMessage}</p>}
    </div>
  );
}
