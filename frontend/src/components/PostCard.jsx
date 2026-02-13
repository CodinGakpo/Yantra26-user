import { useState, useEffect } from "react";
import {
  Calendar,
  Building2,
  Image as ImageIcon,
  ImageOff,
  CheckCircle,
  X,
} from "lucide-react";

function PostCard({ post }) {
  const [previewImage, setPreviewImage] = useState(null);
  const [beforeImage, setBeforeImage] = useState(null);
  const [afterImage, setAfterImage] = useState(null);
  const [loadingImages, setLoadingImages] = useState(true);

  const API_BASE = import.meta.env.VITE_API_BASE_URL;

  useEffect(() => {
    async function fetchImages() {
      try {
        const res = await fetch(
          `${API_BASE}/api/reports/${post.id}/presign-get/`
        );
        const data = await res.json();
        setBeforeImage(data.before || null);
        setAfterImage(data.after || null);
      } catch (err) {
        console.error("Failed to load images:", err);
      } finally {
        setLoadingImages(false);
      }
    }

    fetchImages();
  }, [post.id]);

  return (
    <article className="bg-white border-2 border-gray-200 rounded-2xl overflow-hidden hover:border-emerald-300 hover:shadow-lg transition-all duration-300">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-emerald-50 to-green-50 px-6 md:px-8 py-6 border-b-2 border-gray-200">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h2 className="text-2xl md:text-3xl font-black text-gray-900 mb-2 break-words line-clamp-2">
              {post.issue_title}
            </h2>
            <p className="text-gray-700 leading-relaxed break-words line-clamp-3">
              {post.issue_description}
            </p>
          </div>
          <div className="flex-shrink-0">
            <div className="inline-flex items-center gap-2 bg-green-100 text-green-800 px-4 py-2 rounded-full border-2 border-green-300 font-bold text-sm">
              <CheckCircle className="w-4 h-4" />
              Resolved
            </div>
          </div>
        </div>
      </div>

      {/* Info Section */}
      <div className="px-6 md:px-8 py-5 bg-white border-b border-gray-200">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
          <div className="flex items-center gap-2 text-gray-700">
            <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Calendar className="w-4 h-4 text-emerald-600" />
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase">
                Reported
              </div>
              <div className="font-bold">
                {new Date(post.issue_date).toLocaleDateString("en-IN", {
                  day: "2-digit",
                  month: "short",
                  year: "numeric",
                })}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 text-gray-700">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <CheckCircle className="w-4 h-4 text-green-600" />
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-500 uppercase">
                Resolved
              </div>
              <div className="font-bold">
                {new Date(post.updated_at).toLocaleDateString("en-IN", {
                  day: "2-digit",
                  month: "short",
                  year: "numeric",
                })}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 text-gray-700">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Building2 className="w-4 h-4 text-blue-600" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-gray-500 uppercase">
                Department
              </div>
              <div className="font-bold truncate">{post.department}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Images Section */}
      <div className="px-6 md:px-8 py-6 bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <ImageBox
            title="Before"
            image={beforeImage}
            loading={loadingImages}
            onError={() => setBeforeImage(null)}
            onPreview={setPreviewImage}
            badgeColor="bg-red-100 text-red-700 border-red-300"
          />

          <ImageBox
            title="After"
            image={afterImage}
            loading={loadingImages}
            onError={() => setAfterImage(null)}
            onPreview={setPreviewImage}
            badgeColor="bg-green-100 text-green-700 border-green-300"
          />
        </div>
      </div>

      {/* Image Preview Modal */}
      {previewImage && (
        <div
          className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setPreviewImage(null)}
        >
          <button
            onClick={() => setPreviewImage(null)}
            className="absolute top-4 right-4 w-12 h-12 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center text-white transition-all"
          >
            <X className="w-6 h-6" />
          </button>
          <div
            className="max-w-6xl max-h-[90vh] w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={previewImage}
              alt="Preview"
              className="w-full h-full object-contain rounded-xl"
            />
          </div>
        </div>
      )}
    </article>
  );
}

function ImageBox({ title, image, loading, onError, onPreview, badgeColor }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-gray-600" />
          <span className="font-bold text-gray-900">{title}</span>
        </div>
        <span
          className={`text-xs font-bold px-3 py-1 rounded-full border ${badgeColor}`}
        >
          {title}
        </span>
      </div>

      <div
        className={`border-2 border-gray-300 rounded-xl aspect-video w-full bg-white flex items-center justify-center overflow-hidden transition-all ${
          image ? "cursor-pointer hover:border-emerald-400 hover:shadow-md" : ""
        }`}
        onClick={() => image && onPreview(image)}
      >
        {loading ? (
          <div className="flex flex-col items-center text-gray-400">
            <div className="w-8 h-8 border-2 border-gray-300 border-t-emerald-600 rounded-full animate-spin mb-2"></div>
            <span className="text-xs font-medium">Loading...</span>
          </div>
        ) : image ? (
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover"
            onError={onError}
          />
        ) : (
          <div className="flex flex-col items-center text-gray-400">
            <ImageOff className="w-12 h-12 mb-2 opacity-30" />
            <span className="text-xs font-medium">Image unavailable</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default PostCard;