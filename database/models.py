"""SQLAlchemy ORM models for travel planner database."""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from datetime import datetime
from .db import Base


class Trip(Base):
    """
    Trip model for storing generated travel itineraries.
    
    Stores the complete itinerary along with request parameters,
    weather context, and budget breakdown for retrieval and analytics.
    """
    __tablename__ = "trips"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Request parameters
    destination = Column(String, index=True, nullable=False)
    duration_days = Column(Integer, nullable=False)
    budget = Column(Float, nullable=False)
    interests = Column(String, nullable=True)  # Stored as comma-separated string
    
    # Generated content (stored as JSON strings)
    itinerary_json = Column(Text, nullable=False)
    weather_summary = Column(Text, nullable=True)
    budget_breakdown_json = Column(Text, nullable=True)
    
    # Metadata
    estimated_cost = Column(Float, nullable=True)
    weather_aware = Column(Integer, default=1)  # SQLite doesn't have boolean, use 0/1
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Trip(id={self.id}, destination='{self.destination}', days={self.duration_days}, budget=${self.budget})>"
