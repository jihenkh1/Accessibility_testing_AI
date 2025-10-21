import { useRef, useState } from 'react'
import { Upload, FileJson, Sparkles, Loader2 } from 'lucide-react'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Textarea } from '../components/ui/textarea'
import { Progress } from '../components/ui/progress'
import { useMutation } from '@tanstack/react-query'
import { postScan } from '../lib/api'

export default function UploadNew() {
  const [file, setFile] = useState<File | null>(null)
  const [framework, setFramework] = useState('html')
  const [jsonText, setJsonText] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const analyze = useMutation({
    mutationFn: async () => {
      let report: any = null
      if (jsonText.trim()) report = JSON.parse(jsonText)
      else if (file) report = JSON.parse(await file.text())
      else throw new Error('Provide a JSON file or paste JSON')
      return postScan({ report, framework, use_ai: true, max_ai_issues: 50, url: file?.name || 'uploaded_file' })
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
              <label className="text-sm">Framework</label>
              <Select value={framework} onValueChange={setFramework}>
                <SelectTrigger><SelectValue placeholder="html" /></SelectTrigger>
                <SelectContent>
                  {['html','react','vue','angular','svelte'].map(v => <SelectItem key={v} value={v}>{v}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm">Or paste JSON</label>
              <Textarea 
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
