import { useEffect, useState } from 'react'
import { X, Command, Keyboard } from 'lucide-react'
import { Button } from './ui/button'

type Shortcut = {
  keys: string[]
  description: string
  category: string
}

const shortcuts: Shortcut[] = [
  { keys: ['?'], description: 'Open keyboard shortcuts', category: 'General' },
  { keys: ['Esc'], description: 'Close dialog/modal', category: 'General' },
  { keys: ['g', 'h'], description: 'Go to Home', category: 'Navigation' },
  { keys: ['g', 'u'], description: 'Go to Upload', category: 'Navigation' },
  { keys: ['g', 'd'], description: 'Go to Dashboard', category: 'Navigation' },
  { keys: ['g', 'p'], description: 'Go to Pipeline', category: 'Navigation' },
  { keys: ['g', 'r'], description: 'Go to Runs', category: 'Navigation' },
  { keys: ['n'], description: 'Upload new report', category: 'Actions' },
  { keys: ['t'], description: 'Toggle theme', category: 'Actions' },
  { keys: ['b'], description: 'Toggle sidebar', category: 'Actions' },
]

type Props = {
  isOpen: boolean
  onClose: () => void
}

export function KeyboardShortcuts({ isOpen, onClose }: Props) {
  if (!isOpen) return null

  const categories = [...new Set(shortcuts.map(s => s.category))]

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-lg shadow-lg max-w-2xl w-full max-h-[80vh] overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border sticky top-0 bg-card">
          <div className="flex items-center gap-3">
            <Keyboard className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Keyboard Shortcuts</h2>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {categories.map(category => (
            <div key={category}>
              <h3 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
                {category}
              </h3>
              <div className="space-y-2">
                {shortcuts
                  .filter(s => s.category === category)
                  .map((shortcut, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between py-2 px-3 rounded hover:bg-accent/50 transition-colors"
                    >
                      <span className="text-sm text-foreground">{shortcut.description}</span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, keyIdx) => (
                          <span key={keyIdx} className="flex items-center gap-1">
                            <kbd className="px-2 py-1 text-xs font-semibold text-foreground bg-muted border border-border rounded shadow-sm min-w-[24px] text-center">
                              {key === 'Command' ? '⌘' : key}
                            </kbd>
                            {keyIdx < shortcut.keys.length - 1 && (
                              <span className="text-muted-foreground text-xs">then</span>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-muted/30">
          <p className="text-xs text-muted-foreground text-center">
            Press <kbd className="px-1.5 py-0.5 text-xs font-semibold bg-background border border-border rounded">Esc</kbd> or{' '}
            <kbd className="px-1.5 py-0.5 text-xs font-semibold bg-background border border-border rounded">?</kbd> to close
          </p>
        </div>
      </div>
    </div>
  )
}

type KeyboardShortcutsProviderProps = {
  children: React.ReactNode
  onNavigate: (page: string) => void
  onThemeToggle: () => void
  onToggleSidebar: () => void
  onNewScan: () => void
}

export function KeyboardShortcutsProvider({
  children,
  onNavigate,
  onThemeToggle,
  onToggleSidebar,
  onNewScan,
}: KeyboardShortcutsProviderProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [keySequence, setKeySequence] = useState<string[]>([])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      // Toggle shortcuts panel with ?
      if (e.key === '?' && !isOpen) {
        e.preventDefault()
        setIsOpen(true)
        return
      }

      // Close with Esc or ?
      if ((e.key === 'Escape' || e.key === '?') && isOpen) {
        e.preventDefault()
        setIsOpen(false)
        return
      }

      // Handle key sequences
      const newSequence = [...keySequence, e.key.toLowerCase()]
      setKeySequence(newSequence)

      // Clear sequence after 1 second
      setTimeout(() => setKeySequence([]), 1000)

      // Check for matches
      const seq = newSequence.join('')
      
      // Navigation shortcuts
      if (seq === 'gh') { onNavigate('home'); setKeySequence([]) }
      else if (seq === 'gu') { onNavigate('upload'); setKeySequence([]) }
      else if (seq === 'gd') { onNavigate('dashboard'); setKeySequence([]) }
      else if (seq === 'gp') { onNavigate('pipeline'); setKeySequence([]) }
      else if (seq === 'gr') { onNavigate('runs'); setKeySequence([]) }
      
      // Single key shortcuts
      else if (e.key === 'n') { onNewScan(); setKeySequence([]) }
      else if (e.key === 't') { onThemeToggle(); setKeySequence([]) }
      else if (e.key === 'b') { onToggleSidebar(); setKeySequence([]) }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, keySequence, onNavigate, onThemeToggle, onToggleSidebar, onNewScan])

  return (
    <>
      {children}
      <KeyboardShortcuts isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  )
}
