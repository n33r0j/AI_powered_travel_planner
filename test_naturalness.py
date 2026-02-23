"""
Test for naturalness improvements:
1. International flights handled correctly ($0 with disclaimer)
2. Budget utilization 85-97% (not 98-100%)
3. Price disclaimer in travel tips
4. Natural price variation
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_naturalness():
    """Test all naturalness improvements"""
    
    print("🧪 Testing Naturalness Improvements")
    print("=" * 70)
    
    # Test with Tokyo to check international flight handling
    request_data = {
        "destination": "Tokyo, Japan",
        "duration_days": 4,
        "budget": 1500,
        "currency": "USD",
        "interests": ["culture", "food", "technology", "temples"],
        "weather_aware": True
    }
    
    print("\n📋 Test Request:")
    print(f"   Destination: {request_data['destination']}")
    print(f"   Duration: {request_data['duration_days']} days")
    print(f"   Budget: ${request_data['budget']}")
    
    print("\n🚀 Sending request...")
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
        
        print("\n" + "=" * 70)
        print("NATURALNESS VALIDATION")
        print("=" * 70)
        
        issues = []
        passed = []
        
        # 1. CHECK INTERNATIONAL FLIGHT HANDLING
        print("\n✈️  INTERNATIONAL FLIGHT HANDLING:")
        travel_options = result.get("travel_options", [])
        
        flight_found = False
        flight_cost = None
        flight_details = None
        
        for option in travel_options:
            if 'flight' in option.get('mode', '').lower() or 'air' in option.get('mode', '').lower():
                flight_found = True
                flight_cost = option.get('estimated_cost', None)
                flight_details = option.get('details', '')
                break
        
        if flight_found:
            print(f"   Found flight option:")
            print(f"   Cost: ${flight_cost}")
            print(f"   Details: {flight_details[:80]}...")
            
            if flight_cost == 0:
                if 'not included' in flight_details.lower() or 'varies by origin' in flight_details.lower():
                    print("   ✅ Correctly marked as $0 with disclaimer")
                    passed.append("International flight handling")
                else:
                    print("   ⚠️  Flight is $0 but missing 'not included' disclaimer")
                    issues.append("Missing flight disclaimer")
            else:
                print(f"   ⚠️  Flight has specific cost (${flight_cost}) - should be $0 with disclaimer for international destinations")
        else:
            print("   ⚠️  No flight option found")
            issues.append("No flight option in travel_options")
        
        # 2. CHECK BUDGET UTILIZATION
        print("\n💰 BUDGET UTILIZATION:")
        estimated_cost = result.get("estimated_total_cost", 0)
        budget = request_data["budget"]
        utilization = (estimated_cost / budget) * 100
        
        print(f"   Budget: ${budget}")
        print(f"   Estimated Cost: ${estimated_cost}")
        print(f"   Utilization: {utilization:.1f}%")
        
        if utilization > 97:
            print(f"   ⚠️  Utilization {utilization:.1f}% looks artificially optimized (should be 85-97%)")
            issues.append(f"Budget utilization too high: {utilization:.1f}%")
        elif utilization < 85:
            print(f"   ⚠️  Utilization {utilization:.1f}% is too low (should be 85-97%)")
            issues.append(f"Budget utilization too low: {utilization:.1f}%")
        else:
            print(f"   ✅ Natural utilization: {utilization:.1f}% (sweet spot: 85-97%)")
            passed.append("Budget utilization")
        
        # 3. CHECK PRICE DISCLAIMER IN TRAVEL TIPS
        print("\n💡 PRICE DISCLAIMER:")
        tips = result.get("travel_tips", [])
        
        has_price_disclaimer = any('price' in tip.lower() and ('approximate' in tip.lower() or 'vary' in tip.lower()) 
                                   for tip in tips)
        
        if has_price_disclaimer:
            disclaimer_tip = [tip for tip in tips if 'price' in tip.lower() and 'approximate' in tip.lower()][0]
            print(f"   ✅ Found disclaimer: '{disclaimer_tip}'")
            passed.append("Price disclaimer")
        else:
            print("   ⚠️  No price disclaimer found in travel tips")
            issues.append("Missing price disclaimer")
        
        # 4. CHECK PRICE VARIATION
        print("\n📊 PRICE VARIATION ANALYSIS:")
        all_prices = []
        
        # Collect all prices
        for day in result.get("itinerary", []):
            for activity in day.get("activities", []):
                price = activity.get("estimated_cost", 0)
                if price > 0:
                    all_prices.append(price)
            for food in day.get("food_recommendations", []):
                price = food.get("estimated_cost", 0)
                if price > 0:
                    all_prices.append(price)
        
        # Check for variation (not just multiples of 10)
        if all_prices:
            multiples_of_10 = sum(1 for p in all_prices if p % 10 == 0)
            multiples_of_5 = sum(1 for p in all_prices if p % 5 == 0 and p % 10 != 0)
            other = len(all_prices) - multiples_of_10 - multiples_of_5
            
            print(f"   Total prices: {len(all_prices)}")
            print(f"   Multiples of $10: {multiples_of_10} ({multiples_of_10/len(all_prices)*100:.1f}%)")
            print(f"   Multiples of $5: {multiples_of_5} ({multiples_of_5/len(all_prices)*100:.1f}%)")
            print(f"   Other: {other}")
            
            # Good variation has some $5 multiples, not all $10
            if multiples_of_5 >= 2 or other >= 2:
                print("   ✅ Natural price variation detected")
                passed.append("Price variation")
            elif multiples_of_10 == len(all_prices):
                print("   ⚠️  All prices are multiples of $10 - appears too uniform")
                issues.append("Prices lack variation")
            else:
                print("   ✓ Acceptable price distribution")
        
        # SAMPLE PRICES
        print("\n   Sample prices:")
        for price in sorted(set(all_prices))[:10]:
            print(f"   ${price}")
        
        # FINAL SCORE
        print("\n" + "=" * 70)
        print("FINAL ASSESSMENT")
        print("=" * 70)
        
        total_checks = 4
        passed_count = len([p for p in passed if any(k in p.lower() for k in ['flight', 'budget', 'disclaimer', 'variation'])])
        
        print(f"\n✅ Passed: {passed_count}/{total_checks}")
        print(f"❌ Issues: {len(issues)}")
        
        if len(issues) == 0:
            print("\n🥇 PERFECT! All naturalness improvements working!")
            print("   Output feels authentic and organic")
        elif len(issues) <= 2:
            print("\n🥈 GOOD! Minor improvements achieved")
            print(f"   Score: {10 - len(issues)}/10")
        else:
            print("\n🥉 NEEDS WORK - Several issues detected")
            print(f"   Score: {max(5, 10 - len(issues))}/10")
        
        if issues:
            print("\n📋 Issues to address:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        
        # Save response
        with open("test_naturalness_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\n💾 Full response saved to: test_naturalness_response.json")
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_naturalness()
