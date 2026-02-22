import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from utils.cache import weather_cache, WEATHER_CACHE_TTL

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather forecasts using Open-Meteo API (free, no key needed)"""
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        # Mapping of WMO weather codes to simple conditions
        self.weather_codes = {
            0: "Clear",
            1: "Mostly Clear",
            2: "Partly Cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Foggy",
            51: "Light Drizzle",
            53: "Drizzle",
            55: "Heavy Drizzle",
            61: "Light Rain",
            63: "Rain",
            65: "Heavy Rain",
            71: "Light Snow",
            73: "Snow",
            75: "Heavy Snow",
            77: "Snow Grains",
            80: "Light Showers",
            81: "Showers",
            82: "Heavy Showers",
            85: "Light Snow Showers",
            86: "Snow Showers",
            95: "Thunderstorm",
            96: "Thunderstorm with Hail",
            99: "Heavy Thunderstorm"
        }
    
    def get_coordinates(self, destination: str) -> Optional[tuple]:
        """
        Get coordinates for a destination using geocoding (with caching)
        
        Args:
            destination: Destination name (e.g., "Tokyo, Japan")
            
        Returns:
            Tuple of (latitude, longitude) or None if not found
        """
        # Check cache first
        cache_key = f"geocode:{destination.lower()}"
        cached = weather_cache.get(cache_key)
        if cached is not None:
            logger.info(f"Geocoding cache hit for {destination}")
            return cached
        
        try:
            # Use Open-Meteo's geocoding API
            geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                "name": destination,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            
            logger.info(f"Geocoding API call for {destination}")
            response = requests.get(geocode_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("results"):
                result = data["results"][0]
                coords = (result["latitude"], result["longitude"])
                # Cache coordinates (longer TTL since they don't change)
                weather_cache.set(cache_key, coords, ttl_seconds=7*24*60*60)  # 7 days
                return coords
            
            logger.warning(f"No coordinates found for {destination}")
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding {destination}: {str(e)}")
            return None
    
    def get_weather_forecast(
        self, 
        destination: str, 
        duration_days: int,
        start_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Get simplified weather forecast for destination (with caching)
        
        Args:
            destination: Destination name
            duration_days: Number of days for forecast
            start_date: Start date (defaults to today)
            
        Returns:
            List of daily weather summaries
        """
        # Generate cache key
        if start_date is None:
            start_date = datetime.now()
        
        cache_key = f"forecast:{destination.lower()}:{duration_days}:{start_date.strftime('%Y-%m-%d')}"
        cached = weather_cache.get(cache_key)
        if cached is not None:
            logger.info(f"Weather forecast cache hit for {destination}")
            return cached
        
        try:
            # Get coordinates
            coords = self.get_coordinates(destination)
            if not coords:
                logger.warning(f"Could not get weather for {destination}")
                return []
            
            latitude, longitude = coords
            
            end_date = start_date + timedelta(days=duration_days - 1)
            
            # Fetch weather data
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "timezone": "auto"
            }
            
            logger.info(f"Weather API call for {destination} ({duration_days} days)")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            daily = data.get("daily", {})
            
            # Simplify to daily summaries
            forecasts = []
            for i in range(len(daily.get("time", []))):
                weather_code = daily["weather_code"][i]
                condition = self.weather_codes.get(weather_code, "Unknown")
                
                forecast = {
                    "day": i + 1,
                    "date": daily["time"][i],
                    "condition": condition,
                    "temp_max": round(daily["temperature_2m_max"][i]),
                    "temp_min": round(daily["temperature_2m_min"][i]),
                    "precipitation_probability": daily.get("precipitation_probability_max", [0] * len(daily["time"]))[i],
                    "is_rainy": self._is_rainy(condition),
                    "is_indoor_preferred": self._is_indoor_preferred(condition)
                }
                forecasts.append(forecast)
            
            # Cache the result (6 hours TTL)
            weather_cache.set(cache_key, forecasts, ttl_seconds=WEATHER_CACHE_TTL)
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            return []
    
    def _is_rainy(self, condition: str) -> bool:
        """Check if condition indicates rain"""
        rainy_keywords = ["rain", "drizzle", "shower", "thunderstorm"]
        return any(keyword in condition.lower() for keyword in rainy_keywords)
    
    def _is_indoor_preferred(self, condition: str) -> bool:
        """Check if indoor activities are preferred"""
        indoor_keywords = ["rain", "drizzle", "shower", "thunderstorm", "snow", "heavy"]
        return any(keyword in condition.lower() for keyword in indoor_keywords)
    
    def format_weather_summary(self, forecasts: List[Dict]) -> str:
        """
        Format weather forecasts into a concise summary for LLM
        
        Args:
            forecasts: List of weather forecast dictionaries
            
        Returns:
            Formatted string for prompt injection
        """
        if not forecasts:
            return "Weather data unavailable."
        
        summary_lines = ["Weather Forecast:"]
        
        for forecast in forecasts:
            day = forecast["day"]
            condition = forecast["condition"]
            temp_max = forecast["temp_max"]
            precip = forecast["precipitation_probability"]
            
            line = f"Day {day}: {condition}, High {temp_max}°C"
            if precip > 30:
                line += f" ({precip}% chance of rain)"
            
            summary_lines.append(line)
        
        # Add recommendations
        rainy_days = [f["day"] for f in forecasts if f["is_indoor_preferred"]]
        
        if rainy_days:
            summary_lines.append("")
            summary_lines.append(f"⚠️ Rain expected on Day(s) {', '.join(map(str, rainy_days))}")
            summary_lines.append("Recommendation: Prioritize indoor activities (museums, temples, shopping, covered markets)")
        else:
            summary_lines.append("")
            summary_lines.append("✅ Good weather expected")
            summary_lines.append("Recommendation: Include outdoor sightseeing, parks, and walking tours")
        
        return "\n".join(summary_lines)
    
    def get_weather_context(
        self, 
        destination: str, 
        duration_days: int
    ) -> Dict:
        """
        Get complete weather context for itinerary planning
        
        Args:
            destination: Travel destination
            duration_days: Trip duration
            
        Returns:
            Dictionary with forecasts and formatted summary
        """
        forecasts = self.get_weather_forecast(destination, duration_days)
        
        return {
            "forecasts": forecasts,
            "summary": self.format_weather_summary(forecasts),
            "has_rain": any(f["is_rainy"] for f in forecasts),
            "rainy_days": [f["day"] for f in forecasts if f["is_rainy"]],
            "indoor_preferred_days": [f["day"] for f in forecasts if f["is_indoor_preferred"]]
        }


# Singleton instance
weather_service = WeatherService()
