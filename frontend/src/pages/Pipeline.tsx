import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { GitBranch, Upload, Cog, FileCode, Link2, CheckCircle2 } from 'lucide-react'

export default function Pipeline() {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-2">
        <GitBranch className="h-5 w-5 text-primary" />
        <h1>CI/CD Pipeline Integration</h1>
        <Badge variant="secondary" className="text-xs">New</Badge>
      </div>

      <Card className="border-2">
        <CardHeader>
          <CardTitle>Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Send accessibility reports from your CI/CD (GitHub Actions, GitLab CI, Jenkins) directly to AccessTest.
            We’ll analyze results and surface insights on the dashboard.
          </p>
        </CardContent>
      </Card>

      <Card className="border-2">
        <CardHeader>
          <CardTitle>Set Up</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="grid gap-3 text-sm list-decimal pl-5">
            <li className="flex items-start gap-3">
              <span className="mt-0.5"><FileCode className="h-4 w-4 text-primary" /></span>
              <div>
                <p className="font-medium">Generate a JSON report</p>
                <p className="text-muted-foreground">Use axe-core or Pa11y in your pipeline to produce a JSON report artifact.</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-0.5"><Upload className="h-4 w-4 text-primary" /></span>
              <div>
                <p className="font-medium">POST the report to AccessTest</p>
                <p className="text-muted-foreground">POST to <code className="px-1 rounded bg-muted">/api/scans</code> with the JSON body to create a run.</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-0.5"><Cog className="h-4 w-4 text-primary" /></span>
              <div>
                <p className="font-medium">Optional: enable AI enrichment</p>
                <p className="text-muted-foreground">Set <code className="px-1 rounded bg-muted">use_ai: true</code> and <code className="px-1 rounded bg-muted">max_ai_issues</code> in the request.</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-0.5"><Link2 className="h-4 w-4 text-primary" /></span>
              <div>
                <p className="font-medium">Link from your job logs</p>
                <p className="text-muted-foreground">Print the created scan ID; link to <code className="px-1 rounded bg-muted">/scan/&lt;id&gt;</code> and <code className="px-1 rounded bg-muted">/scan/&lt;id&gt;/issues</code>.</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-0.5"><CheckCircle2 className="h-4 w-4 text-primary" /></span>
              <div>
                <p className="font-medium">Review in Dashboard</p>
                <p className="text-muted-foreground">Top rules, counts, and exportable issues are available after each run.</p>
              </div>
            </li>
          </ol>

          <div className="mt-4 flex gap-2">
            <Button asChild>
              <a href="/PIPELINE_INTEGRATION.md" target="_blank" rel="noopener">View Docs</a>
            </Button>
            <Button variant="outline" asChild>
              <a href="/upload">Try with a file</a>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

