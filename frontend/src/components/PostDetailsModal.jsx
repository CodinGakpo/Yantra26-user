import React, { useState, useEffect, useRef } from 'react';
import { X, Send, ThumbsUp, ThumbsDown, MapPin, Building2, Calendar, User, Loader2, MessageCircle, ChevronLeft, ChevronRight } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL;

function PostDetailsModal({ post, onClose, onInteractionUpdate }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [loadingComments, setLoadingComments] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  
  // Local state for social interactions
  const [likes, setLikes] = useState(post.likes_count || 0);
  const [dislikes, setDislikes] = useState(post.dislikes_count || 0);
  const [isLiked, setIsLiked] = useState(post.is_liked || false);
  const [isDisliked, setIsDisliked] = useState(post.is_disliked || false);

  const [images, setImages] = useState({ before: null, after: null });
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const commentSectionRef = useRef(null);

  // Fetch current user info
  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) return;
        
        const res = await fetch(`${API_BASE}/api/users/me/`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.ok) {
          const userData = await res.json();
          setCurrentUser(userData);
        }
      } catch (err) {
        console.error("Failed to fetch current user:", err);
      }
    };
    
    fetchCurrentUser();
  }, []);

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

  // Handle Like Interaction
  const handleLike = async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
      alert("Please login to like posts!");
      return;
    }

    const prevLikes = likes;
    const prevDislikes = dislikes;
    const prevIsLiked = isLiked;
    const prevIsDisliked = isDisliked;

    // Optimistic update
    if (isLiked) {
      setLikes(p => p - 1);
      setIsLiked(false);
    } else {
      setLikes(p => p + 1);
      setIsLiked(true);
      // Remove dislike if exists
      if (isDisliked) {
        setDislikes(p => p - 1);
        setIsDisliked(false);
      }
    }

    try {
      const res = await fetch(`${API_BASE}/api/reports/${post.id}/like/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!res.ok) throw new Error("Like action failed");
      
      const data = await res.json();
      setLikes(data.likes_count);
      setDislikes(data.dislikes_count);
      
      // Notify parent for synchronization
      if (onInteractionUpdate) {
        onInteractionUpdate(post.id, data.likes_count, data.dislikes_count);
      }
      
    } catch (err) {
      console.error(err);
      setLikes(prevLikes);
      setDislikes(prevDislikes);
      setIsLiked(prevIsLiked);
      setIsDisliked(prevIsDisliked);
    }
  };

  // Handle Dislike Interaction
  const handleDislike = async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) {
      alert("Please login to interact with posts!");
      return;
    }

    const prevLikes = likes;
    const prevDislikes = dislikes;
    const prevIsLiked = isLiked;
    const prevIsDisliked = isDisliked;

    // Optimistic update
    if (isDisliked) {
      setDislikes(p => p - 1);
      setIsDisliked(false);
    } else {
      setDislikes(p => p + 1);
      setIsDisliked(true);
      // Remove like if exists
      if (isLiked) {
        setLikes(p => p - 1);
        setIsLiked(false);
      }
    }

    try {
      const res = await fetch(`${API_BASE}/api/reports/${post.id}/dislike/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!res.ok) throw new Error("Dislike action failed");
      
      const data = await res.json();
      setLikes(data.likes_count);
      setDislikes(data.dislikes_count);
      
      // Notify parent for synchronization
      if (onInteractionUpdate) {
        onInteractionUpdate(post.id, data.likes_count, data.dislikes_count);
      }
      
    } catch (err) {
      console.error(err);
      setLikes(prevLikes);
      setDislikes(prevDislikes);
      setIsLiked(prevIsLiked);
      setIsDisliked(prevIsDisliked);
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

  // Helper function to get user display name
  const getUserDisplayName = (user) => {
    if (!user) return 'Community Member';
    
    // Priority: full_name > first_name + last_name > username > email
    if (user.full_name && user.full_name.trim()) {
      return user.full_name.trim();
    }
    
    const firstName = user.first_name ? user.first_name.trim() : '';
    const lastName = user.last_name ? user.last_name.trim() : '';
    
    if (firstName || lastName) {
      return `${firstName} ${lastName}`.trim();
    }
    
    return user.username || user.email || 'Community Member';
  };

  // Helper function to get user initials
  const getUserInitials = (user) => {
    if (!user) return 'C';
    
    const displayName = getUserDisplayName(user);
    const nameParts = displayName.split(' ').filter(part => part.length > 0);
    
    if (nameParts.length >= 2) {
      return (nameParts[0][0] + nameParts[nameParts.length - 1][0]).toUpperCase();
    } else if (nameParts.length === 1) {
      return nameParts[0][0].toUpperCase();
    }
    
    return 'U';
  };

  const displayImages = [images.before, images.after].filter(Boolean);
  const currentImage = displayImages[currentImageIndex];
  const imageLabels = [];
  if (images.before) imageLabels.push('Before');
  if (images.after) imageLabels.push('After');

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-xl bg-black/40 animate-in fade-in duration-300"
      onClick={onClose}
    >
      <div 
        className="bg-white w-full max-w-7xl max-h-[96vh] rounded-3xl overflow-hidden flex flex-col md:flex-row shadow-2xl relative"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2.5 bg-white/90 hover:bg-white text-gray-700 hover:text-gray-900 rounded-full transition-all shadow-lg"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Left Side: Image Viewer - 60% width */}
        <div className="md:w-[60%] bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center relative min-h-[400px] md:min-h-0">
          {currentImage ? (
            <>
              <img 
                src={currentImage} 
                className="w-full h-full object-contain max-h-[96vh]" 
                alt={imageLabels[currentImageIndex] || "Issue"} 
              />
              
              {/* Image Label Badge */}
              <div className={`absolute top-4 left-4 px-4 py-2 rounded-full text-sm font-bold shadow-lg backdrop-blur-md ${
                imageLabels[currentImageIndex] === 'Before' 
                  ? 'bg-red-500/90 text-white' 
                  : 'bg-emerald-500/90 text-white'
              }`}>
                {imageLabels[currentImageIndex]}
              </div>

              {/* Image Navigation Dots */}
              {displayImages.length > 1 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-3">
                  {displayImages.map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => setCurrentImageIndex(idx)}
                      className={`h-2 rounded-full transition-all ${
                        idx === currentImageIndex 
                          ? 'bg-white w-8 shadow-lg' 
                          : 'bg-white/50 hover:bg-white/75 w-2'
                      }`}
                    />
                  ))}
                </div>
              )}

              {/* LARGER Arrow Navigation */}
              {displayImages.length > 1 && (
                <>
                  <button
                    onClick={() => setCurrentImageIndex((prev) => (prev - 1 + displayImages.length) % displayImages.length)}
                    className="absolute left-6 top-1/2 -translate-y-1/2 w-14 h-14 bg-white/90 hover:bg-white text-gray-800 rounded-full flex items-center justify-center backdrop-blur-md transition-all shadow-xl hover:shadow-2xl hover:scale-110"
                  >
                    <ChevronLeft className="w-8 h-8" />
                  </button>
                  <button
                    onClick={() => setCurrentImageIndex((prev) => (prev + 1) % displayImages.length)}
                    className="absolute right-6 top-1/2 -translate-y-1/2 w-14 h-14 bg-white/90 hover:bg-white text-gray-800 rounded-full flex items-center justify-center backdrop-blur-md transition-all shadow-xl hover:shadow-2xl hover:scale-110"
                  >
                    <ChevronRight className="w-8 h-8" />
                  </button>
                </>
              )}
            </>
          ) : (
            <div className="flex flex-col items-center justify-center text-gray-400 p-12">
              <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center mb-4">
                <Calendar className="w-10 h-10 text-gray-400" />
              </div>
              <p className="text-lg font-medium">No images available</p>
            </div>
          )}
        </div>

        {/* Right Side: Details & Interactions - 40% width */}
        <div className="md:w-[40%] flex flex-col bg-white">
          {/* Header with User Info */}
          <div className="p-5 border-b border-gray-100 flex items-center gap-3">
            <div className="w-11 h-11 bg-gradient-to-br from-emerald-400 to-green-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-md">
              <span className="text-white font-bold text-lg">
                {getUserInitials(post)}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-gray-900 truncate">
                {post.user_name || getUserDisplayName(post) || 'Community Member'}
              </h3>
              <p className="text-sm text-gray-500 flex items-center gap-1 truncate">
                <MapPin className="w-3 h-3 flex-shrink-0" />
                {post.location || 'Unknown location'}
              </p>
            </div>
          </div>

          {/* Post Details */}
          <div className="flex-1 overflow-y-auto">
            {/* Issue Information */}
            <div className="p-5 border-b border-gray-100">
              <h2 className="text-xl font-bold text-gray-900 mb-2 leading-tight">
                {post.issue_title}
              </h2>
              <p className="text-gray-700 leading-relaxed mb-4 text-sm">
                {post.issue_description}
              </p>
              
              {/* Metadata Chips */}
              <div className="flex flex-wrap gap-2">
                <div className="flex items-center gap-1.5 bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full text-xs font-semibold">
                  <Building2 className="w-3.5 h-3.5" />
                  {post.department}
                </div>
                <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-full text-xs font-semibold">
                  <Calendar className="w-3.5 h-3.5" />
                  Resolved {new Date(post.updated_at).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short"
                  })}
                </div>
              </div>
            </div>

            {/* Comments Section */}
            <div className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <MessageCircle className="w-5 h-5 text-gray-600" />
                <h3 className="font-bold text-gray-800">
                  Comments {comments.length > 0 && `(${comments.length})`}
                </h3>
              </div>

              <div 
                className="space-y-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar"
                ref={commentSectionRef}
              >
                {loadingComments ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
                  </div>
                ) : comments.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    <MessageCircle className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p className="text-sm">No comments yet. Be the first to comment!</p>
                  </div>
                ) : (
                  comments.map((comment) => {
                    const commentUserName = comment.full_name || 
                                           (comment.first_name && comment.last_name ? `${comment.first_name} ${comment.last_name}`.trim() : null) ||
                                           comment.username || 
                                           'Anonymous';
                    
                    const commentInitial = commentUserName[0].toUpperCase();
                    
                    return (
                      <div key={comment.id} className="flex gap-3 group">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-emerald-400 to-green-500 flex items-center justify-center flex-shrink-0 shadow-sm">
                          <span className="font-bold text-white text-xs">
                            {commentInitial}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="bg-gray-50 p-3 rounded-2xl rounded-tl-none group-hover:bg-gray-100 transition-colors">
                            <div className="flex items-baseline gap-2 mb-1">
                              <span className="font-bold text-sm text-gray-900 truncate">
                                {commentUserName}
                              </span>
                              <span className="text-[10px] text-gray-400 whitespace-nowrap">
                                {new Date(comment.created_at).toLocaleDateString("en-IN", {
                                  day: "numeric",
                                  month: "short"
                                })}
                              </span>
                            </div>
                            <p className="text-sm text-gray-700 leading-snug break-words">
                              {comment.text}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="p-5 bg-white border-t border-gray-100">
            {/* Like & Dislike Buttons */}
            <div className="flex items-center gap-6 mb-4 pb-4 border-b border-gray-100">
              {/* LIKE Button */}
              <button 
                onClick={handleLike}
                className="flex items-center gap-2 group transition-all"
              >
                <ThumbsUp 
                  className={`w-7 h-7 transition-all duration-300 ${
                    isLiked 
                      ? 'fill-emerald-600 text-emerald-600 scale-110' 
                      : 'text-gray-400 group-hover:text-emerald-500 group-hover:scale-110'
                  }`}
                />
                <span className={`font-bold text-lg transition-colors ${
                  isLiked ? 'text-emerald-600' : 'text-gray-700'
                }`}>
                  {likes}
                </span>
              </button>

              {/* DISLIKE Button */}
              <button 
                onClick={handleDislike}
                className="flex items-center gap-2 group transition-all"
              >
                <ThumbsDown 
                  className={`w-7 h-7 transition-all duration-300 ${
                    isDisliked 
                      ? 'fill-red-600 text-red-600 scale-110' 
                      : 'text-gray-400 group-hover:text-red-500 group-hover:scale-110'
                  }`}
                />
                <span className={`font-bold text-lg transition-colors ${
                  isDisliked ? 'text-red-600' : 'text-gray-700'
                }`}>
                  {dislikes}
                </span>
              </button>
            </div>

            {/* Comment Input */}
            <form onSubmit={handleCommentSubmit} className="relative">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment..."
                className="w-full pl-4 pr-12 py-3 bg-gray-50 rounded-full focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm border border-gray-200 transition-all"
              />
              <button 
                type="submit" 
                disabled={submitting || !newComment.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-emerald-600 hover:bg-emerald-50 rounded-full disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {submitting ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </form>
          </div>
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #cbd5e0;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #a0aec0;
        }
      `}</style>
    </div>
  );
}

export default PostDetailsModal;