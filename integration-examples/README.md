# Integration Examples

This folder contains ready-to-use code and configuration files for integrating the AI Accessibility Dashboard with your testing pipeline.

## 📁 Files

### CI/CD Pipeline Examples
- **`pipeline-integration.yml`** - GitHub Actions workflow example
- **`jenkins-integration.groovy`** - Jenkins pipeline configuration
- **`cli-integration.sh`** - Bash script for any CI/CD platform

### SDK Clients
- **`a11y_dashboard_client.py`** - Python SDK with pytest integration
- **`a11y-dashboard-client.ts`** - TypeScript/JavaScript SDK with Playwright/Cypress support

## 🚀 Quick Start

### 1. Choose Your Integration Method

**For GitHub Actions:** Copy `pipeline-integration.yml` to `.github/workflows/`

**For Jenkins:** Add `jenkins-integration.groovy` to your Jenkinsfile

**For Other CI/CD:** Use `cli-integration.sh` in your build script

**For Python Projects:** Import `a11y_dashboard_client.py`

**For JavaScript/TypeScript:** Import `a11y-dashboard-client.ts`

### 2. Configure Environment Variables

```bash
# Required
export A11Y_DASHBOARD_URL="http://localhost:8000"

# Optional but recommended
export A11Y_DASHBOARD_KEY="your-api-key"
export FAIL_ON_CRITICAL="true"
```

### 3. Test the Integration

```bash
# Using CLI script
chmod +x cli-integration.sh
./cli-integration.sh ./reports/axe-results.json "my-project"

# Using Python SDK
python3 -c "
from a11y_dashboard_client import A11yDashboardClient
client = A11yDashboardClient()
result = client.send_report('./reports/axe-results.json')
print(f'Dashboard: {result[\"dashboard_url\"]}')
"

# Using TypeScript SDK
npx ts-node -e "
import { A11yDashboardClient } from './a11y-dashboard-client'
const client = new A11yDashboardClient()
client.sendReport({ reportPath: './reports/axe-results.json' })
"
```

## 📖 Detailed Documentation

For comprehensive integration guides, see:
- **`../INTEGRATION_STRATEGY.md`** - Recommended approach and implementation plan
- **`../INTEGRATION_GUIDE.md`** - Detailed setup instructions for all platforms
- **`../INTEGRATION_OPTIONS.md`** - Side-by-side comparison of all integration patterns

## 💡 Examples by Use Case

### Use Case 1: Simple API Integration (Fastest)
```bash
curl -X POST "http://localhost:8000/api/scans" \
  -H "Content-Type: application/json" \
  -d @./reports/axe-results.json
```

### Use Case 2: Python with Quality Gates
```python
from a11y_dashboard_client import A11yDashboardClient

client = A11yDashboardClient()
result = client.send_report(
    report_path="./reports/axe.json",
    project_name="main-website",
    fail_on_critical=True  # Fails build if critical issues found
)
```

### Use Case 3: TypeScript with Error Handling
```typescript
import { A11yDashboardClient } from './a11y-dashboard-client'

const client = new A11yDashboardClient({
  apiUrl: process.env.A11Y_DASHBOARD_URL,
  apiKey: process.env.A11Y_DASHBOARD_KEY
})

try {
  const result = await client.sendReport({
    reportPath: './reports/axe.json',
    failOnCritical: true
  })
  console.log(`✅ Analysis complete: ${result.dashboard_url}`)
} catch (error) {
  console.error('❌ Dashboard integration failed:', error)
  // Continue build even if dashboard is unavailable
}
```

## 🔧 Customization

### Add Custom Headers
```python
# Python
import os
client = A11yDashboardClient(api_url="http://dashboard:8000")
client.session.headers['X-Team-ID'] = os.getenv('TEAM_ID')
```

```typescript
// TypeScript - modify the SDK
this.client.defaults.headers['X-Team-ID'] = process.env.TEAM_ID
```

### Change Timeout
```python
# Python
client = A11yDashboardClient(timeout=60)  # 60 seconds
```

```typescript
// TypeScript
const client = new A11yDashboardClient({ timeout: 60000 })
```

### Custom Error Handling
```python
# Python
try:
    result = client.send_report('./report.json')
except FileNotFoundError:
    print("Report file not found - skipping dashboard upload")
except Exception as e:
    print(f"Dashboard error: {e} - continuing build")
```

## 🧪 Testing Your Integration

### Test Locally
```bash
# 1. Start dashboard locally
cd ai-assistant
docker-compose up -d

# 2. Generate a test report
curl -o test-report.json https://raw.githubusercontent.com/dequelabs/axe-core/develop/doc/examples/results/violations.json

# 3. Send to dashboard
./cli-integration.sh test-report.json "test-project"

# 4. Check result
open http://localhost:8000/dashboard
```

### Test in CI/CD
```yaml
# Add a test job to your workflow
test-integration:
  runs-on: ubuntu-latest
  steps:
    - name: Test Dashboard Integration
      run: |
        # Send sample report
        curl -X POST "$DASHBOARD_URL/api/scans" \
          -H "Content-Type: application/json" \
          -d '{"report": {"violations": []}, "url": "test"}'
        
        # Verify response
        if [ $? -eq 0 ]; then
          echo "✅ Dashboard integration working"
        else
          echo "❌ Dashboard integration failed"
          exit 1
        fi
```

## 🎯 Best Practices

1. **Always use environment variables** for API URLs and keys
2. **Fail gracefully** - Don't break builds if dashboard is down
3. **Add timeouts** - Prevent hanging builds
4. **Use HTTPS** in production
5. **Rotate API keys** regularly
6. **Monitor dashboard availability** (uptime checks)
7. **Archive reports** as CI artifacts (backup)

## 🐛 Troubleshooting

### Issue: Connection Refused
**Solution:** Check if dashboard is running and accessible from CI environment

```bash
# Test connectivity
curl -v http://dashboard:8000/api/health
```

### Issue: Timeout
**Solution:** Increase timeout or check dashboard logs

```python
# Python
client = A11yDashboardClient(timeout=60)
```

### Issue: Authentication Failed
**Solution:** Verify API key is set correctly

```bash
echo "Key: $A11Y_DASHBOARD_KEY"  # Should not be empty
```

### Issue: JSON Parse Error
**Solution:** Validate report format

```bash
# Check if valid JSON
cat ./reports/axe-results.json | jq . > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

## 📞 Support

- **Documentation:** See root-level `INTEGRATION_*.md` files
- **Issues:** Open a GitHub issue
- **API Docs:** Visit http://localhost:8000/docs (FastAPI auto-generated)

## 🔄 Updates

When updating the dashboard, you may need to:
1. Update SDK files from this folder
2. Review breaking changes in CHANGELOG.md
3. Test integration before deploying

---

**Ready to integrate? Pick an example and get started! 🚀**
