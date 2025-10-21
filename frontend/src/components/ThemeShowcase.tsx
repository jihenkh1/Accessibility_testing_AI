import { Card, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { themes, applyTheme, getStoredTheme } from '../utils/themes'
import { Palette, Eye, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'

type Props = {
  onThemeSelect?: (themeName: string) => void
}

export function ThemeShowcase({ onThemeSelect }: Props) {
  const stored = getStoredTheme()
  const [current, setCurrent] = useState(stored.themeName)

  useEffect(() => {
    applyTheme(current, stored.isDark)
  }, [])

  const choose = (name: string) => {
    setCurrent(name)
    applyTheme(name, stored.isDark)
    onThemeSelect?.(name)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Palette className="h-5 w-5 text-primary" />
        <h3>Available Themes</h3>
        <Badge variant="outline" className="text-xs">WCAG AA</Badge>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {themes.map((theme) => (
          <div key={theme.name}>
            <Card
              role="button"
              tabIndex={0}
              aria-pressed={current === theme.name}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') choose(theme.name) }}
              className={`cursor-pointer border-2 transition-all hover:scale-[1.02] hover:shadow-lg ${current === theme.name ? 'border-primary ring-2 ring-primary/20' : 'border-border'}`}
              onClick={() => choose(theme.name)}
            >
              <CardContent className="p-3 space-y-2">
                <div className="flex items-start justify-between">
                  <p className={`text-sm ${current === theme.name ? 'text-primary' : ''}`}>{theme.name}</p>
                  {theme.category === 'high-contrast' && (
                    <Badge variant="outline" className="text-xs h-5 px-1"><Zap className="h-3 w-3" /></Badge>
                  )}
                </div>
                <div className="flex gap-1.5">
                  <div
                    className="w-6 h-6 rounded border border-border"
                    style={{ backgroundColor: theme.colors.primary }}
                    title="Primary"
                  />
                  <div
                    className="w-6 h-6 rounded border border-border"
                    style={{ backgroundColor: theme.colors.accent }}
                    title="Accent"
                  />
                  <div
                    className="w-6 h-6 rounded border border-border"
                    style={{ backgroundColor: theme.colors.accentSecondary }}
                    title="Secondary"
                  />
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">{theme.description}</p>
              </CardContent>
            </Card>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Eye className="h-3 w-3" />
        <p>All themes are designed with accessibility in mind and tested for WCAG compliance.</p>
      </div>
    </div>
  )
}
