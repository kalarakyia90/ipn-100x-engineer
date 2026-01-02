export type ReservationStatus = 'pending' | 'confirmed' | 'cancelled';

export interface Reservation {
  id: number;
  restaurant_id: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  party_size: number;
  reservation_date: string;
  reservation_time: string;
  status: ReservationStatus;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ReservationCreate {
  restaurant_id: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  party_size: number;
  reservation_date: string;
  reservation_time: string;
  notes?: string;
}

export interface ReservationUpdate {
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
  party_size?: number;
  reservation_date?: string;
  reservation_time?: string;
  status?: ReservationStatus;
  notes?: string;
}
