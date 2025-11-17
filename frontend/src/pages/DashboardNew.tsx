import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listScanIssues, listScans, getAIUsageStats, getAICacheStats, deleteScan, getFixMetrics, listProjects } from '../lib/api'
import { Link, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Input } from '../components/ui/input'
import { Skeleton } from '../components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '../components/ui/alert-dialog'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../components/ui/tooltip'
import { AlertCircle, AlertTriangle, Clock, TrendingUp, BarChart3, Sparkles, FileSpreadsheet, FileJson, Search, Filter, ArrowUpDown, CheckCircle2, Database, DollarSign, Upload, Trash2, FileJson2, HelpCircle, PieChart, LineChart } from 'lucide-react'
import { EmptyState } from '../components/EmptyState'
import { toast } from 'sonner'
import { formatRelativeTime, formatAbsoluteTime } from '../utils/time'
import { LineChart as RechartsLineChart, Line, AreaChart, Area, PieChart as RechartsPieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, BarChart as RechartsBarChart, Bar } from 'recharts'

export default function DashboardNew() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  // Project selection state
  const [selectedProject, setSelectedProject] = useState<string>('Default Project')
  
  // Fetch all projects
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  })
  
  // Fetch scans filtered by selected project
  const { data, isLoading, error } = useQuery({ 
    queryKey: ['scans', selectedProject], 
    queryFn: () => listScans(selectedProject === 'Default Project' ? undefined : selectedProject)
  })

  // Delete mutation with toast notifications
  const deleteMutation = useMutation({
    mutationFn: deleteScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      queryClient.invalidateQueries({ queryKey: ['fixMetrics'] })
      toast.success('Scan deleted successfully', {
        description: 'The scan and all its data have been removed.'
      })
    },
    onError: (error: any) => {
      toast.error('Failed to delete scan', {
        description: error?.message || 'An error occurred while deleting the scan.'
      })
    }
  })

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [scanToDelete, setScanToDelete] = useState<number | null>(null)

  const handleDeleteClick = (scanId: number, event: React.MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()
    setScanToDelete(scanId)
    setDeleteDialogOpen(true)
  }

  const confirmDelete = () => {
    if (scanToDelete) {
      deleteMutation.mutate(scanToDelete)
      setDeleteDialogOpen(false)
      setScanToDelete(null)
    }
  }

  // Separate analyzed and pending scans
  const analyzedScans = useMemo(() => {
    return data?.filter((scan: any) => scan.total_issues > 0 && scan.framework !== 'documentation') || []
  }, [data])

  const pendingScans = useMemo(() => {
    return data?.filter((scan: any) => scan.total_issues === 0 && scan.framework !== 'documentation') || []
  }, [data])

  // Group pending scans by test cycle (within 5 minutes)
  // Only show COMBINED reports, filter out individual AXE and PA11Y reports
  const groupedPendingScans = useMemo(() => {
    if (!pendingScans.length) return []
    
    // Filter to only keep COMBINED reports
    const combinedOnly = pendingScans.filter((scan: any) => 
      !scan.url.includes('axe') && !scan.url.includes('pa11y')
    )
    
    const sorted = [...combinedOnly].sort((a, b) => 
      new Date(a.ts).getTime() - new Date(b.ts).getTime()
    )
    
    const groups: any[] = []
    let currentGroup: any[] = []
    
    sorted.forEach((scan, index) => {
      if (index === 0) {
        currentGroup.push(scan)
      } else {
        const prevTime = new Date(sorted[index - 1].ts).getTime()
        const currTime = new Date(scan.ts).getTime()
        const diffMinutes = (currTime - prevTime) / (1000 * 60)
        
        if (diffMinutes <= 5) {
          currentGroup.push(scan)
        } else {
          groups.push([...currentGroup])
          currentGroup = [scan]
        }
      }
    })
    
    if (currentGroup.length > 0) {
      groups.push(currentGroup)
    }
    
    return groups
  }, [pendingScans])

  const latest = analyzedScans && analyzedScans.length ? analyzedScans[0] : (null as any)
  const total = latest ? Number(latest.total_issues || 0) : 0
  const critical = latest ? Number(latest.critical_issues || 0) : 0
  const effortMin = latest ? Number(latest.estimated_total_time_minutes || 0) : 0
  const effortH = effortMin ? (effortMin / 60).toFixed(1) : '0.0'
  const critPct = total ? Math.round((critical / total) * 100) : 0

  const scanId = latest?.id as number | undefined
  const { data: latestIssues, isLoading: loadingIssues } = useQuery({
    enabled: !!scanId,
    queryKey: ['scan-issues', scanId],
    queryFn: () => listScanIssues(scanId as number, 1000),
  })

  const topRules: Array<{ id: string; count: number; severity?: string }> = useMemo(() => {
    const issues = latestIssues?.items as Array<any> | undefined
    if (!issues || !issues.length) {
      return []
    }
    const counter = new Map<string, { count: number; severity?: string }>()
    for (const it of issues) {
      const key = String(it.rule_id || it.id || it.code || 'unknown')
      const sev = String(it.priority || it.severity || it.impact || '')
      const prev = counter.get(key)
      if (prev) prev.count += 1
      else counter.set(key, { count: 1, severity: sev })
    }
    return Array.from(counter.entries())
      .map(([id, v]) => ({ id, count: v.count, severity: v.severity }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6)
  }, [latestIssues])

  const [searchQuery, setSearchQuery] = useState('')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [sortBy, setSortBy] = useState<'severity' | 'instances' | 'effort'>('severity')

  // Fetch AI stats for dashboard overview
  const { data: aiUsageStats } = useQuery({
    queryKey: ['aiUsageStats'],
    queryFn: getAIUsageStats,
    refetchInterval: 60000, // Refresh every 60s
    retry: 1,
  })

  const { data: aiCacheStats } = useQuery({
    queryKey: ['aiCacheStats'],
    queryFn: getAICacheStats,
    refetchInterval: 60000,
    retry: 1,
  })

  const { data: fixMetrics } = useQuery({
    queryKey: ['fixMetrics'],
    queryFn: getFixMetrics,
    refetchInterval: 30000, // Refresh every 30s
    retry: 1,
  })

  // Chart data processing
  const trendChartData = useMemo(() => {
    if (!analyzedScans || analyzedScans.length === 0) return []
    return analyzedScans
      .slice(0, 10)
      .reverse()
      .map((scan: any) => ({
        name: new Date(scan.ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        critical: scan.critical_issues || 0,
        high: scan.high_issues || 0,
        medium: scan.medium_issues || 0,
        low: scan.low_issues || 0,
        total: scan.total_issues || 0,
      }))
  }, [analyzedScans])

  const severityDistributionData = useMemo(() => {
    if (!latest) return []
    return [
      { name: 'Critical', value: latest.critical_issues || 0, color: '#b91c1c' },
      { name: 'High', value: latest.high_issues || 0, color: '#c2410c' },
      { name: 'Medium', value: latest.medium_issues || 0, color: '#b45309' },
      { name: 'Low', value: latest.low_issues || 0, color: '#2563eb' },
    ].filter(item => item.value > 0)
  }, [latest])

  // WCAG compliance data
  const wcagComplianceData = useMemo(() => {
    const issues = latestIssues?.items as Array<any> | undefined
    if (!issues || !issues.length) return []
    
    const wcagMap = new Map<string, number>()
    issues.forEach((issue) => {
      const wcagRefs = issue.wcag_refs || []
      wcagRefs.forEach((ref: string) => {
        const match = ref.match(/(\d+\.\d+\.\d+)/)
        if (match) {
          const criterion = match[1]
          wcagMap.set(criterion, (wcagMap.get(criterion) || 0) + 1)
        }
      })
    })
    
    return Array.from(wcagMap.entries())
      .map(([criterion, count]) => ({ criterion, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8)
  }, [latestIssues])

  // Quick Wins - low effort, high severity issues
  const quickWins = useMemo(() => {
    const issues = latestIssues?.items as Array<any> | undefined
    if (!issues || !issues.length) return []
    
    return issues
      .filter((issue) => {
        const effort = Number(issue.effort_minutes || 0)
        const severity = String(issue.priority || issue.severity || '').toLowerCase()
        return effort <= 10 && (severity === 'critical' || severity === 'high' || severity === 'serious')
      })
      .slice(0, 5)
      .map((issue, idx) => ({
        id: idx,
        rule: String(issue.rule_id || 'unknown'),
        severity: String(issue.priority || issue.severity || 'high'),
        effort: Number(issue.effort_minutes || 5),
        description: String(issue.description || issue.message || ''),
      }))
  }, [latestIssues])

  // Industry-standard Accessibility Score Calculation
  // Based on Lighthouse scoring methodology and WCAG compliance
  const accessibilityScore = useMemo(() => {
    if (!latest || !analyzedScans) return null
    
    // Calculate score for a single scan
    const calculateScore = (scan: any) => {
      const critical = scan.critical_issues || 0
      const high = scan.high_issues || 0
      const medium = scan.medium_issues || 0
      const low = scan.low_issues || 0
      const total = scan.total_issues || 0
      
      if (total === 0) return 100
      
      // Weighted penalty system (similar to Lighthouse)
      let score = 100
      score -= critical * 10
      score -= high * 5
      score -= medium * 2
      score -= low * 0.5
      
      return Math.max(0, Math.round(score))
    }
    
    // Current scan data
    const critical = latest.critical_issues || 0
    const high = latest.high_issues || 0
    const medium = latest.medium_issues || 0
    const low = latest.low_issues || 0
    const total = latest.total_issues || 0
    
    // Calculate current score
    const currentScore = calculateScore(latest)
    
    // Calculate project metrics (all scans)
    const allScores = analyzedScans.map(calculateScore)
    const averageScore = allScores.length > 0 
      ? Math.round(allScores.reduce((a, b) => a + b, 0) / allScores.length)
      : currentScore
    const bestScore = allScores.length > 0 ? Math.max(...allScores) : currentScore
    const worstScore = allScores.length > 0 ? Math.min(...allScores) : currentScore
    
    // Calculate previous score for trend
    const previousScore = analyzedScans.length > 1 ? calculateScore(analyzedScans[1]) : currentScore
    const scoreDelta = currentScore - previousScore
    const trendDirection = scoreDelta > 0 ? 'up' : scoreDelta < 0 ? 'down' : 'stable'
    
    // Determine grade, WCAG level, and status based on current score
    let grade = ''
    let wcagLevel = ''
    let status = ''
    let color = ''
    let bgColor = ''
    
    if (currentScore >= 90) {
      grade = 'A'
      wcagLevel = critical === 0 && high === 0 ? 'AAA' : 'AA'
      status = 'Excellent'
      color = 'text-green-500'
      bgColor = 'from-green-500/20 to-emerald-500/20'
    } else if (currentScore >= 75) {
      grade = 'B'
      wcagLevel = critical === 0 ? 'AA' : 'A'
      status = 'Good'
      color = 'text-blue-500'
      bgColor = 'from-blue-500/20 to-cyan-500/20'
    } else if (currentScore >= 60) {
      grade = 'C'
      wcagLevel = critical === 0 ? 'A' : 'Partial'
      status = 'Fair'
      color = 'text-yellow-500'
      bgColor = 'from-yellow-500/20 to-amber-500/20'
    } else if (currentScore >= 40) {
      grade = 'D'
      wcagLevel = 'Partial'
      status = 'Needs Work'
      color = 'text-orange-500'
      bgColor = 'from-orange-500/20 to-red-500/20'
    } else {
      grade = 'F'
      wcagLevel = 'Non-Compliant'
      status = 'Critical'
      color = 'text-red-500'
      bgColor = 'from-red-500/20 to-rose-500/20'
    }
    
    return {
      score: currentScore,
      grade,
      color,
      bgColor,
      status,
      wcagLevel,
      description: `${total} total issues found`,
      breakdown: {
        critical,
        high,
        medium,
        low
      },
      // Project-level metrics
      project: {
        averageScore,
        bestScore,
        worstScore,
        totalRuns: analyzedScans.length,
        previousScore,
        scoreDelta,
        trendDirection
      }
    }
  }, [latest, analyzedScans])

  const tableItems = useMemo(() => {
    const items = (latestIssues?.items || []) as Array<any>
    const mapped = items.map((it, idx) => ({
      id: idx,
      rule: String(it.rule_id || 'unknown'),
      element: String(it.selector || ''),
      severity: String(it.priority || it.severity || 'medium'),
      wcag: (it.wcag_refs && it.wcag_refs[0]) || '',
      aiSuggestion: String(it.fix_suggestion || ''),
      effort: `${Number(it.effort_minutes || 5)} min`,
      instances: 1,
    }))
    return mapped
  }, [latestIssues])

  const filtered = tableItems.filter((issue) => {
    const s = searchQuery.toLowerCase()
    const matchesSearch = issue.rule.toLowerCase().includes(s) || issue.element.toLowerCase().includes(s)
    const matchesSeverity = severityFilter === 'all' || issue.severity === severityFilter
    return matchesSearch && matchesSeverity
  })

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'instances') return b.instances - a.instances
    if (sortBy === 'effort') return parseInt(a.effort) - parseInt(b.effort)
    const order: Record<string, number> = { critical: 0, high: 1, serious: 1, moderate: 2, medium: 2, minor: 3, low: 3 }
    return (order[a.severity] ?? 9) - (order[b.severity] ?? 9)
  })

  function downloadCSV(rows: typeof sorted) {
    const headers = ['rule','element','aiSuggestion','severity','wcag','instances','effort']
    const lines = [headers.join(',')].concat(rows.map(r => headers.map(h => JSON.stringify((r as any)[h] ?? '')).join(',')))
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'accessibility-report.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  function downloadJSON(rows: typeof sorted) {
    const blob = new Blob([JSON.stringify(rows, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'accessibility-report.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  // Helper function for severity tooltips
  const getSeverityTooltip = (severity: string) => {
    const tooltips: Record<string, string> = {
      critical: 'Critical: Must be fixed immediately. Blocks access for many users.',
      high: 'High: Major accessibility barrier. Should be fixed soon.',
      serious: 'High: Major accessibility barrier. Should be fixed soon.',
      medium: 'Medium: Moderate impact. Fix in next iteration.',
      moderate: 'Medium: Moderate impact. Fix in next iteration.',
      low: 'Low: Minor issue. Fix when convenient.',
      minor: 'Low: Minor issue. Fix when convenient.',
    }
    return tooltips[severity.toLowerCase()] || 'Accessibility issue'
  }

  // Calculate summary metrics
  // Count only unique analyzed scans (exclude framework-specific duplicates and documentation)
  const totalScans = analyzedScans?.length || 0
  const avgFixRate = fixMetrics?.fix_rate || 0
  const openCriticals = analyzedScans?.reduce((sum: number, scan: any) => sum + (scan.critical_issues || 0), 0) || 0

  return (
    <TooltipProvider>
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Sticky Summary Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b pb-4 -mx-6 px-6 -mt-6 pt-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Welcome back</h1>
              <p className="text-muted-foreground mt-1">
                Monitor accessibility testing progress and team performance
              </p>
            </div>
            {/* Project Selector */}
            {projects && projects.length > 0 && (
              <div className="flex items-center gap-2">
                <label htmlFor="project-select" className="text-sm font-medium text-muted-foreground whitespace-nowrap">
                  Project:
                </label>
                <Select value={selectedProject} onValueChange={setSelectedProject}>
                  <SelectTrigger id="project-select" className="w-[200px]">
                    <SelectValue placeholder="Select project" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project} value={project}>
                        {project}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          <Button onClick={() => navigate('/upload')} size="lg" className="gap-2">
            <Upload className="h-4 w-4" />
            Upload New Scan
          </Button>
        </div>

        {/* Quick Stats Bar */}
        {!isLoading && totalScans > 0 && (
          <div className="flex items-center gap-6 text-sm">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Total Scans:</span>
                  <span className="font-semibold">{totalScans}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Total number of analyzed accessibility scans with issues found</p>
              </TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Avg Fix Rate:</span>
                  <span className="font-semibold text-green-700 dark:text-green-400">{avgFixRate.toFixed(1)}%</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Percentage of issues marked as fixed across all scans</p>
              </TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Open Criticals:</span>
                  <span className={`font-semibold ${openCriticals > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {openCriticals}
                  </span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Number of critical accessibility issues that need immediate attention</p>
              </TooltipContent>
            </Tooltip>
          </div>
        )}
      </div>
      
      {isLoading && (
        <div className="space-y-6">
          {/* Header Skeleton */}
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton className="h-10 w-64" />
              <Skeleton className="h-4 w-96" />
            </div>
            <Skeleton className="h-10 w-40" />
          </div>

          {/* Metric Cards Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="border-2">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="space-y-3 flex-1">
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-12 w-20" />
                      <Skeleton className="h-3 w-32" />
                    </div>
                    <Skeleton className="h-12 w-12 rounded-2xl" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Large Card Skeleton */}
          <Card className="border-2">
            <CardHeader>
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-96 mt-2" />
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {error && (
        <Card className="border-2 border-destructive/50">
          <CardContent className="py-8">
            <EmptyState
              icon={AlertCircle}
              title="Failed to load dashboard"
              description="There was an error loading your accessibility data. Please try again."
              action={{
                label: "Retry",
                onClick: () => window.location.reload(),
                variant: "outline"
              }}
            />
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && !latest && pendingScans.length === 0 && (
        <Card className="border-2 bg-gradient-to-br from-primary/5 via-accent/5 to-background">
          <CardContent className="py-12">
            <EmptyState
              icon={Upload}
              title="Your dashboard is waiting for its first scan 🚀"
              description="Upload an accessibility report from axe-core, pa11y, Lighthouse, or any other tool to get started with AI-powered insights."
              action={{
                label: "Upload Your First Scan",
                onClick: () => navigate('/upload')
              }}
            />
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && (
        <>
      {/* Latest Scan Overview - Enhanced */}
      <section aria-labelledby="latest-scan-heading">
        <h2 id="latest-scan-heading" className="text-lg font-semibold mb-3">Latest Scan Overview</h2>
        {latest ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Issues Found Card */}
          <Card className="relative overflow-hidden border-2 hover:shadow-lg transition-all duration-300 group" role="article" aria-label="Total issues found">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-16 translate-x-16 group-hover:scale-110 transition-transform" aria-hidden="true" />
            <CardContent className="p-6 relative">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Issues Found</p>
                  <p className="text-4xl font-bold tracking-tight" aria-label={`${total} total issues found`}>{total}</p>
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" aria-hidden="true" />
                    <span>In latest test</span>
                  </p>
                </div>
                <div className="p-3 rounded-2xl bg-primary/10 ring-8 ring-primary/5" aria-hidden="true">
                  <AlertCircle className="h-6 w-6 text-primary" aria-hidden="true" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Critical Issues Card */}
          <Card className="relative overflow-hidden border-2 border-destructive/20 hover:shadow-lg hover:shadow-destructive/10 transition-all duration-300 group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-destructive/5 rounded-full -translate-y-16 translate-x-16 group-hover:scale-110 transition-transform" />
            <CardContent className="p-6 relative">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Critical Issues</p>
                  <h2 className="text-4xl font-bold tracking-tight text-destructive">{critical}</h2>
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    {critPct}% of total
                  </p>
                </div>
                <div className="p-3 rounded-2xl bg-destructive/10 ring-8 ring-destructive/5">
                  <AlertTriangle className="h-6 w-6 text-destructive" />
                </div>
              </div>
              {critical > 0 && scanId && (
                <div className="mt-4 pt-4 border-t">
                  <Button 
                    variant="destructive" 
                    size="sm" 
                    className="w-full"
                    onClick={() => navigate(`/scan/${scanId}/issues?severity=critical`)}
                  >
                    View Critical Issues →
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Estimated Effort Card */}
          <Card className="relative overflow-hidden border-2 hover:shadow-lg transition-all duration-300 group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full -translate-y-16 translate-x-16 group-hover:scale-110 transition-transform" />
            <CardContent className="p-6 relative">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-muted-foreground">Estimated Effort</p>
                  <h2 className="text-4xl font-bold tracking-tight">{effortH}h</h2>
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {effortMin} minutes to fix
                  </p>
                </div>
                <div className="p-3 rounded-2xl bg-blue-500/10 ring-8 ring-blue-500/5">
                  <Clock className="h-6 w-6 text-blue-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        ) : (
        <Card className="border-2">
          <CardContent className="p-8">
            <EmptyState 
              icon={AlertCircle}
              title="No scan data available"
              description="Upload a scan report to see the latest accessibility test results."
            />
          </CardContent>
        </Card>
        )}
      </section>

      {/* Accessibility Score Card - Industry Standard */}
      {accessibilityScore && (
        <Card className="border-2 overflow-hidden">
          <div className={`bg-gradient-to-r ${accessibilityScore.bgColor} p-6 border-b`}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <CardTitle className="text-2xl">Accessibility Score</CardTitle>
                <CardDescription className="mt-1">
                  Based on WCAG 2.1 compliance and issue severity
                </CardDescription>
              </div>
              <Badge className={`${accessibilityScore.color} bg-background text-lg px-4 py-2`}>
                {accessibilityScore.wcagLevel}
              </Badge>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mt-6">
              {/* Score Circle */}
              <div className="md:col-span-3 flex items-center justify-center">
                <div className="relative">
                  <svg className="w-40 h-40 transform -rotate-90">
                    <circle
                      cx="80"
                      cy="80"
                      r="70"
                      stroke="currentColor"
                      strokeWidth="10"
                      fill="none"
                      className="text-muted/20"
                    />
                    <circle
                      cx="80"
                      cy="80"
                      r="70"
                      stroke="currentColor"
                      strokeWidth="10"
                      fill="none"
                      strokeDasharray={`${2 * Math.PI * 70}`}
                      strokeDashoffset={`${2 * Math.PI * 70 * (1 - accessibilityScore.score / 100)}`}
                      className={`${accessibilityScore.color} transition-all duration-1000 ease-out`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className={`text-5xl font-bold ${accessibilityScore.color}`}>
                      {accessibilityScore.score}
                    </span>
                    <span className="text-sm text-muted-foreground mt-1">/ 100</span>
                  </div>
                </div>
              </div>

              {/* Score Details */}
              <div className="md:col-span-9 space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Grade</p>
                    <p className={`text-4xl font-bold ${accessibilityScore.color}`}>
                      {accessibilityScore.grade}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Status</p>
                    <p className="text-2xl font-semibold">
                      {accessibilityScore.status}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Trend</p>
                    <div className="flex items-center gap-2">
                      {accessibilityScore.project.trendDirection === 'up' && (
                        <TrendingUp className="h-6 w-6 text-green-500" />
                      )}
                      {accessibilityScore.project.trendDirection === 'down' && (
                        <AlertTriangle className="h-6 w-6 text-red-500" />
                      )}
                      {accessibilityScore.project.trendDirection === 'stable' && (
                        <span className="text-2xl">→</span>
                      )}
                      <span className={`text-xl font-bold ${
                        accessibilityScore.project.scoreDelta > 0 ? 'text-green-500' :
                        accessibilityScore.project.scoreDelta < 0 ? 'text-red-500' :
                        'text-muted-foreground'
                      }`}>
                        {accessibilityScore.project.scoreDelta > 0 ? '+' : ''}
                        {accessibilityScore.project.scoreDelta}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Test Runs</p>
                    <p className="text-2xl font-bold">
                      {accessibilityScore.project.totalRuns}
                    </p>
                  </div>
                </div>

                <div className="bg-background/50 rounded-lg p-4 border">
                  <p className="text-xs font-medium mb-3">Project Statistics</p>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-lg font-bold text-green-500">{accessibilityScore.project.bestScore}</p>
                      <p className="text-xs text-muted-foreground">Best Score</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold">{accessibilityScore.project.averageScore}</p>
                      <p className="text-xs text-muted-foreground">Average Score</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-orange-500">{accessibilityScore.project.worstScore}</p>
                      <p className="text-xs text-muted-foreground">Worst Score</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <p className="text-sm font-medium">Issue Breakdown</p>
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-background rounded-lg p-3 border-2">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-2 h-2 rounded-full bg-red-500"></div>
                        <p className="text-xs text-muted-foreground">Critical</p>
                      </div>
                      <p className="text-2xl font-bold">{accessibilityScore.breakdown?.critical || 0}</p>
                      <p className="text-xs text-muted-foreground mt-1">-{(accessibilityScore.breakdown?.critical || 0) * 10} pts</p>
                    </div>

                    <div className="bg-background rounded-lg p-3 border-2">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                        <p className="text-xs text-muted-foreground">High</p>
                      </div>
                      <p className="text-2xl font-bold">{accessibilityScore.breakdown?.high || 0}</p>
                      <p className="text-xs text-muted-foreground mt-1">-{(accessibilityScore.breakdown?.high || 0) * 5} pts</p>
                    </div>

                    <div className="bg-background rounded-lg p-3 border-2">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                        <p className="text-xs text-muted-foreground">Medium</p>
                      </div>
                      <p className="text-2xl font-bold">{accessibilityScore.breakdown?.medium || 0}</p>
                      <p className="text-xs text-muted-foreground mt-1">-{(accessibilityScore.breakdown?.medium || 0) * 2} pts</p>
                    </div>

                    <div className="bg-background rounded-lg p-3 border-2">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                        <p className="text-xs text-muted-foreground">Low</p>
                      </div>
                      <p className="text-2xl font-bold">{accessibilityScore.breakdown?.low || 0}</p>
                      <p className="text-xs text-muted-foreground mt-1">-{((accessibilityScore.breakdown?.low || 0) * 0.5).toFixed(1)} pts</p>
                    </div>
                  </div>
                </div>

                <div className="bg-background/50 rounded-lg p-4 border">
                  <p className="text-xs text-muted-foreground">
                    <strong>Scoring:</strong> Critical (-10 pts), High (-5 pts), Medium (-2 pts), Low (-0.5 pts) | 
                    <strong className="ml-2">WCAG Levels:</strong> A (Basic), AA (Industry Standard), AAA (Enhanced) | 
                    <strong className="ml-2">Project Tracking:</strong> Aggregates all {accessibilityScore.project.totalRuns} test runs for your website
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* AI Performance Overview - Enhanced */}
      <Card className="border-2">
        <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 p-6 border-b">
          <CardTitle className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-background">
              <Sparkles className="h-5 w-5 text-purple-500" />
            </div>
            AI Performance Overview
          </CardTitle>
          <CardDescription className="mt-2">
            AI-powered analysis statistics and usage metrics. <Link to="/settings?tab=ai" className="text-primary hover:underline font-medium">View detailed stats →</Link>
          </CardDescription>
        </div>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* AI Requests */}
            <div className="rounded-xl border-2 p-5 bg-gradient-to-br from-purple-50 to-purple-100/50 dark:from-purple-950/30 dark:to-purple-900/20 hover:shadow-md transition-all group">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium text-muted-foreground">AI Requests</p>
                <div className="p-2 rounded-lg bg-purple-500/10 group-hover:scale-110 transition-transform">
                  <Sparkles className="h-4 w-4 text-purple-500" />
                </div>
              </div>
              {aiUsageStats?.available ? (
                <>
                  <h3 className="text-3xl font-bold mb-1">{aiUsageStats.stats?.total_requests || 0}</h3>
                  <p className="text-xs text-muted-foreground">Total API calls</p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Not available</p>
              )}
            </div>

            {/* Token Usage */}
            <div className="rounded-xl border-2 p-5 bg-gradient-to-br from-blue-50 to-blue-100/50 dark:from-blue-950/30 dark:to-blue-900/20 hover:shadow-md transition-all group">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium text-muted-foreground">Tokens Used</p>
                <div className="p-2 rounded-lg bg-blue-500/10 group-hover:scale-110 transition-transform">
                  <BarChart3 className="h-4 w-4 text-blue-500" />
                </div>
              </div>
              {aiUsageStats?.available ? (
                <>
                  <h3 className="text-3xl font-bold mb-1">{(aiUsageStats.stats?.total_tokens || 0).toLocaleString()}</h3>
                  <p className="text-xs text-muted-foreground">
                    ${(aiUsageStats.stats?.estimated_cost_usd || 0).toFixed(4)} cost
                  </p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Not available</p>
              )}
            </div>

            {/* Success Rate */}
            <div className="rounded-xl border-2 p-5 bg-gradient-to-br from-green-50 to-green-100/50 dark:from-green-950/30 dark:to-green-900/20 hover:shadow-md transition-all group">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium text-muted-foreground">Success Rate</p>
                <div className="p-2 rounded-lg bg-green-500/10 group-hover:scale-110 transition-transform">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                </div>
              </div>
              {aiUsageStats?.available ? (
                <>
                  <h3 className="text-3xl font-bold mb-1 text-green-600 dark:text-green-400">
                    {Math.min(100, (aiUsageStats.stats?.success_rate || 0) * 100).toFixed(1)}%
                  </h3>
                  <p className="text-xs text-muted-foreground">API reliability</p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Not available</p>
              )}
            </div>

            {/* Cache Performance */}
            <div className="rounded-xl border-2 p-5 bg-gradient-to-br from-orange-50 to-orange-100/50 dark:from-orange-950/30 dark:to-orange-900/20 hover:shadow-md transition-all group">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium text-muted-foreground">Cache Entries</p>
                <div className="p-2 rounded-lg bg-orange-500/10 group-hover:scale-110 transition-transform">
                  <Database className="h-4 w-4 text-orange-500" />
                </div>
              </div>
              {aiCacheStats?.available ? (
                <>
                  <h3 className="text-3xl font-bold mb-1">{aiCacheStats.stats?.total_entries || 0}</h3>
                  <p className="text-xs text-muted-foreground">
                    {aiCacheStats.stats?.valid_entries || 0} valid, {aiCacheStats.stats?.expired_entries || 0} expired
                  </p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Not available</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Fix Turnaround Metrics - Enhanced */}
      <Card className="border-2 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 p-6 border-b">
          <CardTitle className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-background">
              <TrendingUp className="h-5 w-5 text-blue-500" />
            </div>
            Fix Turnaround Metrics
          </CardTitle>
          <CardDescription className="mt-2">
            Track how quickly issues are being resolved by your team
          </CardDescription>
        </div>
        <CardContent className="p-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* Total Issues */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Total Issues</p>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <h3 className="text-3xl font-bold">{fixMetrics?.total_issues || 0}</h3>
                <p className="text-xs text-muted-foreground">All tracked</p>
              </div>
            </div>

            {/* Fixed Issues with Progress Bar */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Fixed</p>
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              </div>
              <div className="space-y-2">
                <h3 className="text-3xl font-bold text-green-600 dark:text-green-400">
                  {fixMetrics?.fixed_issues || 0}
                </h3>
                <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-500"
                    style={{ width: `${fixMetrics?.fix_rate || 0}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Fix Rate with Circular Progress */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Fix Rate</p>
                <TrendingUp className="h-4 w-4 text-blue-500" />
              </div>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <svg className="w-16 h-16 transform -rotate-90">
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                      className="text-secondary"
                    />
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                      strokeDasharray={`${2 * Math.PI * 28}`}
                      strokeDashoffset={`${2 * Math.PI * 28 * (1 - (fixMetrics?.fix_rate || 0) / 100)}`}
                      className="text-blue-500 transition-all duration-500"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-bold">{fixMetrics?.fix_rate || 0}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Avg Fix Time */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Avg Time</p>
                <Clock className="h-4 w-4 text-orange-500" />
              </div>
              <div className="space-y-1">
                {fixMetrics?.avg_fix_time_hours ? (
                  <>
                    <h3 className="text-3xl font-bold">
                      {fixMetrics.avg_fix_time_hours < 1 
                        ? `${Math.round(fixMetrics.avg_fix_time_hours * 60)}`
                        : fixMetrics.avg_fix_time_hours.toFixed(1)
                      }
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      {fixMetrics.avg_fix_time_hours < 1 ? 'minutes' : 'hours'}
                    </p>
                  </>
                ) : (
                  <>
                    <h3 className="text-3xl font-bold text-muted-foreground">—</h3>
                    <p className="text-xs text-muted-foreground">No data</p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Fix Time by Severity - Enhanced */}
          {fixMetrics && fixMetrics.avg_by_severity && fixMetrics.avg_by_severity.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold">Fix Time by Severity</h4>
                <Badge variant="outline" className="text-xs">
                  {fixMetrics.avg_by_severity.length} severities tracked
                </Badge>
              </div>
              
              <div className="space-y-3">
                {fixMetrics.avg_by_severity.map((item) => {
                  const severityConfig = {
                    critical: { bg: 'bg-red-500', text: 'text-red-600 dark:text-red-400', icon: '🔴' },
                    high: { bg: 'bg-orange-500', text: 'text-orange-600 dark:text-orange-400', icon: '🟠' },
                    medium: { bg: 'bg-yellow-500', text: 'text-yellow-600 dark:text-yellow-400', icon: '🟡' },
                    low: { bg: 'bg-blue-500', text: 'text-blue-600 dark:text-blue-400', icon: '🔵' },
                  }
                  const config = severityConfig[item.priority as keyof typeof severityConfig] || severityConfig.low
                  
                  const maxTime = Math.max(...(fixMetrics.avg_by_severity?.map(s => s.avg_fix_time_hours) || [1]))
                  const widthPercent = (item.avg_fix_time_hours / maxTime) * 100
                  
                  return (
                    <div key={item.priority} className="group">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{config.icon}</span>
                          <span className="text-sm font-medium capitalize">{item.priority}</span>
                          <Badge variant="secondary" className="text-xs">
                            {item.count} fixed
                          </Badge>
                        </div>
                        <span className={`text-sm font-semibold ${config.text}`}>
                          {item.avg_fix_time_hours < 1 
                            ? `${Math.round(item.avg_fix_time_hours * 60)}m`
                            : `${item.avg_fix_time_hours.toFixed(1)}h`
                          }
                        </span>
                      </div>
                      <div className="h-3 w-full bg-secondary rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${config.bg} transition-all duration-500 group-hover:opacity-80`}
                          style={{ width: `${widthPercent}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Empty State */}
          {(!fixMetrics || !fixMetrics.avg_by_severity || fixMetrics.avg_by_severity.length === 0) && fixMetrics && fixMetrics.total_issues > 0 && (
            <div className="text-center py-6 text-muted-foreground border-t">
              <p className="text-sm">No completed issues with tracked fix times yet.</p>
              <p className="text-xs mt-1">Mark issues as done to see breakdown by severity.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Analytics & Charts Section */}
      {analyzedScans && analyzedScans.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Trend Chart */}
          {trendChartData.length > 0 && (
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <LineChart className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <CardTitle>Issues Trend</CardTitle>
                    <CardDescription>Track accessibility issues over time</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={trendChartData}>
                    <defs>
                      <linearGradient id="criticalGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#b91c1c" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#b91c1c" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="highGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#c2410c" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#c2410c" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="mediumGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#b45309" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#b45309" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis 
                      dataKey="name" 
                      className="text-xs"
                      tick={{ fill: 'currentColor' }}
                    />
                    <YAxis 
                      className="text-xs"
                      tick={{ fill: 'currentColor' }}
                    />
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="critical" 
                      stackId="1"
                      stroke="#b91c1c" 
                      fill="url(#criticalGradient)"
                      name="Critical"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="high" 
                      stackId="1"
                      stroke="#c2410c" 
                      fill="url(#highGradient)"
                      name="High"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="medium" 
                      stackId="1"
                      stroke="#b45309" 
                      fill="url(#mediumGradient)"
                      name="Medium"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="low" 
                      stackId="1"
                      stroke="#2563eb" 
                      fill="#2563eb"
                      fillOpacity={0.1}
                      name="Low"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Severity Distribution Pie Chart */}
          {severityDistributionData.length > 0 && (
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <PieChart className="h-5 w-5 text-purple-500" />
                  </div>
                  <div>
                    <CardTitle>Severity Distribution</CardTitle>
                    <CardDescription>Latest scan issue breakdown</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      data={severityDistributionData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(entry) => `${entry.name}: ${entry.value}`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {severityDistributionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                  </RechartsPieChart>
                </ResponsiveContainer>
                
                {/* Summary Stats */}
                <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{total}</p>
                    <p className="text-xs text-muted-foreground">Total Issues</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-600 dark:text-red-400">{critical}</p>
                    <p className="text-xs text-muted-foreground">Need Urgent Fix</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* WCAG Compliance & Quick Wins */}
      {latest && latestIssues && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* WCAG Compliance Breakdown */}
          {wcagComplianceData.length > 0 && (
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-indigo-500/10">
                    <BarChart3 className="h-5 w-5 text-indigo-500" />
                  </div>
                  <div>
                    <CardTitle>WCAG 2.1 Violations</CardTitle>
                    <CardDescription>Most frequently violated criteria</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsBarChart data={wcagComplianceData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis type="number" className="text-xs" tick={{ fill: 'currentColor' }} />
                    <YAxis 
                      dataKey="criterion" 
                      type="category" 
                      width={80}
                      className="text-xs"
                      tick={{ fill: 'currentColor' }}
                    />
                    <RechartsTooltip 
                      contentStyle={{ 
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                    />
                    <Bar dataKey="count" fill="#6366f1" radius={[0, 8, 8, 0]} />
                  </RechartsBarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Quick Wins */}
          {quickWins.length > 0 && (
            <Card className="border-2 border-green-500/30 bg-gradient-to-br from-green-50/50 to-emerald-50/50 dark:from-green-950/20 dark:to-emerald-950/20">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-green-500/10">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      Quick Wins
                      <Badge className="bg-green-500">
                        {quickWins.length} issues
                      </Badge>
                    </CardTitle>
                    <CardDescription>High priority, low effort - fix these first!</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {quickWins.map((win) => (
                    <div 
                      key={win.id} 
                      className="p-4 rounded-lg border-2 bg-background hover:shadow-md transition-all group"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge 
                              variant={win.severity === 'critical' ? 'destructive' : 'default'}
                              className="capitalize"
                            >
                              {win.severity}
                            </Badge>
                            <Badge variant="outline" className="text-green-600 border-green-600">
                              {win.effort} min
                            </Badge>
                          </div>
                          <p className="text-sm font-medium mb-1">{win.rule}</p>
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {win.description}
                          </p>
                        </div>
                        <Button 
                          size="sm" 
                          variant="ghost"
                          className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => scanId && navigate(`/scan/${scanId}/issues`)}
                        >
                          Fix →
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
                
                {scanId && (
                  <Button 
                    className="w-full mt-4 bg-green-600 hover:bg-green-700"
                    onClick={() => navigate(`/scan/${scanId}/issues`)}
                  >
                    View All Quick Wins →
                  </Button>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Explore Section - Always visible */}
      <Card className="border-2">
        <CardHeader><CardTitle>Explore</CardTitle></CardHeader>
        <CardContent>
          <Tabs defaultValue="summary" className="space-y-6">
            <TabsList className="grid w-full max-w-md grid-cols-3">
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="issues">Issues Table</TabsTrigger>
              <TabsTrigger value="ai">AI Insights</TabsTrigger>
            </TabsList>

            <TabsContent value="summary">
              {topRules.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {topRules.map((r, idx) => {
                  // Compute percentage width relative to the top rule
                  const maxCount = topRules[0]?.count || 1
                  const rawPct = Math.round((r.count / maxCount) * 100)
                  const pct = Math.min(100, Math.max(8, rawPct))
                  // Use Tailwind arbitrary width class (e.g. w-[45%]) safely
                  const widthClass = `w-[${pct}%]`
                  return (
                    <div key={r.id + idx} className="rounded-xl border p-3 bg-card">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm truncate max-w-[28ch]" title={r.id}>{r.id}</p>
                        <span className="text-xs text-muted-foreground">{r.count}</span>
                      </div>
                      <div className="mt-2 h-2 w-full rounded bg-secondary overflow-hidden">
                        <div className={`${widthClass} h-2 bg-primary`} />
                      </div>
                      {r.severity && (
                        <p className="mt-1 text-[10px] uppercase tracking-wide text-muted-foreground">{String(r.severity)}</p>
                      )}
                    </div>
                  )
                })}
              </div>
              ) : (
              <Card className="border-2">
                <CardContent className="p-8">
                  <EmptyState 
                    icon={BarChart3}
                    title="No issues to display"
                    description="Upload a scan with issues to see the top rules summary."
                  />
                </CardContent>
              </Card>
              )}
            </TabsContent>

            <TabsContent value="issues" className="space-y-4">
              <Card className="border-2">
                <CardContent className="pt-6">
                  <div className="flex flex-col sm:flex-row gap-4">
                    <div className="relative flex-1">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <label htmlFor="search-issues" className="sr-only">Search issues</label>
                      <Input id="search-issues" placeholder="Search issues by rule or element..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
                    </div>
                    <label htmlFor="severity-filter" className="sr-only">Filter by severity</label>
                    <Select value={severityFilter} onValueChange={setSeverityFilter}>
                      <SelectTrigger id="severity-filter" className="w-full sm:w-48">
                        <Filter className="h-4 w-4 mr-2" />
                        <SelectValue placeholder="Filter by severity" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Severities</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="serious">Serious</SelectItem>
                        <SelectItem value="moderate">Moderate</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="minor">Minor</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                      </SelectContent>
                    </Select>
                    <label htmlFor="sort-by" className="sr-only">Sort by</label>
                    <Select value={sortBy} onValueChange={(v) => setSortBy(v as any)}>
                      <SelectTrigger id="sort-by" className="w-full sm:w-48">
                        <ArrowUpDown className="h-4 w-4 mr-2" />
                        <SelectValue placeholder="Sort by" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="severity">Sort by Severity</SelectItem>
                        <SelectItem value="instances">Sort by Instances</SelectItem>
                        <SelectItem value="effort">Sort by Effort</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Detailed Issue Breakdown</CardTitle>
                      <p className="text-sm text-muted-foreground">{sorted.length} issues found</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={() => downloadCSV(sorted)}><FileSpreadsheet className="h-4 w-4 mr-2" />Export CSV</Button>
                      <Button variant="outline" size="sm" onClick={() => downloadJSON(sorted)}><FileJson className="h-4 w-4 mr-2" />Export JSON</Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {loadingIssues && <Skeleton className="h-32" />}
                  {!loadingIssues && (
                    <div className="rounded-md border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Rule</TableHead>
                            <TableHead>Element</TableHead>
                            <TableHead>AI Fix Suggestion</TableHead>
                            <TableHead>Severity</TableHead>
                            <TableHead>WCAG</TableHead>
                            <TableHead className="text-right">Instances</TableHead>
                            <TableHead className="text-right">Est. Effort</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {sorted.length === 0 ? (
                            <TableRow>
                              <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                                <div className="flex flex-col items-center gap-2">
                                  <CheckCircle2 className="h-8 w-8 text-accent" />
                                  <p>No issues found matching your filters</p>
                                </div>
                              </TableCell>
                            </TableRow>
                          ) : (
                            sorted.map((issue) => (
                              <TableRow key={issue.id} className="hover:bg-muted/30">
                                <TableCell>{issue.rule}</TableCell>
                                <TableCell><code className="text-xs bg-muted px-2 py-1 rounded">{issue.element}</code></TableCell>
                                <TableCell><div className="text-xs text-muted-foreground max-w-xs line-clamp-2">{issue.aiSuggestion}</div></TableCell>
                                <TableCell>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Badge variant={issue.severity === 'critical' ? 'destructive' : issue.severity === 'high' || issue.severity === 'serious' ? 'default' : 'secondary'}>
                                        {issue.severity}
                                      </Badge>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      <p>{getSeverityTooltip(issue.severity)}</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TableCell>
                                <TableCell>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Badge variant="outline">{issue.wcag}</Badge>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      <p>WCAG 2.1 Success Criterion</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TableCell>
                                <TableCell className="text-right">{issue.instances}</TableCell>
                                <TableCell className="text-right text-muted-foreground">{issue.effort}</TableCell>
                              </TableRow>
                            ))
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="ai">
              <Card className="border-2 bg-gradient-to-br from-primary/10 to-accent/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-primary" />AI-Powered Analysis Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">AI analyzed your issues and provided actionable suggestions and estimated effort to accelerate fixes.</p>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Pending Test Cycles - Enhanced */}
      {groupedPendingScans.length > 0 && (
        <Card className="border-2 border-amber-500/30 bg-gradient-to-br from-amber-50/50 to-orange-50/50 dark:from-amber-950/20 dark:to-orange-950/20">
          <div className="border-b bg-background/50 backdrop-blur p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-amber-500/10 ring-4 ring-amber-500/5">
                  <Clock className="h-5 w-5 text-amber-600 dark:text-amber-500" />
                </div>
                <div>
                  <CardTitle>Pending Test Cycles</CardTitle>
                  <CardDescription className="mt-1">
                    {groupedPendingScans.reduce((acc, group) => acc + group.length, 0)} reports awaiting analysis
                  </CardDescription>
                </div>
              </div>
              <Badge className="bg-amber-500 hover:bg-amber-600">
                {groupedPendingScans.length} cycles
              </Badge>
            </div>
          </div>
          <CardContent className="pt-6">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {groupedPendingScans.map((group, groupIndex) => {
                const firstScan = group[0]
                const testDate = new Date(firstScan.ts)
                
                return (
                  <Card 
                    key={`cycle-${groupIndex}`} 
                    className="group hover:shadow-xl hover:scale-[1.02] transition-all duration-300 border-2 border-amber-200/50 dark:border-amber-800/50 bg-background/80 backdrop-blur"
                  >
                    <CardHeader className="pb-3 space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="p-2.5 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 group-hover:scale-110 transition-transform">
                          <FileJson2 className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                        </div>
                        <Badge variant="outline" className="font-mono text-xs border-amber-300 dark:border-amber-700">
                          {group.length} reports
                        </Badge>
                      </div>
                      <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                          Test Cycle #{groupedPendingScans.length - groupIndex}
                        </CardTitle>
                        <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {testDate.toLocaleDateString()} at {testDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      {group.map((scan: any, index: number) => (
                        <div key={scan.id} className="flex gap-2 items-center">
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1 justify-between text-xs group/btn hover:bg-amber-50 dark:hover:bg-amber-950/30 hover:border-amber-400 dark:hover:border-amber-600 transition-all"
                            onClick={() => navigate(`/scan/${scan.id}`)}
                          >
                            <span className="truncate flex items-center gap-2">
                              <span className="w-5 h-5 rounded-full bg-amber-100 dark:bg-amber-900 flex items-center justify-center text-[10px] font-bold">
                                {index + 1}
                              </span>
                              {scan.url.split('/').pop() || scan.url}
                            </span>
                            <span className="ml-2 group-hover/btn:translate-x-1 transition-transform">→</span>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0 text-destructive hover:text-destructive hover:bg-destructive/10 transition-colors"
                            onClick={(e) => handleDeleteClick(scan.id, e)}
                            disabled={deleteMutation.isPending}
                            aria-label="Delete pending scan"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Analyzed Runs - Industry Standard Table */}
      {analyzedScans && analyzedScans.length > 0 && (
        <Card className="border-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Analyzed Runs</CardTitle>
                <CardDescription className="mt-1">
                  {analyzedScans.length} scans with accessibility issues detected
                </CardDescription>
              </div>
              <Link to="/runs">
                <Button variant="outline" size="sm">
                  View All →
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Date & Time</TableHead>
                    <TableHead>Framework</TableHead>
                    <TableHead className="text-right">Issues</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {analyzedScans.slice(0, 5).map((scan: any) => (
                    <TableRow key={scan.id} className="group">
                      <TableCell className="font-mono text-sm">
                        <Badge variant="outline">#{scan.id}</Badge>
                      </TableCell>
                      <TableCell className="max-w-[250px]">
                        <Link 
                          to={`/scan/${scan.id}`}
                          className="truncate hover:text-primary transition-colors font-medium text-sm block"
                        >
                          {scan.url}
                        </Link>
                      </TableCell>
                      <TableCell className="text-sm whitespace-nowrap">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div className="flex flex-col cursor-help">
                              <span className="font-medium">{formatRelativeTime(scan.ts)}</span>
                              <span className="text-xs text-muted-foreground">
                                {new Date(scan.ts).toLocaleDateString()}
                              </span>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="font-mono text-xs">{formatAbsoluteTime(scan.ts)}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="capitalize">
                          {scan.framework}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="text-lg font-semibold">{scan.total_issues}</span>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1.5">
                          {scan.critical_issues > 0 && (
                            <Badge className="bg-red-700 hover:bg-red-800 text-white dark:bg-red-700 dark:hover:bg-red-800 dark:text-white font-mono text-xs px-1.5">
                              {scan.critical_issues}C
                            </Badge>
                          )}
                          {scan.high_issues > 0 && (
                            <Badge className="bg-orange-700 hover:bg-orange-800 text-white dark:bg-orange-700 dark:hover:bg-orange-800 dark:text-white font-mono text-xs px-1.5">
                              {scan.high_issues}H
                            </Badge>
                          )}
                          {scan.medium_issues > 0 && (
                            <Badge className="bg-amber-800 hover:bg-amber-900 text-white dark:bg-amber-700 dark:hover:bg-amber-800 dark:text-white font-mono text-xs px-1.5">
                              {scan.medium_issues}M
                            </Badge>
                          )}
                          {scan.low_issues > 0 && (
                            <Badge variant="secondary" className="font-mono text-xs px-1.5">
                              {scan.low_issues}L
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/scan/${scan.id}/issues`)}
                            className="h-8"
                          >
                            View Issues
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteClick(scan.id, e)
                            }}
                            className="h-8 w-8 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                            aria-label="Delete scan"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
      </>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Scan</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this scan? This action cannot be undone. 
              All associated data, including issues and analysis results, will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setScanToDelete(null)}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={confirmDelete} 
              className="bg-destructive hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
    </TooltipProvider>
  )
}

