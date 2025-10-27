import { useMemo, useState } from 'react'
import { useParams, useSearchParams, Link as RouterLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Select } from '../components/ui/select'
import { ChevronDown, ChevronRight, Copy, Check, AlertCircle, AlertTriangle, Info, Circle, Clock, CheckCircle, XCircle } from 'lucide-react'

type Issue = {
  id?: number
  rule_id: string
  priority: string
  user_impact: string
  fix_suggestion: string
  effort_minutes: number
  wcag_refs: string[]
  selector?: string
  source?: string
  status?: string
}

type PageResult = { items: Issue[]; total: number }

// Severity badge component with color coding
const SeverityBadge = ({ priority }: { priority: string }) => {
  const severityConfig = {
    critical: { color: 'bg-red-500 hover:bg-red-600 text-white', icon: AlertCircle, label: 'Critical' },
    high: { color: 'bg-orange-500 hover:bg-orange-600 text-white', icon: AlertTriangle, label: 'High' },
    medium: { color: 'bg-yellow-500 hover:bg-yellow-600 text-white', icon: AlertTriangle, label: 'Medium' },
    low: { color: 'bg-blue-500 hover:bg-blue-600 text-white', icon: Info, label: 'Low' },
  }
  const config = severityConfig[priority.toLowerCase() as keyof typeof severityConfig] || severityConfig.low
  const Icon = config.icon

  return (
    <Badge className={`${config.color} flex items-center gap-1`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </Badge>
  )
}

// Copy button component with feedback
const CopyButton = ({ text, label }: { text: string; label?: string }) => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleCopy}
      className="h-7 px-2 gap-1"
    >
      {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
      {label && <span>{label}</span>}
    </Button>
  )
}

