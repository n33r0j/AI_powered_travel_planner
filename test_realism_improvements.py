"""
Validation test for realism improvements:
1. Rounded pricing (no artificial precision like $42, $23)
2. Comprehensive travel options (airports, trains, ferries)
3. Realistic accommodation pricing
4. Correct currency context in tips
"""
import requests
import json
import time
import re

BASE_URL = "http://localhost:8000"

def is_rounded_naturally(price):
    """Check if price is rounded to natural numbers"""
    if price == 0:
        return True  # Free items are OK
    
    # Good: multiples of 5, 10, 50, 100
    if price >= 100:
        return price % 50 == 0 or price % 100 == 0
    elif price >= 20:
        return price % 10 == 0 or price % 5 == 0
    else:
        return price % 5 == 0 or price % 10 == 0

def check_currency_context(tips, budget, currency):
    """Check if travel tips reference the correct currency"""
    issues = []
    for tip in tips:
        # Look for currency mentions
        if '$' in tip or 'USD' in tip or '₹' in tip or 'INR' in tip or 'budget' in tip.lower():
            # Check if it mentions the wrong currency
            if currency == 'USD' and ('₹' in tip or 'INR' in tip):
                issues.append(f"Wrong currency in tip: {tip}")
            elif currency == 'INR' and ('USD' in tip and 'INR' not in tip):
                # If budget is in INR but tip only mentions USD, that's suspicious
                if 'budget' in tip.lower():
                    issues.append(f"Currency context issue in tip: {tip}")
    return issues

