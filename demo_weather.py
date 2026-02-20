#!/usr/bin/env python3
"""
Weather-Aware Itinerary Demo
Demonstrates the difference between weather-aware and non-weather-aware planning
"""

import requests
import json
from typing import Dict, Any


def generate_itinerary(destination: str, days: int, budget: int, interests: list, weather_aware: bool) -> Dict[str, Any]:
    """Generate itinerary with or without weather awareness"""
    url = "http://localhost:8000/generate-itinerary"
    
    payload = {
        "destination": destination,
        "duration_days": days,
        "budget": budget,
        "interests": interests,
        "weather_aware": weather_aware
    }
    
    print(f"\n{'='*70}")
    print(f"🌍 Generating {'WEATHER-AWARE' if weather_aware else 'STANDARD'} itinerary...")
    print(f"{'='*70}")
    print(f"📍 Destination: {destination}")
    print(f"📅 Duration: {days} days")
    print(f"💰 Budget: ${budget}")
    print(f"🎯 Interests: {', '.join(interests)}")
    print(f"🌤️  Weather-Aware: {'✅ YES' if weather_aware else '❌ NO'}")
    print(f"\n⏳ Generating... (this may take 10-30 seconds)\n")
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())
            return None
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to the API.")
        print("   Make sure the server is running: python main.py")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def analyze_activities(itinerary: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze activities in the itinerary"""
    if not itinerary:
        return {}
    
    outdoor_keywords = ["park", "outdoor", "walking tour", "garden", "hike", "beach", "market", "street"]
    indoor_keywords = ["museum", "temple", "mall", "shopping", "indoor", "gallery", "theater", "aquarium"]
    
    outdoor_count = 0
    indoor_count = 0
    total_activities = 0
    
    for day in itinerary.get("itinerary", []):
        for activity in day.get("activities", []):
            total_activities += 1
            activity_text = (activity.get("name", "") + " " + activity.get("description", "")).lower()
            
            if any(keyword in activity_text for keyword in outdoor_keywords):
                outdoor_count += 1
            elif any(keyword in activity_text for keyword in indoor_keywords):
                indoor_count += 1
    
    return {
        "total": total_activities,
        "outdoor": outdoor_count,
        "indoor": indoor_count,
        "mixed": total_activities - outdoor_count - indoor_count
    }


def display_comparison(standard: Dict[str, Any], weather_aware: Dict[str, Any]):
    """Display side-by-side comparison"""
    print("\n" + "="*70)
    print("📊 COMPARISON RESULTS")
    print("="*70)
    
    if not standard or not weather_aware:
        print("❌ Could not generate both itineraries for comparison")
        return
    
    std_activities = analyze_activities(standard)
    wa_activities = analyze_activities(weather_aware)
    
    print(f"\n{'Metric':<30} {'Standard':<20} {'Weather-Aware':<20}")
    print("-" * 70)
    print(f"{'Total Activities':<30} {std_activities['total']:<20} {wa_activities['total']:<20}")
    print(f"{'Outdoor Activities':<30} {std_activities['outdoor']:<20} {wa_activities['outdoor']:<20}")
    print(f"{'Indoor Activities':<30} {std_activities['indoor']:<20} {wa_activities['indoor']:<20}")
    print(f"{'Estimated Cost':<30} ${standard['estimated_total_cost']:<19.2f} ${weather_aware['estimated_total_cost']:<19.2f}")
    
    # Show first day comparison
    print(f"\n📅 DAY 1 COMPARISON:")
    print("-" * 70)
    
    if standard.get("itinerary") and weather_aware.get("itinerary"):
        std_day1 = standard["itinerary"][0]
        wa_day1 = weather_aware["itinerary"][0]
        
        print(f"\n🔵 Standard Plan - Day 1: {std_day1['title']}")
        for i, activity in enumerate(std_day1['activities'][:3], 1):
            print(f"   {i}. {activity['name']}")
        
        print(f"\n🌤️  Weather-Aware Plan - Day 1: {wa_day1['title']}")
        for i, activity in enumerate(wa_day1['activities'][:3], 1):
            print(f"   {i}. {activity['name']}")
    
    print(f"\n{'='*70}")
    print("💡 KEY INSIGHT:")
    print("="*70)
    
    if wa_activities['indoor'] > std_activities['indoor']:
        print("✅ Weather-aware plan prioritizes MORE INDOOR activities")
        print("   This is ideal for rainy/bad weather conditions!")
    elif wa_activities['outdoor'] > std_activities['outdoor']:
        print("✅ Weather-aware plan includes MORE OUTDOOR activities")  
        print("   Taking advantage of good weather!")
    else:
        print("✅ Both plans are balanced for current weather conditions")
    
    print()


def save_results(standard: Dict, weather_aware: Dict):
    """Save comparison results"""
    results = {
        "comparison": "Weather-Aware vs Standard Itinerary",
        "standard_itinerary": standard,
        "weather_aware_itinerary": weather_aware,
        "analysis": {
            "standard": analyze_activities(standard),
            "weather_aware": analyze_activities(weather_aware)
        }
    }
    
    filename = "weather_comparison.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Full comparison saved to: {filename}\n")


def main():
    """Run the weather awareness demo"""
    print("\n" + "="*70)
    print("🌤️  WEATHER-AWARE ITINERARY DEMO")
    print("="*70)
    print("\nThis demo generates TWO itineraries for the same trip:")
    print("1. 🔵 Standard (no weather context)")
    print("2. 🌤️  Weather-Aware (with live weather forecast)")
    print("\nYou'll see how the AI adapts activities based on weather!")
    print("="*70)
    
    # Test parameters
    destination = "Paris, France"
    days = 3
    budget = 1000
    interests = ["art", "food", "culture"]
    
    # Generate standard itinerary (no weather)
    standard = generate_itinerary(destination, days, budget, interests, weather_aware=False)
    
    # Generate weather-aware itinerary
    weather_aware = generate_itinerary(destination, days, budget, interests, weather_aware=True)
    
    # Display comparison
    if standard and weather_aware:
        display_comparison(standard, weather_aware)
        save_results(standard, weather_aware)
        
        print("="*70)
        print("✨ DEMO COMPLETE!")
        print("="*70)
        print("\n🎯 What This Demonstrates:")
        print("   ✅ Real-time weather integration")
        print("   ✅ Context-aware AI planning")
        print("   ✅ Adaptive activity selection")
        print("   ✅ Hybrid AI orchestration system\n")
        
        print("🚀 Recruiter Impact:")
        print('   "This is not just an LLM wrapper - it\'s a context-aware')
        print('    AI system that augments LLM reasoning with live data."\n')
    else:
        print("\n❌ Demo failed - check if the server is running")
        print("   Run: python main.py\n")


if __name__ == "__main__":
    main()
