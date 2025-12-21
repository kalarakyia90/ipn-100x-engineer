# API Endpoints PRD: Reservations & Reviews with SQLite

This document outlines the plan for adding reservation booking and user reviews functionality using SQLite with **Next.js API routes**.

> **Alternative:** For a separate Python backend, see [fastapi-backend.md](./fastapi-backend.md)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Why SQLite?](#why-sqlite)
3. [Database Schema](#database-schema)
4. [Implementation Steps](#implementation-steps)
5. [File Structure](#file-structure)
6. [Deployment Considerations](#deployment-considerations)
7. [Estimated Effort](#estimated-effort)

---

## Executive Summary

Add reservation booking and user reviews functionality using SQLite as a lightweight, file-based database. **No Docker required** - SQLite runs as a single file in your project.

---

## Why SQLite?

| Advantage | Description |
|-----------|-------------|
| Zero Configuration | No server setup, no Docker, no external dependencies |
| File-Based | Database is a single `.db` file in your project |
| Fast | Up to 2000+ queries/second with proper indexing |
| Production-Ready | Used by major apps (WhatsApp, Firefox, many mobile apps) |
| Easy Backup | Just copy the `.db` file |

### Technical Approach

**Recommended Stack:**

- `better-sqlite3` - Fastest SQLite library for Node.js (synchronous API)
- **OR** `Prisma + SQLite` - If you prefer an ORM with migrations

---

## Database Schema

```sql
-- Reservations Table
CREATE TABLE reservations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  restaurant_id TEXT NOT NULL,
  customer_name TEXT NOT NULL,
  customer_email TEXT NOT NULL,
  customer_phone TEXT,
  party_size INTEGER NOT NULL,
  reservation_date DATE NOT NULL,
  reservation_time TEXT NOT NULL,
  status TEXT DEFAULT 'pending', -- pending, confirmed, cancelled
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Reviews Table
CREATE TABLE reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  restaurant_id TEXT NOT NULL,
  reviewer_name TEXT NOT NULL,
  reviewer_email TEXT,
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
  title TEXT,
  comment TEXT,
  visit_date DATE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_reservations_restaurant ON reservations(restaurant_id);
CREATE INDEX idx_reservations_date ON reservations(reservation_date);
CREATE INDEX idx_reviews_restaurant ON reviews(restaurant_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
```

---

## Implementation Steps

### Phase 1: Database Setup

1. **Install better-sqlite3**

   ```bash
   npm install better-sqlite3
   npm install -D @types/better-sqlite3
   ```

2. **Create database utility** (`lib/db.ts`)

   ```typescript
   import Database from 'better-sqlite3';
   import path from 'path';

   const dbPath = path.join(process.cwd(), 'data', 'restaurant-finder.db');
   const db = new Database(dbPath);

   // Enable WAL mode for better performance
   db.pragma('journal_mode = WAL');

   export default db;
   ```

3. **Create migration script** (`scripts/init-db.ts`)

   ```typescript
   import db from '../lib/db';

   const initSQL = `
     CREATE TABLE IF NOT EXISTS reservations (...);
     CREATE TABLE IF NOT EXISTS reviews (...);
   `;

   db.exec(initSQL);
   console.log('Database initialized!');
   ```

4. **Add to package.json**

   ```json
   {
     "scripts": {
       "db:init": "tsx scripts/init-db.ts",
       "db:reset": "rm -f data/restaurant-finder.db && npm run db:init"
     }
   }
   ```

### Phase 2: Reservations API

**`app/api/reservations/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server';
import db from '@/lib/db';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const restaurantId = searchParams.get('restaurantId');

  const stmt = db.prepare(`
    SELECT * FROM reservations
    WHERE restaurant_id = ?
    ORDER BY reservation_date, reservation_time
  `);

  const reservations = stmt.all(restaurantId);
  return NextResponse.json(reservations);
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  const stmt = db.prepare(`
    INSERT INTO reservations
    (restaurant_id, customer_name, customer_email, customer_phone,
     party_size, reservation_date, reservation_time, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const result = stmt.run(
    body.restaurantId,
    body.customerName,
    body.customerEmail,
    body.customerPhone,
    body.partySize,
    body.reservationDate,
    body.reservationTime,
    body.notes
  );

  return NextResponse.json({ id: result.lastInsertRowid }, { status: 201 });
}
```

### Phase 3: Reviews API

**`app/api/reviews/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server';
import db from '@/lib/db';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const restaurantId = searchParams.get('restaurantId');

  const stmt = db.prepare(`
    SELECT * FROM reviews
    WHERE restaurant_id = ?
    ORDER BY created_at DESC
  `);

  const reviews = stmt.all(restaurantId);

  // Calculate average rating
  const avgStmt = db.prepare(`
    SELECT AVG(rating) as avgRating, COUNT(*) as totalReviews
    FROM reviews WHERE restaurant_id = ?
  `);
  const stats = avgStmt.get(restaurantId);

  return NextResponse.json({ reviews, stats });
}

export async function POST(request: NextRequest) {
  const body = await request.json();

  const stmt = db.prepare(`
    INSERT INTO reviews
    (restaurant_id, reviewer_name, reviewer_email, rating, title, comment, visit_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);

  const result = stmt.run(
    body.restaurantId,
    body.reviewerName,
    body.reviewerEmail,
    body.rating,
    body.title,
    body.comment,
    body.visitDate
  );

  return NextResponse.json({ id: result.lastInsertRowid }, { status: 201 });
}
```

### Phase 4: UI Components

1. **ReservationForm Component**
   - Date/time picker
   - Party size selector
   - Contact information fields
   - Confirmation display

2. **ReviewForm Component**
   - Star rating selector
   - Text input for title/comment
   - Submit and validation

3. **ReviewsList Component**
   - Display reviews with ratings
   - Sort by date/rating
   - Pagination

4. **Restaurant Detail Page**
   - Integrate reservation form
   - Show reviews section
   - Display average rating

---

## File Structure

```text
├── data/
│   └── restaurant-finder.db      # SQLite database file
├── lib/
│   └── db.ts                     # Database connection
├── scripts/
│   └── init-db.ts                # Database initialization
├── app/
│   ├── api/
│   │   ├── reservations/
│   │   │   └── route.ts
│   │   └── reviews/
│   │       └── route.ts
│   └── restaurant/
│       └── [id]/
│           └── page.tsx          # Restaurant detail page
├── components/
│   ├── ReservationForm.tsx
│   ├── ReviewForm.tsx
│   └── ReviewsList.tsx
└── types/
    ├── reservation.ts
    └── review.ts
```

---

## Deployment Considerations

| Platform | SQLite Support | Notes |
|----------|----------------|-------|
| Vercel | Limited | Use Turso or external DB for serverless |
| Railway | Yes | Persistent volume required |
| Render | Yes | Disk-backed service |
| Self-hosted | Yes | Best option for SQLite |
| Local Dev | Yes | Just works |

**Recommendation for Production:**

- For serverless (Vercel): Consider Turso (SQLite edge) or Supabase
- For traditional hosting: SQLite works great

---

## Estimated Effort

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Setup | Install deps, create db utils | Low |
| Reservations API | CRUD endpoints | Low-Medium |
| Reviews API | CRUD + aggregations | Low-Medium |
| UI Components | Forms, lists, validation | Medium |
| Integration | Connect to restaurant pages | Medium |

---

## Quick Start

```bash
# Install dependencies
npm install better-sqlite3
npm install -D @types/better-sqlite3

# Create data directory
mkdir -p data

# Initialize database
npm run db:init
```

---

## Related Documentation

- [fastapi-backend.md](./fastapi-backend.md) - FastAPI + Python alternative

## References

- [better-sqlite3 Documentation](https://www.npmjs.com/package/better-sqlite3)
- [Next.js 14 with SQLite Guide](https://medium.com/@claudio-dev/setting-up-and-seeding-an-sqlite-database-in-a-next-js-14-fullstack-project-using-prisma-cc5f5f678b19)
- [Drizzle ORM + Next.js + SQLite Example](https://github.com/gustavocadev/nextjs-drizzle-orm-sqlite)
