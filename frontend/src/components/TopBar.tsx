import { Moon, Sun, User, ChevronDown } from 'lucide-react'
import { Button } from './ui/button'

type Props = {
  projectName: string
  theme: 'light' | 'dark'
  onThemeToggle: () => void
}

export function TopBar({ projectName, theme, onThemeToggle }: Props) {
  return (
    <div className="h-16 border-b border-border bg-card px-6 flex items-center justify-between">
      <div>
        <h2 className="text-foreground">{projectName}</h2>
        <p className="text-xs text-muted-foreground">Accessibility Testing Platform</p>
      </div>
      <div className="flex items-center gap-3">
        <Button variant="outline" onClick={onThemeToggle} className="rounded-full" aria-label="Toggle theme">
          {theme === 'light' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>
        
      </div>
    </div>
  )
}

