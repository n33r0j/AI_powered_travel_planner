#!/usr/bin/env python3
"""Quick test to verify weather service works"""

from services.weather_service import weather_service

print("Testing Weather Service...")
print("="*60)

# Test geocoding
print("\n1. Testing Geocoding:")
coords = weather_service.get_coordinates("Paris, France")
print(f"   Paris coordinates: {coords}")

# Test weather forecast
print("\n2. Testing Weather Forecast:")
forecasts = weather_service.get_weather_forecast("Paris, France", 3)
print(f"   Got {len(forecasts)} days of forecast")
for f in forecasts:
    print(f"   Day {f['day']}: {f['condition']}, {f['temp_max']}°C")

# Test weather context
print("\n3. Testing Weather Context:")
context = weather_service.get_weather_context("Tokyo, Japan", 3)
print(f"   Has rain: {context['has_rain']}")
print(f"   Rainy days: {context['rainy_days']}")
print("\n   Summary:")
print("   " + "\n   ".join(context['summary'].split('\n')))

print("\n" + "="*60)
print("✅ Weather Service Working!")
