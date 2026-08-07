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

        <div className="input-group" style={{ marginBottom: '24px', gap: 0 }}>
          <span style={{
            background: 'rgba(255,255,255,0.6)',
            padding: '16px 12px 16px 24px',
            borderRadius: '20px 0 0 20px',
            border: '1px solid rgba(255,255,255,0.8)',
            borderRight: 'none',
            display: 'flex',
            alignItems: 'center'
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
          </span>
          <input
            type="text"
            className="url-input"
            style={{ borderRadius: '0 20px 20px 0', borderLeft: 'none', paddingLeft: '8px', boxShadow: 'none' }}
            placeholder="Enter YouTube/Twitch URL..."
            value={videoInput}
            onChange={(e) => setVideoInput(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: '32px' }}>
          <h4 style={{ color: '#0f172a', marginBottom: '16px' }}>AI Styles</h4>
          <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <div className="nav-item" style={{ width: '200px', padding: '24px', background: videoType === 'speech' ? 'rgba(255,255,255,0.8)' : 'transparent' }} onClick={() => setVideoType('speech')}>
              <img src="/Assets/Podcast_mic.png" alt="Podcast" style={{ width: '150px', height: '150px', objectFit: 'contain' }} />
              <span style={{ fontSize: '1.1rem', marginTop: '12px', fontWeight: 800 }}>Podcast</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'center' }}>Ideal for conversations</span>
            </div>
            <div className="nav-item" style={{ width: '200px', padding: '24px', background: videoType === 'center' ? 'rgba(255,255,255,0.8)' : 'transparent' }} onClick={() => setVideoType('center')}>
              <img src="/Assets/Center focus.png" alt="Center" style={{ width: '150px', height: '150px', objectFit: 'contain' }} />
              <span style={{ fontSize: '1.1rem', marginTop: '12px', fontWeight: 800 }}>Center Focus</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'center' }}>Keeps speaker centered</span>
            </div>
            <div className="nav-item" style={{ width: '200px', padding: '24px', background: videoType === 'visual' ? 'rgba(255,255,255,0.8)' : 'transparent' }} onClick={() => setVideoType('visual')}>
              <img src="/Assets/Gaming_controller.png" alt="Gaming" style={{ width: '150px', height: '150px', objectFit: 'contain' }} />
              <span style={{ fontSize: '1.1rem', marginTop: '12px', fontWeight: 800 }}>Gaming</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'center' }}>Highlights action scenes</span>
            </div>
            <div className="nav-item" style={{ width: '200px', padding: '24px', background: videoType === 'vlog' ? 'rgba(255,255,255,0.8)' : 'transparent' }} onClick={() => setVideoType('vlog')}>
              <img src="/Assets/Vlog_logo.png" alt="Vlog" style={{ width: '150px', height: '150px', objectFit: 'contain' }} />
              <span style={{ fontSize: '1.1rem', marginTop: '12px', fontWeight: 800 }}>Vlog</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'center' }}>Dynamic camera angles</span>
            </div>
            <div className="nav-item" style={{ width: '200px', padding: '24px', background: videoType === 'visual_split' ? 'rgba(255,255,255,0.8)' : 'transparent' }} onClick={() => setVideoType('visual_split')}>
              <img src="/Assets/ChatGPT Image Aug 1, 2026, 01_39_02 PM.png" alt="Split Screen" style={{ width: '150px', height: '150px', objectFit: 'contain' }} />
              <span style={{ fontSize: '1.1rem', marginTop: '12px', fontWeight: 800 }}>Faszy (Split)</span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'center' }}>Split screen gameplay</span>
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

        <button type="submit" className="btn-primary" disabled={isGenerating} style={{ width: '100%', background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))', color: 'white', border: 'none', boxShadow: '0 4px 15px rgba(139, 92, 246, 0.3)' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path ></path></svg>
          {isGenerating ? 'Processing...' : '🪄Generate Clips'}
        </button>
      </form>
      {genMessage && <p style={{ marginTop: '12px', fontSize: '0.85rem', color: '#475569', textAlign: 'center' }}>{genMessage}</p>}
    </div>
  );
}
