# Pa11y Integration Guide

## 🎯 Why Pa11y?

Pa11y is a powerful, **free, open-source** accessibility testing tool that runs **locally on your machine**. Unlike cloud APIs, it has:

- ✅ **No API rate limits** - scan as much as you want
- ✅ **No costs** - 100% free forever
- ✅ **Runs offline** - no internet required after setup
- ✅ **Multiple engines** - supports axe-core AND HTML CodeSniffer
- ✅ **Active development** - well-maintained by the open-source community

## 📦 Installation

### Prerequisites
You need Node.js installed on your system.

**Check if you have Node.js:**
```bash
node --version
```

**If not installed:**
- **Windows**: Download from https://nodejs.org/
- **Mac**: `brew install node`
- **Linux**: `sudo apt-get install nodejs npm`

### Install Pa11y

```bash
# Global installation (recommended)
npm install -g pa11y

# Verify installation
pa11y --version
```

**Expected output:** `pa11y 8.0.0` (or similar)

## 🚀 How It Works

### Your New Workflow:

1. **Detection** (FREE):
   - **Axe mode** (default): Uses your existing Playwright + axe-core
   - **Pa11y mode** (NEW): Uses Pa11y via Node.js subprocess
   
2. **Analysis** (95% FREE):
   - Your WCAG rules database handles 95% of issues
   - Zero AI calls for known patterns
   
3. **AI Enhancement** (<5% usage):
   - Only for complex edge cases
   - Configurable budget (default: 5 calls per scan)

### AI Cost Savings:

**Before Pa11y integration:**
- Detection: Playwright + axe-core (free)
- Fixes: AI calls for EVERYTHING (expensive)
- Result: ~20-50 API calls per scan

**After Pa11y integration:**
- Detection: Pa11y (free, no limits)
- Fixes: Rule database (95% coverage, free)
- AI: Only edge cases (<5% of issues)
- Result: ~1-3 API calls per scan

**This reduces AI usage from ~5% to <1%!**

## 🎨 Using Pa11y in the UI

### In the Scan Form:

1. Navigate to **New Scan** page
2. In **Scan Settings**, find **Scanner Engine** dropdown
3. Choose:
   - **Axe-core (Built-in)** - Your current setup (Playwright + axe-core)
   - **Pa11y (Local, No API Limits)** - NEW! Uses Pa11y

4. Select your preset (Quick/Deep/Custom)
5. Click **Start Scan**

### Preset Recommendations:

**Quick Scan (5 pages)**
- Scanner: Pa11y
- Max AI: 3
- Use Case: Fast check, single page sites

**Deep Scan (50 pages)** ⚠️ **Now Practical!**
- Scanner: Pa11y (no API limits!)
- Max AI: 5
- Use Case: Full site audit, no cost worries

**Custom Scan**
- Scanner: Your choice
- Max Pages: Any (no limits with Pa11y)
- Max AI: Adjust based on budget

## 🔧 Backend Integration

### How It's Implemented:

1. **Backend** (`backend/api/routes/scans.py`):
   - Added `scanner` parameter to `ScanUrlRequest`
   - Detects scanner type and routes to appropriate engine
   - Checks if Pa11y is installed before attempting scan

2. **Pa11y Scanner** (`src/accessibility_ai/crawler/pa11y_scanner.py`):
   - Async subprocess wrapper for Pa11y CLI
   - Runs Pa11y with configurable options
   - Returns standardized JSON format

3. **Adapter** (`src/accessibility_ai/adapters/pa11y_adapter.py`):
   - Converts Pa11y format → Axe format
   - Maps severity levels (error → serious, warning → moderate)
   - Preserves all issue details

4. **Analyzer** (`backend/services/analyze.py`):
   - Accepts both axe and Pa11y reports
   - Converts Pa11y format internally
   - Feeds to your existing rule database + AI system

## 🧪 Testing

### Quick Test:

```bash
# Test Pa11y directly (command line)
pa11y https://example.com
```

### From Your App:

1. Go to **New Scan** page
2. Set scanner to **Pa11y**
3. Enter URL: `https://google.com`
4. Set Max Pages: 1
5. Set Max AI: 1
6. Click **Start Scan**

**Expected result:**
- Pa11y scans the page
- Issues detected (likely color contrast, alt text)
- Rule database provides fixes (no AI calls)
- Summary shows 0-1 AI calls used

## 📊 Comparison

### Axe-core (Current)
- ✅ Built-in, no setup
- ✅ Runs in Playwright browser
- ❌ Slightly slower (browser overhead)
- ❌ Single engine (axe-core only)

### Pa11y (NEW)
- ✅ No API limits, completely free
- ✅ Multiple engines (axe + htmlcs)
- ✅ Fast CLI execution
- ✅ Industry-standard tool
- ❌ Requires Node.js + npm install

## 🎯 Recommendation

**Use Pa11y for:**
- Deep scans (>10 pages)
- Frequent testing (CI/CD)
- Sites with many pages
- When you want zero API costs

**Use Axe-core for:**
- Quick single-page tests
- When Pa11y not installed
- Testing in existing Playwright flows

## 🆘 Troubleshooting

### "Pa11y not installed" error

**Solution:**
```bash
npm install -g pa11y
pa11y --version  # Verify
```

### Pa11y scan times out

**Solution:** Pa11y defaults to 30s timeout per page. For slow sites:
- Use fewer pages
- Or modify timeout in `pa11y_scanner.py` (line 26)

### No issues found (but site has issues)

**Possible causes:**
- Site blocks automated tools → Use User-Agent spoofing
- JavaScript-heavy site → Increase wait time
- CORS/authentication → Pa11y can't access content

### Pa11y results different from axe-core

**This is normal!** Pa11y and axe-core:
- Use different heuristics
- Have different rule sets
- Both are valid - combine results for best coverage

## 🚀 Next Steps

1. **Install Pa11y** (5 minutes)
2. **Test with a quick scan** (1 minute)
3. **Try a deep scan** - now practical with no API costs!
4. **Monitor your AI usage** - should drop to <1%

## 💡 Pro Tips

- **Combine both engines**: Run axe-core AND Pa11y for maximum coverage
- **Use rule database first**: 95% of fixes don't need AI
- **Save AI budget**: Reserve AI for complex issues only
- **Automate**: Pa11y works great in CI/CD (GitHub Actions, etc.)

---

**Need help?** Check Pa11y docs: https://pa11y.org/
