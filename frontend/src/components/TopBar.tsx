import { Moon, Sun, Upload, ClipboardCheck } from 'lucide-react'
import { Button } from './ui/button'
import { Link } from 'react-router-dom'

type Props = {
  projectName: string
  theme: 'light' | 'dark'
  onThemeToggle: () => void
}

export function TopBar({ projectName, theme, onThemeToggle }: Props) {
  return (
    <div className="grid grid-cols-3 items-center h-[var(--app-header-height)] px-6 lg:px-8">
      <div className="flex items-center gap-2">
        <span className="text-xs uppercase tracking-wide text-muted-foreground">Project</span>
        <span className="text-muted-foreground">›</span>
        <span className="text-sm font-semibold text-foreground truncate">{projectName}</span>
      </div>

      {/* Center: Title */}
      <div className="flex justify-center">
        <span className="text-sm font-semibold text-foreground text-center">
          Accessibility Testing Platform
        </span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center justify-end gap-2">
        <Button variant="default" size="sm" asChild>
          <Link to="/manual-testing">
            <ClipboardCheck className="mr-2 h-4 w-4" />
            Start Manual Testing
          </Link>
        </Button>
        <Button variant="outline" size="sm" asChild>
          <Link to="/upload">
            <Upload className="mr-2 h-4 w-4" />
            Upload New Scan
          </Link>
        </Button>
        <Button variant="ghost" size="sm" onClick={onThemeToggle} className="rounded-full" aria-label="Toggle theme">
          {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>
      </div>
    </div>
  )
}
