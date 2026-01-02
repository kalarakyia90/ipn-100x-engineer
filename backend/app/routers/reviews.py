"""
Reviews API endpoints.

Provides CRUD operations for restaurant reviews with
aggregated statistics.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..database import get_db
from ..models import ReviewCreate, ReviewResponse, ReviewsWithStats, ReviewStats

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("", response_model=ReviewsWithStats)
def get_reviews(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Minimum rating"),
    sort_by: Optional[str] = Query(
        "created_at",
        regex="^(created_at|rating)$",
        description="Sort field"
    ),
    order: Optional[str] = Query(
        "desc",
        regex="^(asc|desc)$",
        description="Sort order"
    ),
):
    """
    Get reviews with optional filtering, sorting, and aggregated stats.

    Returns both the list of reviews and statistics (average rating, count).
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Build reviews query
        query = "SELECT * FROM reviews WHERE 1=1"
        params: list = []

        if restaurant_id:
            query += " AND restaurant_id = ?"
            params.append(restaurant_id)

        if min_rating:
            query += " AND rating >= ?"
            params.append(min_rating)

        query += f" ORDER BY {sort_by} {order.upper()}"

        cursor.execute(query, params)
        reviews = [dict(row) for row in cursor.fetchall()]

        # Calculate stats (respecting restaurant filter)
        stats_query = """
            SELECT AVG(rating) as avg_rating, COUNT(*) as total_reviews
            FROM reviews
        """
        stats_params: list = []

        if restaurant_id:
            stats_query += " WHERE restaurant_id = ?"
            stats_params.append(restaurant_id)

        cursor.execute(stats_query, stats_params)
        stats_row = cursor.fetchone()

        stats = ReviewStats(
            avg_rating=(
                round(stats_row["avg_rating"], 2)
                if stats_row["avg_rating"]
                else None
            ),
            total_reviews=stats_row["total_reviews"],
        )

        return ReviewsWithStats(reviews=reviews, stats=stats)


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int):
    """Get a specific review by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Review not found")

        return dict(row)


@router.post("", response_model=ReviewResponse, status_code=201)
def create_review(review: ReviewCreate):
    """
    Create a new review.

    Returns the created review with generated ID and timestamp.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO reviews
            (restaurant_id, reviewer_name, reviewer_email, rating,
             title, comment, visit_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review.restaurant_id,
                review.reviewer_name,
                review.reviewer_email,
                review.rating,
                review.title,
                review.comment,
                review.visit_date,
            ),
        )

        review_id = cursor.lastrowid

        # Fetch and return the created review
        cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        return dict(cursor.fetchone())


@router.delete("/{review_id}", status_code=204)
def delete_review(review_id: int):
    """Delete a review permanently."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Review not found")

        cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
