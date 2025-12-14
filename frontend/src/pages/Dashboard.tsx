import { useMemo, useState, useEffect } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listScanIssues, listScans, deleteScan, getFixMetrics, listProjects, cleanupDummyScans, deleteProject } from '../lib/api'
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
import { AlertCircle, Clock, Sparkles, FileSpreadsheet, FileJson, Search, Upload, Trash2, FileJson2, MoreVertical, BellRing, Zap, BarChart } from 'lucide-react'
import { EmptyState } from '../components/EmptyState'
import { toast } from 'sonner'
import { formatRelativeTime, formatAbsoluteTime } from '../utils/time'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu'
import MotionCard from '../components/MotionCard'
import { EmptyHero } from '../components/EmptyHero'

export default function DashboardNew() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  // Project selection state - persisted in localStorage
  const [selectedProject, setSelectedProject] = useState<string>(() => {
    return localStorage.getItem('selectedProject') || 'Default Project'
  })
  
  // Fetch all projects
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  })
  
  // Fetch scans filtered by selected project
  const { data, isLoading, error } = useQuery({ 
    queryKey: ['scans', selectedProject], 
    queryFn: () => listScans(selectedProject)
  })

  // Persist selected project to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('selectedProject', selectedProject)
  }, [selectedProject])

  // Clean up old project_creation placeholder scans on mount
  useEffect(() => {
    cleanupDummyScans()
      .then(result => {
        if (result.deleted_count > 0) {
          queryClient.invalidateQueries({ queryKey: ['scans'] })
        }
      })
      .catch(() => {
        // Silently fail on cleanup errors
      })
  }, [])

  // Delete mutation with toast notifications
  const deleteMutation = useMutation({
    mutationFn: deleteScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      queryClient.invalidateQueries({ queryKey: ['fixMetrics'] })
      queryClient.invalidateQueries({ queryKey: ['automated-context'] })
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

  const deleteProjectMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      queryClient.invalidateQueries({ queryKey: ['automated-context'] })
      setSelectedProject('Default Project')
      toast.success('Project deleted successfully', {
        description: 'The project and all its scans have been removed.'
      })
    },
    onError: (error: any) => {
      toast.error('Failed to delete project', {
        description: error?.response?.data?.detail || error.message
      })
    }
  })

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [scanToDelete, setScanToDelete] = useState<number | null>(null)
  const [deleteProjectDialogOpen, setDeleteProjectDialogOpen] = useState(false)

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

  const formatTime = (minutes: number): { display: string; unit: string } => {
    if (minutes < 60) {
      return { display: `${minutes}`, unit: 'min' }
    }
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (mins === 0) {
      return { display: `${hours}h`, unit: '' }
    }
    return { display: `${hours}h ${mins}min`, unit: '' }
  }

  const latest = analyzedScans && analyzedScans.length ? analyzedScans[0] : (null as any)
  const total = latest ? Number(latest.total_issues || 0) : 0
  const critical = latest ? Number(latest.critical_issues || 0) : 0
  const effortMin = latest ? Number(latest.estimated_total_time_minutes || 0) : 0
  const effortFormatted = effortMin ? formatTime(effortMin) : { display: '0', unit: 'min' }
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

  const { data: fixMetrics } = useQuery({
    queryKey: ['fixMetrics'],
    queryFn: getFixMetrics,
    refetchInterval: 30000, // Refresh every 30s
    retry: 1,
  })

  // Chart data processing
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

  const criticalBlockers = useMemo(() => {
    const issues = latestIssues?.items as Array<any> | undefined
    if (!issues || !issues.length) return []
    return issues
      .filter((issue) => String(issue.priority || issue.severity || '').toLowerCase() === 'critical')
      .map((issue) => ({
        rule: String(issue.rule_id || 'unknown'),
        selector: String(issue.selector || ''),
        effort: Number(issue.effort_minutes || 5),
        id: String(issue.rule_id || issue.id || issue.code || issue.selector || Math.random()),
      }))
  }, [latestIssues])

  const criticalPreview = criticalBlockers.slice(0, 2)
  const extraCriticalCount = Math.max(0, criticalBlockers.length - criticalPreview.length)

  const lastRunRelative = latest?.ts ? formatRelativeTime(latest.ts) : null
  const lastRunAbsolute = latest?.ts ? formatAbsoluteTime(latest.ts) : null

  const avgFixRateDisplay =
    fixMetrics?.fixed_issues && fixMetrics.fixed_issues > 0 ? `${(fixMetrics?.fix_rate ?? 0).toFixed(1)}%` : 'N/A'

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
      // More accurate status based on open issues
      if (critical > 0) {
        status = `Good (${critical} critical ${critical === 1 ? 'issue' : 'issues'} to fix)`
        color = 'text-orange-500'
        bgColor = 'from-orange-500/20 to-yellow-500/20'
      } else if (high > 0) {
        status = `Good (${high} high priority ${high === 1 ? 'fix' : 'fixes'} needed)`
        color = 'text-blue-500'
        bgColor = 'from-blue-500/20 to-cyan-500/20'
      } else if (medium > 0 || low > 0) {
        status = 'Near Compliant'
        color = 'text-green-500'
        bgColor = 'from-green-500/20 to-emerald-500/20'
      } else {
        status = 'Excellent'
        color = 'text-green-500'
        bgColor = 'from-green-500/20 to-emerald-500/20'
      }
    } else if (currentScore >= 75) {
      grade = 'B'
      wcagLevel = critical === 0 ? 'AA' : 'A'
      status = critical > 0 ? `Needs Improvement (${critical} critical)` : 'Good'
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
      description: `${total} total ${total === 1 ? 'issue' : 'issues'} found`,
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
  const hasScans = totalScans > 0
  const prefersReducedMotion = useReducedMotion()
  const containerVariants = {
    hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 8 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        staggerChildren: prefersReducedMotion ? 0 : 0.06,
        ease: 'easeOut',
      },
    },
  }
  const itemVariants = {
    hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 8 },
    show: { opacity: 1, y: 0 },
  }

  return (
    <TooltipProvider>
    <main className="w-full px-10 py-10 space-y-10">

      
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
              <Card key={i} className="shadow-sm">
                <CardHeader>
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-start justify-between">
                    <div className="space-y-3 flex-1">
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
          <Card className="shadow-sm">
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
        <Card className="border-destructive/50 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-destructive">Dashboard Error</CardTitle>
          </CardHeader>
          <CardContent className="py-6">
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

      {!isLoading && !error && (
        <div className="relative rounded-3xl bg-muted/40 p-8 space-y-8 overflow-hidden">
          <div className="pointer-events-none absolute inset-0 opacity-[0.04] bg-[radial-gradient(circle_at_top,rgba(0,0,0,0.25),transparent)]" aria-hidden />

          {hasScans ? (
            <div className="space-y-8">
              <section className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between relative">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h1 className="text-2xl font-semibold tracking-tight text-foreground">{selectedProject}</h1>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {totalScans} {totalScans === 1 ? 'test run' : 'test runs'} · {latest ? `Last analyzed ${lastRunRelative}` : 'Awaiting first scan'}
                  </p>
                  {lastRunAbsolute && (
                    <p className="text-sm text-muted-foreground">Recorded at {lastRunAbsolute}</p>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2 justify-end">
                  {projects && projects.length > 0 && (
                    <Select value={selectedProject} onValueChange={setSelectedProject}>
                      <SelectTrigger className="w-[220px] h-9 focus-visible:ring-[color:var(--accent)] focus-visible:ring-offset-2">
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
                  )}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-9 w-9 rounded-full border border-border bg-card shadow-sm hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                        aria-label="Project actions"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48 rounded-xl border border-border bg-popover shadow-lg">
                      <DropdownMenuLabel>Project Actions</DropdownMenuLabel>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => navigate('/settings')}>
                        Settings
                      </DropdownMenuItem>
                      {selectedProject !== 'Default Project' && (
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() => setDeleteProjectDialogOpen(true)}
                          aria-label="Delete project"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete Project
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </section>

              <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="show"
                className="space-y-8"
              >
                <section className="grid gap-6 md:grid-cols-2">
            <MotionCard variants={itemVariants} className="p-6 space-y-4 rounded-2xl border border-border bg-card/95 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2">
                    <BarChart className="h-4 w-4 text-primary" />
                    Action Center
                  </h2>
                  <p className="text-sm text-muted-foreground">Keep testers and developers focused on the next move.</p>
                </div>
                {latest && (
                  <Badge variant="framework" className="capitalize">
                    {latest.framework}
                  </Badge>
                )}
              </div>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {lastRunRelative ? `Last scan ${lastRunRelative}` : 'No scans analyzed yet'}
                  </p>
                  {lastRunAbsolute && (
                    <p className="text-sm text-muted-foreground">{lastRunAbsolute}</p>
                  )}
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl border bg-card/80 p-4">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Total Scans
                    </p>
                    <p className="mt-1 text-3xl font-semibold">{totalScans}</p>
                  </div>
                  <div className="rounded-2xl border bg-card/80 p-4">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Avg Fix Rate
                    </p>
                    <p className="mt-1 text-3xl font-semibold">{avgFixRateDisplay}</p>
                  </div>
                  <div className="rounded-2xl border bg-card/80 p-4">
                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      Critical Open
                    </p>
                    <p className="mt-1 text-3xl font-semibold text-destructive">
                      {criticalBlockers.length}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    variant="ghost"
                    className="text-primary gap-2"
                    onClick={() => latest && navigate(`/scan/${latest.id}/issues`)}
                    disabled={!latest}
                  >
                    View Latest Issues
                  </Button>
                  {accessibilityScore && (
                    <Badge variant="neutral" className="flex items-center gap-2">
                      Score {accessibilityScore.score} · Grade {accessibilityScore.grade}
                    </Badge>
                  )}
                </div>
              </div>
            </MotionCard>

            {criticalPreview.length > 0 ? (
            <MotionCard variants={itemVariants} className="p-6 space-y-3 rounded-2xl border border-destructive/60 bg-[color:var(--destructive-soft)] shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2 text-destructive">
                      <BellRing className="h-4 w-4" />
                      Action Required
                    </h2>
                    <p className="text-sm text-foreground">
                      {criticalBlockers.length} critical {criticalBlockers.length === 1 ? 'issue' : 'issues'} blocking accessibility
                    </p>
                  </div>
                  {extraCriticalCount > 0 && (
                    <Badge variant="outline">+{extraCriticalCount} more</Badge>
                  )}
                </div>
                {criticalPreview.map((issue) => (
                  <div
                    key={issue.id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-destructive/20 bg-card p-4"
                  >
                    <div>
                      <p className="text-sm font-semibold">{issue.rule}</p>
                      <p className="text-sm text-foreground/80 dark:text-foreground/90">
                        {issue.selector || 'Unknown location'}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="effort">~{issue.effort} min</Badge>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => latest && navigate(`/scan/${latest.id}/issues?severity=critical`)}
                    className="
                                gap-2
                                bg-destructive text-destructive-foreground
                                hover:bg-destructive/90
                                dark:bg-red-800 dark:hover:bg-red-800 dark:text-white
                                "
                              >
  Fix Now
</Button>

                    </div>
                  </div>
                ))}
              </MotionCard>
            ) : (
              <MotionCard variants={itemVariants} className="p-6 space-y-3 rounded-2xl border border-border bg-card/95 shadow-sm hover:shadow-md transition-shadow">
                <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  No Critical Blockers
                </h2>
                <p className="text-sm text-foreground">
                  You're clear of critical issues for now. Prioritize high and medium severity items in the tables below.
                </p>
              </MotionCard>
            )}
          </section>

          <section className="grid gap-6 md:grid-cols-2">
            <MotionCard variants={itemVariants} className="p-6 space-y-4 rounded-2xl border border-border bg-card/95 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-semibold tracking-tight text-foreground">Latest Scan Overview</h2>
                  <p className="text-sm text-muted-foreground">Snapshot of the most recent analysis</p>
                </div>
                <Badge variant="framework" className="capitalize">
                  {latest?.framework || '—'}
                </Badge>
              </div>
              {latest ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border bg-muted/20 p-3">
                    <p className="text-sm text-foreground/80">Total issues</p>
                    <p className="text-3xl font-semibold">{total}</p>
                  </div>
                  <div className="rounded-xl border bg-muted/20 p-3">
                    <p className="text-sm text-foreground/80">Critical</p>
                    <p className="text-3xl font-semibold text-destructive">{critical}</p>
                  </div>
                  <div className="rounded-xl border bg-muted/20 p-3">
                    <p className="text-sm text-foreground/80">Effort</p>
                    <p className="text-3xl font-semibold">
                      {effortFormatted.display}
                      {effortFormatted.unit}
                    </p>
                  </div>
                  <div className="rounded-xl border bg-muted/20 p-3">
                    <p className="text-sm text-foreground/80">Framework</p>
                    <p className="text-xl font-semibold capitalize">{latest.framework}</p>
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={AlertCircle}
                  title="No scan data available"
                  description="Upload a scan report to see the latest accessibility test results."
                />
              )}
            </MotionCard>

                {quickWins.length > 0 ? (
            <MotionCard variants={itemVariants} className="p-6 space-y-3 rounded-2xl border border-[color:var(--success)]/60 bg-[color:var(--success-soft)] shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2">
                      <Zap className="h-4 w-4 text-green-600 dark:text-green-400" />
                      Quick Wins
                    </h2>
                    <p className="text-sm text-foreground/80">High priority, low effort fixes</p>
                  </div>
                  <Badge variant="neutral">{quickWins.length} items</Badge>
                </div>
                {quickWins.slice(0, 3).map((win) => (
                  <div key={win.id} className="rounded-lg border bg-card p-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold">{win.rule}</p>
                      <p className="text-sm text-foreground/80 line-clamp-2">
                        {win.description || 'AI generated fix suggestion'}
                      </p>
                    </div>
                    <Badge variant="effort">{win.effort} min</Badge>
                  </div>
                ))}
                {quickWins.length > 3 && (
                  <Button variant="outline" size="sm" className="w-full gap-2" onClick={() => navigate(`/scan/${latest?.id}/issues`)}>
                    View all quick wins →
                  </Button>
                )}
              </MotionCard>
            ) : (
              <MotionCard variants={itemVariants} className="p-6 space-y-3 rounded-2xl border border-border bg-card/95 shadow-sm hover:shadow-md transition-shadow">
                <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2">
                  <Zap className="h-4 w-4 text-primary" />
                  Quick Wins
                </h2>
                <p className="text-sm text-muted-foreground">
                  No quick wins detected yet. Run another scan or review the issues table for potential low-effort fixes.
                </p>
              </MotionCard>
            )}
          </section>

          {latest && latestIssues && (
            <MotionCard variants={itemVariants} className="p-6 space-y-4 rounded-2xl border border-border bg-muted/40 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="text-lg font-semibold tracking-tight">Summary & Issues Table</h2>
                  <p className="text-sm text-muted-foreground">Switch between executive summary and a detailed table.</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="flex items-center gap-2">
                    <Search className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                    <div className="flex flex-col">
                      <label htmlFor="issues-search-input" className="sr-only">
                        Search rule or selector
                      </label>
                      <Input
                        id="issues-search-input"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search rule or selector"
                        className="h-9 w-[240px]"
                      />
                    </div>
                  </div>
                  <Select value={severityFilter} onValueChange={setSeverityFilter}>
                    <SelectTrigger className="h-9 w-[140px]">
                      <SelectValue placeholder="Severity" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All severities</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
                <Tabs defaultValue="summary">
                  <TabsList className="w-full sm:w-auto">
                    <TabsTrigger value="summary" className="flex-1 sm:flex-none data-[state=active]:text-[color:var(--accent)] data-[state=active]:border-b-2 data-[state=active]:border-[color:var(--accent)] rounded-none">Summary</TabsTrigger>
                    <TabsTrigger value="issues" className="flex-1 sm:flex-none data-[state=active]:text-[color:var(--accent)] data-[state=active]:border-b-2 data-[state=active]:border-[color:var(--accent)] rounded-none">Issues Table</TabsTrigger>
                  </TabsList>
                <TabsContent value="summary" className="space-y-4 pt-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-xl border p-4">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">AI enhanced issues</p>
                      <p className="text-3xl font-semibold">{latest.ai_enhanced_issues || 0}</p>
                    </div>
                    <div className="rounded-xl border p-4">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Estimated effort</p>
                      <p className="text-3xl font-semibold">
                        {effortFormatted.display}
                        {effortFormatted.unit}
                      </p>
                    </div>
                  </div>
                  <div className="rounded-xl border p-4 bg-muted/40">
                    <p className="text-sm font-semibold mb-1">AI Guidance</p>
                    <p className="text-sm text-muted-foreground">
                      Use the quick wins above to clear the fastest fixes, then hand off any complex issues with the table below.
                    </p>
                  </div>
                </TabsContent>
                <TabsContent value="issues" className="pt-4">
                  <div className="space-y-3">
                    <div className="rounded-lg border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Rule</TableHead>
                            <TableHead>Element</TableHead>
                            <TableHead>Severity</TableHead>
                            <TableHead>WCAG</TableHead>
                            <TableHead>AI Fix Suggestion</TableHead>
                            <TableHead className="text-right">Instances</TableHead>
                            <TableHead className="text-right">Effort</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {sorted.length === 0 ? (
                            <TableRow>
                              <TableCell colSpan={7} className="text-center text-muted-foreground">
                                No issues match your filters.
                              </TableCell>
                            </TableRow>
                          ) : (
                            sorted.slice(0, 25).map((issue) => (
                              <TableRow key={issue.id}>
                                <TableCell className="font-medium">{issue.rule}</TableCell>
                                <TableCell>
                                  <code className="text-xs bg-muted px-1 rounded">
                                    {issue.element || 'N/A'}
                                  </code>
                                </TableCell>
                                <TableCell>
                                  <Tooltip>
                                    <TooltipTrigger>
                                      <Badge
                                        variant={
                                          issue.severity === 'critical'
                                            ? 'critical'
                                            : issue.severity === 'high'
                                            ? 'high'
                                            : 'neutral'
                                        }
                                        className="capitalize"
                                      >
                                        {issue.severity}
                                      </Badge>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      <p>{getSeverityTooltip(issue.severity)}</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TableCell>
                                <TableCell>{issue.wcag || '—'}</TableCell>
                                <TableCell>
                                  <p className="max-w-[260px] text-sm text-muted-foreground line-clamp-2">
                                    {issue.aiSuggestion || 'AI fix guidance not available'}
                                  </p>
                                </TableCell>
                                <TableCell className="text-right">{issue.instances}</TableCell>
                                <TableCell className="text-right text-muted-foreground">{issue.effort}</TableCell>
                              </TableRow>
                            ))
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </MotionCard>
          )}

          {groupedPendingScans.length > 0 && (
            <MotionCard variants={itemVariants} className="p-6 space-y-4 rounded-2xl border border-border bg-card/95 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-muted">
                    <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold tracking-tight">Pending Test Cycles</h2>
                    <p className="text-sm text-muted-foreground">
                      {groupedPendingScans.reduce((acc, group) => acc + group.length, 0)} reports awaiting analysis
                    </p>
                  </div>
                </div>
                <Badge variant="outline">
                  {groupedPendingScans.length} cycles
                </Badge>
              </div>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {groupedPendingScans.map((group, groupIndex) => {
                  const firstScan = group[0]
                  const testDate = new Date(firstScan.ts)
                  
                  return (
                    <MotionCard 
                      key={`cycle-${groupIndex}`} 
                      variants={itemVariants}
                      className="p-4 space-y-3 rounded-2xl border border-border bg-card/95 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between">
                        <div className="p-2.5 rounded-xl bg-muted">
                          <FileJson2 className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                        </div>
                        <Badge variant="outline" className="font-mono text-xs">
                          {group.length} reports
                        </Badge>
                      </div>
                      <div>
                        <h3 className="text-base font-semibold flex items-center gap-2">
                          Test Cycle #{groupedPendingScans.length - groupIndex}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {testDate.toLocaleDateString()} at {testDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                      <div className="space-y-2">
                        {group.map((scan: any, index: number) => (
                          <div key={scan.id} className="flex gap-2 items-center">
                            <Button
                              size="sm"
                              variant="outline"
                              className="flex-1 justify-between text-xs hover:bg-muted transition-all min-w-0"
                              onClick={() => navigate(`/scan/${scan.id}`)}
                            >
                              <span className="truncate flex items-center gap-2 min-w-0">
                                <span className="w-5 h-5 rounded-full bg-muted text-foreground flex items-center justify-center text-[10px] font-bold">
                                  {index + 1}
                                </span>
                                <span className="truncate">{scan.url.split('/').pop() || scan.url}</span>
                              </span>
                              <span className="ml-2 transition-transform">→</span>
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
                      </div>
                    </MotionCard>
                  )
                })}
              </div>
            </MotionCard>
          )}

          {analyzedScans && analyzedScans.length > 0 && (
            <MotionCard variants={itemVariants} className="p-6 space-y-4 rounded-2xl border border-border bg-card/95 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold tracking-tight text-foreground">Recent Analyzed Runs</h2>
                  <p className="text-sm text-muted-foreground">
                    {analyzedScans.length} scans with accessibility issues detected
                  </p>
                </div>
                <Link to="/runs">
                  <Button variant="outline" size="sm" className="gap-2">
                    View All →
                  </Button>
                </Link>
              </div>
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
                          <Badge variant="framework" className="capitalize">
                            {scan.framework}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <span className="text-lg font-semibold">{scan.total_issues}</span>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1.5">
                            {scan.critical_issues > 0 && (
                              <Badge variant="critical">
                                Critical {scan.critical_issues}
                              </Badge>
                            )}
                            {scan.high_issues > 0 && (
                              <Badge variant="high">
                                High {scan.high_issues}
                              </Badge>
                            )}
                            {scan.medium_issues > 0 && (
                              <Badge variant="neutral">
                                Medium {scan.medium_issues}
                              </Badge>
                            )}
                            {scan.low_issues > 0 && (
                              <Badge variant="neutral">
                                Low {scan.low_issues}
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
                              className="h-8 gap-2"
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
            </MotionCard>
          )}
        </motion.div>
      </div>
    ) : (
            <EmptyHero
              selectedProject={selectedProject}
              totalScans={totalScans}
              lastRunRelative={lastRunRelative}
              projects={projects}
              setSelectedProject={setSelectedProject}
              setDeleteProjectDialogOpen={setDeleteProjectDialogOpen}
              navigate={navigate}
            />
          )}
        </div>
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

      {/* Delete Project Confirmation Dialog */}
      <AlertDialog open={deleteProjectDialogOpen} onOpenChange={setDeleteProjectDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Project</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the project "{selectedProject}"? This will permanently delete 
              the project and ALL its scans and issues. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={() => {
                deleteProjectMutation.mutate(selectedProject)
                setDeleteProjectDialogOpen(false)
              }}
              className="bg-destructive hover:bg-destructive/90"
            >
              Delete Project
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
    </TooltipProvider>
  )
}
