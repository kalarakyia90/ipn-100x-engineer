/**
 * API client for FastAPI backend.
 *
 * Handles all communication with the reservations and reviews endpoints.
 * Uses the NEXT_PUBLIC_API_URL env var, defaulting to localhost:8000.
 */

import {
  Reservation,
  ReservationCreate,
  ReservationUpdate,
} from '@/types/reservation';
import { Review, ReviewCreate, ReviewsResponse } from '@/types/review';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling.
 */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// =============================================================================
// Reservations API
// =============================================================================

export async function getReservations(
  restaurantId?: string
): Promise<Reservation[]> {
  const params = new URLSearchParams();
  if (restaurantId) params.set('restaurant_id', restaurantId);

  const query = params.toString();
  return apiFetch<Reservation[]>(
    `/api/reservations${query ? `?${query}` : ''}`
  );
}

export async function getReservation(id: number): Promise<Reservation> {
  return apiFetch<Reservation>(`/api/reservations/${id}`);
}

export async function createReservation(
  data: ReservationCreate
): Promise<Reservation> {
  return apiFetch<Reservation>('/api/reservations', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateReservation(
  id: number,
  data: ReservationUpdate
): Promise<Reservation> {
  return apiFetch<Reservation>(`/api/reservations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function cancelReservation(id: number): Promise<Reservation> {
  return updateReservation(id, { status: 'cancelled' });
}

export async function deleteReservation(id: number): Promise<void> {
  return apiFetch<void>(`/api/reservations/${id}`, {
    method: 'DELETE',
  });
}

// =============================================================================
// Reviews API
// =============================================================================

export async function getReviews(
  restaurantId?: string,
  options?: { minRating?: number; sortBy?: 'created_at' | 'rating'; order?: 'asc' | 'desc' }
): Promise<ReviewsResponse> {
  const params = new URLSearchParams();

  if (restaurantId) params.set('restaurant_id', restaurantId);
  if (options?.minRating) params.set('min_rating', String(options.minRating));
  if (options?.sortBy) params.set('sort_by', options.sortBy);
  if (options?.order) params.set('order', options.order);

  const query = params.toString();
  return apiFetch<ReviewsResponse>(`/api/reviews${query ? `?${query}` : ''}`);
}

export async function getReview(id: number): Promise<Review> {
  return apiFetch<Review>(`/api/reviews/${id}`);
}

export async function createReview(data: ReviewCreate): Promise<Review> {
  return apiFetch<Review>('/api/reviews', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteReview(id: number): Promise<void> {
  return apiFetch<void>(`/api/reviews/${id}`, {
    method: 'DELETE',
  });
}
