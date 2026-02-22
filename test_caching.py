#!/usr/bin/env python3
"""
Test script to demonstrate caching and cost tracking
"""
import requests
import time
import json


def test_caching_and_costs():
    """Test cache performance and token tracking"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Caching & Cost Control")
    print("=" * 60)
    
    # Test request
    payload = {
        "destination": "Paris, France",
        "duration_days": 3,
        "budget": 1000,
        "currency": "USD",
        "interests": ["art", "food", "culture"],
        "weather_aware": True
    }
    
    print("\n📊 FIRST REQUEST (Cold Cache)")
    print("-" * 60)
    start = time.time()
    response1 = requests.post(f"{base_url}/generate-itinerary", json=payload, timeout=120)
    duration1 = time.time() - start
    
    if response1.status_code == 200:
        print(f"✅ Success")
        print(f"⏱️  Duration: {duration1:.2f}s")
        data1 = response1.json()
        print(f"💰 Estimated Cost: ${data1['estimated_total_cost']}")
    else:
        print(f"❌ Error: {response1.status_code}")
        print(response1.text)
        return
    
    # Get stats
    print("\n📈 Getting Stats...")
    stats1 = requests.get(f"{base_url}/stats").json()
    print(f"Weather Cache: {stats1['cache']['weather']['hits']} hits, {stats1['cache']['weather']['misses']} misses")
    print(f"LLM Cache: {stats1['cache']['llm']['hits']} hits, {stats1['cache']['llm']['misses']} misses")
    print(f"Tokens Used: {stats1['tokens']['total_tokens']} (~${stats1['tokens']['estimated_cost_usd']})")
    
    # Wait a moment
    print("\n⏳ Waiting 2 seconds...")
    time.sleep(2)
    
    print("\n📊 SECOND REQUEST (Warm Cache)")
    print("-" * 60)
    print("Making identical request...")
    start = time.time()
    response2 = requests.post(f"{base_url}/generate-itinerary", json=payload, timeout=120)
    duration2 = time.time() - start
    
    if response2.status_code == 200:
        print(f"✅ Success")
        print(f"⏱️  Duration: {duration2:.2f}s")
        print(f"🚀 Speed Improvement: {((duration1 - duration2) / duration1 * 100):.1f}% faster")
    else:
        print(f"❌ Error: {response2.status_code}")
    
    # Get updated stats
    print("\n📈 Updated Stats...")
    stats2 = requests.get(f"{base_url}/stats").json()
    weather_stats = stats2['cache']['weather']
    llm_stats = stats2['cache']['llm']
    
    print(f"\nWeather Cache:")
    print(f"  Size: {weather_stats['size']}/{weather_stats['max_size']}")
    print(f"  Hit Rate: {weather_stats['hit_rate']}")
    print(f"  Total Requests: {weather_stats['total_requests']}")
    
    print(f"\nLLM Cache:")
    print(f"  Size: {llm_stats['size']}/{llm_stats['max_size']}")
    print(f"  Hit Rate: {llm_stats['hit_rate']}")
    print(f"  Total Requests: {llm_stats['total_requests']}")
    
    print(f"\nToken Usage:")
    token_stats = stats2['tokens']
    print(f"  Total Tokens: {token_stats['total_tokens']:,}")
    print(f"  Total Requests: {token_stats['total_requests']}")
    print(f"  Avg Tokens/Request: {token_stats['avg_tokens_per_request']}")
    print(f"  Estimated Cost: ${token_stats['estimated_cost_usd']}")
    
    print(f"\nRate Limiting:")
    print(f"  Limit: {stats2['rate_limit']['limit_per_minute']} requests/minute")
    print(f"  Active Clients: {stats2['rate_limit']['active_clients']}")
    
    print("\n" + "=" * 60)
    print("✨ Test Complete!")
    print("=" * 60)
    
    print("\n💡 Key Observations:")
    if llm_stats['hit_rate'] != '0.0%':
        print(f"  ✅ LLM cache is working - saved ${stats2['tokens']['estimated_cost_usd']} on 2nd request")
    if weather_stats['hit_rate'] != '0.0%':
        print(f"  ✅ Weather cache is working - reduced API calls")
    print(f"  📊 Total cost so far: ${token_stats['estimated_cost_usd']}")
    print(f"  🚀 Second request was {((duration1 - duration2) / duration1 * 100):.1f}% faster due to caching")


def test_rate_limiting():
    """Test rate limiting by making rapid requests"""
    base_url = "http://localhost:8000"
    
    print("\n\n🚦 Testing Rate Limiting")
    print("=" * 60)
    print("Making 22 rapid requests (limit is 20/minute)...")
    
    success_count = 0
    rate_limited_count = 0
    
    for i in range(22):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                success_count += 1
                print(f"  Request {i+1}: ✅")
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"  Request {i+1}: ⛔ Rate Limited")
        except Exception as e:
            print(f"  Request {i+1}: ❌ Error: {str(e)}")
        
        time.sleep(0.1)  # Small delay
    
    print("\n📊 Results:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ⛔ Rate Limited: {rate_limited_count}")
    
    if rate_limited_count > 0:
        print("\n✅ Rate limiting is working correctly!")
    else:
        print("\n⚠️  Rate limiting might not be triggered (requests too slow)")


if __name__ == "__main__":
    try:
        # Check if server is running
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            exit(1)
    except:
        print("❌ Server is not running. Start it with: python main.py")
        exit(1)
    
    # Run tests
    test_caching_and_costs()
    test_rate_limiting()
    
    print("\n🎯 All tests complete!")
