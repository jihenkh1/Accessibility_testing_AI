import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../lib/api'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Sparkles, Zap, Microscope, Settings, Globe, CheckCircle, AlertCircle, Clock, Loader2, Pause, StopCircle, ArrowRight, TrendingUp, AlertTriangle } from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { useNavigate } from 'react-router-dom'

type ScanPreset = 'quick' | 'deep' | 'custom'

type ScanResponse = {
  scan_id?: number
  summary: {
    total_issues: number
    critical_issues: number
    high_issues: number
    medium_issues: number
    low_issues: number
    estimated_total_time_minutes: number
  }
  issues: any[]
}

export default function ScanNew() {
  const navigate = useNavigate()
  
  // Form state
  const [url, setUrl] = useState('')
  const [framework, setFramework] = useState('html')
  const [useAI, setUseAI] = useState(true)
  const [maxAI, setMaxAI] = useState(5)
  const [maxPages, setMaxPages] = useState(10)
  const [sameOrigin, setSameOrigin] = useState(true)
  const [preset, setPreset] = useState<ScanPreset>('quick')
  const [scanner, setScanner] = useState<'axe' | 'pa11y'>('axe')  // NEW: Scanner selection
  
  // UI state
  const [urlValid, setUrlValid] = useState<boolean | null>(null)
  const [scanStage, setScanStage] = useState<'form' | 'scanning' | 'complete'>('form')
  const [progress, setProgress] = useState(0)
  const [scannedPages, setScannedPages] = useState<Array<{ url: string; issues: number }>>([])
  const [currentPage, setCurrentPage] = useState('')
  const [startTime, setStartTime] = useState<number>(0)
  const [elapsedTime, setElapsedTime] = useState(0)

  // Validate URL
  useEffect(() => {
    if (!url) {
      setUrlValid(null)
      return
    }
    try {
      new URL(url)
      setUrlValid(true)
    } catch {
      setUrlValid(false)
    }
  }, [url])

  // Timer for elapsed time
  useEffect(() => {
    if (scanStage !== 'scanning') return
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [scanStage, startTime])

  // Apply preset
  const applyPreset = (p: ScanPreset) => {
    setPreset(p)
    if (p === 'quick') {
      setMaxPages(5)
      setMaxAI(3)
      setSameOrigin(true)
    } else if (p === 'deep') {
      setMaxPages(50)
      setMaxAI(10)
      setSameOrigin(false)
    }
  }

  // Estimate calculations
  const estimatedPages = preset === 'quick' ? '3-5' : preset === 'deep' ? '20-50' : `~${maxPages}`
  const estimatedTime = preset === 'quick' ? '1-2' : preset === 'deep' ? '5-10' : `~${Math.ceil(maxPages / 3)}`
  const estimatedAICalls = preset === 'quick' ? '2-3' : preset === 'deep' ? '5-10' : `~${maxAI}`

  const scan = useMutation({
    mutationFn: async () => {
      if (!url) throw new Error('Enter a URL')
      setScanStage('scanning')
      setStartTime(Date.now())
      setProgress(0)
      setScannedPages([])
      
      // Simulate real-time progress (since backend doesn't support streaming yet)
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + Math.random() * 15, 95))
      }, 1000)

      try {
        const res = await api.post('/scans/scan_url', {
          url,
          framework,
          use_ai: useAI,
          max_ai_issues: maxAI,
          max_pages: maxPages,
          same_origin_only: sameOrigin,
          scanner,  // NEW: Include scanner type
        }, {
          timeout: 600_000, // 10 minutes for scan endpoint specifically
        })
        clearInterval(progressInterval)
        setProgress(100)
        setScanStage('complete')
        return res.data as ScanResponse
      } catch (error) {
        clearInterval(progressInterval)
        setScanStage('form')
        throw error
      }
    },
  })

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  const estimatedRemaining = () => {
    if (progress === 0) return estimatedTime
    const elapsed = elapsedTime
    const estimated = (elapsed / progress) * 100
    const remaining = Math.max(0, Math.ceil(estimated - elapsed))
    return formatTime(remaining)
  }

  // ============ PHASE 1: PRE-SCAN FORM ============
  if (scanStage === 'form') {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">🔍 New Accessibility Scan</h1>
          <p className="text-muted-foreground">Crawl your website and analyze accessibility issues with AI-powered insights</p>
        </div>

        {/* Preset Buttons */}
        <Card className="border-2 bg-gradient-to-br from-primary/5 to-accent/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              Quick Start (Recommended)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Button
                variant={preset === 'quick' ? 'default' : 'outline'}
                className="h-auto flex-col items-start p-4 text-left"
                onClick={() => applyPreset('quick')}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4" />
                  <span className="font-semibold">Quick Scan</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  1-5 pages • 2 min • Perfect for quick checks
                </div>
              </Button>

              <Button
                variant={preset === 'deep' ? 'default' : 'outline'}
                className="h-auto flex-col items-start p-4 text-left"
                onClick={() => applyPreset('deep')}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Microscope className="w-4 h-4" />
                  <span className="font-semibold">Deep Scan</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  20-50 pages • 10 min • Comprehensive analysis
                </div>
              </Button>

              <Button
                variant={preset === 'custom' ? 'default' : 'outline'}
                className="h-auto flex-col items-start p-4 text-left"
                onClick={() => setPreset('custom')}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Settings className="w-4 h-4" />
                  <span className="font-semibold">Custom</span>
                </div>
                <div className="text-xs text-muted-foreground">
                  Configure all settings manually
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* URL Input */}
        <Card className="border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="w-5 h-5" />
              Website URL
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="relative">
              <input
                className="w-full border bg-input-background border-input rounded-md px-4 py-3 text-sm pr-10"
                type="url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
              {urlValid !== null && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  {urlValid ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-destructive" />
                  )}
                </div>
              )}
            </div>
            {urlValid === true && (
              <div className="text-sm text-green-600 dark:text-green-400 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Valid URL • Ready to scan
              </div>
            )}
            {urlValid === false && (
              <div className="text-sm text-destructive flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Please enter a valid URL (e.g., https://example.com)
              </div>
            )}
          </CardContent>
        </Card>

        {/* Scan Settings */}
        <Card className="border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Scan Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Scanner Engine</label>
                <Select value={scanner} onValueChange={(v) => setScanner(v as 'axe' | 'pa11y')}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="axe">
                      Axe-core (Built-in) 🔧
                    </SelectItem>
                    <SelectItem value="pa11y">
                      Pa11y (Local, No API Limits) 🚀
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {scanner === 'axe' ? 'Playwright + axe-core (current)' : 'Pa11y via Node.js (install: npm i -g pa11y)'}
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Framework</label>
                <Select value={framework} onValueChange={setFramework}>
                  <SelectTrigger>
                    <SelectValue placeholder="html" />
                  </SelectTrigger>
                  <SelectContent>
                    {['html', 'react', 'vue', 'angular', 'svelte'].map(v => (
                      <SelectItem key={v} value={v}>
                        {v.charAt(0).toUpperCase() + v.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label htmlFor="maxpages" className="text-sm font-medium">
                  Max Pages
                </label>
                <input
                  id="maxpages"
                  className="w-full border bg-input-background border-input rounded-md px-3 py-2 text-sm"
                  type="number"
                  min={1}
                  max={100}
                  value={maxPages}
                  onChange={(e) => setMaxPages(parseInt(e.target.value || '1', 10))}
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="maxai" className="text-sm font-medium">
                  Max AI Calls
                </label>
                <input
                  id="maxai"
                  className="w-full border bg-input-background border-input rounded-md px-3 py-2 text-sm"
                  type="number"
                  min={0}
                  max={50}
                  value={maxAI}
                  onChange={(e) => setMaxAI(parseInt(e.target.value || '0', 10))}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Options</label>
                <div className="flex flex-col gap-2">
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useAI}
                      onChange={(e) => setUseAI(e.target.checked)}
                      className="rounded"
                    />
                    Use AI for enhanced analysis
                  </label>
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sameOrigin}
                      onChange={(e) => setSameOrigin(e.target.checked)}
                      className="rounded"
                    />
                    Same origin only
                  </label>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t">
              <p className="text-xs text-muted-foreground">
                💡 Tip: Start with Quick Scan to get fast results, then run Deep Scan for comprehensive analysis
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Scan Preview */}
        <Card className="border-2 bg-muted/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              📊 Scan Preview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground mb-1">Estimated Pages</div>
                <div className="font-semibold">{estimatedPages}</div>
              </div>
              <div>
                <div className="text-muted-foreground mb-1">Estimated Time</div>
                <div className="font-semibold">{estimatedTime} min</div>
              </div>
              <div>
                <div className="text-muted-foreground mb-1">AI Calls</div>
                <div className="font-semibold">{estimatedAICalls}</div>
              </div>
              <div>
                <div className="text-muted-foreground mb-1">Framework</div>
                <Badge variant="outline">{framework.toUpperCase()}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <Button
            size="lg"
            className="bg-primary"
            onClick={() => scan.mutate()}
            disabled={!url || !urlValid || scan.isPending}
          >
            {scan.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Starting Scan...
              </>
            ) : (
              <>
                Start Scan
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
          <Button variant="outline" size="lg" onClick={() => navigate('/dashboard')}>
            Cancel
          </Button>
        </div>

        {scan.isError && (
          <Card className="border-2 border-destructive">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="w-5 h-5" />
                <span className="font-medium">Scan failed: {(scan.error as Error)?.message}</span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    )
  }

  // ============ PHASE 2: SCANNING IN PROGRESS ============
  if (scanStage === 'scanning') {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">🔍 Scanning {new URL(url).hostname}...</h1>
          <p className="text-muted-foreground">Analyzing accessibility issues across your website</p>
        </div>

        {/* Progress Bar */}
        <Card className="border-2">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Progress</span>
                <span className="text-muted-foreground">{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500"
                  ref={(el) => {
                    if (el) el.style.width = `${progress}%`
                  }}
                />
              </div>
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span className="flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Elapsed: {formatTime(elapsedTime)}
                </span>
                <span>Remaining: ~{estimatedRemaining()}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Current Status */}
        <Card className="border-2 bg-blue-50 dark:bg-blue-950/20">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-3">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
              <span className="font-semibold">Currently Scanning</span>
            </div>
            <div className="text-sm text-muted-foreground">
              Crawling pages and running accessibility tests...
            </div>
          </CardContent>
        </Card>

        {/* Control Buttons */}
        <div className="flex items-center gap-3">
          <Button variant="outline" disabled>
            <Pause className="w-4 h-4 mr-2" />
            Pause (Coming Soon)
          </Button>
          <Button variant="destructive" onClick={() => setScanStage('form')}>
            <StopCircle className="w-4 h-4 mr-2" />
            Stop Scan
          </Button>
        </div>

        {/* Info Card */}
        <Card className="border-2">
          <CardContent className="p-6">
            <h4 className="font-medium mb-3">What we're checking:</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm text-muted-foreground">
              <div>✓ Images & Alt Text</div>
              <div>✓ Color Contrast</div>
              <div>✓ Keyboard Navigation</div>
              <div>✓ Form Labels</div>
              <div>✓ ARIA Attributes</div>
              <div>✓ Semantic HTML</div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // ============ PHASE 3: SCAN COMPLETE ============
  if (scanStage === 'complete' && scan.data) {
    const summary = scan.data.summary
    const score = Math.max(0, Math.min(100, 100 - (summary.critical_issues * 5 + summary.high_issues * 2)))

    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">✅ Scan Complete!</h1>
          <p className="text-muted-foreground">Your accessibility scan has finished</p>
        </div>

        {/* Score Card */}
        <Card className="border-2 bg-gradient-to-br from-green-50 to-blue-50 dark:from-green-950/20 dark:to-blue-950/20">
          <CardContent className="p-8">
            <div className="text-center space-y-4">
              <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-gradient-to-br from-green-500 to-blue-500 text-white">
                <div className="text-4xl font-bold">{score}</div>
              </div>
              <div>
                <h3 className="text-2xl font-bold mb-1">Accessibility Score: {score}/100</h3>
                <p className="text-muted-foreground">
                  {summary.total_issues} issues found • {Math.floor(summary.estimated_total_time_minutes / 60)}h {summary.estimated_total_time_minutes % 60}m estimated fix time
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Issue Breakdown */}
        <Card className="border-2">
          <CardHeader>
            <CardTitle>Issue Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 rounded-lg bg-red-50 dark:bg-red-950/20">
                <div className="text-3xl font-bold text-red-500">{summary.critical_issues}</div>
                <div className="text-sm text-muted-foreground mt-1">🔴 Critical</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-orange-50 dark:bg-orange-950/20">
                <div className="text-3xl font-bold text-orange-500">{summary.high_issues}</div>
                <div className="text-sm text-muted-foreground mt-1">🟠 High</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-yellow-50 dark:bg-yellow-950/20">
                <div className="text-3xl font-bold text-yellow-500">{summary.medium_issues}</div>
                <div className="text-sm text-muted-foreground mt-1">🟡 Medium</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20">
                <div className="text-3xl font-bold text-blue-500">{summary.low_issues}</div>
                <div className="text-sm text-muted-foreground mt-1">🟢 Low</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Priority Actions */}
        {summary.critical_issues > 0 && (
          <Card className="border-2 border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/20">
            <CardContent className="p-6">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h4 className="font-semibold text-red-900 dark:text-red-100 mb-1">
                    {summary.critical_issues} Critical Issues Found
                  </h4>
                  <p className="text-sm text-red-700 dark:text-red-300">
                    These issues severely impact accessibility and should be fixed immediately. They may prevent users with disabilities from accessing your content.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Stats */}
        <Card className="border-2">
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              <div>
                <div className="text-3xl font-bold mb-1">
                  {formatTime(elapsedTime)}
                </div>
                <div className="text-sm text-muted-foreground">Scan Duration</div>
              </div>
              <div>
                <div className="text-3xl font-bold mb-1">
                  {summary.total_issues}
                </div>
                <div className="text-sm text-muted-foreground">Total Issues</div>
              </div>
              <div>
                <div className="flex items-center justify-center gap-2 text-3xl font-bold mb-1">
                  <TrendingUp className="w-8 h-8" />
                  {score >= 70 ? 'Good' : score >= 50 ? 'Fair' : 'Needs Work'}
                </div>
                <div className="text-sm text-muted-foreground">Overall Rating</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <Button
            size="lg"
            className="bg-primary"
            onClick={() => {
              if (scan.data?.scan_id) {
                navigate(`/scan/${scan.data.scan_id}/issues`)
              }
            }}
          >
            View All Issues
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
          {scan.data?.scan_id && (
            <Button variant="outline" size="lg" onClick={() => navigate(`/scan/${scan.data.scan_id}`)}>
              View Summary
            </Button>
          )}
          <Button
            variant="outline"
            size="lg"
            onClick={() => {
              setScanStage('form')
              scan.reset()
            }}
          >
            Scan Another Site
          </Button>
        </div>
      </div>
    )
  }

  return null
}
