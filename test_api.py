#!/usr/bin/env python3
"""
Quick test script for the AI Travel Planner API
"""

import requests
import json
from typing import Dict, Any


def test_generate_itinerary():
    """Test the generate-itinerary endpoint"""
    
    url = "http://localhost:8000/generate-itinerary"
    
    # Test case 1: Tokyo trip
    payload = {
        "destination": "Tokyo, Japan",
        "duration_days": 5,
        "budget": 2000,
        "interests": ["culture", "food", "technology", "temples"]
    }
    
    print("🚀 Testing AI Travel Planner API")
    print("=" * 50)
    print(f"\n📍 Destination: {payload['destination']}")
    print(f"📅 Duration: {payload['duration_days']} days")
    print(f"💰 Budget: ${payload['budget']}")
    print(f"🎯 Interests: {', '.join(payload['interests'])}")
    print("\n⏳ Generating itinerary... (this may take 10-30 seconds)\n")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Itinerary generated.")
            print("=" * 50)
            print(f"\n📊 Budget Status: {data.get('budget_status', 'N/A')}")
            print(f"💵 Estimated Total Cost: ${data.get('estimated_total_cost', 0):.2f}")
            print(f"📝 Number of Days: {len(data.get('itinerary', []))}")
            
            # Show first day's activities
            if data.get('itinerary'):
                first_day = data['itinerary'][0]
                print(f"\n🗓️  Day 1: {first_day.get('title', 'N/A')}")
                print(f"   Activities: {len(first_day.get('activities', []))}")
                print(f"   Estimated Cost: ${first_day.get('estimated_day_cost', 0):.2f}")
            
            # Budget breakdown
            if data.get('budget_breakdown'):
                breakdown = data['budget_breakdown']
                print("\n💳 Budget Breakdown:")
                print(f"   🏨 Accommodation: ${breakdown.get('accommodation_total', 0):.2f}")
                print(f"   🚗 Transportation: ${breakdown.get('transportation_total', 0):.2f}")
                print(f"   🎭 Activities: ${breakdown.get('activities_total', 0):.2f}")
                print(f"   🍽️  Food: ${breakdown.get('food_total', 0):.2f}")
                print(f"   📦 Miscellaneous: ${breakdown.get('miscellaneous', 0):.2f}")
            
            # Save to file
            filename = f"itinerary_{payload['destination'].replace(', ', '_').replace(' ', '_').lower()}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n💾 Full itinerary saved to: {filename}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to the API.")
        print("   Make sure the server is running on http://localhost:8000")
        print("   Run: python main.py")
    
    except requests.exceptions.Timeout:
        print("⏰ Request timed out. The API might be taking longer than expected.")
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")


def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy!")
            return True
        else:
            print("⚠️  API returned non-200 status")
            return False
    except:
        print("❌ API is not reachable. Start the server with: python main.py")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🧪 AI Travel Planner - API Test Script")
    print("=" * 50 + "\n")
    
    # First check if API is running
    if test_health_check():
        print()
        test_generate_itinerary()
    
    print("\n" + "=" * 50)
    print("✨ Test complete!")
    print("=" * 50 + "\n")
