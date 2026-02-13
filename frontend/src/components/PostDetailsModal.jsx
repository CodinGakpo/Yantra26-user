import React, { useState, useEffect, useRef } from 'react';
import { X, Send, ThumbsUp, ThumbsDown, User, Loader2 } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL;

function PostDetailsModal({ post, onClose }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [loadingComments, setLoadingComments] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  
  // Local state for social interactions
  const [likes, setLikes] = useState(post.likes_count || 0);
  const [dislikes, setDislikes] = useState(post.dislikes_count || 0);
  const [isLiked, setIsLiked] = useState(post.is_liked || false);
  const [isDisliked, setIsDisliked] = useState(post.is_disliked || false);

  const [images, setImages] = useState({ before: null, after: null });
  const commentSectionRef = useRef(null);

  // Fetch Images
  useEffect(() => {
    async function fetchImages() {
      try {
        const res = await fetch(`${API_BASE}/api/reports/${post.id}/presign-get/`);
        const data = await res.json();
        setImages({ before: data.before, after: data.after });
      } catch (err) {
        console.error("Failed to load images", err);
      }
    }
    fetchImages();
  }, [post.id]);

  // Fetch Comments
  const fetchComments = async () => {
    try {
      const token = localStorage.getItem('accessToken'); 
      // Allow viewing comments without token, but headers logic handles it
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      const res = await fetch(`${API_BASE}/api/reports/${post.id}/comments/`, { headers });
      if (res.ok) {
        const data = await res.json();
        setComments(data);
      }
    } catch (err) {
      console.error("Failed to fetch comments", err);
    } finally {
      setLoadingComments(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [post.id]);

  // Handle Interactions
  const handleInteraction = async (type) => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
      alert("Please login to interact with posts!");
      return;
    }

    // Optimistic Update
    if (type === 'like') {
      if (isLiked) {
        setLikes(p => p - 1); setIsLiked(false);
      } else {
        setLikes(p => p + 1); setIsLiked(true);
        if (isDisliked) { setDislikes(p => p - 1); setIsDisliked(false); }
      }
    } else {
      if (isDisliked) {
        setDislikes(p => p - 1); setIsDisliked(false);
      } else {
        setDislikes(p => p + 1); setIsDisliked(true);
        if (isLiked) { setLikes(p => p - 1); setIsLiked(false); }
      }
    }

    try {
      const res = await fetch(`${API_BASE}/api/reports/${post.id}/${type}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!res.ok) throw new Error("Action failed");
      
      const data = await res.json();
      // Sync with server source of truth
      setLikes(data.likes_count);
      setDislikes(data.dislikes_count);
    } catch (err) {
      console.error(err);
      // Revert interaction on error would go here
    }
  };

  // Submit Comment
  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('accessToken');
    if (!token) return alert("Please login to comment!");
    if (!newComment.trim()) return;

    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/reports/${post.id}/comments/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: newComment })
      });

      if (res.ok) {
        const comment = await res.json();
        setComments([...comments, comment]);
        setNewComment("");
        // Scroll to bottom
        setTimeout(() => {
            if(commentSectionRef.current) {
                commentSectionRef.current.scrollTop = commentSectionRef.current.scrollHeight;
            }
        }, 100);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-6xl h-[85vh] rounded-2xl overflow-hidden flex flex-col md:flex-row shadow-2xl relative">
        
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 bg-black/50 hover:bg-black/70 text-white rounded-full transition-colors md:hidden"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Left Side: Images & Details */}
        <div className="md:w-3/5 bg-gray-100 flex flex-col overflow-y-auto">
          {/* Images */}
          <div className="grid grid-cols-2 gap-1 p-1 flex-shrink-0 min-h-[300px]">
            <div className="relative group bg-gray-200 aspect-square">
              {images.before ? (
                <img src={images.before} className="w-full h-full object-cover" alt="Before" />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">No Image</div>
              )}
              <div className="absolute top-2 left-2 bg-black/60 text-white text-xs px-2 py-1 rounded">Before</div>
            </div>
            <div className="relative group bg-gray-200 aspect-square">
              {images.after ? (
                <img src={images.after} className="w-full h-full object-cover" alt="After" />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">No Image</div>
              )}
              <div className="absolute top-2 left-2 bg-emerald-600 text-white text-xs px-2 py-1 rounded">After</div>
            </div>
          </div>

          {/* Details */}
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{post.issue_title}</h2>
            <p className="text-gray-600 leading-relaxed mb-4">{post.issue_description}</p>
            
            <div className="flex gap-4 text-sm text-gray-500">
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-medium">
                {post.department}
              </span>
              <span className="flex items-center gap-1">
                📍 {post.location}
              </span>
            </div>
          </div>
        </div>

        {/* Right Side: Social Panel */}
        <div className="md:w-2/5 flex flex-col bg-white border-l border-gray-200">
          {/* Header */}
          <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-white">
            <h3 className="font-bold text-gray-800">Comments</h3>
            <button onClick={onClose} className="hidden md:block p-2 hover:bg-gray-100 rounded-full">
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Comments List */}
          <div 
            className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
            ref={commentSectionRef}
          >
            {loadingComments ? (
              <div className="flex justify-center py-10">
                <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
              </div>
            ) : comments.length === 0 ? (
              <div className="text-center py-10 text-gray-400">
                <p>No comments yet. Be the first!</p>
              </div>
            ) : (
              comments.map((comment) => (
                <div key={comment.id} className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                    <span className="font-bold text-emerald-700 text-xs">
                        {comment.username ? comment.username[0].toUpperCase() : 'U'}
                    </span>
                  </div>
                  <div className="bg-white p-3 rounded-tr-xl rounded-br-xl rounded-bl-xl shadow-sm border border-gray-100 max-w-[85%]">
                    <div className="flex items-baseline gap-2 mb-1">
                      <span className="font-bold text-xs text-gray-900">{comment.username || 'User'}</span>
                      <span className="text-[10px] text-gray-400">
                        {new Date(comment.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 leading-snug">{comment.text}</p>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Actions Bar */}
          <div className="p-4 bg-white border-t border-gray-100">
            <div className="flex items-center gap-6 mb-4">
              <button 
                onClick={() => handleInteraction('like')}
                className={`flex items-center gap-2 transition-colors ${isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'}`}
              >
                <ThumbsUp className={`w-6 h-6 ${isLiked ? 'fill-current' : ''}`} />
                <span className="font-medium">{likes}</span>
              </button>

              <button 
                onClick={() => handleInteraction('dislike')}
                className={`flex items-center gap-2 transition-colors ${isDisliked ? 'text-gray-900' : 'text-gray-500 hover:text-gray-900'}`}
              >
                <ThumbsDown className={`w-6 h-6 ${isDisliked ? 'fill-current' : ''}`} />
                <span className="font-medium">{dislikes}</span>
              </button>
            </div>

            {/* Comment Input */}
            <form onSubmit={handleCommentSubmit} className="relative">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write a comment..."
                className="w-full pl-4 pr-12 py-3 bg-gray-100 rounded-full focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm"
              />
              <button 
                type="submit" 
                disabled={submitting || !newComment.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-emerald-600 hover:bg-emerald-100 rounded-full disabled:opacity-50"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PostDetailsModal;