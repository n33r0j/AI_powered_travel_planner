from fastapi import FastAPI, HTTPException, status, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import logging
import json
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict

from models import TravelRequest, TravelResponse, ErrorResponse
from services.llm_service import llm_service, token_tracker
from services.weather_service import weather_service
from utils.budget_validator import BudgetValidator
from utils.currency_converter import currency_converter
from utils.cache import weather_cache, llm_cache
from database import Base, engine, get_db, create_trip, get_trip_by_id, list_trips, delete_trip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered Travel Planner API",
    description="Generate personalized travel itineraries with AI-powered planning and budget validation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Database initialization on startup
@app.on_event("startup")
def startup_event():
    """Create database tables if they don't exist"""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")

# Add CORS middleware (for frontend integration in future)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Simple rate limiting middleware
class RateLimitMiddleware:
    """
    Basic in-memory rate limiter
    
    For production, use Redis-based rate limiting like slowapi or fastapi-limiter
    """
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True


rate_limiter = RateLimitMiddleware(requests_per_minute=20)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to API endpoints"""
    # Skip rate limiting for health, docs, and static pages
    if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json", "/stats"]:
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for {client_ip}")
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "detail": "Rate limit exceeded. Please try again later.",
                "retry_after": 60
            }
        )
    
    return await call_next(request)

# Initialize budget validator
budget_validator = BudgetValidator()

# Initialize Jinja2 templates for UI
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def home(request: Request):
    """Serve the premium dark mode UI landing page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api", tags=["Root"])
