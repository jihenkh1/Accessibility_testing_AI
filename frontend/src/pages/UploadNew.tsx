import { useRef, useState, useMemo } from 'react'
import { Upload, FileJson, Sparkles, Loader2, Clock, Download } from 'lucide-react'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Textarea } from '../components/ui/textarea'
import { Progress } from '../components/ui/progress'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
import { useMutation, useQuery } from '@tanstack/react-query'
import { postScan, listScans, listProjects } from '../lib/api'
import { useNavigate } from 'react-router-dom'

export default function UploadNew() {
  const [file, setFile] = useState<File | null>(null)
  const [framework, setFramework] = useState('html')
  const [projectName, setProjectName] = useState('Default Project')
  const [customProjectName, setCustomProjectName] = useState('')
  const [jsonText, setJsonText] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  const { data: scans } = useQuery({ queryKey: ['scans'], queryFn: () => listScans() })
  const { data: projects } = useQuery({ queryKey: ['projects'], queryFn: listProjects })

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
  })

  const onFile = (f: File) => {
    setFile(f)
    setJsonText('')
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="mb-2">Upload & Analyze</h1>
        <p className="text-muted-foreground">Upload your accessibility scan results for intelligent analysis</p>
      </div>

      {/* Pending Scans Section */}
      {groupedPendingScans.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-amber-600 dark:text-amber-500" />
              <h2 className="text-xl font-semibold">Pending Analysis</h2>
            </div>
            <Badge variant="secondary" className="bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200">
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
                <Card key={`group-${groupIndex}`} className="border-2 border-amber-500/50 hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <FileJson className="h-5 w-5 text-amber-600 dark:text-amber-500" />
                      <Badge className="text-xs bg-amber-500">Test Cycle</Badge>
                    </div>
                    <CardTitle className="text-lg">
                      Test Cycle {groupedPendingScans.length - groupIndex}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-1.5 text-xs">
                      <Clock className="h-3 w-3" />
                      {testDate}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="space-y-2">
                      {group.map((scan: any) => (
                        <Button
                          key={scan.id}
                          size="sm"
                          variant="outline"
                          className="w-full justify-between hover:bg-amber-100 dark:hover:bg-amber-500/20 dark:hover:text-amber-100 dark:hover:border-amber-500/40"
                          onClick={() => navigate(`/scan/${scan.id}`)}
                        >
                          <span className="text-xs truncate">{scan.url}</span>
                          <span className="text-xs ml-2">Analyze →</span>
                        </Button>
                      ))}
                    </div>
                    
                    <div className="pt-1">
                      <p className="text-xs text-center text-muted-foreground">
                        {group.length} report{group.length !== 1 ? 's' : ''} in this cycle
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}

      <div>
        <Card className="border-2">
          <CardHeader>
            <CardTitle>Upload Scan File</CardTitle>
            <CardDescription>Supports JSON format from axe-core or Pa11y</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
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

            <div className="space-y-2">
              <label htmlFor="framework-upload-select" className="text-sm">Framework</label>
              <Select value={framework} onValueChange={setFramework}>
                <SelectTrigger id="framework-upload-select"><SelectValue placeholder="html" /></SelectTrigger>
                <SelectContent>
                  {['html','react','vue','angular','svelte'].map(v => <SelectItem key={v} value={v}>{v}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label htmlFor="project-select" className="text-sm font-medium">Project</label>
              <div className="space-y-2">
                <Select value={projectName} onValueChange={setProjectName}>
                  <SelectTrigger id="project-select">
                    <SelectValue placeholder="Select project" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects?.map((project) => (
                      <SelectItem key={project} value={project}>
                        {project}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">or create new:</span>
                  <Input
                    id="custom-project-input"
                    type="text"
                    placeholder="Enter new project name"
                    value={customProjectName}
                    onChange={(e) => setCustomProjectName(e.target.value)}
                    className="flex-1"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="json-text-input" className="text-sm">Or paste JSON</label>
              <Textarea 
                id="json-text-input"
                className="font-mono text-xs h-32" 
                value={jsonText} 
                onChange={(e) => setJsonText(e.target.value)} 
                placeholder={`{ "violations": [...] }`}
              />
            </div>

            <Button className="w-full bg-primary hover:bg-primary/90" size="lg" disabled={analyze.isPending} onClick={() => analyze.mutate()}>
              {analyze.isPending ? (<><Loader2 className="mr-2 h-4 w-4 animate-spin" />Analyzing...</>) : (<><Sparkles className="mr-2 h-4 w-4" />Analyze with AI</>)}
            </Button>
          </CardContent>
        </Card>
      </div>

      {analyze.isPending && (
        <div>
          <Card className="border-2">
            <CardHeader><CardTitle>Analysis Progress</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <Progress value={60} className="h-2" />
            </CardContent>
          </Card>
        </div>
      )}

      {analyze.data && (
        <div>
          <Card className="border-2"><CardHeader><CardTitle>Summary</CardTitle></CardHeader><CardContent><pre className="text-xs overflow-auto max-h-80">{JSON.stringify(analyze.data.summary, null, 2)}</pre></CardContent></Card>
        </div>
      )}
      {analyze.data?.scan_id !== undefined && (
        <div className="flex gap-3">
          <Button asChild>
            <a href={`/scan/${analyze.data.scan_id}`}>Open Summary</a>
          </Button>
          <Button variant="outline" asChild>
            <a href={`/scan/${analyze.data.scan_id}/issues`}>Open Issues</a>
          </Button>
        </div>
      )}
    </div>
  )
}
