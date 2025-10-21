#!/bin/bash
# Example: CLI Integration Script
# Run this after your test suite completes

set -e

DASHBOARD_URL="${DASHBOARD_URL:-http://localhost:8000}"
REPORT_PATH="${1:-./reports/axe-results.json}"
PROJECT_NAME="${2:-main-website}"

echo "🔍 Sending accessibility report to AI Dashboard..."

# Send report and capture response
response=$(curl -s -X POST "$DASHBOARD_URL/api/scans" \
  -H "Content-Type: application/json" \
  -d "{
    \"report\": $(cat $REPORT_PATH),
    \"url\": \"$PROJECT_NAME\",
    \"framework\": \"axe\",
    \"use_ai\": true,
    \"max_ai_issues\": 50
  }")

# Parse response
scan_id=$(echo $response | jq -r '.scan_id')
total=$(echo $response | jq -r '.summary.total_issues')
critical=$(echo $response | jq -r '.summary.critical_issues')
high=$(echo $response | jq -r '.summary.high_issues')
effort=$(echo $response | jq -r '.summary.estimated_total_time_minutes')

# Display summary
echo ""
echo "📊 Analysis Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total Issues:    $total"
echo "Critical:        $critical"
echo "High Priority:   $high"
echo "Est. Fix Time:   ${effort} minutes"
echo ""
echo "🌐 View Dashboard: $DASHBOARD_URL/scan/$scan_id"
echo ""

# Exit with error if critical issues found
if [ "$critical" -gt 0 ]; then
  echo "❌ Build failed: $critical critical accessibility issues found"
  exit 1
fi

echo "✅ No critical issues found"
exit 0
