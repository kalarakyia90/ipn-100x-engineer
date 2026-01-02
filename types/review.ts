export interface Review {
  id: number;
  restaurant_id: string;
  reviewer_name: string;
  reviewer_email?: string;
  rating: number;
  title?: string;
  comment?: string;
  visit_date?: string;
  created_at: string;
}

export interface ReviewCreate {
  restaurant_id: string;
  reviewer_name: string;
  reviewer_email?: string;
  rating: number;
  title?: string;
  comment?: string;
  visit_date?: string;
}

export interface ReviewStats {
  avg_rating: number | null;
  total_reviews: number;
}

export interface ReviewsResponse {
  reviews: Review[];
  stats: ReviewStats;
}
