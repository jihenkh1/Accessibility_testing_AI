# Token Counting & Async API - Visual Guide

## 📊 Token Counting Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SimpleAIClient                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │ analyze_accessibility_issue()                  │         │
│  └────────────────┬───────────────────────────────┘         │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │ _make_api_call()                               │         │
│  │  • Send request to OpenRouter                  │         │
│  │  • Get response with token counts              │         │
│  └────────────────┬───────────────────────────────┘         │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │ Extract usage from response:                   │         │
│  │                                                 │         │
│  │  {                                              │         │
│  │    "usage": {                                   │         │
│  │      "prompt_tokens": 150,                      │         │
│  │      "completion_tokens": 85,                   │         │
│  │      "total_tokens": 235                        │         │
│  │    }                                            │         │
│  │  }                                              │         │
│  └────────────────┬───────────────────────────────┘         │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │ UsageStats.add_usage()                         │         │
│  │  • total_prompt_tokens += 150                  │         │
│  │  • total_completion_tokens += 85               │         │
│  │  • total_tokens += 235                         │         │
│  │  • Calculate cost (free models = $0)           │         │
│  │  • Increment successful_requests                │         │
│  └────────────────────────────────────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Later, query stats:

┌────────────────────────────────────────────────┐
│ client.get_usage_stats()                       │
├────────────────────────────────────────────────┤
│ Returns:                                       │
│  {                                             │
│    "total_requests": 5,                        │
│    "successful_requests": 5,                   │
│    "total_tokens": 1,175,                      │
│    "estimated_cost_usd": 0.0                   │
│  }                                             │
└────────────────────────────────────────────────┘
```

---

## ⚡ Async Batch Processing Flow

### Sequential (Sync) - BEFORE

```
Issue 1 ────────────► [API] ────────────► Result 1  (2 seconds)
                                            │
Issue 2 ────────────────────────────────────┴─► [API] ────────────► Result 2  (2 seconds)
                                                                       │
Issue 3 ────────────────────────────────────────────────────────────────┴─► [API] ──► Result 3  (2 seconds)

Total Time: 6 seconds
```

### Parallel (Async) - AFTER

```
Issue 1 ────┐
Issue 2 ────┼──► [Semaphore]  ───┬──► [API] ──► Result 1  ┐
Issue 3 ────┘    (max 3)         ├──► [API] ──► Result 2  ├─► All Results
                                 └──► [API] ──► Result 3  ┘

Total Time: 2 seconds (3x faster!)
```

**With Semaphore (max_concurrent=3):**

```
┌─────────────────────────────────────────────────────────┐
│  Semaphore (3 slots)                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [Slot 1: Issue 1] ───► API ───► Result 1               │
│  [Slot 2: Issue 2] ───► API ───► Result 2               │
│  [Slot 3: Issue 3] ───► API ───► Result 3               │
│                                                          │
│  Issue 4 waits...  ───► [Slot 1 freed] ───► API ───► Result 4
│  Issue 5 waits...  ───► [Slot 2 freed] ───► API ───► Result 5
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Usage Example Timeline

```
Time (seconds)
  0s │ client = SimpleAIClient()
     │ client.reset_usage_stats()
     │
  1s │ issues = [...]  # 10 issues
     │
  2s │ results = await client.analyze_batch_async(
     │     issues,
     │     max_concurrent=5
     │ )
     │
     │ ┌─────────────────────────────────────┐
  3s │ │ Batch 1 (5 concurrent):             │
     │ │  [1] [2] [3] [4] [5] ──► API calls  │
     │ └─────────────────────────────────────┘
     │
  5s │ ┌─────────────────────────────────────┐
     │ │ Batch 2 (5 concurrent):             │
     │ │  [6] [7] [8] [9] [10] ──► API calls │
     │ └─────────────────────────────────────┘
     │
  7s │ All results returned
     │
     │ stats = client.get_usage_stats()
     │
  8s │ print(stats)
     │ >>> {
     │       "total_requests": 10,
     │       "successful_requests": 10,
     │       "total_tokens": 2350,
     │       "estimated_cost_usd": 0.0,
     │       "success_rate": 100.0
     │     }
```

**Sequential would take:** 10 issues × 2s = 20 seconds  
**Async takes:** 2 batches × 2s = 4 seconds  
**Speedup:** 5x faster! ⚡

---

## 💰 Cost Tracking Example

### Free Model (deepseek-r1t2-chimera:free)

```
┌──────────────────────────────────────────────────┐
│ Configuration:                                   │
│  price_per_1m_prompt_tokens = 0.0               │
│  price_per_1m_completion_tokens = 0.0           │
└──────────────────────────────────────────────────┘

After 100 API calls:

  Total Tokens: 23,500
  
  Cost Calculation:
  ─────────────────
  Prompt:     15,000 tokens × ($0 / 1M) = $0.00
  Completion:  8,500 tokens × ($0 / 1M) = $0.00
  ────────────────────────────────────────────
  Total Cost:                             $0.00
```

### Paid Model (e.g., GPT-4)

