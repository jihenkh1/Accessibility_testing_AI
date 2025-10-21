import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listScanIssues, listScans, getAIUsageStats, getAICacheStats } from '../lib/api'
import { Link, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Input } from '../components/ui/input'
import { Skeleton } from '../components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table'
import { AlertCircle, AlertTriangle, Clock, TrendingUp, BarChart3, Sparkles, FileSpreadsheet, FileJson, Search, Filter, ArrowUpDown, CheckCircle2, Database, DollarSign, Upload } from 'lucide-react'
import { EmptyState } from '../components/EmptyState'

export default function DashboardNew() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useQuery({ queryKey: ['scans'], queryFn: listScans })

  const latest = data && data.length ? data[0] : (null as any)
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

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <h1 className="mb-2">Dashboard</h1>
      
      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
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

      {!isLoading && !error && !latest && (
        <Card className="border-2">
          <CardContent className="py-8">
            <EmptyState
              icon={Upload}
              title="No scans yet"
              description="Get started by uploading an accessibility scan report or running a live scan on your website."
              action={{
                label: "Upload Scan",
                onClick: () => navigate('/upload')
              }}
            />
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && latest && (
        <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-2 hover:shadow-sm transition-shadow">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Issues</p>
              <h2>{total}</h2>
            </div>
            <div className="p-3 rounded-xl bg-primary/10"><AlertCircle className="h-5 w-5 text-primary" /></div>
          </CardContent>
        </Card>
        <Card className="border-2 hover:shadow-sm transition-shadow">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Critical</p>
              <h2 className="text-destructive">{critPct}%</h2>
              <p className="text-xs text-muted-foreground">{critical} of {total}</p>
            </div>
            <div className="p-3 rounded-xl bg-destructive/10"><TrendingUp className="h-5 w-5 text-destructive" /></div>
          </CardContent>
        </Card>
        <Card className="border-2 hover:shadow-sm transition-shadow">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Estimated Effort</p>
              <h2>{effortH}h</h2>
              <p className="text-xs text-muted-foreground">{effortMin} minutes</p>
            </div>
            <div className="p-3 rounded-xl bg-accent/20"><Clock className="h-5 w-5 text-foreground" /></div>
          </CardContent>
        </Card>
      </div>

      {/* AI Performance Overview */}
      <Card className="border-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            AI Performance Overview
          </CardTitle>
          <CardDescription>
            Quick stats about AI-powered analysis features. <Link to="/settings" className="text-primary hover:underline">View detailed stats →</Link>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* AI Requests */}
            <div className="rounded-xl border p-4 bg-card hover:bg-accent/5 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-muted-foreground">AI Requests</p>
                <Sparkles className="h-4 w-4 text-purple-500" />
              </div>
              {aiUsageStats?.available ? (
                <>
                  <h3 className="text-2xl font-bold">{aiUsageStats.stats?.total_requests || 0}</h3>
                  <p className="text-xs text-muted-foreground mt-1">Total API calls</p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Not available</p>
              )}
            </div>

            {/* Token Usage */}
            <div className="rounded-xl border p-4 bg-card hover:bg-accent/5 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-muted-foreground">Tokens Used</p>
                <BarChart3 className="h-4 w-4 text-blue-500" />
              </div>
              {aiUsageStats?.available ? (
                <>
                  <h3 className="text-2xl font-bold">{(aiUsageStats.stats?.total_tokens || 0).toLocaleString()}</h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    ${(aiUsageStats.stats?.estimated_cost_usd || 0).toFixed(4)} cost
                  </p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Not available</p>
              )}
            </div>

            {/* Success Rate */}
            <div className="rounded-xl border p-4 bg-card hover:bg-accent/5 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-muted-foreground">Success Rate</p>
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              </div>
              {aiUsageStats?.available ? (
                <>
                  <h3 className="text-2xl font-bold">{((aiUsageStats.stats?.success_rate || 0) * 100).toFixed(1)}%</h3>
                  <p className="text-xs text-muted-foreground mt-1">API reliability</p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Not available</p>
              )}
            </div>

            {/* Cache Performance */}
            <div className="rounded-xl border p-4 bg-card hover:bg-accent/5 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-muted-foreground">Cache Entries</p>
                <Database className="h-4 w-4 text-orange-500" />
              </div>
              {aiCacheStats?.available ? (
                <>
                  <h3 className="text-2xl font-bold">{aiCacheStats.stats?.total_entries || 0}</h3>
                  <p className="text-xs text-muted-foreground mt-1">
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
            </TabsContent>

            <TabsContent value="issues" className="space-y-4">
              <Card className="border-2">
                <CardContent className="pt-6">
                  <div className="flex flex-col sm:flex-row gap-4">
                    <div className="relative flex-1">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input placeholder="Search issues by rule or element..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9" />
                    </div>
                    <Select value={severityFilter} onValueChange={setSeverityFilter}>
                      <SelectTrigger className="w-full sm:w-48">
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
                    <Select value={sortBy} onValueChange={(v) => setSortBy(v as any)}>
                      <SelectTrigger className="w-full sm:w-48">
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
                                <TableCell><Badge variant={issue.severity === 'critical' ? 'destructive' : issue.severity === 'high' || issue.severity === 'serious' ? 'default' : 'secondary'}>{issue.severity}</Badge></TableCell>
                                <TableCell><Badge variant="outline">{issue.wcag}</Badge></TableCell>
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

      {data && data.length > 0 && (
        <Card className="border-2">
          <CardHeader><CardTitle>Recent Runs</CardTitle></CardHeader>
          <CardContent>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b">
                    <th className="p-2">ID</th>
                    <th className="p-2">Date</th>
                    <th className="p-2">Framework</th>
                    <th className="p-2">URL</th>
                    <th className="p-2">Totals</th>
                    <th className="p-2">Severities</th>
                    <th className="p-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((r: any) => (
                    <tr key={r.id} className="border-b">
                      <td className="p-2">{r.id}</td>
                      <td className="p-2">{r.ts}</td>
                      <td className="p-2">{r.framework}</td>
                      <td className="p-2 truncate max-w-[32ch]" title={r.url}>{r.url}</td>
                      <td className="p-2">{r.total_issues} issues</td>
                      <td className="p-2 text-xs">C {r.critical_issues} · H {r.high_issues} · M {r.medium_issues} · L {r.low_issues}</td>
                      <td className="p-2"><div className="flex gap-3"><Link className="text-primary underline" to={`/scan/${r.id}`}>Summary</Link><Link className="text-primary underline" to={`/scan/${r.id}/issues`}>Issues</Link></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
      </>
      )}
    </div>
  )
}