def test_realism_improvements():
    """Test all realism improvements"""
    
    print("🧪 Testing Realism Improvements")
    print("=" * 70)
    
    # Test with INR to catch currency context issues
    request_data = {
        "destination": "Kochi, India",
        "duration_days": 3,
        "budget": 15000,
        "currency": "INR",
        "interests": ["culture", "food", "history", "beaches"],
        "weather_aware": True
    }
    
    print("\n📋 Test Request:")
    print(f"   Destination: {request_data['destination']}")
    print(f"   Duration: {request_data['duration_days']} days")
    print(f"   Budget: {request_data['currency']} {request_data['budget']}")
    
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
        print("REALISM VALIDATION")
        print("=" * 70)
        
        issues = []
        passed = []
        
        # 1. CHECK PRICING REALISM
        print("\n💰 PRICING REALISM:")
        all_prices = []
        
        # Collect all prices from itinerary
        for day in result.get("itinerary", []):
            for activity in day.get("activities", []):
                price = activity.get("estimated_cost", 0)
                if price > 0:
                    all_prices.append((price, f"Activity: {activity['name']}"))
            for food in day.get("food_recommendations", []):
                price = food.get("estimated_cost", 0)
                if price > 0:
                    all_prices.append((price, f"Food: {food['dish']}"))
        
        # Check accommodations
        for hotel in result.get("accommodation_suggestions", []):
            price = hotel.get("price_per_night", 0)
            if price > 0:
                all_prices.append((price, f"Hotel: {hotel['name']}"))
        
        # Check travel options
        for option in result.get("travel_options", []):
            price = option.get("estimated_cost", 0)
            if price > 0:
                all_prices.append((price, f"Travel: {option['mode']}"))
        
        # Check beverages
        for bev in result.get("local_beverages", []):
            price = bev.get("estimated_cost", 0)
            if price > 0:
                all_prices.append((price, f"Beverage: {bev['name']}"))
        
        badly_rounded = []
        for price, source in all_prices:
            if not is_rounded_naturally(price):
                badly_rounded.append(f"   ${price} - {source}")
        
        if badly_rounded:
            print("   ⚠️  Found artificial precision:")
            for item in badly_rounded[:5]:  # Show first 5
                print(item)
            issues.append(f"Pricing: {len(badly_rounded)} prices not naturally rounded")
        else:
            print("   ✅ All prices naturally rounded (multiples of $5, $10, $50)")
            passed.append("Pricing realism")
        
        # 2. CHECK TRAVEL OPTIONS COMPLETENESS
        print("\n✈️  TRAVEL OPTIONS COMPLETENESS:")
        travel_options = result.get("travel_options", [])
        
        if not travel_options:
            print("   ❌ No travel options provided")
            issues.append("Travel options: Missing entirely")
        else:
            has_airport = any('airport' in opt.get('details', '').lower() or 
                            'cok' in opt.get('details', '').lower() for opt in travel_options)
            has_train = any('train' in opt.get('mode', '').lower() or 
                          'junction' in opt.get('details', '').lower() or
                          'ers' in opt.get('details', '').lower() for opt in travel_options)
            has_codes = any(re.search(r'\\([A-Z]{3}\\)', opt.get('details', '')) for opt in travel_options)
            
            print(f"   Found {len(travel_options)} option(s):")
            for opt in travel_options:
                print(f"   • {opt.get('mode')}: {opt.get('details', '')[:60]}")
            
            if not has_airport:
                issues.append("Travel options: Missing airport details")
                print("   ⚠️  No airport code/details found")
            else:
                print("   ✅ Includes airport information")
            
            if not has_train and 'india' in request_data['destination'].lower():
                print("   ⚠️  No train station details (expected for India)")
                issues.append("Travel options: Missing train station")
            elif has_train:
                print("   ✅ Includes train station")
            
            if has_codes:
                print("   ✅ Uses specific codes (e.g., COK, ERS)")
                passed.append("Travel options with codes")
            else:
                print("   ⚠️  No airport/station codes used")
        
        # 3. CHECK ACCOMMODATION PRICING REALISM
        print("\n🏨 ACCOMMODATION PRICING:")
        hotels = result.get("accommodation_suggestions", [])
        
        if hotels:
            hostel_prices = [h['price_per_night'] for h in hotels if 'hostel' in h.get('type', '').lower()]
            hotel_prices = [h['price_per_night'] for h in hotels if 'hotel' in h.get('type', '').lower()]
            
            print(f"   Hostels: {hostel_prices}")
            print(f"   Hotels: {hotel_prices}")
            
            # For India, hostels should be $10-30, hotels $40-150
            unrealistic_low = [p for p in hostel_prices if p < 8]  # $8 is too low even for India
            unrealistic_high = [p for p in hotel_prices if p > 200 and result.get('estimated_total_cost', 0) < 500]
            
            if unrealistic_low:
                print(f"   ⚠️  Unrealistically low hostel prices: ${unrealistic_low}")
                issues.append(f"Accommodation: Prices too low ({unrealistic_low})")
            elif all(p >= 10 for p in hostel_prices):
                print("   ✅ Realistic hostel pricing (≥$10/night)")
                passed.append("Accommodation pricing")
            
        # 4. CHECK CURRENCY CONTEXT IN TIPS
        print("\n💡 CURRENCY CONTEXT IN TIPS:")
        tips = result.get("travel_tips", [])
        currency_issues = check_currency_context(tips, request_data['budget'], request_data['currency'])
        
        if currency_issues:
            print("   ⚠️  Currency context issues found:")
            for issue in currency_issues:
                print(f"   {issue}")
            issues.extend(currency_issues)
        else:
            print("   ✅ No currency context bugs detected")
            passed.append("Currency context")
        
        # FINAL SCORE
        print("\n" + "=" * 70)
        print("FINAL ASSESSMENT")
        print("=" * 70)
        
        total_checks = 4
        passed_count = len([p for p in passed if any(k in p.lower() for k in ['pricing', 'travel', 'accommodation', 'currency'])])
        
        print(f"\n✅ Passed: {passed_count}/{total_checks}")
        print(f"❌ Issues: {len(issues)}")
        
        if len(issues) == 0:
            print("\n🥇 PERFECT! All realism improvements working!")
            print("   Score: 10/10")
        elif len(issues) <= 2:
            print("\n🥈 GOOD! Minor improvements still possible")
            print(f"   Score: {10 - len(issues)}/10")
        else:
            print("\n🥉 NEEDS WORK - Several issues detected")
            print(f"   Score: {max(5, 10 - len(issues))}/10")
        
        if issues:
            print("\n📋 Issues to address:")
            for i, issue in enumerate(issues[:5], 1):
                print(f"   {i}. {issue}")
        
        # Save response
        with open("test_realism_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\n💾 Full response saved to: test_realism_response.json")
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>120s)")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_realism_improvements()
