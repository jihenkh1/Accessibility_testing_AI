import { Upload, ShieldCheck, Sparkles, Activity, MoreVertical } from 'lucide-react'
import { Button } from './ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'
import { defaultTheme, getThemeByName, getStoredTheme } from '../utils/themes'
import { cn } from './ui/utils'

type EmptyHeroProps = {
  selectedProject: string
  totalScans: number
  lastRunRelative: string | null
  projects?: string[]
  setSelectedProject: (value: string) => void
  setDeleteProjectDialogOpen: (open: boolean) => void
  navigate: (path: string) => void
}

export function EmptyHero({
  selectedProject,
  totalScans,
  lastRunRelative,
  projects,
  setSelectedProject,
  setDeleteProjectDialogOpen,
  navigate,
}: EmptyHeroProps) {
  const stored = getStoredTheme()
  const theme = getThemeByName(stored.themeName) ?? defaultTheme
  const heroGradient = `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.accentSecondary})`

  const features = [
    {
      icon: <ShieldCheck className="h-4 w-4" />,
      title: 'Comprehensive Analysis',
      desc: 'WCAG, axe-core, Pa11y insights in one place.',
    },
    {
      icon: <Sparkles className="h-4 w-4" />,
      title: 'AI Guidance',
      desc: 'Actionable fix suggestions with effort estimates.',
    },
    {
      icon: <Activity className="h-4 w-4" />,
      title: 'Continuous Tracking',
      desc: 'Monitor regressions and track accessibility health.',
    },
  ]

  return (
    <div className="relative w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="relative space-y-8">
        {/* Header row (project + selector + actions) */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {selectedProject}
            </h1>
            <p className="text-sm text-muted-foreground">
              {totalScans} test runs ·{' '}
              {lastRunRelative
                ? `Last analyzed ${lastRunRelative}`
                : 'Awaiting first scan'}
            </p>
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
              <DropdownMenuContent
                align="end"
                className="w-48 rounded-xl border border-border bg-popover shadow-lg"
              >
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
                    Delete Project
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Hero card */}
        <div className="rounded-3xl bg-card shadow-lg p-10 space-y-4 text-center">
          <div
            className="mx-auto w-14 h-14 flex items-center justify-center rounded-2xl text-white shadow-md"
            style={{ backgroundImage: heroGradient }}
          >
            <Upload className="h-5 w-5" />
          </div>
          <h2 className="text-xl font-semibold">Start Your Accessibility Journey</h2>
          <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
            Upload your first accessibility scan to populate your dashboard.
            Supports WCAG, axe, and Pa11y JSON reports.
          </p>
          <div className="space-y-2">
            <Button
              className={cn(
                'mt-4 inline-flex items-center gap-2 px-6 py-2 text-sm font-medium text-white shadow-md focus-visible:ring-[color:var(--accent)] focus-visible:ring-offset-2',
              )}
              style={{ backgroundImage: heroGradient }}
              onClick={() => navigate('/upload')}
            >
              <Upload className="h-4 w-4" />
              Upload Your First Scan
            </Button>
            <p className="text-xs text-muted-foreground">
              Supports WCAG, axe, Pa11y JSON imports.
            </p>
          </div>
        </div>

        {/* Feature list */}
        <div className="space-y-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="flex items-start gap-3 rounded-2xl bg-card shadow-sm p-4"
            >
              <div
                className="flex h-9 w-9 items-center justify-center rounded-xl text-white shadow-sm"
                style={{ backgroundImage: heroGradient }}
              >
                {feature.icon}
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">{feature.title}</p>
                <p className="text-xs text-muted-foreground">{feature.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
