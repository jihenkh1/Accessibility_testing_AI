import { useRef, useState, useMemo } from 'react'
import { Upload, FileJson, Sparkles, Loader2, Clock, Download, CheckCircle2, Layers } from 'lucide-react'
import { Button } from '../components/ui/button'
import { CardContent, CardTitle, CardDescription } from '../components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Textarea } from '../components/ui/textarea'
import { Progress } from '../components/ui/progress'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { postScan, listScans, listProjects, createProject as createProjectAPI } from '../lib/api'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import MotionCard from '../components/MotionCard'

export default function UploadNew() {
  const [file, setFile] = useState<File | null>(null)
  const [framework, setFramework] = useState('html')
  const [projectName, setProjectName] = useState('Default Project')
  const [customProjectName, setCustomProjectName] = useState('')
  const [jsonText, setJsonText] = useState('')
  const [latestScanId, setLatestScanId] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: scans } = useQuery({ queryKey: ['scans'], queryFn: () => listScans() })
  const { data: projects } = useQuery({ queryKey: ['projects'], queryFn: listProjects })

  // Create project mutation for instant creation
  const createProject = useMutation({
    mutationFn: async (newProjectName: string) => {
      return createProjectAPI(newProjectName)
    },
    onSuccess: (data, newProjectName) => {
      // Invalidate queries to refresh project list
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      
      // Update selected project and clear input
      setProjectName(newProjectName)
      setCustomProjectName('')
      
      toast.success('Project created!', {
        description: `"${newProjectName}" is now available`
      })
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.detail || error.message || 'Please try again'
      toast.error('Failed to create project', {
        description: errorMsg
      })
    }
  })

  // Get pending scans and group by test cycle (within 5 minutes)
  const pendingScans = useMemo(() => {
    return scans?.filter((scan: any) => scan.total_issues === 0) || []
  }, [scans])

  // Group pending scans by test cycle (scans within 5 minutes of each other)
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

  const analyze = useMutation({
    mutationFn: async () => {
      let report: any = null
      if (jsonText.trim()) report = JSON.parse(jsonText)
      else if (file) report = JSON.parse(await file.text())
      else throw new Error('Provide a JSON file or paste JSON')
      
      // Use custom project name if provided, otherwise use selected project
      const finalProjectName = customProjectName.trim() || projectName
      
      return postScan({ 
        report, 
        framework, 
        use_ai: true, 
        max_ai_issues: 50, 
        url: file?.name || 'uploaded_file',
        project_name: finalProjectName
      })
    },
    onSuccess: (data) => {
      // Clear custom project input and show success feedback
      if (customProjectName.trim()) {
        setProjectName(customProjectName.trim())
        setCustomProjectName('')
      }
      if (data?.scan_id) {
        setLatestScanId(data.scan_id)
      }
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    },
  })

  const onFile = (f: File) => {
    setFile(f)
    setJsonText('')
  }

  return (
    <main className="max-w-7xl mx-auto px-4 lg:px-8 py-10 space-y-10">
      <div className="rounded-2xl bg-muted/40 p-8 space-y-8 relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.03] bg-[radial-gradient(circle_at_top,rgba(0,0,0,0.4),transparent)] pointer-events-none" aria-hidden />

        <header className="flex flex-wrap items-start justify-between gap-4 relative">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">Upload & Analyze</h1>
            </div>
            <p className="text-sm text-muted-foreground">
              Upload your accessibility scan results for intelligent analysis
            </p>
          </div>
          <Button variant="outline" size="sm" className="gap-2" onClick={() => navigate('/dashboard')}>
            <Layers className="h-4 w-4" />
            Back to Dashboard
          </Button>
        </header>

        {groupedPendingScans.length > 0 && (
          <MotionCard className="p-6 space-y-4 rounded-xl border border-amber-400/60 bg-amber-100/40 dark:bg-amber-900/20 shadow-sm hover:shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                <h2 className="text-lg font-semibold tracking-tight">Pending Analysis</h2>
              </div>
              <Badge variant="secondary" className="bg-amber-500/80 text-amber-950 dark:bg-amber-400 dark:text-amber-950">
                {groupedPendingScans.reduce((sum, group) => sum + group.length, 0)} report{groupedPendingScans.reduce((sum, group) => sum + group.length, 0) !== 1 ? 's' : ''} waiting
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              These reports have been uploaded but not analyzed yet. Reports from the same test cycle are grouped together.
            </p>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {groupedPendingScans.map((group, groupIndex) => {
                const firstScan = group[0]
                const testDate = new Date(firstScan.ts).toLocaleString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })
                
                return (
                  <MotionCard key={`group-${groupIndex}`} className="p-4 space-y-3 rounded-xl border border-amber-400/50 bg-card shadow-sm hover:shadow-md">
                    <div className="flex items-start justify-between">
                      <FileJson className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                      <Badge className="text-xs bg-amber-500 text-amber-950 dark:text-amber-50">Test Cycle</Badge>
                    </div>
                    <div>
                      <h3 className="text-base font-semibold">Test Cycle {groupedPendingScans.length - groupIndex}</h3>
                      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {testDate}
                      </p>
                    </div>
                    <div className="space-y-2">
                      {group.map((scan: any) => (
                        <Button
                          key={scan.id}
                          size="sm"
                          variant="outline"
                          className="w-full justify-between hover:bg-amber-50 dark:hover:bg-amber-900/30"
                          onClick={() => navigate(`/scan/${scan.id}`)}
                        >
                          <span className="text-xs truncate">{scan.url}</span>
                          <span className="text-xs ml-2">Analyze →</span>
                        </Button>
                      ))}
                    </div>
                    <p className="text-xs text-center text-muted-foreground">
                      {group.length} report{group.length !== 1 ? 's' : ''} in this cycle
                    </p>
                  </MotionCard>
                )
              })}
            </div>
          </MotionCard>
        )}

        <MotionCard className="p-6 space-y-6 rounded-xl border border-border bg-card shadow-sm hover:shadow-md">
          <div className="flex items-start justify-between gap-3">
            <div>
              <CardTitle className="text-lg font-semibold tracking-tight">Upload Scan File</CardTitle>
              <CardDescription>Supports JSON format from axe-core or Pa11y</CardDescription>
            </div>
            <Badge variant="framework" className="capitalize">{framework}</Badge>
          </div>
          <CardContent className="p-0 space-y-6">
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f && f.type === 'application/json') onFile(f) }}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-border rounded-xl p-12 text-center cursor-pointer hover:bg-muted/30 transition-colors"
            >
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                  {file ? <FileJson className="h-8 w-8 text-primary" /> : <Upload className="h-8 w-8 text-primary" />}
                </div>
                {file ? (
                  <div>
                    <p className="text-foreground mb-1">{file.name}</p>
                    <p className="text-sm text-muted-foreground">{(file.size/1024).toFixed(2)} KB</p>
                  </div>
                ) : (
                  <div>
                    <p className="text-foreground mb-1">Drag and drop your scan file here</p>
                    <p className="text-sm text-muted-foreground">or click to browse</p>
                  </div>
                )}
              </div>
              <input ref={fileInputRef} type="file" accept=".json" onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} className="hidden" aria-label="Upload JSON scan file" />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Framework</label>
                <Select value={framework} onValueChange={setFramework}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select framework" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="html">HTML</SelectItem>
                    <SelectItem value="react">React</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Project</label>
                <Select value={projectName} onValueChange={setProjectName}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select project" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects?.map((project) => (
                      <SelectItem key={project} value={project}>{project}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Or create a new project"
                  value={customProjectName}
                  onChange={(e) => setCustomProjectName(e.target.value)}
                  aria-label="Custom project name"
                />
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="gap-2"
                  onClick={() => customProjectName.trim() && createProject.mutate(customProjectName.trim())}
                  disabled={createProject.isPending || !customProjectName.trim()}
                >
                  {createProject.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Add Project
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Paste JSON (optional)</label>
              <Textarea
                value={jsonText}
                onChange={(e) => setJsonText(e.target.value)}
                placeholder="Paste your JSON report here"
                className="min-h-[160px]"
              />
              <div className="text-xs text-muted-foreground">If both file and text are provided, the file takes precedence.</div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Button
                className="gap-2 min-w-[180px] bg-[color:var(--accent)] text-[color:var(--accent-foreground,var(--primary-foreground))] hover:bg-[color:var(--accent-dark,var(--accent))] focus-visible:ring-[color:var(--accent)] focus-visible:ring-offset-2"
                onClick={() => {
                  setLatestScanId(null)
                  analyze.mutate()
                }}
                disabled={analyze.isPending}
              >
                {analyze.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                Analyze Report
              </Button>
              {latestScanId && (
                <Button
                  variant="outline"
                  className="gap-2"
                  onClick={() => navigate(`/scan/${latestScanId}`)}
                >
                  View Results
                </Button>
              )}
              {analyze.isSuccess && (
                <Badge variant="neutral" className="gap-1">
                  <CheckCircle2 className="h-3 w-3 text-green-600" />
                  Uploaded
                </Badge>
              )}
            </div>

            {analyze.isPending && (
              <div className="space-y-2">
                <Progress value={60} aria-label="Analyzing report" />
                <p className="text-sm text-muted-foreground">Analyzing... This may take a moment.</p>
              </div>
            )}
          </CardContent>
        </MotionCard>
      </div>
    </main>
  )
}