// Status badge component
const StatusBadge = ({ status }: { status: string }) => {
  const statusConfig = {
    todo: { color: 'bg-gray-500 hover:bg-gray-600 text-white', icon: Circle, label: 'To Do' },
    in_progress: { color: 'bg-blue-500 hover:bg-blue-600 text-white', icon: Clock, label: 'In Progress' },
    done: { color: 'bg-green-500 hover:bg-green-600 text-white', icon: CheckCircle, label: 'Done' },
    wont_fix: { color: 'bg-gray-400 hover:bg-gray-500 text-white', icon: XCircle, label: "Won't Fix" },
  }
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.todo
  const Icon = config.icon

  return (
    <Badge className={`${config.color} flex items-center gap-1 text-xs`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </Badge>
  )
}

// Status dropdown component
const StatusDropdown = ({ 
  issueId, 
  currentStatus, 
  onStatusChange 
}: { 
  issueId: number
  currentStatus: string
  onStatusChange: (newStatus: string) => void
}) => {
  const statuses = [
    { value: 'todo', label: 'To Do', icon: Circle },
    { value: 'in_progress', label: 'In Progress', icon: Clock },
    { value: 'done', label: 'Done', icon: CheckCircle },
    { value: 'wont_fix', label: "Won't Fix", icon: XCircle },
  ]

  return (
    <select
      value={currentStatus}
      onChange={(e) => onStatusChange(e.target.value)}
      className="text-xs border border-input rounded-md px-2 py-1 bg-background hover:bg-muted transition-colors cursor-pointer"
      onClick={(e) => e.stopPropagation()}
      aria-label="Issue status"
      title="Change issue status"
    >
      {statuses.map((s) => (
        <option key={s.value} value={s.value}>
          {s.label}
        </option>
      ))}
    </select>
  )
}

// Individual issue card component
const IssueCard = ({ 
  issue, 
  index, 
  expanded, 
  onToggle,
  onStatusChange 
}: { 
  issue: Issue
  index: number
  expanded: boolean
  onToggle: () => void
  onStatusChange: (newStatus: string) => void
}) => {
  const currentStatus = issue.status || 'todo'

  return (
    <Card className={`border hover:border-primary/50 transition-colors ${currentStatus === 'done' ? 'opacity-60' : ''}`}>
      <CardContent className="p-0">
        {/* Collapsed view - always visible */}
        <div
          className="p-4 cursor-pointer flex items-center justify-between hover:bg-muted/50 transition-colors"
          onClick={onToggle}
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="flex-shrink-0">
              {expanded ? (
                <ChevronDown className="w-5 h-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="w-5 h-5 text-muted-foreground" />
              )}
            </div>
            <SeverityBadge priority={issue.priority} />
            <StatusBadge status={currentStatus} />
            <div className="flex-1 min-w-0">
              <div className={`font-medium truncate ${currentStatus === 'done' ? 'line-through' : ''}`}>
                {issue.rule_id}
              </div>
              <div className="text-xs text-muted-foreground">
                {issue.effort_minutes}min • {issue.wcag_refs?.join(', ') || 'N/A'}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0 ml-4">
            {issue.id && (
              <StatusDropdown
                issueId={issue.id}
                currentStatus={currentStatus}
                onStatusChange={onStatusChange}
              />
            )}
            <span className="text-xs text-muted-foreground">#{index + 1}</span>
          </div>
        </div>

        {/* Expanded view - shows on click */}
        {expanded && (
          <div className="border-t p-4 space-y-4 bg-muted/20">
            {/* User Impact */}
            <div>
              <div className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                User Impact
              </div>
              <div className="text-sm">{issue.user_impact}</div>
            </div>

            {/* Fix Suggestion */}
            <div>
              <div className="text-xs font-semibold text-muted-foreground uppercase mb-1 flex items-center justify-between">
                Fix Suggestion
                <CopyButton text={issue.fix_suggestion} label="Copy" />
              </div>
              <pre className="text-sm bg-card p-3 rounded-md border overflow-x-auto">
                <code>{issue.fix_suggestion}</code>
              </pre>
            </div>

            {/* Selector */}
            {issue.selector && (
              <div>
                <div className="text-xs font-semibold text-muted-foreground uppercase mb-1 flex items-center justify-between">
                  CSS Selector
                  <CopyButton text={issue.selector} label="Copy" />
                </div>
                <code className="text-sm bg-card p-2 rounded-md border block overflow-x-auto">
                  {issue.selector}
                </code>
              </div>
            )}

            {/* Source Code */}
            {issue.source && (
              <div>
                <div className="text-xs font-semibold text-muted-foreground uppercase mb-1 flex items-center justify-between">
                  Source HTML
                  <CopyButton text={issue.source} label="Copy" />
                </div>
                <pre className="text-sm bg-card p-3 rounded-md border overflow-x-auto max-h-32">
                  <code>{issue.source}</code>
                </pre>
              </div>
            )}

            {/* WCAG References */}
            <div className="flex items-center gap-2 flex-wrap">
              <div className="text-xs font-semibold text-muted-foreground uppercase">
                WCAG:
              </div>
              {issue.wcag_refs?.map((ref, i) => (
                <Badge key={i} variant="outline" className="text-xs">
                  {ref}
                </Badge>
              ))}
              <CopyButton text={issue.wcag_refs?.join(', ') || ''} />
            </div>

            {/* Quick Stats Footer */}
            <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
              <span>⏱️ Estimated fix: {issue.effort_minutes} minutes</span>
              <span>🔍 Rule: {issue.rule_id}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default function RunIssues() {
  const { id } = useParams()
  const runId = Number(id)
  const [searchParams, setSearchParams] = useSearchParams()

  const [severities, setSeverities] = useState<string[]>(searchParams.getAll('severity') || [])
  const [ruleId, setRuleId] = useState<string>(searchParams.get('rule_id') || '')
  const [q, setQ] = useState<string>(searchParams.get('q') || '')
  const [page, setPage] = useState<number>(Number(searchParams.get('page') || '1'))
  const [size, setSize] = useState<number>(Number(searchParams.get('size') || '50'))
  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set())
  const [groupBySeverity, setGroupBySeverity] = useState<boolean>(false)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const queryKey = useMemo(() => ['issues', runId, { severities, ruleId, q, page, size }], [runId, severities, ruleId, q, page, size])

  const { data, isLoading, error } = useQuery({
    queryKey,
    queryFn: async (): Promise<PageResult> => {
      const params = new URLSearchParams()
      severities.forEach(s => params.append('severity', s))
      if (ruleId) params.set('rule_id', ruleId)
      if (q) params.set('q', q)
      params.set('page', String(page))
      params.set('size', String(size))
      const res = await api.get(`/scans/${runId}/issues?` + params.toString())
      return res.data as PageResult
    },
    enabled: !Number.isNaN(runId),
  })

  // Fetch status summary
  const { data: statusSummary } = useQuery({
    queryKey: ['status-summary', runId],
    queryFn: async () => {
      const res = await api.get(`/scans/${runId}/status-summary`)
      return res.data
    },
    enabled: !Number.isNaN(runId),
  })

  const total = data?.total ?? 0

  // Group issues by severity
  const groupedIssues = useMemo(() => {
    if (!data?.items) return {}
    const groups: Record<string, Issue[]> = {
      critical: [],
      high: [],
      medium: [],
      low: [],
    }
    data.items.forEach(issue => {
      const severity = issue.priority.toLowerCase()
      if (groups[severity]) {
        groups[severity].push(issue)
      }
    })
    return groups
  }, [data?.items])

  const csvUrl = useMemo(() => {
    const params = new URLSearchParams()
    severities.forEach(s => params.append('severity', s))
    if (ruleId) params.set('rule_id', ruleId)
    if (q) params.set('q', q)
    return `/api/scans/${runId}/issues.csv?` + params.toString()
  }, [runId, severities, ruleId, q])

  const applyFilters = () => {
    const params = new URLSearchParams()
    severities.forEach(s => params.append('severity', s))
    if (ruleId) params.set('rule_id', ruleId)
    if (q) params.set('q', q)
    params.set('page', String(1))
    params.set('size', String(size))
    setSearchParams(params)
    setPage(1)
  }

  const handleStatusChange = async (issueId: number, newStatus: string) => {
    try {
      await api.patch(`/issues/${issueId}/status?status=${newStatus}`)
      // Refetch data to update UI
      window.location.reload()
    } catch (error) {
      console.error('Failed to update status:', error)
    }
  }

  return (
    <div className="space-y-3">
      <h1 className="mb-2">Issues for scan #{runId}</h1>
      <Card className="border-2">
        <CardHeader><CardTitle>Filters</CardTitle></CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              {['critical','high','medium','low'].map(s => (
                <label key={s} className="flex items-center gap-1 text-sm">
                  <input type="checkbox" checked={severities.includes(s)} onChange={(e) => {
                    setSeverities(prev => e.target.checked ? [...prev, s] : prev.filter(x => x!==s))
                  }} /> {s}
                </label>
              ))}
            </div>
            <input className="border bg-input-background border-input rounded-md px-3 py-2 text-sm text-foreground" placeholder="Rule ID" value={ruleId} onChange={e => setRuleId(e.target.value)} />
            <input className="border bg-input-background border-input rounded-md px-3 py-2 text-sm min-w-[260px] text-foreground" placeholder="Search" value={q} onChange={e => setQ(e.target.value)} />
            <Button onClick={applyFilters}>Apply</Button>
            <a className="underline text-primary" href={csvUrl} target="_blank" rel="noopener">Export CSV</a>
            <RouterLink className="underline" to={`/dashboard`}>Back</RouterLink>
          </div>
        </CardContent>
      </Card>

      {isLoading && <div>Loading...</div>}
      {error && <div className="text-destructive">Failed to load issues</div>}

      {/* Status Summary Card */}
      {statusSummary && (
        <Card className="border-2 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              📊 Progress Tracker
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="text-center p-3 bg-white dark:bg-gray-900 rounded-md shadow-sm">
                <div className="text-2xl font-bold text-gray-500">
                  {statusSummary.status_counts?.todo || 0}
                </div>
                <div className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
                  <Circle className="w-3 h-3" /> To Do
                </div>
              </div>
              <div className="text-center p-3 bg-white dark:bg-gray-900 rounded-md shadow-sm">
                <div className="text-2xl font-bold text-blue-500">
                  {statusSummary.status_counts?.in_progress || 0}
                </div>
                <div className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
                  <Clock className="w-3 h-3" /> In Progress
                </div>
              </div>
              <div className="text-center p-3 bg-white dark:bg-gray-900 rounded-md shadow-sm">
                <div className="text-2xl font-bold text-green-500">
                  {statusSummary.status_counts?.done || 0}
                </div>
                <div className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
                  <CheckCircle className="w-3 h-3" /> Done
                </div>
              </div>
              <div className="text-center p-3 bg-white dark:bg-gray-900 rounded-md shadow-sm">
                <div className="text-2xl font-bold text-gray-400">
                  {statusSummary.status_counts?.wont_fix || 0}
                </div>
                <div className="text-xs text-muted-foreground flex items-center justify-center gap-1 mt-1">
                  <XCircle className="w-3 h-3" /> Won't Fix
                </div>
              </div>
              <div className="text-center p-3 bg-gradient-to-br from-green-500 to-blue-500 text-white rounded-md shadow-sm">
                <div className="text-2xl font-bold">
                  {statusSummary.completion_percentage || 0}%
                </div>
                <div className="text-xs mt-1">Complete</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {data && (
        <>
          {/* Summary Stats */}
          <Card className="border-2 bg-muted/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-6">
                  <div>
                    <div className="text-2xl font-bold">{total}</div>
                    <div className="text-xs text-muted-foreground">Total Issues</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold">
                      {Math.round(data.items.reduce((sum, it) => sum + it.effort_minutes, 0) / 60)}h
                    </div>
                    <div className="text-xs text-muted-foreground">Est. Time</div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => {
                      const allIndexes = data.items.map((_, idx) => (page - 1) * size + idx)
                      setExpandedIssues(new Set(allIndexes))
                    }}>
                      Expand All
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => {
                      setExpandedIssues(new Set())
                    }}>
                      Collapse All
                    </Button>
                    <Button 
                      variant={groupBySeverity ? "default" : "outline"} 
                      size="sm" 
                      onClick={() => setGroupBySeverity(!groupBySeverity)}
                    >
                      {groupBySeverity ? "List View" : "Group by Severity"}
                    </Button>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  Page {page} • Showing {data.items.length} of {total}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Issues List */}
          {groupBySeverity ? (
            // Grouped by severity view
            <div className="space-y-4">
              {(['critical', 'high', 'medium', 'low'] as const).map(severity => {
                const severityIssues = groupedIssues[severity] || []
                if (severityIssues.length === 0) return null

                return (
                  <div key={severity}>
                    <div className="flex items-center gap-2 mb-2">
                      <SeverityBadge priority={severity} />
                      <span className="text-sm font-medium">
                        {severityIssues.length} {severityIssues.length === 1 ? 'issue' : 'issues'}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {severityIssues.map((issue: Issue, idx: number) => {
                        const issueIndex = (page - 1) * size + data.items.indexOf(issue)
                        return (
                          <IssueCard 
                            key={`${severity}-${idx}`} 
                            issue={issue} 
                            index={issueIndex}
                            expanded={expandedIssues.has(issueIndex)}
                            onToggle={() => {
                              setExpandedIssues(prev => {
                                const newSet = new Set(prev)
                                if (newSet.has(issueIndex)) {
                                  newSet.delete(issueIndex)
                                } else {
                                  newSet.add(issueIndex)
                                }
                                return newSet
                              })
                            }}
                            onStatusChange={(newStatus) => {
                              if (issue.id) handleStatusChange(issue.id, newStatus)
                            }}
                          />
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            // Standard list view
            <div className="space-y-2">
              {(data?.items ?? []).map((issue: Issue, idx: number) => {
                const issueIndex = (page - 1) * size + idx
                return (
                  <IssueCard 
                    key={idx} 
                    issue={issue} 
                    index={issueIndex}
                    expanded={expandedIssues.has(issueIndex)}
                    onToggle={() => {
                      setExpandedIssues(prev => {
                        const newSet = new Set(prev)
                        if (newSet.has(issueIndex)) {
                          newSet.delete(issueIndex)
                        } else {
                          newSet.add(issueIndex)
                        }
                        return newSet
                      })
                    }}
                    onStatusChange={(newStatus) => {
                      if (issue.id) handleStatusChange(issue.id, newStatus)
                    }}
                  />
                )
              })}
            </div>
          )}

          {/* Pagination */}
          <Card className="border-2">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  Showing {(page - 1) * size + 1} - {Math.min(page * size, total)} of {total} issues
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      const p = Math.max(1, page - 1)
                      setPage(p)
                      const pr = new URLSearchParams(location.search)
                      pr.set('page', String(p))
                      pr.set('size', String(size))
                      history.replaceState(null, '', `?${pr.toString()}`)
                    }}
                    disabled={page <= 1}
                  >
                    Prev
                  </Button>
                  <span className="text-sm text-muted-foreground px-3">
                    Page {page}
                  </span>
                  <Button
                    variant="outline"
                    onClick={() => {
                      const p = page + 1
                      if ((p - 1) * size >= total) return
                      setPage(p)
                      const pr = new URLSearchParams(location.search)
                      pr.set('page', String(p))
                      pr.set('size', String(size))
                      history.replaceState(null, '', `?${pr.toString()}`)
                    }}
                    disabled={page * size >= total}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