async def api_info() -> Dict[str, str]:
    """API information endpoint"""
    return {
        "message": "AI-Powered Travel Planner API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "ui": "/",
        "endpoints": {
            "create": "/generate-itinerary",
            "retrieve": "/trips/{trip_id}",
            "list": "/trips",
            "delete": "/trips/{trip_id}"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Travel Planner"
    }


@app.get("/stats", tags=["Monitoring"])
async def get_stats() -> Dict[str, Any]:
    """
    Get system statistics including cache performance and token usage
    
    Returns cache hit rates, token consumption, and estimated costs
    """
    return {
        "cache": {
            "weather": weather_cache.stats(),
            "llm": llm_cache.stats()
        },
        "tokens": token_tracker.stats(),
        "rate_limit": {
            "limit_per_minute": rate_limiter.requests_per_minute,
            "active_clients": len(rate_limiter.requests)
        },
        "timestamp": time.time()
    }


def convert_response_currency(data: dict, from_currency: str, to_currency: str) -> dict:
    """
    Recursively convert all monetary values in response data
    
    Args:
        data: Response dictionary containing monetary values
        from_currency: Source currency (typically USD)
        to_currency: Target currency for display
        
    Returns:
        Dictionary with converted monetary values
    """
    if from_currency == to_currency:
        return data
        
    # Fields that contain monetary values
    money_fields = [
        'estimated_cost', 'estimated_day_cost', 'estimated_total_cost',
        'price_per_night', 'estimated_daily_cost'
    ]
    
    # Create a deep copy to avoid modifying original
    import copy
    converted_data = copy.deepcopy(data)
    
    def convert_recursive(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in money_fields and isinstance(value, (int, float)):
                    obj[key] = round(currency_converter.convert_from_usd(value, to_currency))
                elif isinstance(value, (dict, list)):
                    convert_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    convert_recursive(item)
    
    convert_recursive(converted_data)
    return converted_data


@app.post("/generate-ui", response_class=HTMLResponse, tags=["UI"])
async def generate_ui(
    request: Request,
    destination: str = Form(...),
    duration_days: int = Form(...),
    budget: int = Form(...),
    currency: str = Form(default="USD"),
    interests: str = Form(""),
    weather_aware: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Generate travel itinerary from web form and display results
    
    This endpoint handles form submissions from the UI and returns
    a rendered HTML page with the trip itinerary.
    Supports USD and INR currencies.
    """
    try:
        # Parse interests (comma-separated string to list)
        interest_list = [i.strip() for i in interests.split(",") if i.strip()]
        if not interest_list:
            interest_list = ["general"]
        
        # Convert weather_aware checkbox to boolean
        weather_aware_bool = weather_aware == "true"
        
        # Store original currency and budget
        original_currency = currency.upper()
        original_budget = budget
        
        # HYBRID APPROACH: Use native INR for Indian destinations, USD for others
        if original_currency == "INR" and currency_converter.is_indian_destination(destination):
            # Keep INR for authentic Indian pricing
            processing_budget = budget
            processing_currency = "INR"
            logger.info(
                f"UI request: {destination}, {duration_days} days, "
                f"₹{original_budget} INR (using native currency)"
            )
        else:
            # Convert to USD for international destinations
            processing_budget = int(currency_converter.convert_to_usd(budget, original_currency))
            processing_currency = "USD"
            logger.info(
                f"UI request: {destination}, {duration_days} days, "
                f"{original_budget} {original_currency} (≈${processing_budget} USD)"
            )
        
        # Create TravelRequest object
        travel_request = TravelRequest(
            destination=destination,
            duration_days=duration_days,
            budget=processing_budget,
            currency=processing_currency,
            interests=interest_list,
            weather_aware=weather_aware_bool
        )
        
        # Get weather context if enabled
        weather_context = ""
        if travel_request.weather_aware:
            try:
                weather_data = weather_service.get_weather_context(
                    travel_request.destination,
                    travel_request.duration_days
                )
                weather_context = weather_data["summary"]
            except Exception as e:
                logger.warning(f"Could not fetch weather data: {str(e)}")
        
        # Generate itinerary
        response = llm_service.generate_with_budget_constraint(
            travel_request, 
            max_retries=2,
            weather_context=weather_context
        )
        
        # Get budget summary
        budget_summary = budget_validator.get_budget_summary(
            response.model_dump(),
            travel_request.budget
        )
        
        # Save to database
        trip = create_trip(
            db=db,
            destination=travel_request.destination,
            duration_days=travel_request.duration_days,
            budget=travel_request.budget,
            interests=travel_request.interests,
            itinerary_data=response.model_dump(),
            weather_summary=weather_context if weather_context else None,
            budget_breakdown=budget_summary['breakdown'],
            estimated_cost=budget_summary['estimated_total_cost'],
            weather_aware=travel_request.weather_aware
        )
        
        logger.info(f"UI: Trip saved to database with ID: {trip.id}")
        
        # Prepare data for template - convert all prices to display currency
        result_data = response.model_dump()
        
        # Only convert if processing currency differs from display currency
        if processing_currency != original_currency:
            # Convert all monetary values to display currency
            result_data = convert_response_currency(result_data, processing_currency, original_currency)
            
            # Convert budget breakdown
            for key in budget_summary['breakdown']:
                if processing_currency == "USD":
                    budget_summary['breakdown'][key] = round(
                        currency_converter.convert_from_usd(
                            budget_summary['breakdown'][key], 
                            original_currency
                        )
                    )
                # If processing in INR already, no conversion needed
            
            if processing_currency == "USD":
                estimated_cost_converted = currency_converter.convert_from_usd(
                    budget_summary['estimated_total_cost'],
                    original_currency
                )
                remaining_budget_converted = currency_converter.convert_from_usd(
                    budget_summary['remaining_budget'],
                    original_currency
                )
            else:
                # Already in target currency
                estimated_cost_converted = budget_summary['estimated_total_cost']
                remaining_budget_converted = budget_summary['remaining_budget']
        else:
            estimated_cost_converted = budget_summary['estimated_total_cost']
            remaining_budget_converted = budget_summary['remaining_budget']
        
        result_data["trip_id"] = trip.id
        result_data["budget_status"] = budget_summary['status']
        result_data["budget_breakdown"] = budget_summary['breakdown']
        result_data["user_budget"] = original_budget
        result_data["estimated_total_cost"] = estimated_cost_converted
        result_data["budget_utilization"] = budget_summary['percentage_used']
        result_data["remaining_budget"] = remaining_budget_converted
        result_data["currency"] = original_currency
        result_data["currency_symbol"] = currency_converter.get_currency_symbol(original_currency)
        
        # Render result page
        return templates.TemplateResponse(
            "result.html",
            {"request": request, "result": result_data}
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        # Return error page or redirect to form with error
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-br from-gray-950 via-gray-900 to-black min-h-screen flex items-center justify-center text-white">
            <div class="max-w-lg p-8 rounded-2xl backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl text-center">
                <h1 class="text-3xl font-bold mb-4 text-red-400">❌ Error</h1>
                <p class="text-gray-300 mb-6">{str(e)}</p>
                <a href="/" class="inline-block px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 transition">
                    ← Back to Form
                </a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html)
    
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}")
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-br from-gray-950 via-gray-900 to-black min-h-screen flex items-center justify-center text-white">
            <div class="max-w-lg p-8 rounded-2xl backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl text-center">
                <h1 class="text-3xl font-bold mb-4 text-red-400">❌ Server Error</h1>
                <p class="text-gray-300 mb-2">Failed to generate itinerary</p>
                <p class="text-sm text-gray-500 mb-6">{str(e)}</p>
                <a href="/" class="inline-block px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 transition">
                    ← Try Again
                </a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html)


@app.post(
    "/generate-itinerary",
    response_model=TravelResponse,
    status_code=status.HTTP_200_OK,
    tags=["Itinerary"],
    summary="Generate Travel Itinerary",
    description="Generate a personalized travel itinerary based on destination, budget, duration, and interests",
    responses={
        200: {
            "description": "Successfully generated itinerary",
            "model": TravelResponse
        },
        400: {
            "description": "Invalid request data",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def generate_itinerary(request: TravelRequest, db: Session = Depends(get_db)):
    """
    Generate a comprehensive travel itinerary
    
    **Request Body:**
    - destination: Target destination (e.g., "Tokyo, Japan" or "Kochi, India")
    - duration_days: Number of days (1-30)
    - budget: Total budget (in specified currency)
    - currency: Currency code (USD or INR)
    - interests: List of interests (e.g., ["culture", "food", "adventure"])
    - weather_aware: Include weather forecast (default: True)
    
    **Returns:**
    - Complete itinerary in requested currency
    - Accommodation suggestions
    - Transportation options
    - Budget breakdown
    - Travel tips
    - Weather-adapted activities (if enabled)
    
    **Note:** For Indian destinations with INR, prices use native authentic pricing.
    """
    try:
        # HYBRID APPROACH: Use native currency for Indian destinations
        original_currency = request.currency
        if request.currency == "INR" and currency_converter.is_indian_destination(request.destination):
            # Keep INR for authentic pricing
            logger.info(
                f"Generating itinerary for {request.destination}, "
                f"{request.duration_days} days, ₹{request.budget} INR (native), "
                f"weather_aware={request.weather_aware}"
            )
        else:
            # Convert to USD if needed
            if request.currency != "USD":
                original_budget = request.budget
                request.budget = int(currency_converter.convert_to_usd(request.budget, request.currency))
                request.currency = "USD"
                logger.info(
                    f"Generating itinerary for {request.destination}, "
                    f"{request.duration_days} days, ${request.budget} USD (from {original_currency} {original_budget}), "
                    f"weather_aware={request.weather_aware}"
                )
            else:
                logger.info(
                    f"Generating itinerary for {request.destination}, "
                    f"{request.duration_days} days, ${request.budget} USD, "
                    f"weather_aware={request.weather_aware}"
                )
        
        # Get weather context if enabled
        weather_context = ""
        if request.weather_aware:
            try:
                weather_data = weather_service.get_weather_context(
                    request.destination,
                    request.duration_days
                )
                weather_context = weather_data["summary"]
                logger.info(f"Weather context: {weather_data['has_rain']=}, rainy_days={weather_data['rainy_days']}")
            except Exception as e:
                logger.warning(f"Could not fetch weather data: {str(e)}")
                # Continue without weather context
        
        # Generate itinerary with budget validation
        response = llm_service.generate_with_budget_constraint(
            request, 
            max_retries=2,
            weather_context=weather_context
        )
        
        # Get budget summary
        budget_summary = budget_validator.get_budget_summary(
            response.model_dump(),
            request.budget
        )
        
        logger.info(
            f"Itinerary generated successfully. "
            f"Total cost: ${budget_summary['estimated_total_cost']:.2f}, "
            f"Status: {budget_summary['status']}"
        )
        
        # Save trip to database
        trip = create_trip(
            db=db,
            destination=request.destination,
            duration_days=request.duration_days,
            budget=request.budget,
            interests=request.interests,
            itinerary_data=response.model_dump(),
            weather_summary=weather_context if weather_context else None,
            budget_breakdown=budget_summary,
            estimated_cost=budget_summary['estimated_total_cost'],
            weather_aware=request.weather_aware
        )
        
        logger.info(f"Trip saved to database with ID: {trip.id}")
        
        # Return response with trip_id
        response_dict = response.model_dump()
        response_dict["trip_id"] = trip.id
        
        return response_dict
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request data: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Error generating itinerary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate itinerary: {str(e)}"
        )


@app.post(
    "/validate-budget",
    tags=["Budget"],
    summary="Validate Itinerary Budget",
    description="Validate if an itinerary stays within the specified budget"
)
async def validate_budget(
    itinerary_data: Dict[str, Any],
    user_budget: int
) -> Dict[str, Any]:
    """
    Validate budget for a given itinerary
    
    **Request Body:**
    - itinerary_data: Complete itinerary data
    - user_budget: User's budget in USD
    
    **Returns:**
    - Budget validation results with breakdown
    """
    try:
        summary = budget_validator.get_budget_summary(itinerary_data, user_budget)
        return summary
    
    except Exception as e:
        logger.error(f"Error validating budget: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate budget: {str(e)}"
        )


@app.get(
    "/trips/{trip_id}",
    tags=["Trips"],
    summary="Get Trip by ID",
    description="Retrieve a previously generated trip itinerary by its ID"
)
async def get_trip(trip_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Retrieve a specific trip by ID
    
    **Path Parameters:**
    - trip_id: Unique trip identifier
    
    **Returns:**
    - Complete trip data including itinerary, weather context, and metadata
    """
    try:
        trip = get_trip_by_id(db, trip_id)
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip with ID {trip_id} not found"
            )
        
        # Parse JSON fields
        response = {
            "trip_id": trip.id,
            "destination": trip.destination,
            "duration_days": trip.duration_days,
            "budget": trip.budget,
            "interests": trip.interests.split(",") if trip.interests else [],
            "itinerary": json.loads(trip.itinerary_json),
            "weather_summary": trip.weather_summary,
            "budget_breakdown": json.loads(trip.budget_breakdown_json) if trip.budget_breakdown_json else None,
            "estimated_cost": trip.estimated_cost,
            "weather_aware": bool(trip.weather_aware),
            "created_at": trip.created_at.isoformat()
        }
        
        logger.info(f"Retrieved trip {trip_id}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve trip: {str(e)}"
        )


@app.get(
    "/trips",
    tags=["Trips"],
    summary="List Trips",
    description="List all trips with optional filtering by destination"
)
async def get_trips(
    destination: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List trips with pagination and filtering
    
    **Query Parameters:**
    - destination: Filter by destination (partial match, case-insensitive)
    - limit: Maximum number of results (default: 20, max: 100)
    - offset: Number of results to skip (default: 0)
    
    **Returns:**
    - List of trips with summary information
    """
    try:
        # Limit max results
        limit = min(limit, 100)
        
        trips = list_trips(db, destination=destination, limit=limit, offset=offset)
        
        # Format response
        trips_data = []
        for trip in trips:
            trips_data.append({
                "trip_id": trip.id,
                "destination": trip.destination,
                "duration_days": trip.duration_days,
                "budget": trip.budget,
                "estimated_cost": trip.estimated_cost,
                "weather_aware": bool(trip.weather_aware),
                "created_at": trip.created_at.isoformat()
            })
        
        logger.info(f"Listed {len(trips_data)} trips (offset={offset}, limit={limit})")
        
        return {
            "trips": trips_data,
            "count": len(trips_data),
            "offset": offset,
            "limit": limit
        }
    
    except Exception as e:
        logger.error(f"Error listing trips: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list trips: {str(e)}"
        )


@app.delete(
    "/trips/{trip_id}",
    tags=["Trips"],
    summary="Delete Trip",
    description="Delete a trip by its ID"
)
async def remove_trip(trip_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Delete a specific trip
    
    **Path Parameters:**
    - trip_id: Unique trip identifier
    
    **Returns:**
    - Confirmation message
    """
    try:
        deleted = delete_trip(db, trip_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip with ID {trip_id} not found"
            )
        
        logger.info(f"Deleted trip {trip_id}")
        return {
            "message": f"Trip {trip_id} deleted successfully",
            "status": "success"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trip {trip_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete trip: {str(e)}"
        )


# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred",
            "detail": str(exc),
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting AI Travel Planner API...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
