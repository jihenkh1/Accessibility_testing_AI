# Token Counting & Async API Features

## 🎯 What Changed

Added two critical production features to `SimpleAIClient`:

1. **✅ Token Counting & Cost Tracking** - Track API usage and costs in real-time
2. **✅ Async API Calls** - Process multiple issues in parallel for 3-5x speed improvement

---

## 📊 Token Counting & Cost Tracking

### What It Does

Automatically tracks every API call's token usage and estimated cost:

- **Prompt tokens** (input you send)
- **Completion tokens** (AI's response)
- **Total tokens** (sum of both)
- **Estimated cost** (based on model pricing)
- **Success/failure rates**

### How to Use

```python
from accessibility_ai.simple_ai import SimpleAIClient

client = SimpleAIClient()

# Make some API calls
result1 = client.analyze_accessibility_issue("Missing alt text", rule_id="image-alt")
result2 = client.analyze_accessibility_issue("Low contrast", rule_id="color-contrast")

# Get usage statistics
stats = client.get_usage_stats()

print(f"Total requests: {stats['total_requests']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Estimated cost: ${stats['estimated_cost_usd']}")
print(f"Success rate: {stats['success_rate']}%")

# Reset stats (e.g., for new session)
client.reset_usage_stats()
```

### Output Example

```json
{
  "total_requests": 25,
  "successful_requests": 24,
  "failed_requests": 1,
  "total_prompt_tokens": 15420,
  "total_completion_tokens": 8760,
  "total_tokens": 24180,
  "estimated_cost_usd": 0.0,
  "success_rate": 96.0
}
```

### Cost Calculation

For **free models** (like `deepseek-r1t2-chimera:free`):
- Cost is always `$0.00`

For **paid models**, update pricing in `__init__`:

```python
# Example for GPT-4
self.price_per_1m_prompt_tokens = 30.0      # $30 per 1M prompt tokens
self.price_per_1m_completion_tokens = 60.0  # $60 per 1M completion tokens
```

Cost formula:
```
cost = (prompt_tokens / 1,000,000 × prompt_price) + 
       (completion_tokens / 1,000,000 × completion_price)
```

---

## ⚡ Async API Calls

### What It Does

Process multiple accessibility issues **in parallel** instead of sequentially:

- **3-5x faster** for batches of 10+ issues
- **Controlled concurrency** (don't overwhelm the API)
- **Same reliability** as sync version (automatic retries, error handling)

### When to Use

✅ **Use Async When:**
- Analyzing 10+ issues at once
- Processing entire scan results (50-100+ issues)
- Time is critical (CI/CD pipelines)

❌ **Use Sync When:**
- Single issue analysis
- Real-time UI requests (< 5 issues)
- Simpler code is preferred

### Single Issue (Async)

```python
import asyncio
from accessibility_ai.simple_ai import SimpleAIClient

async def analyze_one():
    client = SimpleAIClient()
    
    result = await client.analyze_accessibility_issue_async(
        issue_description="Button has no accessible name",
        rule_id="button-name",
        framework="react"
    )
    
    print(f"Priority: {result['priority']}")
    print(f"Fix: {result['fix_suggestion']}")

# Run it
asyncio.run(analyze_one())
```

### Batch Processing (Async)

```python
import asyncio
from accessibility_ai.simple_ai import SimpleAIClient

async def analyze_many():
    client = SimpleAIClient()
    
    # Your issues from axe/Pa11y report
    issues = [
        {"description": "Missing alt text", "rule_id": "image-alt"},
        {"description": "Low contrast", "rule_id": "color-contrast"},
        {"description": "No button label", "rule_id": "button-name"},
        # ... 50 more issues
    ]
    
    # Process all in parallel (max 5 concurrent)
    results = await client.analyze_batch_async(
        issues, 
        max_concurrent=5  # Adjust based on API limits
    )
    
    # Results are in same order as input
    for issue, result in zip(issues, results):
        if result:
            print(f"{issue['description']}: {result['priority']}")

asyncio.run(analyze_many())
```

### Concurrency Control

The `max_concurrent` parameter controls how many API calls run simultaneously:

| Value | Use Case | Speed | API Load |
|-------|----------|-------|----------|
| 1     | Testing, debugging | Slowest | Minimal |
| 3     | Conservative (default) | Good | Low |
| 5     | Balanced | Great | Medium |
| 10    | Aggressive | Fastest | High |

**Recommendation:** Start with `5` and adjust based on:
- API rate limits (429 errors = lower it)
- Your API plan tier
- Network stability

---

## 🔄 Performance Comparison

### Sequential (Sync)

```python
# 10 issues × 2 seconds each = 20 seconds
for issue in issues:
    result = client.analyze_accessibility_issue(issue["description"])
```

**Time:** ~20 seconds

### Parallel (Async)

```python
# 10 issues / 5 concurrent = 2 batches × 2 seconds = 4 seconds
results = await client.analyze_batch_async(issues, max_concurrent=5)
```

**Time:** ~4 seconds (5x faster!)

---

## 📈 Real-World Example

### Scenario: Analyze 50 accessibility issues from axe-core report

```python
import asyncio
from accessibility_ai.simple_ai import SimpleAIClient
import json

async def process_scan_report(report_path: str):
    # Load axe report
    with open(report_path) as f:
        report = json.load(f)
    
    client = SimpleAIClient()
    client.reset_usage_stats()
    
    # Convert violations to issue format
    issues = []
    for violation in report.get("violations", []):
        for node in violation.get("nodes", []):
            issues.append({
                "description": violation["description"],
                "rule_id": violation["id"],
                "impact": violation.get("impact"),
                "framework": "html"  # or detect from context
            })
    
    print(f"Processing {len(issues)} issues...")
    
    # Analyze all in parallel
    results = await client.analyze_batch_async(
        issues,
        max_concurrent=5
    )
    
    # Show statistics
    stats = client.get_usage_stats()
    print(f"\n✅ Complete!")
    print(f"   Analyzed: {stats['successful_requests']}/{stats['total_requests']}")
    print(f"   Tokens: {stats['total_tokens']:,}")
    print(f"   Cost: ${stats['estimated_cost_usd']:.4f}")
    
    # Save enriched results
    enriched = []
    for issue, result in zip(issues, results):
        if result:
            enriched.append({**issue, "ai_analysis": result})
    
    with open("enriched_report.json", "w") as f:
        json.dump(enriched, f, indent=2)

# Run it
asyncio.run(process_scan_report("axe-report.json"))
```

**Output:**
```
Processing 53 issues...

✅ Complete!
   Analyzed: 52/53
   Tokens: 48,234
   Cost: $0.0000
```

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_async_and_usage.py
```

Tests include:
1. ✅ Usage tracking accuracy
2. ✅ Async single issue
3. ✅ Async batch processing (5 issues)
4. ✅ Sync vs Async performance comparison

---

## 🔧 Implementation Details

### New Classes

**`UsageStats` (dataclass):**
- Tracks cumulative token usage
- Calculates estimated costs
- Thread-safe (all updates within locks)

### New Methods

**`get_usage_stats()` → dict:**
- Returns current usage statistics
- Safe to call anytime

**`reset_usage_stats()`:**
- Resets counters to zero
- Useful for session-based tracking

**`analyze_accessibility_issue_async()` → coroutine:**
- Async version of main analysis method
- Same parameters as sync version

**`analyze_batch_async(issues, max_concurrent)` → coroutine:**
- Batch processing with concurrency control
- Uses asyncio.Semaphore for limiting
- Returns results in input order

### Technical Notes

1. **Thread Safety:** Usage stats are updated within the rate limiter lock
2. **Async Rate Limiting:** Controlled via `max_concurrent` semaphore, not per-call delays
3. **Error Handling:** Failed requests increment `failed_requests` counter
4. **Token Extraction:** Uses `usage` field from OpenRouter API response
5. **Cost Calculation:** Configurable per-model pricing (default: $0 for free models)

---

## 🚀 Next Steps

### Expose in API

Add usage stats endpoint:

```python
# backend/api/routes/scans.py
@router.get("/api/usage-stats")
async def get_ai_usage_stats():
    """Get current AI usage statistics"""
    from accessibility_ai.analyzer import AccessibilityAnalyzer
    
    analyzer = AccessibilityAnalyzer()
    if analyzer.ai_client:
        return analyzer.ai_client.get_usage_stats()
    return {"error": "AI client not available"}
```

### Display in Frontend

```typescript
// Show token usage in dashboard
const stats = await fetch('/api/usage-stats').then(r => r.json());

console.log(`Total tokens used: ${stats.total_tokens}`);
console.log(`Estimated cost: $${stats.estimated_cost_usd}`);
```

### Use Async in Analyzer

Update `analyzer.py` to use batch async:

```python
# In AccessibilityAnalyzer.analyze()
if len(to_enrich) > 10:
    # Use async for large batches
    loop = asyncio.get_event_loop()
    enriched = loop.run_until_complete(
        self.ai_client.analyze_batch_async(to_enrich, max_concurrent=5)
    )
else:
    # Use sync for small batches
    enriched = [self.ai_client.analyze_accessibility_issue(...) for ...]
```

---

## 📝 Summary

| Feature | Before | After |
|---------|--------|-------|
| **Token Tracking** | ❌ None | ✅ Full metrics |
| **Cost Visibility** | ❌ None | ✅ Real-time estimates |
| **Batch Processing** | Sequential | Parallel (3-5x faster) |
| **Concurrency Control** | N/A | ✅ Configurable |
| **Production Ready** | Partial | ✅ Yes |

**Impact:**
- 💰 **Cost Control:** Know exactly how much AI usage costs
- ⚡ **Performance:** 3-5x faster for large batches
- 📊 **Visibility:** Real-time metrics for monitoring
- 🎯 **Optimization:** Identify expensive operations

---

## 📚 Related Documentation

- [Rate Limiting & Retry Logic](./RATE_LIMITING_AND_RETRY.md)
- [API Reference](../README.md)
- [Testing Guide](./test_async_and_usage.py)
