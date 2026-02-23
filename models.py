from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class TravelRequest(BaseModel):
    """Request model for travel itinerary generation"""
    destination: str = Field(..., min_length=2, max_length=100, description="Travel destination")
    duration_days: int = Field(..., gt=0, le=30, description="Number of days (1-30)")
    budget: int = Field(..., gt=0, description="Total budget in specified currency")
    currency: str = Field(default="USD", description="Budget currency (USD or INR)")
    interests: List[str] = Field(..., min_length=1, max_length=10, description="List of interests")
    weather_aware: bool = Field(default=True, description="Include weather forecast in planning")
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        allowed_currencies = ['USD', 'INR']
        v_upper = v.upper()
        if v_upper not in allowed_currencies:
            raise ValueError(f'Currency must be one of {allowed_currencies}')
        return v_upper
    
    @field_validator('destination')
    @classmethod
    def validate_destination(cls, v):
        if not v.strip():
            raise ValueError('Destination cannot be empty')
        # Clean up destination formatting
        destination = v.strip()
        # Fix comma spacing (e.g., "Tokyo,Japan" -> "Tokyo, Japan")
        if ',' in destination:
            parts = [part.strip() for part in destination.split(',')]
            destination = ', '.join(parts)
        return destination
    
    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v):
        if not v:
            raise ValueError('At least one interest is required')
        return [interest.strip() for interest in v if interest.strip()]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "destination": "Tokyo, Japan",
                    "duration_days": 5,
                    "budget": 2000,
                    "currency": "USD",
                    "interests": ["culture", "food", "technology", "temples"],
                    "weather_aware": True
                },
                {
                    "destination": "Goa, India",
                    "duration_days": 4,
                    "budget": 50000,
                    "currency": "INR",
                    "interests": ["beaches", "nightlife", "food"],
                    "weather_aware": True
                }
            ]
        }
    }


class Activity(BaseModel):
    """Single activity in the itinerary"""
    time: str
    name: str
    description: str
    estimated_cost: float
    location: str


class FoodRecommendation(BaseModel):
    """Food recommendation for a meal"""
    meal_type: str
    restaurant: str
    dish: str
    estimated_cost: float


class DayItinerary(BaseModel):
    """Itinerary for a single day"""
    day: int
    title: str
    activities: List[Activity]
    food_recommendations: List[FoodRecommendation]
    estimated_day_cost: float


class Accommodation(BaseModel):
    """Accommodation suggestion"""
    name: str
    type: str
    price_per_night: float
    location: str
    amenities: List[str]


class TravelOption(BaseModel):
    """Travel option to reach destination"""
    mode: str = Field(..., description="Transportation mode (Flight/Train/Bus)")
    details: str = Field(..., description="Specific details (airport, station, route)")
    estimated_cost: float = Field(..., description="Estimated cost in specified currency")


class KeyAttraction(BaseModel):
    """Key attraction or landmark"""
    name: str = Field(..., description="Attraction name")
    description: str = Field(..., description="Brief description")
    category: str = Field(..., description="Category (Historical/Cultural/Natural/Entertainment)")


class LocalBeverage(BaseModel):
    """Local beverage recommendation"""
    name: str = Field(..., description="Beverage name")
    description: str = Field(..., description="Description and cultural significance")
    where_to_try: str = Field(..., description="Where to find it")
    estimated_cost: float = Field(..., description="Approximate cost")


class TransportationOption(BaseModel):
    """Transportation option details"""
    mode: str
    estimated_cost: Optional[float] = 0
    duration: Optional[str] = ""
    tips: str


class Transportation(BaseModel):
    """Complete transportation information"""
    to_destination: List[TransportationOption]
    local_transport: List[TransportationOption]


class BudgetBreakdown(BaseModel):
    """Detailed budget breakdown"""
    accommodation_total: float
    transportation_total: float
    activities_total: float
    food_total: float
    miscellaneous: float


class TravelResponse(BaseModel):
    """Complete travel itinerary response"""
    destination: str
    duration: int
    estimated_total_cost: float
    currency: str = "USD"
    travel_options: List[TravelOption] = Field(default_factory=list)
    key_attractions: List[KeyAttraction] = Field(default_factory=list)
    local_beverages: List[LocalBeverage] = Field(default_factory=list)
    itinerary: List[DayItinerary]
    accommodation_suggestions: List[Accommodation]
    transportation: Transportation
    budget_breakdown: BudgetBreakdown
    travel_tips: List[str]
    budget_status: str = Field(default="within_budget")  # within_budget, over_budget, adjusted
    
    
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int
