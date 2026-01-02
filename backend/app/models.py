"""
Pydantic models for request/response validation.

Separates Create (input) models from Response (output) models
to control what data is accepted vs returned.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class ReservationStatus(str, Enum):
    """Valid status values for reservations."""
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


# =============================================================================
# Reservation Models
# =============================================================================

class ReservationCreate(BaseModel):
    """Input model for creating a reservation."""
    restaurant_id: str
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    party_size: int = Field(..., ge=1, le=20)
    reservation_date: str  # YYYY-MM-DD format
    reservation_time: str  # HH:MM format
    notes: Optional[str] = None


class ReservationUpdate(BaseModel):
    """Input model for updating a reservation. All fields optional."""
    customer_name: Optional[str] = Field(None, min_length=1, max_length=100)
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    party_size: Optional[int] = Field(None, ge=1, le=20)
    reservation_date: Optional[str] = None
    reservation_time: Optional[str] = None
    status: Optional[ReservationStatus] = None
    notes: Optional[str] = None


class ReservationResponse(BaseModel):
    """Output model for reservation data."""
    id: int
    restaurant_id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str]
    party_size: int
    reservation_date: str
    reservation_time: str
    status: str
    notes: Optional[str]
    created_at: str
    updated_at: str


# =============================================================================
# Review Models
# =============================================================================

class ReviewCreate(BaseModel):
    """Input model for creating a review."""
    restaurant_id: str
    reviewer_name: str = Field(..., min_length=1, max_length=100)
    reviewer_email: Optional[EmailStr] = None
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    comment: Optional[str] = None
    visit_date: Optional[str] = None  # YYYY-MM-DD format


class ReviewResponse(BaseModel):
    """Output model for review data."""
    id: int
    restaurant_id: str
    reviewer_name: str
    reviewer_email: Optional[str]
    rating: int
    title: Optional[str]
    comment: Optional[str]
    visit_date: Optional[str]
    created_at: str


class ReviewStats(BaseModel):
    """Aggregated review statistics."""
    avg_rating: Optional[float]
    total_reviews: int


class ReviewsWithStats(BaseModel):
    """Reviews list with aggregated stats."""
    reviews: list[ReviewResponse]
    stats: ReviewStats
