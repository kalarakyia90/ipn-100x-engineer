# FastAPI Backend: Reservations & Reviews

This document covers setting up a FastAPI backend with SQLite for reservations and reviews, connecting to the Next.js frontend.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Setup](#project-setup)
3. [Database Models](#database-models)
4. [API Endpoints](#api-endpoints)
5. [Running the Backend](#running-the-backend)
6. [Connecting Next.js Frontend](#connecting-nextjs-frontend)
7. [Quick Start](#quick-start)

---

## Architecture Overview

```text
┌─────────────────────┐     HTTP      ┌─────────────────────┐
│   Next.js Frontend  │ ◄──────────► │   FastAPI Backend   │
│   localhost:3000    │    (JSON)     │   localhost:8000    │
└─────────────────────┘               └──────────┬──────────┘
                                                 │
                                                 ▼
                                      ┌─────────────────────┐
                                      │   SQLite Database   │
                                      │   restaurant.db     │
                                      └─────────────────────┘
```

---

## Project Setup

### 1. Create Backend Directory

```bash
mkdir -p backend
cd backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

Create `backend/requirements.txt`:

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
python-multipart==0.0.20
```

Install:

```bash
pip install -r requirements.txt
```

### 4. Project Structure

```text
backend/
├── venv/
├── data/
│   └── restaurant.db        # SQLite database (auto-created)
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # Database connection
│   ├── models.py            # Pydantic models
│   └── routers/
│       ├── __init__.py
│       ├── reservations.py  # Reservations endpoints
│       └── reviews.py       # Reviews endpoints
├── requirements.txt
└── init_db.py               # Database initialization script
```

---

## Database Models

### `backend/app/database.py`

```python
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "restaurant.db"

def get_db_connection():
    """Create a database connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize database tables."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Reservations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                customer_phone TEXT,
                party_size INTEGER NOT NULL,
                reservation_date TEXT NOT NULL,
                reservation_time TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id TEXT NOT NULL,
                reviewer_name TEXT NOT NULL,
                reviewer_email TEXT,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                title TEXT,
                comment TEXT,
                visit_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservations_restaurant ON reservations(restaurant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservations_date ON reservations(reservation_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_restaurant ON reviews(restaurant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating)")

        print("Database initialized successfully!")
```

### `backend/app/models.py`

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum

class ReservationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"

# Reservation Models
class ReservationCreate(BaseModel):
    restaurant_id: str
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    party_size: int = Field(..., ge=1, le=20)
    reservation_date: str  # YYYY-MM-DD format
    reservation_time: str  # HH:MM format
    notes: Optional[str] = None

class ReservationUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    party_size: Optional[int] = Field(None, ge=1, le=20)
    reservation_date: Optional[str] = None
    reservation_time: Optional[str] = None
    status: Optional[ReservationStatus] = None
    notes: Optional[str] = None

class ReservationResponse(BaseModel):
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

# Review Models
class ReviewCreate(BaseModel):
    restaurant_id: str
    reviewer_name: str = Field(..., min_length=1, max_length=100)
    reviewer_email: Optional[EmailStr] = None
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    comment: Optional[str] = None
    visit_date: Optional[str] = None  # YYYY-MM-DD format

class ReviewResponse(BaseModel):
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
    avg_rating: Optional[float]
    total_reviews: int

class ReviewsWithStats(BaseModel):
    reviews: list[ReviewResponse]
    stats: ReviewStats
```

---

## API Endpoints

### `backend/app/routers/reservations.py`

```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..database import get_db
from ..models import ReservationCreate, ReservationUpdate, ReservationResponse

router = APIRouter(prefix="/api/reservations", tags=["reservations"])

@router.get("", response_model=list[ReservationResponse])
def get_reservations(
    restaurant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get reservations, optionally filtered by restaurant and/or status."""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM reservations WHERE 1=1"
        params = []

        if restaurant_id:
            query += " AND restaurant_id = ?"
            params.append(restaurant_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY reservation_date, reservation_time"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(reservation_id: int):
    """Get a specific reservation by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Reservation not found")

        return dict(row)

@router.post("", response_model=ReservationResponse, status_code=201)
def create_reservation(reservation: ReservationCreate):
    """Create a new reservation."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reservations
            (restaurant_id, customer_name, customer_email, customer_phone,
             party_size, reservation_date, reservation_time, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reservation.restaurant_id,
            reservation.customer_name,
            reservation.customer_email,
            reservation.customer_phone,
            reservation.party_size,
            reservation.reservation_date,
            reservation.reservation_time,
            reservation.notes
        ))

        reservation_id = cursor.lastrowid

        cursor.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
        return dict(cursor.fetchone())

@router.patch("/{reservation_id}", response_model=ReservationResponse)
def update_reservation(reservation_id: int, update: ReservationUpdate):
    """Update a reservation."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if reservation exists
        cursor.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Reservation not found")

        # Build update query dynamically
        update_data = update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(reservation_id)

        cursor.execute(
            f"UPDATE reservations SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values
        )

        cursor.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
        return dict(cursor.fetchone())

@router.delete("/{reservation_id}", status_code=204)
def delete_reservation(reservation_id: int):
    """Delete a reservation."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reservations WHERE id = ?", (reservation_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Reservation not found")

        cursor.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
```

### `backend/app/routers/reviews.py`

```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..database import get_db
from ..models import ReviewCreate, ReviewResponse, ReviewsWithStats, ReviewStats

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

@router.get("", response_model=ReviewsWithStats)
def get_reviews(
    restaurant_id: Optional[str] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    sort_by: Optional[str] = Query("created_at", regex="^(created_at|rating)$"),
    order: Optional[str] = Query("desc", regex="^(asc|desc)$")
):
    """Get reviews with optional filtering and sorting."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM reviews WHERE 1=1"
        params = []

        if restaurant_id:
            query += " AND restaurant_id = ?"
            params.append(restaurant_id)

        if min_rating:
            query += " AND rating >= ?"
            params.append(min_rating)

        query += f" ORDER BY {sort_by} {order.upper()}"

        cursor.execute(query, params)
        reviews = [dict(row) for row in cursor.fetchall()]

        # Calculate stats
        stats_query = "SELECT AVG(rating) as avg_rating, COUNT(*) as total_reviews FROM reviews"
        stats_params = []

        if restaurant_id:
            stats_query += " WHERE restaurant_id = ?"
            stats_params.append(restaurant_id)

        cursor.execute(stats_query, stats_params)
        stats_row = cursor.fetchone()

        stats = ReviewStats(
            avg_rating=round(stats_row["avg_rating"], 2) if stats_row["avg_rating"] else None,
            total_reviews=stats_row["total_reviews"]
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
    """Create a new review."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO reviews
            (restaurant_id, reviewer_name, reviewer_email, rating, title, comment, visit_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            review.restaurant_id,
            review.reviewer_name,
            review.reviewer_email,
            review.rating,
            review.title,
            review.comment,
            review.visit_date
        ))

        review_id = cursor.lastrowid

        cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        return dict(cursor.fetchone())

@router.delete("/{review_id}", status_code=204)
def delete_review(review_id: int):
    """Delete a review."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reviews WHERE id = ?", (review_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Review not found")

        cursor.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
```

### `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_database
from .routers import reservations, reviews

# Initialize FastAPI app
app = FastAPI(
    title="Restaurant Finder API",
    description="API for restaurant reservations and reviews",
    version="1.0.0"
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reservations.router)
app.include_router(reviews.router)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "restaurant-api"}

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_database()

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Restaurant Finder API",
        "docs": "/docs",
        "health": "/health"
    }
```

### `backend/app/routers/__init__.py`

```python
from . import reservations, reviews
```

### `backend/app/__init__.py`

```python
# Package marker
```

---

## Running the Backend

### Start the Server

From the `backend` directory:

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run with auto-reload (development)
uvicorn app.main:app --reload --port 8000

# Run for production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, access:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Create a reservation
curl -X POST http://localhost:8000/api/reservations \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "rest-001",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "party_size": 4,
    "reservation_date": "2024-12-25",
    "reservation_time": "19:00"
  }'

# Get all reservations
curl http://localhost:8000/api/reservations

# Create a review
curl -X POST http://localhost:8000/api/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "rest-001",
    "reviewer_name": "Jane Doe",
    "rating": 5,
    "title": "Amazing food!",
    "comment": "Best Italian in the city"
  }'

# Get reviews with stats
curl "http://localhost:8000/api/reviews?restaurant_id=rest-001"
```

---

## Connecting Next.js Frontend

### 1. Create API Client

Create `lib/api.ts` in the Next.js project:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Reservation {
  id: number;
  restaurant_id: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  party_size: number;
  reservation_date: string;
  reservation_time: string;
  status: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface Review {
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

interface ReviewsResponse {
  reviews: Review[];
  stats: {
    avg_rating: number | null;
    total_reviews: number;
  };
}

// Reservations API
export async function getReservations(restaurantId?: string): Promise<Reservation[]> {
  const url = new URL(`${API_BASE_URL}/api/reservations`);
  if (restaurantId) url.searchParams.set('restaurant_id', restaurantId);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error('Failed to fetch reservations');
  return res.json();
}

export async function createReservation(data: Omit<Reservation, 'id' | 'status' | 'created_at' | 'updated_at'>): Promise<Reservation> {
  const res = await fetch(`${API_BASE_URL}/api/reservations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      restaurant_id: data.restaurant_id,
      customer_name: data.customer_name,
      customer_email: data.customer_email,
      customer_phone: data.customer_phone,
      party_size: data.party_size,
      reservation_date: data.reservation_date,
      reservation_time: data.reservation_time,
      notes: data.notes,
    }),
  });

  if (!res.ok) throw new Error('Failed to create reservation');
  return res.json();
}

export async function updateReservation(id: number, data: Partial<Reservation>): Promise<Reservation> {
  const res = await fetch(`${API_BASE_URL}/api/reservations/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) throw new Error('Failed to update reservation');
  return res.json();
}

export async function cancelReservation(id: number): Promise<Reservation> {
  return updateReservation(id, { status: 'cancelled' });
}

// Reviews API
export async function getReviews(restaurantId?: string): Promise<ReviewsResponse> {
  const url = new URL(`${API_BASE_URL}/api/reviews`);
  if (restaurantId) url.searchParams.set('restaurant_id', restaurantId);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error('Failed to fetch reviews');
  return res.json();
}

export async function createReview(data: Omit<Review, 'id' | 'created_at'>): Promise<Review> {
  const res = await fetch(`${API_BASE_URL}/api/reviews`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      restaurant_id: data.restaurant_id,
      reviewer_name: data.reviewer_name,
      reviewer_email: data.reviewer_email,
      rating: data.rating,
      title: data.title,
      comment: data.comment,
      visit_date: data.visit_date,
    }),
  });

  if (!res.ok) throw new Error('Failed to create review');
  return res.json();
}
```

### 2. Add Environment Variable

Create or update `.env.local` in the Next.js project:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Example Component Usage

```tsx
'use client';

import { useState, useEffect } from 'react';
import { getReviews, createReview, type ReviewsResponse } from '@/lib/api';

export function RestaurantReviews({ restaurantId }: { restaurantId: string }) {
  const [data, setData] = useState<ReviewsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getReviews(restaurantId)
      .then(setData)
      .finally(() => setLoading(false));
  }, [restaurantId]);

  if (loading) return <div>Loading reviews...</div>;
  if (!data) return <div>Failed to load reviews</div>;

  return (
    <div>
      <h2>Reviews ({data.stats.total_reviews})</h2>
      {data.stats.avg_rating && (
        <p>Average Rating: {data.stats.avg_rating.toFixed(1)} / 5</p>
      )}
      <ul>
        {data.reviews.map((review) => (
          <li key={review.id}>
            <strong>{review.reviewer_name}</strong> - {review.rating}/5
            {review.title && <h4>{review.title}</h4>}
            {review.comment && <p>{review.comment}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Quick Start

### Terminal 1: FastAPI Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Next.js Frontend

```bash
npm run dev
```

### Verify Connection

1. Open http://localhost:8000/docs - FastAPI Swagger UI
2. Open http://localhost:3000 - Next.js app
3. Test API from Next.js:
   - Create a reservation via Swagger UI
   - Fetch it from Next.js using the API client

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [SQLite Python Documentation](https://docs.python.org/3/library/sqlite3.html)
- [Next.js Data Fetching](https://nextjs.org/docs/app/building-your-application/data-fetching)
