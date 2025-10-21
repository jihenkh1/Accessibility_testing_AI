import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Calendar, Globe, Code, CheckCircle, Clock, Circle } from 'lucide-react'

type Scan = {
  id: number
  ts: string
  url: string
  framework: string
  total_issues: number
  critical_issues: number
  high_issues: number
  medium_issues: number
  low_issues: number
}

type StatusSummary = {
  todo: number
  in_progress: number
  done: number
  wont_fix: number
}

const ScanCard = ({ scan }: { scan: Scan }) => {
  const navigate = useNavigate()
  
  // Fetch status summary for this scan
  const { data: statusSummary } = useQuery({
    queryKey: ['status-summary', scan.id],
    queryFn: async () => {
      const res = await api.get(`/scans/${scan.id}/status-summary`)
      return res.data as { status_counts: StatusSummary; completion_percentage: number }
    },
  })

  const formatDate = (ts: string) => {
    try {
      return new Date(ts).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return ts
    }
  }

  const getUrlDisplay = (url: string) => {
    if (url === 'api_request') return 'Uploaded Report'
    try {
      const parsed = new URL(url)
      return parsed.hostname || url
    } catch {
      return url.substring(0, 40)
    }
  }

  const completionPct = statusSummary?.completion_percentage || 0

  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          {/* Left side - Scan info */}
          <div className="flex-1 space-y-3">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-muted-foreground text-sm">
                <Calendar className="w-4 h-4" />
                {formatDate(scan.ts)}
              </div>
              <Badge variant="outline" className="flex items-center gap-1">
                <Code className="w-3 h-3" />
                {scan.framework}
              </Badge>
            </div>

            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <span className="font-medium truncate">{getUrlDisplay(scan.url)}</span>
            </div>

            {/* Issue counts */}
            <div className="flex items-center gap-3 text-sm">
              {scan.critical_issues > 0 && (
                <span className="text-red-500 font-medium">{scan.critical_issues} Critical</span>
              )}
              {scan.high_issues > 0 && (
                <span className="text-orange-500 font-medium">{scan.high_issues} High</span>
              )}
              {scan.medium_issues > 0 && (
                <span className="text-yellow-500 font-medium">{scan.medium_issues} Medium</span>
              )}
              {scan.low_issues > 0 && (
                <span className="text-blue-500 font-medium">{scan.low_issues} Low</span>
              )}
              <span className="text-muted-foreground">• {scan.total_issues} total</span>
            </div>

            {/* Progress bar */}
            {statusSummary && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Progress</span>
                  <span className="font-medium">{completionPct}% complete</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                    data-width={completionPct}
                    ref={(el) => {
                      if (el) el.style.width = `${completionPct}%`
                    }}
                  />
                </div>
                <div className="flex items-center gap-3 text-xs pt-1">
                  <span className="flex items-center gap-1 text-gray-500">
                    <Circle className="w-3 h-3" /> {statusSummary.status_counts.todo} To Do
                  </span>
                  <span className="flex items-center gap-1 text-blue-500">
                    <Clock className="w-3 h-3" /> {statusSummary.status_counts.in_progress} In Progress
                  </span>
                  <span className="flex items-center gap-1 text-green-500">
                    <CheckCircle className="w-3 h-3" /> {statusSummary.status_counts.done} Done
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Right side - Action button */}
          <div className="flex flex-col gap-2">
            <Button
              onClick={() => navigate(`/scan/${scan.id}/issues`)}
              className="min-w-[140px]"
            >
              View Issues
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate(`/scan/${scan.id}`)}
              className="min-w-[140px]"
            >
              Summary
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function Runs() {
  const { data: scans, isLoading, error } = useQuery({
    queryKey: ['scans'],
    queryFn: async () => {
      const res = await api.get('/scans')
      return res.data as Scan[]
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold">Scan Runs</h1>
        <div className="text-muted-foreground">Loading scans...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold">Scan Runs</h1>
        <Card>
          <CardContent className="p-6">
            <div className="text-destructive">Failed to load scans. Please try again.</div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const totalScans = scans?.length || 0
  const totalIssues = scans?.reduce((sum, s) => sum + s.total_issues, 0) || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Scan Runs</h1>
          <p className="text-muted-foreground mt-1">
            Manage and track your accessibility scan results
          </p>
        </div>
        <div className="flex gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{totalScans}</div>
            <div className="text-xs text-muted-foreground">Total Scans</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{totalIssues}</div>
            <div className="text-xs text-muted-foreground">Total Issues</div>
          </div>
        </div>
      </div>

      {/* Scans list */}
      {scans && scans.length > 0 ? (
        <div className="space-y-3">
          {scans.map((scan) => (
            <ScanCard key={scan.id} scan={scan} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-muted-foreground mb-4">No scans yet</div>
            <Button onClick={() => window.location.href = '/scan'}>
              Run Your First Scan
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
