import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ProgressOverlay from './components/ProgressOverlay';
import OverviewTab from './components/OverviewTab';
import GenerateTab from './components/GenerateTab';
import ReviewQueueTab from './components/ReviewQueueTab';
import PostsLibraryTab from './components/PostsLibraryTab';
import AnalyticsTab from './components/AnalyticsTab';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState({
    total_clips: 0,
    pending_review_count: 0,
    recent_posts_count: 0,
    total_views: 0,
    total_likes: 0,
    recent_activity: []
  });

  const [clips, setClips] = useState([]);
  const [posts, setPosts] = useState([]);
  const [videoInput, setVideoInput] = useState('');
  const [videoType, setVideoType] = useState('speech');
  const [burnCaptions, setBurnCaptions] = useState(true);
  const [captionColor, setCaptionColor] = useState('white');
  const [captionAnimation, setCaptionAnimation] = useState('none');
  const [quantity, setQuantity] = useState(3);
  const [quality, setQuality] = useState('high');
  const [isGenerating, setIsGenerating] = useState(false);
  const [genMessage, setGenMessage] = useState('');
  const [progressMsg, setProgressMsg] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Connect to SSE stream
  useEffect(() => {
    const sse = new EventSource('/api/stream');
    sse.onmessage = (event) => {
      if (event.data === 'update') {
        setRefreshTrigger(prev => prev + 1);
      } else if (event.data.startsWith('progress:')) {
        const msg = event.data.substring(9);
        if (msg === 'done') {
            setProgressMsg(null);
            setIsGenerating(false);
            setGenMessage('Generation complete! Check Review tab.');
        } else if (msg.startsWith('Error:')) {
            setProgressMsg(null);
            setIsGenerating(false);
            setGenMessage(msg);
        } else {
            setProgressMsg(msg);
            setIsGenerating(true);
        }
      }
    };
    return () => sse.close();
  }, []);

  // Fetch overview data
  const fetchOverview = async () => {
    try {
      const res = await fetch('/api/overview');
      if (res.ok) {
        const data = await res.json();
        setOverview(data);
      }
    } catch (e) {
      console.error("Failed to fetch overview:", e);
    }
  };

  // Fetch clips
  const fetchClips = async (status = '') => {
    try {
      const url = status ? `/api/clips?status=${status}` : '/api/clips';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setClips(data);
      }
    } catch (e) {
      console.error("Failed to fetch clips:", e);
    }
  };

  // Fetch posts
  const fetchPosts = async () => {
    try {
      const res = await fetch('/api/posts');
      if (res.ok) {
        const data = await res.json();
        setPosts(data);
      }
    } catch (e) {
      console.error("Failed to fetch posts:", e);
    }
  };

  useEffect(() => {
    fetchOverview();
    if (activeTab === 'review') fetchClips('pending');
    if (activeTab === 'posts') fetchPosts();
    if (activeTab === 'clips') fetchClips();
  }, [activeTab, refreshTrigger]);

  const handleGenerateSubmit = async (e) => {
    e.preventDefault();
    if (!videoInput) return;

    setIsGenerating(true);
    setGenMessage('🚀 Generation started in background! Downloading, transcribing with Whisper, & selecting clips via Ollama...');

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          video_input: videoInput, 
          video_type: videoType, 
          burn_captions: burnCaptions,
          quantity: quantity,
          quality: quality,
          caption_color: captionColor,
          caption_animation: captionAnimation
        })
      });

      const data = await res.json();
      if (res.ok || res.status === 202) {
        setGenMessage('⚡ Processing active in background! Clips will automatically land in the Review Queue when rendered.');
        setVideoInput('');
        setProgressMsg("Initializing...");
        setIsGenerating(true);
      } else {
        setGenMessage(`Error: ${data.detail || 'Generation failed'}`);
        setIsGenerating(false);
      }
    } catch (err) {
      setGenMessage(`Network Error: ${err.message}`);
      setIsGenerating(false);
    }
  };

  const handleApprove = async (clipId, customTitle) => {
    try {
      const res = await fetch(`/api/clips/${clipId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: customTitle, platforms: ['youtube', 'instagram'] })
      });
      if (res.ok) {
        fetchClips('pending');
        fetchOverview();
      }
    } catch (e) {
      console.error("Approve failed:", e);
    }
  };

  const handleReject = async (clipId) => {
    try {
      const res = await fetch(`/api/clips/${clipId}/reject`, {
        method: 'POST'
      });
      if (res.ok) {
        fetchClips('pending');
        fetchOverview();
      }
    } catch (e) {
      console.error("Reject failed:", e);
    }
  };

  const generatorProps = {
    videoInput, setVideoInput,
    videoType, setVideoType,
    quantity, setQuantity,
    quality, setQuality,
    burnCaptions, setBurnCaptions,
    captionColor, setCaptionColor,
    captionAnimation, setCaptionAnimation,
    isGenerating, handleGenerateSubmit, genMessage
  };

  return (
    <div className="app-container">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        pendingReviewCount={overview.pending_review_count} 
      />

      <ProgressOverlay progressMsg={progressMsg} />

      <main className="main-content">
        {activeTab === 'overview' && (
          <OverviewTab overview={overview} generatorProps={generatorProps} />
        )}

        {activeTab === 'generate' && (
          <GenerateTab generatorProps={generatorProps} />
        )}

        {activeTab === 'review' && (
          <ReviewQueueTab 
            clips={clips} 
            handleApprove={handleApprove} 
            handleReject={handleReject} 
          />
        )}

        {activeTab === 'posts' && (
          <PostsLibraryTab posts={posts} />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsTab overview={overview} fetchOverview={fetchOverview} />
        )}
      </main>
    </div>
  );
}
