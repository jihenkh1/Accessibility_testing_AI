// TypeScript/JavaScript SDK for AI Accessibility Dashboard
// Install: npm install axios

import axios, { AxiosInstance } from 'axios'
import * as fs from 'fs'

export interface DashboardConfig {
  apiUrl?: string
  apiKey?: string
  timeout?: number
}

export interface ScanResult {
  scan_id: number
  summary: {
    total_issues: number
    critical_issues: number
    high_issues: number
    medium_issues: number
    low_issues: number
    estimated_total_time_minutes: number
    ai_enhanced_issues?: number
  }
  dashboard_url?: string
}

export class A11yDashboardClient {
  private client: AxiosInstance

  constructor(config: DashboardConfig = {}) {
    const baseURL = config.apiUrl || process.env.A11Y_DASHBOARD_URL || 'http://localhost:8000'
    const apiKey = config.apiKey || process.env.A11Y_DASHBOARD_KEY
    
    this.client = axios.create({
      baseURL,
      timeout: config.timeout || 30000,
      headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {}
    })
  }

  /**
   * Send an accessibility report to the dashboard
   */
  async sendReport(options: {
    reportPath: string
    projectName?: string
    framework?: 'axe' | 'pa11y'
    useAI?: boolean
    maxAIIssues?: number
    failOnCritical?: boolean
  }): Promise<ScanResult> {
    const {
      reportPath,
      projectName = 'unknown',
      framework = 'axe',
      useAI = true,
      maxAIIssues = 50,
      failOnCritical = false
    } = options

    // Load report
    const reportData = JSON.parse(fs.readFileSync(reportPath, 'utf-8'))

    // Send to API
    const response = await this.client.post<ScanResult>('/api/scans', {
      report: reportData,
      url: projectName,
      framework,
      use_ai: useAI,
      max_ai_issues: maxAIIssues
    })

    const result = response.data
    result.dashboard_url = `${this.client.defaults.baseURL}/scan/${result.scan_id}`

    // Print summary
    console.log('\n' + '='.repeat(50))
    console.log('📊 Accessibility Analysis Complete')
    console.log('='.repeat(50))
    console.log(`Total Issues:     ${result.summary.total_issues}`)
    console.log(`Critical:         ${result.summary.critical_issues}`)
    console.log(`High Priority:    ${result.summary.high_issues}`)
    console.log(`AI Enhanced:      ${result.summary.ai_enhanced_issues || 0}`)
    console.log(`Est. Fix Time:    ${result.summary.estimated_total_time_minutes} min`)
    console.log(`\n🌐 Dashboard:     ${result.dashboard_url}`)
    console.log('='.repeat(50) + '\n')

    // Fail if requested
    if (failOnCritical && result.summary.critical_issues > 0) {
      throw new Error(
        `Build failed: ${result.summary.critical_issues} critical accessibility issues. ` +
        `View: ${result.dashboard_url}`
      )
    }

    return result
  }

  /**
   * Get details of a previous scan
   */
  async getScan(scanId: number) {
    const response = await this.client.get(`/api/scans/${scanId}`)
    return response.data
  }

  /**
   * List recent scans
   */
  async listScans(limit = 20) {
    const response = await this.client.get('/api/scans')
    return response.data.slice(0, limit)
  }
}

// Playwright Reporter Integration
export class A11yDashboardReporter {
  private client: A11yDashboardClient

  constructor(config: DashboardConfig = {}) {
    this.client = new A11yDashboardClient(config)
  }

  async onEnd(result: any) {
    // Save axe results to temp file
    const reportPath = './playwright-report/a11y-results.json'
    if (fs.existsSync(reportPath)) {
      await this.client.sendReport({
        reportPath,
        projectName: process.env.PROJECT_NAME || 'playwright-tests',
        failOnCritical: process.env.FAIL_ON_CRITICAL === 'true'
      })
    }
  }
}

// Cypress Plugin Integration
export function cypressA11yPlugin(on: any, config: any) {
  const client = new A11yDashboardClient()

  on('after:run', async (results: any) => {
    const reportPath = './cypress/reports/a11y-results.json'
    if (fs.existsSync(reportPath)) {
      await client.sendReport({
        reportPath,
        projectName: config.env.PROJECT_NAME || 'cypress-tests'
      })
    }
  })

  return config
}
