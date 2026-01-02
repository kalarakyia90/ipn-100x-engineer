"""
Reservations API endpoints.

Provides CRUD operations for restaurant reservations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..database import get_db
from ..models import ReservationCreate, ReservationUpdate, ReservationResponse

router = APIRouter(prefix="/api/reservations", tags=["reservations"])


@router.get("", response_model=list[ReservationResponse])
def get_reservations(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    Get all reservations with optional filtering.

    - **restaurant_id**: Filter to specific restaurant
    - **status**: Filter by pending/confirmed/cancelled
    """
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM reservations WHERE 1=1"
        params: list = []

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
        cursor.execute(
            "SELECT * FROM reservations WHERE id = ?",
            (reservation_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Reservation not found")

        return dict(row)


@router.post("", response_model=ReservationResponse, status_code=201)
def create_reservation(reservation: ReservationCreate):
    """
    Create a new reservation.

    Returns the created reservation with generated ID and timestamps.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO reservations
            (restaurant_id, customer_name, customer_email, customer_phone,
             party_size, reservation_date, reservation_time, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reservation.restaurant_id,
                reservation.customer_name,
                reservation.customer_email,
                reservation.customer_phone,
                reservation.party_size,
                reservation.reservation_date,
                reservation.reservation_time,
                reservation.notes,
            ),
        )

        reservation_id = cursor.lastrowid

        # Fetch and return the created reservation
        cursor.execute(
            "SELECT * FROM reservations WHERE id = ?",
            (reservation_id,)
        )
        return dict(cursor.fetchone())


@router.patch("/{reservation_id}", response_model=ReservationResponse)
def update_reservation(reservation_id: int, update: ReservationUpdate):
    """
    Update a reservation.

    Only provided fields are updated; others remain unchanged.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check if reservation exists
        cursor.execute(
            "SELECT * FROM reservations WHERE id = ?",
            (reservation_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Reservation not found")

        # Build update query from provided fields only
        update_data = update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Convert enum to string if present
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value

        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(reservation_id)

        cursor.execute(
            f"UPDATE reservations SET {set_clause}, updated_at = CURRENT_TIMESTAMP "
            f"WHERE id = ?",
            values,
        )

        # Return updated reservation
        cursor.execute(
            "SELECT * FROM reservations WHERE id = ?",
            (reservation_id,)
        )
        return dict(cursor.fetchone())


@router.delete("/{reservation_id}", status_code=204)
def delete_reservation(reservation_id: int):
    """Delete a reservation permanently."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM reservations WHERE id = ?",
            (reservation_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Reservation not found")

        cursor.execute(
            "DELETE FROM reservations WHERE id = ?",
            (reservation_id,)
        )
