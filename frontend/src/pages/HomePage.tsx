import { Upload, Play, TrendingUp, AlertCircle, CheckCircle2, Activity, GitBranch, Zap } from 'lucide-react'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Alert, AlertDescription } from '../components/ui/alert'
import { useQuery } from '@tanstack/react-query'
import { listScans } from '../lib/api'
import { EmptyState } from '../components/EmptyState'

type Props = { onNavigate: (page: string) => void }

export function HomePage({ onNavigate }: Props) {
  const { data: scans, isLoading } = useQuery({ queryKey: ['scans'], queryFn: listScans })
  const recentScans = scans && scans.length ? scans.slice(0, 4) : []
  const totalIssues = scans ? scans.reduce((s: number, it: any) => s + (Number(it.total_issues || 0)), 0) : 0
  const totalCritical = scans ? scans.reduce((s: number, it: any) => s + (Number(it.critical_issues || 0)), 0) : 0
  const criticalPct = totalIssues ? Math.round((totalCritical / totalIssues) * 100) : 0
  const trend = scans && scans.length ? (scans[0].trend !== undefined ? String(scans[0].trend) : '-') : '-'
  return (
    <div className="space-y-8">
      <div className="text-center py-12 px-6 rounded-2xl bg-gradient-to-br from-primary/10 via-accent/5 to-background border-2 border-border">
        <h1 className="mb-3">Welcome to AccessTest</h1>
        <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">Make your applications accessible to everyone. Upload scan results, analyze issues, and get intelligent guidance for fixing accessibility problems.</p>
        <div className="flex items-center justify-center gap-4">
          <Button size="lg" className="bg-primary hover:bg-primary/90" onClick={() => onNavigate('upload')}><Upload className="mr-2 h-4 w-4" />Upload Scan</Button>
          <Button size="lg" variant="outline" onClick={() => onNavigate('scan')}><Play className="mr-2 h-4 w-4" />Start Live Scan</Button>
          <Button size="lg" variant="outline" onClick={() => onNavigate('dashboard')}><TrendingUp className="mr-2 h-4 w-4" />View Progress</Button>
        </div>
      </div>

      <div>
        <Alert className="border-2 border-primary/50 bg-primary/5">
          <div className="flex items-start gap-4">
            <div className="p-2 rounded-lg bg-primary/10"><GitBranch className="h-5 w-5 text-primary" /></div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-primary">New: CI/CD Pipeline Integration</h4>
                <Badge variant="secondary" className="text-xs"><Zap className="h-3 w-3 mr-1" />Just Released</Badge>
              </div>
              <AlertDescription>Automatically receive accessibility reports from your CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins). Reports appear instantly in your dashboard.</AlertDescription>
              <div className="flex gap-2 mt-3">
                <Button size="sm" className="bg-primary hover:bg-primary/90" onClick={() => onNavigate('pipeline')}><GitBranch className="h-4 w-4 mr-2" />Setup Pipeline</Button>
                <Button size="sm" variant="outline" onClick={() => window.open('/PIPELINE_INTEGRATION.md', '_blank')}>View Documentation</Button>
              </div>
            </div>
          </div>
        </Alert>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <Card className="border-2 hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div><p className="text-sm text-muted-foreground mb-1">Total Issues</p><h2>{totalIssues}</h2></div>
                <div className="p-3 rounded-xl bg-primary/10"><AlertCircle className="h-5 w-5 text-primary" /></div>
              </div>
              <div className="flex items-center gap-2"><Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20">{criticalPct}% Critical</Badge></div>
            </CardContent>
          </Card>
        </div>
        <div>
          <Card className="border-2 hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Most Violated Rule</p>
                  <h4 className="mb-1">{scans && scans.length && scans[0].most_violated_rule ? scans[0].most_violated_rule : '—'}</h4>
                  <p className="text-sm text-muted-foreground">{scans && scans.length && scans[0].most_violated_wcag ? scans[0].most_violated_wcag : ''}</p>
                </div>
                <div className="p-3 rounded-xl bg-accent"><Activity className="h-5 w-5 text-white" /></div>
              </div>
            </CardContent>
          </Card>
        </div>
        <div>
          <Card className="border-2 hover:shadow-lg transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div><p className="text-sm text-muted-foreground mb-1">Trend Indicator</p><h2 className="text-green-600">{trend}%</h2><p className="text-sm text-muted-foreground">vs last week</p></div>
                <div className="p-3 rounded-xl bg-accent-secondary"><CheckCircle2 className="h-5 w-5 text-white" /></div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div>
        <Card className="border-2">
          <CardHeader>
            <div className="flex items-center justify-between"><CardTitle>Recent Scans</CardTitle><Button variant="ghost" size="sm" onClick={() => onNavigate('runs')}>View All</Button></div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                <div className="h-12 bg-muted/10 rounded" />
                <div className="h-12 bg-muted/10 rounded" />
                <div className="h-12 bg-muted/10 rounded" />
              </div>
            ) : recentScans.length === 0 ? (
              <EmptyState
                icon={Upload}
                title="No recent scans"
                description="Upload a scan or start a live scan to see recent results here."
                action={{ label: 'Upload Scan', onClick: () => onNavigate('upload') }}
              />
            ) : (
              <div className="space-y-3">
                {recentScans.map((scan: any) => (
                  <div key={scan.id} className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-muted/30 transition-colors cursor-pointer" onClick={() => onNavigate('scan-detail')}>
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Activity className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h4>{scan.name || scan.url || `Scan #${scan.id}`}</h4>
                        <p className="text-xs text-muted-foreground">{scan.ts || scan.date}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm">{scan.total_issues || scan.issues || 0} issues</p>
                        <Badge variant="outline" className="text-xs">{scan.status || 'completed'}</Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
