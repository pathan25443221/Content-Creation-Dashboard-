import React, { useState, useEffect, useRef } from 'react';

export default function Sidebar({ activeTab, setActiveTab, pendingReviewCount }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: '/Assets/Overview_logo.png' },
    { id: 'generate', label: 'Generate Clip', icon: '/Assets/Generate_clip_logo.png' },
    { id: 'review', label: `Review Queue (${pendingReviewCount})`, icon: '/Assets/Review_queue.png' },
    { id: 'posts', label: 'Posts / Library', icon: '/Assets/posts_library.png' },
    { id: 'analytics', label: 'Analytics', icon: '/Assets/Analytics.png' },
  ];

  const itemRefs = useRef([]);
  const [pillStyle, setPillStyle] = useState({ left: 0, width: 0 });

  useEffect(() => {
    const activeIdx = navItems.findIndex(item => item.id === activeTab);
    const activeEl = itemRefs.current[activeIdx];
    if (activeEl) {
      setPillStyle({
        left: activeEl.offsetLeft,
        width: activeEl.offsetWidth,
        top: activeEl.offsetTop,
        height: activeEl.offsetHeight
      });
    }
  }, [activeTab, pendingReviewCount]);

  const [currentTheme, setCurrentTheme] = useState(() => localStorage.getItem('app-theme') || 'midnight');

  const changeTheme = (theme) => {
    setCurrentTheme(theme);
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('app-theme', theme);
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', currentTheme);
  }, []);

  return (
    <header className="top-navbar glass-panel">
      {/* Brand Logo */}
      <div className="navbar-brand">
        <img src="/Assets/LOGO_Website.png" alt="ClipForge" />
      </div>

      {/* Horizontal Nav */}
      <nav className="navbar-nav">
        <span className="glide-pill" style={{ ...pillStyle }} />
        {navItems.map((item, idx) => (
          <button
            key={item.id}
            ref={el => (itemRefs.current[idx] = el)}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <img src={item.icon} alt={item.label} className="nav-icon" />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* OKLCH Theme Switcher */}
      <div className="navbar-theme-switcher">
        <button
          onClick={() => changeTheme('midnight')}
          className={`theme-btn ${currentTheme === 'midnight' ? 'active' : ''}`}
          title="Midnight Studio"
        >
          🌙
        </button>
        <button
          onClick={() => changeTheme('cyberpunk')}
          className={`theme-btn ${currentTheme === 'cyberpunk' ? 'active' : ''}`}
          title="Cyberpunk Obsidian"
        >
          🔥
        </button>
        <button
          onClick={() => changeTheme('nordic')}
          className={`theme-btn ${currentTheme === 'nordic' ? 'active' : ''}`}
          title="Nordic Frost"
        >
          ❄️
        </button>
      </div>
    </header>
  );
}
