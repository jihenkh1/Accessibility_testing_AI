import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getScan, analyzeExistingScan } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Sparkles, Clock, FileJson, Download, Loader2, CheckCircle } from 'lucide-react'
import { useState } from 'react'

export default function ScanDetail() {
  const { id } = useParams()
  const scanId = Number(id)
  const queryClient = useQueryClient()
  const [framework, setFramework] = useState('html')
  const [useAI, setUseAI] = useState(true)
  
  const { data, isLoading, error } = useQuery({ 
    queryKey: ['scan', scanId], 
    queryFn: () => getScan(scanId), 
    enabled: !Number.isNaN(scanId) 
  })

  const isPending = data && data.total_issues === 0
  const hasRawReport = data?.raw_report_json

  const analyzeMutation = useMutation({
    mutationFn: async () => {
      if (!hasRawReport) throw new Error('No raw report available')
      const report = JSON.parse(data.raw_report_json)
      return analyzeExistingScan(scanId, { 
        report, 
        framework, 
        use_ai: useAI, 
        max_ai_issues: 50, 
        url: data.url || `Scan #${scanId}` 
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scan', scanId] })
      queryClient.invalidateQueries({ queryKey: ['scans'] })
    }
  })

  if (Number.isNaN(scanId)) return <div className="p-4">Invalid scan id</div>
  
  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="mb-2">Scan #{scanId}</h1>
          {data && <p className="text-sm text-muted-foreground">{data.url}</p>}
        </div>
        {isPending && (
          <Badge variant="secondary" className="gap-1.5 bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200">
            <Clock className="h-3.5 w-3.5" />
            Pending Analysis
          </Badge>
        )}
        {!isPending && data && (
          <Badge variant="secondary" className="gap-1.5 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
            <CheckCircle className="h-3.5 w-3.5" />
            Analyzed
          </Badge>
        )}
      </div>
      
      {isLoading && <div>Loading...</div>}
      {error && <div className="text-red-600">Failed to load</div>}
      
      {/* Pending Analysis Card */}
      {isPending && hasRawReport && (
        <Card className="border-2 border-amber-500/50 bg-amber-50 dark:bg-amber-950/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-amber-600" />
              Ready to Analyze
            </CardTitle>
            <CardDescription>
              This report was uploaded but hasn't been analyzed yet. Configure settings and run analysis.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label htmlFor="framework-select" className="text-sm font-medium">Framework</label>
                <Select value={framework} onValueChange={setFramework}>
                  <SelectTrigger id="framework-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="html">HTML</SelectItem>
                    <SelectItem value="react">React</SelectItem>
                    <SelectItem value="vue">Vue</SelectItem>
                    <SelectItem value="angular">Angular</SelectItem>
                    <SelectItem value="svelte">Svelte</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <label htmlFor="ai-analysis-select" className="text-sm font-medium">AI Analysis</label>
                <Select value={useAI ? 'enabled' : 'disabled'} onValueChange={(v) => setUseAI(v === 'enabled')}>
                  <SelectTrigger id="ai-analysis-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="enabled">Enabled (50 issues)</SelectItem>
                    <SelectItem value="disabled">Disabled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <Button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="w-full gap-2"
              size="lg"
            >
              {analyzeMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Analyze Report
                </>
              )}
            </Button>
            
            {analyzeMutation.isError && (
              <p className="text-sm text-red-600">
                Error: {(analyzeMutation.error as Error).message}
              </p>
            )}
            
            {analyzeMutation.isSuccess && (
              <p className="text-sm text-green-600 flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                Analysis complete! Refreshing...
              </p>
            )}
          </CardContent>
        </Card>
      )}
      
      {/* Download Reports */}
      {(data?.pdf_report_path || data?.html_report_path) && (
        <Card className="border-2">
          <CardHeader>
            <CardTitle>Attached Reports</CardTitle>
            <CardDescription>Download the original report files</CardDescription>
          </CardHeader>
          <CardContent className="flex gap-3">
            {data.pdf_report_path && (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => window.open(`/api/scans/${scanId}/pdf-report`, '_blank')}
              >
                <Download className="h-4 w-4" />
                Download PDF
              </Button>
            )}
            {data.html_report_path && (
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => window.open(`/api/scans/${scanId}/html-report`, '_blank')}
              >
                <Download className="h-4 w-4" />
                Download HTML
              </Button>
            )}
          </CardContent>
        </Card>
      )}
      
      {data && !isPending && (
        <Tabs defaultValue="summary" className="space-y-3">
          <TabsList>
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="issues">Issues</TabsTrigger>
          </TabsList>
          <TabsContent value="summary">
            <Card className="border-2">
              <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
              <CardContent>
                <pre className="text-xs overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="issues">
            <Card className="border-2">
              <CardHeader><CardTitle>Issues</CardTitle></CardHeader>
              <CardContent>
                <div className="text-sm">
                  View issues table <Link className="text-primary underline" to={`/scan/${scanId}/issues`}>here</Link> for filters and export.
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
