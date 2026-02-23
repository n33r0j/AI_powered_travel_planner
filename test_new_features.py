"""
Test script to validate the new travel planner features:
1. Travel Options (how to reach destination)
2. Key Attractions (must-see places)
3. Local Beverages (iconic drinks)
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_new_features():
    """Test the newly added structured sections"""
    
    print("🧪 Testing AI Travel Planner - New Features")
    print("=" * 70)
    
    # Test request
    request_data = {
        "destination": "Kochi, India",
        "duration_days": 3,
        "budget": 15000,
        "currency": "INR",
        "interests": ["culture", "food", "history", "nature"],
        "weather_aware": True
    }
    
    print("\n📋 Test Request:")
    print(f"   Destination: {request_data['destination']}")
    print(f"   Duration: {request_data['duration_days']} days")
    print(f"   Budget: {request_data['currency']} {request_data['budget']}")
    print(f"   Interests: {', '.join(request_data['interests'])}")
    
    print("\n🚀 Sending request to /generate-itinerary endpoint...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate-itinerary",
            json=request_data,
            timeout=120
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Response received in {elapsed:.1f}s")
        
        if response.status_code != 200:
            print(f"\n❌ Error: {response.status_code}")
            print(response.json())
            return
        
        result = response.json()
        
        # Validate new sections
        print("\n" + "=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        
        # 1. Travel Options
        print("\n✈️  TRAVEL OPTIONS:")
        if "travel_options" in result:
            travel_options = result.get("travel_options", [])
            if travel_options:
                print(f"   ✅ Found {len(travel_options)} travel option(s)")
                for i, option in enumerate(travel_options[:3], 1):
                    print(f"\n   {i}. {option.get('mode', 'N/A')}")
                    print(f"      Details: {option.get('details', 'N/A')}")
                    print(f"      Cost: ${option.get('estimated_cost', 0)}")
            else:
                print("   ⚠️  No travel options provided (should have at least 1)")
        else:
            print("   ❌ MISSING: travel_options field not found")
        
        # 2. Key Attractions
        print("\n⭐ KEY ATTRACTIONS:")
        if "key_attractions" in result:
            attractions = result.get("key_attractions", [])
            if attractions:
                print(f"   ✅ Found {len(attractions)} attraction(s)")
                for i, attraction in enumerate(attractions[:5], 1):
                    print(f"\n   {i}. {attraction.get('name', 'N/A')}")
                    print(f"      Category: {attraction.get('category', 'N/A')}")
                    print(f"      {attraction.get('description', 'N/A')[:60]}...")
            else:
                print("   ⚠️  No key attractions provided (should have 5-8)")
        else:
            print("   ❌ MISSING: key_attractions field not found")
        
        # 3. Local Beverages
        print("\n🍹 LOCAL BEVERAGES:")
        if "local_beverages" in result:
            beverages = result.get("local_beverages", [])
            if beverages:
                print(f"   ✅ Found {len(beverages)} beverage(s)")
                for i, beverage in enumerate(beverages, 1):
                    print(f"\n   {i}. {beverage.get('name', 'N/A')}")
                    print(f"      {beverage.get('description', 'N/A')[:60]}...")
                    print(f"      Where: {beverage.get('where_to_try', 'N/A')}")
                    print(f"      Cost: ${beverage.get('estimated_cost', 0)}")
            else:
                print("   ⚠️  No local beverages provided (should have 2-3)")
        else:
            print("   ❌ MISSING: local_beverages field not found")
        
        # Overall assessment
        print("\n" + "=" * 70)
        print("COMPLETENESS SCORE")
        print("=" * 70)
        
        score = 0
        max_score = 3
        
        if result.get("travel_options") and len(result["travel_options"]) > 0:
            score += 1
            print("✅ Travel Options: PASS")
        else:
            print("❌ Travel Options: FAIL")
        
        if result.get("key_attractions") and len(result["key_attractions"]) >= 5:
            score += 1
            print("✅ Key Attractions: PASS (≥5 attractions)")
        else:
            print("❌ Key Attractions: FAIL (need ≥5)")
        
        if result.get("local_beverages") and len(result["local_beverages"]) >= 2:
            score += 1
            print("✅ Local Beverages: PASS (≥2 beverages)")
        else:
            print("❌ Local Beverages: FAIL (need ≥2)")
        
        print(f"\n📊 Final Score: {score}/{max_score}")
        
        if score == max_score:
            print("🥇 PERFECT! All new features implemented correctly!")
            print("   Output is now RECRUITER-PROOF ✨")
        elif score >= 2:
            print("🥈 Good! Most features working, minor improvements needed")
        else:
            print("🥉 Needs work - some features missing")
        
        # Save full response for inspection
        with open("test_new_features_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\n💾 Full response saved to: test_new_features_response.json")
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>120s)")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_new_features()
