"""CRUD operations for travel planner database."""
import json
from sqlalchemy.orm import Session
from typing import Optional, List
from .models import Trip


def create_trip(
    db: Session,
    destination: str,
    duration_days: int,
    budget: float,
    interests: List[str],
    itinerary_data: dict,
    weather_summary: Optional[str],
    budget_breakdown: dict,
    estimated_cost: float,
    weather_aware: bool
) -> Trip:
    """
    Create a new trip record in the database.
    
    Args:
        db: Database session
        destination: Trip destination
        duration_days: Number of days
        budget: User's budget
        interests: List of interests
        itinerary_data: Complete itinerary dictionary
        weather_summary: Weather context used (if any)
        budget_breakdown: Budget breakdown dictionary
        estimated_cost: Total estimated cost
        weather_aware: Whether weather data was used
    
    Returns:
        Created Trip object with assigned ID
    """
    trip = Trip(
        destination=destination,
        duration_days=duration_days,
        budget=budget,
        interests=",".join(interests) if interests else None,
        itinerary_json=json.dumps(itinerary_data),
        weather_summary=weather_summary,
        budget_breakdown_json=json.dumps(budget_breakdown),
        estimated_cost=estimated_cost,
        weather_aware=1 if weather_aware else 0
    )
    
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def get_trip_by_id(db: Session, trip_id: int) -> Optional[Trip]:
    """
    Retrieve a trip by its ID.
    
    Args:
        db: Database session
        trip_id: Trip ID to retrieve
    
    Returns:
        Trip object if found, None otherwise
    """
    return db.query(Trip).filter(Trip.id == trip_id).first()


def list_trips(
    db: Session,
    destination: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[Trip]:
    """
    List trips with optional filtering.
    
    Args:
        db: Database session
        destination: Filter by destination (partial match)
        limit: Maximum number of results
        offset: Number of results to skip
    
    Returns:
        List of Trip objects
    """
    query = db.query(Trip)
    
    if destination:
        query = query.filter(Trip.destination.ilike(f"%{destination}%"))
    
    return query.order_by(Trip.created_at.desc()).offset(offset).limit(limit).all()


def delete_trip(db: Session, trip_id: int) -> bool:
    """
    Delete a trip by its ID.
    
    Args:
        db: Database session
        trip_id: Trip ID to delete
    
    Returns:
        True if deleted, False if not found
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip:
        db.delete(trip)
        db.commit()
        return True
    return False


def get_trip_count(db: Session) -> int:
    """
    Get total number of trips in database.
    
    Args:
        db: Database session
    
    Returns:
        Total trip count
    """
    return db.query(Trip).count()
