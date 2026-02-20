from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from models import TravelRequest, TravelResponse, ErrorResponse
from services.llm_service import llm_service
from services.weather_service import weather_service
from utils.budget_validator import BudgetValidator

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
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware (for frontend integration in future)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize budget validator
budget_validator = BudgetValidator()


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root endpoint with API information"""
    return {
        "message": "AI-Powered Travel Planner API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Travel Planner"
    }


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
async def generate_itinerary(request: TravelRequest) -> TravelResponse:
    """
    Generate a comprehensive travel itinerary
    
    **Request Body:**
    - destination: Target destination (e.g., "Tokyo, Japan")
    - duration_days: Number of days (1-30)
    - budget: Total budget in USD
    - interests: List of interests (e.g., ["culture", "food", "adventure"])
    - weather_aware: Include weather forecast (default: True)
    
    **Returns:**
    - Complete itinerary with day-by-day activities
    - Accommodation suggestions
    - Transportation options
    - Budget breakdown
    - Travel tips
    - Weather-adapted activities (if enabled)
    """
    try:
        logger.info(
            f"Generating itinerary for {request.destination}, "
            f"{request.duration_days} days, ${request.budget}, "
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
        
        return response
    
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
