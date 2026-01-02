'use client';

import { useState, useEffect } from 'react';
import { getReviews } from '@/lib/api';
import { Review, ReviewStats } from '@/types/review';

interface ReviewsListProps {
  restaurantId: string;
  refreshTrigger?: number; // Increment to trigger refresh
}

export default function ReviewsList({
  restaurantId,
  refreshTrigger = 0,
}: ReviewsListProps) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'created_at' | 'rating'>('created_at');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  useEffect(() => {
    const fetchReviews = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await getReviews(restaurantId, {
          sortBy,
          order: sortOrder,
        });
        setReviews(data.reviews);
        setStats(data.stats);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reviews');
      } finally {
        setLoading(false);
      }
    };

    fetchReviews();
  }, [restaurantId, sortBy, sortOrder, refreshTrigger]);

  const renderStars = (rating: number) => {
    return (
      <span className="text-yellow-400">
        {'★'.repeat(rating)}
        {'☆'.repeat(5 - rating)}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-6 bg-gray-200 rounded w-1/4" />
        <div className="h-24 bg-gray-200 rounded" />
        <div className="h-24 bg-gray-200 rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Summary */}
      {stats && stats.total_reviews > 0 && (
        <div className="flex items-center gap-4 pb-4 border-b">
          <div className="text-4xl font-bold text-gray-900">
            {stats.avg_rating?.toFixed(1) || '—'}
          </div>
          <div>
            <div className="text-xl">{renderStars(Math.round(stats.avg_rating || 0))}</div>
            <div className="text-sm text-gray-500">
              {stats.total_reviews} {stats.total_reviews === 1 ? 'review' : 'reviews'}
            </div>
          </div>
        </div>
      )}

      {/* Sort Controls */}
      {reviews.length > 1 && (
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-600">Sort by:</span>
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [newSortBy, newOrder] = e.target.value.split('-') as [
                'created_at' | 'rating',
                'desc' | 'asc'
              ];
              setSortBy(newSortBy);
              setSortOrder(newOrder);
            }}
            className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="created_at-desc">Most Recent</option>
            <option value="created_at-asc">Oldest First</option>
            <option value="rating-desc">Highest Rated</option>
            <option value="rating-asc">Lowest Rated</option>
          </select>
        </div>
      )}

      {/* Reviews List */}
      {reviews.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">📝</div>
          <p>No reviews yet. Be the first to share your experience!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div
              key={review.id}
              className="bg-gray-50 rounded-lg p-4 border border-gray-100"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="font-medium text-gray-900">
                    {review.reviewer_name}
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(review.created_at)}
                    {review.visit_date && (
                      <span> · Visited {formatDate(review.visit_date)}</span>
                    )}
                  </div>
                </div>
                <div className="text-lg">{renderStars(review.rating)}</div>
              </div>

              {review.title && (
                <h4 className="font-medium text-gray-900 mb-1">{review.title}</h4>
              )}

              {review.comment && (
                <p className="text-gray-700 whitespace-pre-wrap">{review.comment}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
