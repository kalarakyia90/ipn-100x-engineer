"""
FastAPI application entry point.

Configures CORS for Next.js frontend, includes routers,
and initializes the database on startup.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_database
from .routers import reservations, reviews

# Initialize FastAPI app
app = FastAPI(
    title="Restaurant Finder API",
    description="API for restaurant reservations and reviews",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for Next.js frontend
# In production, replace with your actual domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(reservations.router)
app.include_router(reviews.router)


@app.on_event("startup")
def startup_event():
    """Initialize database tables on application startup."""
    init_database()


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "Restaurant Finder API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "restaurant-api"}
