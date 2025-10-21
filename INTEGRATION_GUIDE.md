# 🔗 Integration Guide: AI Accessibility Dashboard

This guide explains how to integrate the AI Accessibility Dashboard with your existing testing pipeline.

---

## 📋 Table of Contents

1. [Integration Patterns](#integration-patterns)
2. [Quick Start](#quick-start)
3. [CI/CD Platform Examples](#cicd-platform-examples)
4. [SDK Usage](#sdk-usage)
5. [Authentication & Security](#authentication--security)
6. [Advanced Configurations](#advanced-configurations)
7. [Comparison with Market Solutions](#comparison-with-market-solutions)

---

## 🎯 Integration Patterns

### Pattern 1: API-First (Recommended) ⭐
**Best for:** Teams with existing test infrastructure

```
Your Tests → Generate JSON → POST to Dashboard API → View Results
```

**Pros:**
- ✅ Loose coupling - Projects stay independent
- ✅ Reusable - Multiple teams can use same dashboard
- ✅ Language agnostic - Works with any tech stack
- ✅ Easy to maintain separate deployments

**Market Examples:** Datadog, Sentry, Percy.io

---

### Pattern 2: SDK Integration
**Best for:** Teams wanting type safety and convenience

```
Your Tests → Import SDK → SDK.send() → Dashboard
```

**Pros:**
- ✅ Type-safe API calls
- ✅ Built-in error handling
- ✅ Cleaner code
- ✅ Can run locally or in CI

**Market Examples:** @sentry/node, @datadog/browser-rum

---

### Pattern 3: Webhook/Event-Driven
**Best for:** Async workflows, resilient systems

```
Tests Complete → Webhook Event → Dashboard Listens → Process
```

**Pros:**
- ✅ Non-blocking - Tests don't wait
- ✅ Resilient - Tests pass even if dashboard is down
- ✅ Scalable - Queue-based processing

**Market Examples:** GitHub Status API, Slack webhooks

---

### Pattern 4: Monorepo Shared Packages
**Best for:** Single team, rapid iteration

```
/packages
  /testing-core
  /ai-analyzer
  /shared-types
```

**Pros:**
- ✅ Code sharing
- ✅ Atomic changes
- ✅ Single deploy

**Cons:**
- ❌ Tight coupling

**Market Examples:** Next.js + Vercel, Jest

---

## 🚀 Quick Start

### Step 1: Deploy the Dashboard

**Option A: Local Development**
```bash
# Backend
cd ai-assistant
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

**Option B: Production (Docker)**
```bash
docker-compose up -d
```

**Option C: Cloud (Vercel + Railway)**
```bash
# Frontend to Vercel
vercel deploy

# Backend to Railway
railway up
```

---

### Step 2: Configure Environment

Create `.env` in your **testing project**:

```bash
# Dashboard API
A11Y_DASHBOARD_URL=https://dashboard.yourcompany.com
A11Y_DASHBOARD_KEY=your-secret-api-key  # Optional but recommended

# Behavior
FAIL_ON_CRITICAL=true
MAX_AI_ISSUES=50
```

---

### Step 3: Choose Integration Method

#### Method A: Direct API Call (Universal)

```bash
# After your tests generate reports/axe-results.json
curl -X POST "$A11Y_DASHBOARD_URL/api/scans" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $A11Y_DASHBOARD_KEY" \
  -d @./reports/axe-results.json
```

#### Method B: Python SDK

```python
from a11y_dashboard_client import A11yDashboardClient

client = A11yDashboardClient()
result = client.send_report(
    report_path="./reports/axe-results.json",
    project_name="main-website",
    fail_on_critical=True
)
print(f"Dashboard: {result['dashboard_url']}")
```

#### Method C: JavaScript/TypeScript SDK

```typescript
import { A11yDashboardClient } from './a11y-dashboard-client'

const client = new A11yDashboardClient()
const result = await client.sendReport({
  reportPath: './reports/axe-results.json',
  projectName: 'main-website',
  failOnCritical: true
})
console.log(`Dashboard: ${result.dashboard_url}`)
```

---

## 🔧 CI/CD Platform Examples

### GitHub Actions

```yaml
# .github/workflows/accessibility.yml
name: Accessibility Testing

on: [pull_request, push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run A11y Tests
        run: npm run test:a11y
      
      - name: Send to Dashboard
        env:
          A11Y_DASHBOARD_URL: ${{ secrets.A11Y_DASHBOARD_URL }}
          A11Y_DASHBOARD_KEY: ${{ secrets.A11Y_DASHBOARD_KEY }}
        run: |
          response=$(curl -s -X POST "$A11Y_DASHBOARD_URL/api/scans" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $A11Y_DASHBOARD_KEY" \
            -d @./reports/axe-results.json)
          
          scan_id=$(echo $response | jq -r '.scan_id')
          critical=$(echo $response | jq -r '.summary.critical_issues')
          
          echo "dashboard_url=$A11Y_DASHBOARD_URL/scan/$scan_id" >> $GITHUB_OUTPUT
          
          if [ "$critical" -gt 0 ]; then
            echo "::error::Found $critical critical issues"
            exit 1
          fi
      
      - name: Comment PR
        uses: actions/github-script@v6
        if: github.event_name == 'pull_request'
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '🔍 [View Accessibility Report](${{ steps.send.outputs.dashboard_url }})'
            })
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - report

accessibility_test:
  stage: test
  script:
    - npm run test:a11y
  artifacts:
    paths:
      - reports/axe-results.json

dashboard_upload:
  stage: report
  script:
    - |
      curl -X POST "$A11Y_DASHBOARD_URL/api/scans" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $A11Y_DASHBOARD_KEY" \
        -d @./reports/axe-results.json
  dependencies:
    - accessibility_test
```

### Jenkins

See `integration-examples/jenkins-integration.groovy`

### CircleCI

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  accessibility:
    docker:
      - image: cimg/node:18.0
    steps:
      - checkout
      - run: npm run test:a11y
      - run:
          name: Send to Dashboard
          command: |
            curl -X POST "$A11Y_DASHBOARD_URL/api/scans" \
              -H "Content-Type: application/json" \
              -d @./reports/axe-results.json

workflows:
  test:
    jobs:
      - accessibility
```

---

## 📚 SDK Usage

### Python SDK

**Installation:**
```bash
# Copy to your project
cp integration-examples/a11y_dashboard_client.py your_tests/
```

**Basic Usage:**
```python
from a11y_dashboard_client import A11yDashboardClient

client = A11yDashboardClient(
    api_url="https://dashboard.company.com",
    api_key="optional-api-key"
)

# Send existing report
result = client.send_report(
    report_path="./reports/axe.json",
    project_name="main-website",
    use_ai=True,
    max_ai_issues=50
)

# Or scan a live URL
result = client.scan_url(
    url="https://yoursite.com",
    max_pages=20
)
```

**Pytest Integration:**
```python
# conftest.py
from a11y_dashboard_client import pytest_a11y_report

def pytest_sessionfinish(session, exitstatus):
    """Send report at end of test session"""
    pytest_a11y_report(
        './reports/a11y.json',
        project_name='myapp',
        fail_on_critical=True
    )
```

### TypeScript/JavaScript SDK

**Installation:**
```bash
npm install axios
# Copy integration-examples/a11y-dashboard-client.ts to your project
```

**Basic Usage:**
```typescript
import { A11yDashboardClient } from './a11y-dashboard-client'

const client = new A11yDashboardClient({
  apiUrl: 'https://dashboard.company.com'
})

const result = await client.sendReport({
  reportPath: './reports/axe.json',
  projectName: 'main-website',
  failOnCritical: true
})
```

**Playwright Integration:**
```typescript
// playwright.config.ts
import { A11yDashboardReporter } from './a11y-dashboard-client'

export default {
  reporter: [
    ['html'],
    [A11yDashboardReporter, { apiUrl: 'https://dashboard.company.com' }]
  ]
}
```

**Cypress Integration:**
```typescript
// cypress.config.ts
import { cypressA11yPlugin } from './a11y-dashboard-client'

export default {
  e2e: {
    setupNodeEvents(on, config) {
      cypressA11yPlugin(on, config)
    }
  }
}
```

---

## 🔒 Authentication & Security

### Option 1: API Keys (Recommended)

**Backend Update:**
```python
# backend/api/routes/scans.py
from fastapi import Header, HTTPException

async def verify_api_key(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "Missing API key")
    
    token = authorization.replace("Bearer ", "")
    if token not in VALID_API_KEYS:  # Load from env/database
        raise HTTPException(403, "Invalid API key")

@router.post("/scans", dependencies=[Depends(verify_api_key)])
def post_scan(req: AnalyzeRequest):
    # ... existing code
```

**Usage:**
```bash
curl -H "Authorization: Bearer your-api-key" \
  -X POST http://dashboard/api/scans ...
```

### Option 2: OAuth2/SSO

For enterprise deployments, integrate with your existing SSO:
- Okta
- Auth0
- Azure AD
- Google Workspace

### Option 3: IP Whitelisting

Restrict API access to your CI/CD servers:
```python
# backend/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["ci-server-1.company.com", "*.actions.github.com"]
)
```

---

## ⚙️ Advanced Configurations

### 1. Quality Gates

**Fail build on thresholds:**

```python
result = client.send_report(...)

# Custom validation
if result['summary']['critical_issues'] > 0:
    raise Exception("Critical issues found!")

if result['summary']['total_issues'] > 100:
    print("Warning: Too many issues")
```

### 2. Trend Analysis

Track metrics over time:

```python
# Store scan IDs in your CI artifacts
with open('previous_scan_id.txt', 'r') as f:
    prev_id = int(f.read())

prev = client.get_scan(prev_id)
current = client.send_report(...)

# Compare
if current['summary']['total_issues'] > prev['total_issues']:
    print("⚠️  Issues increased!")
```

### 3. Multi-Environment Testing

```python
environments = ['dev', 'staging', 'prod']

for env in environments:
    result = client.scan_url(
        url=f"https://{env}.yoursite.com",
        max_pages=10
    )
    print(f"{env}: {result['summary']['total_issues']} issues")
```

### 4. Selective AI Enhancement

Save costs by only using AI for critical issues:

```python
result = client.send_report(
    report_path="./reports/axe.json",
    use_ai=True,
    max_ai_issues=20  # Only enhance top 20 issues
)
```

---

## 📊 Comparison with Market Solutions

| Feature | This Dashboard | Sentry | Percy.io | SonarQube |
|---------|---------------|--------|----------|-----------|
| **Accessibility Focus** | ✅ Yes | ❌ No | ❌ No | ⚠️ Limited |
| **AI Enhancement** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Self-Hosted** | ✅ Free | 💰 Paid | 💰 Paid | ✅ Free |
| **API Integration** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Cost** | Free | $26+/mo | $149+/mo | Free/Paid |
| **Custom Reports** | ✅ Yes | ⚠️ Limited | ⚠️ Limited | ✅ Yes |

**Why use this dashboard:**
- ✅ **Free & Open Source** - No per-seat pricing
- ✅ **AI-Powered** - Automated fix suggestions
- ✅ **Accessibility-First** - Purpose-built for WCAG compliance
- ✅ **Extensible** - Add custom rules, integrations
- ✅ **Privacy** - Self-host your data

---

## 🎯 Recommended Architecture

### For Small Teams (1-5 developers)
```
Tests → Direct API → Shared Dashboard (single instance)
```

### For Medium Teams (5-20 developers)
```
Tests → SDK → Dashboard API → Database
        ↓
   Quality Gates in CI
```

### For Large Organizations (20+ developers)
```
Multiple Teams → API Gateway → Dashboard Cluster
                                      ↓
                              Centralized Database
                                      ↓
                          Metrics to DataDog/Grafana
```

---

## 🚀 Next Steps

1. **Deploy Dashboard** (see deployment guide)
2. **Add to CI/CD** (use examples above)
3. **Create Quality Gates** (fail on critical issues)
4. **Train Team** (share dashboard URL)
5. **Monitor Trends** (track improvements over time)

---

## 📞 Support

- **Documentation**: See README.md
- **Issues**: GitHub Issues
- **API Reference**: http://localhost:8000/docs (FastAPI auto-generated)

---

## 🔄 Migration from Other Tools

### From Axe DevTools
```python
# Your existing axe output is already compatible!
client.send_report('./axe-results.json', framework='axe')
```

### From Pa11y
```python
client.send_report('./pa11y-results.json', framework='pa11y')
```

### From Lighthouse CI
```bash
# Extract accessibility results from Lighthouse JSON
jq '.categories.accessibility' lighthouse-report.json > a11y.json
# Then send to dashboard
```

---

**🎉 You're all set! Start integrating accessibility analysis into your pipeline.**
