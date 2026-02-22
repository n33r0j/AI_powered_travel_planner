# ⚡ Caching & Cost Control

## Overview

The AI Travel Planner implements production-grade caching and cost tracking to optimize performance and reduce API costs.

## Features Implemented

### 1. **Weather Caching** (6-hour TTL)
- **Geocoding Cache**: 7-day TTL (coordinates don't change)
- **Forecast Cache**: 6-hour TTL (balances freshness vs cost)
- **Impact**: Reduces Open-Meteo API calls by ~80% for repeated destinations

### 2. **LLM Response Caching** (24-hour TTL)
- Caches identical itinerary requests
- Cache key: `destination:duration:budget:interests:weather_aware`
- **Impact**: Near-instant responses for duplicate requests
- **Cost Savings**: $0.10 per 1M tokens avoided

### 3. **Token Usage Tracking**
- Logs input/output tokens for every Gemini API call
- Tracks cumulative usage and estimated costs
- Real-time cost monitoring via `/stats` endpoint

#### Token Costs (Gemini 2.5 Flash)
```
~$0.10 per 1M tokens
Average request: 2,000-4,000 tokens (~$0.0004)
With caching: 50-80% cost reduction
```

### 4. **Rate Limiting** (20 requests/minute)
- In-memory rate limiter per client IP
- Protects against abuse and excessive costs
- Returns `HTTP 429` when limit exceeded
- **Production Ready**: Easily replaceable with Redis-based limiter

## Monitoring Endpoint

### `GET /stats`
Returns real-time system statistics:

```json
{
  "cache": {
    "weather": {
      "size": 12,
      "max_size": 500,
      "hits": 45,
      "misses": 12,
      "hit_rate": "78.9%",
      "total_requests": 57
    },
    "llm": {
      "size": 8,
      "max_size": 200,
      "hits": 3,
      "misses": 8,
      "hit_rate": "27.3%",
      "total_requests": 11
    }
  },
  "tokens": {
    "total_tokens": 35420,
    "total_requests": 8,
    "avg_tokens_per_request": 4428,
    "estimated_cost_usd": 0.0035
  },
  "rate_limit": {
    "limit_per_minute": 20,
    "active_clients": 2
  }
}
```

## Testing

Run the caching test script:

```bash
python test_caching.py
```

**Expected Results:**
- First request: ~10-15 seconds (cold cache)
- Second identical request: <1 second (cache hit)
- 70-80% speed improvement
- Token cost only incurred once

## Architecture

```
Request Flow:
┌─────────────────────┐
│   User Request      │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   Rate Limiter      │ ← 20 req/min per IP
└──────────┬──────────┘
           │
           ↓
    ┌─────────────┐
    │ Cache Check │
    └──────┬──────┘
           │
     ┌─────┴─────┐
     │           │
   Hit ✓      Miss ✗
     │           │
     │           ↓
     │    ┌──────────────┐
     │    │ Weather API  │ ← cached 6h
     │    └──────┬───────┘
     │           │
     │           ↓
     │    ┌──────────────┐
     │    │ Gemini LLM   │ ← cached 24h
     │    │ + Log Tokens │
     │    └──────┬───────┘
     │           │
     │           ↓
     │    ┌──────────────┐
     │    │ Cache Store  │
     │    └──────┬───────┘
     │           │
     └───────────┼─────┘
                 │
                 ↓
          ┌─────────────┐
          │   Response  │
          └─────────────┘
```

## Cache Management

### Manual Cache Control

```python
from utils.cache import weather_cache, llm_cache

# Clear all caches
weather_cache.clear()
llm_cache.clear()

# Get stats
print(weather_cache.stats())
print(llm_cache.stats())
```

### Production Considerations

For multi-instance deployments, replace in-memory cache with:
- **Redis**: Distributed caching
- **Memcached**: High-performance caching
- **slowapi**: Redis-based rate limiting

Example Redis integration:
```python
from redis import Redis
from slowapi import Limiter

redis_client = Redis(host='localhost', port=6379)
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")
```

## Cost Optimization Tips

1. **Enable Caching**: 50-80% cost reduction on repeat requests
2. **Weather-Aware Toggle**: Disable for indoor destinations (saves 1 API call)
3. **Monitor `/stats`**: Track cache hit rates and token usage
4. **Longer TTLs**: Increase cache duration for static data
5. **Budget Limits**: Set monthly API spend alerts

## Real-World Impact

**Before Caching:**
- 100 requests/day
- ~400,000 tokens/day
- ~$0.40/day = $12/month

**After Caching (70% hit rate):**
- 30 API calls/day  
- ~120,000 tokens/day
- ~$0.12/day = $3.60/month

**Savings: 70% cost reduction + 80% faster responses**

## Logs

Token usage is automatically logged:

```
INFO - Token usage: 1200 input + 2800 output = 4000 total (~$0.000400 this request, ~$0.0012 total)
INFO - LLM cache hit for Tokyo, Japan (3d, $1500)
INFO - Weather forecast cache hit for Paris, France
```

## Next Steps

- [ ] Add Redis for distributed caching
- [ ] Implement cache warming for popular destinations  
- [ ] Add Prometheus metrics export
- [ ] Set up Grafana dashboards
- [ ] Add cost alerts (SNS/email)