```
┌──────────────────────────────────────────────────┐
│ Configuration:                                   │
│  price_per_1m_prompt_tokens = 30.0              │
│  price_per_1m_completion_tokens = 60.0          │
└──────────────────────────────────────────────────┘

After 100 API calls:

  Total Tokens: 23,500
  
  Cost Calculation:
  ─────────────────
  Prompt:     15,000 tokens × ($30 / 1M) = $0.45
  Completion:  8,500 tokens × ($60 / 1M) = $0.51
  ────────────────────────────────────────────
  Total Cost:                             $0.96
```

---

## 🎯 Concurrency Control

### max_concurrent=1 (Sequential)

```
Time: ──────────────────────────────────────────►
      [1]──► [2]──► [3]──► [4]──► [5]──►
      
Total: 10 seconds (2s × 5 issues)
```

### max_concurrent=3 (Balanced)

```
Time: ──────────────────────────────────────────►
      [1]──►
      [2]──► [4]──►
      [3]──► [5]──►
      
Total: 4 seconds (2 batches × 2s)
```

### max_concurrent=5 (Aggressive)

```
Time: ──────────────────────────────────────────►
      [1]──►
      [2]──►
      [3]──►
      [4]──►
      [5]──►
      
Total: 2 seconds (1 batch × 2s)
```

**Trade-off:**
- ⬆️ Higher concurrency = Faster ⚡
- ⬇️ Lower concurrency = Safer (less risk of rate limits)

---

## 📊 Usage Stats Over Time

```
Request Timeline:

0s    ┌─────────────────────────────────────┐
      │ stats = {                           │
      │   total_requests: 0                 │
      │   total_tokens: 0                   │
      │ }                                   │
      └─────────────────────────────────────┘

2s    Request 1: +235 tokens
      ┌─────────────────────────────────────┐
      │ stats = {                           │
      │   total_requests: 1                 │
      │   total_tokens: 235                 │
      │ }                                   │
      └─────────────────────────────────────┘

4s    Request 2: +240 tokens
      ┌─────────────────────────────────────┐
      │ stats = {                           │
      │   total_requests: 2                 │
      │   total_tokens: 475                 │
      │ }                                   │
      └─────────────────────────────────────┘

6s    Request 3 FAILED
      ┌─────────────────────────────────────┐
      │ stats = {                           │
      │   total_requests: 3                 │
      │   successful_requests: 2            │
      │   failed_requests: 1                │
      │   total_tokens: 475                 │
      │   success_rate: 66.67%              │
      │ }                                   │
      └─────────────────────────────────────┘
```

---

## 🔧 Architecture: Sync vs Async

### Sync Architecture

```
┌───────────────────────────────────────────────┐
│ analyze_accessibility_issue()                 │
├───────────────────────────────────────────────┤
│                                               │
│  For each issue:                              │
│   ┌─────────────────────────────┐            │
│   │ _make_api_call()            │            │
│   │  • requests.post()          │            │
│   │  • Wait for response        │            │
│   │  • Track usage              │            │
│   └─────────────────────────────┘            │
│        │                                      │
│        ▼                                      │
│   Return result                               │
│                                               │
└───────────────────────────────────────────────┘
```

### Async Architecture

```
┌───────────────────────────────────────────────┐
│ analyze_batch_async(issues, max_concurrent=5) │
├───────────────────────────────────────────────┤
│                                               │
│  ┌────────────────────────────┐              │
│  │ Semaphore (max 5 slots)    │              │
│  └────────────────────────────┘              │
│                                               │
│  For all issues (parallel):                   │
│   ┌─────────────────────────────┐            │
│   │ _make_api_call_async()      │            │
│   │  • aiohttp.post()           │            │
│   │  • Await response           │            │
│   │  • Track usage              │            │
│   └─────────────────────────────┘            │
│        │                                      │
│        ▼                                      │
│   asyncio.gather(*all_tasks)                 │
│                                               │
└───────────────────────────────────────────────┘
```

---

## 🎓 When to Use What

```
┌──────────────────────────────────────────────────────────┐
│ Number of Issues to Analyze                              │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  1-5 issues          Use: analyze_accessibility_issue()  │
│                      (sync version)                       │
│                      Reason: Simple, no overhead          │
│                                                           │
│  ─────────────────────────────────────────────────────── │
│                                                           │
│  10-50 issues        Use: analyze_batch_async()          │
│                      max_concurrent=3-5                   │
│                      Reason: 3-5x faster                  │
│                                                           │
│  ─────────────────────────────────────────────────────── │
│                                                           │
│  50+ issues          Use: analyze_batch_async()          │
│                      max_concurrent=5-10                  │
│                      Reason: Massive speedup              │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## ✅ Summary

### Token Counting ✓

```
Before: No visibility into API usage
After:  Full metrics (requests, tokens, cost, success rate)
```

### Async API ✓

```
Before: Sequential processing (slow for large batches)
After:  Parallel processing with controlled concurrency (3-5x faster)
```

### Production Ready ✓

```
✅ Rate limiting (from previous implementation)
✅ Retry with exponential backoff (from previous implementation)
✅ Token counting & cost tracking (NEW)
✅ Async batch processing (NEW)
```

**Result:** Enterprise-grade AI client ready for production! 🚀
