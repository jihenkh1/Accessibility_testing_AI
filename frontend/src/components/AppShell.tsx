import { ReactNode, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { AppSidebar } from './AppSidebar'
import { TopBar } from './TopBar'
import { KeyboardShortcutsProvider } from './KeyboardShortcuts'
import { applyTheme, getStoredTheme } from '../utils/themes'

type Props = { children: ReactNode }

const routeMap: Record<string, string> = {
  home: '/home',
  upload: '/upload',
  scan: '/scan',
  dashboard: '/dashboard',
  runs: '/runs',
  settings: '/settings',
  pipeline: '/pipeline',
}

function pageFromPath(pathname: string): string {
  if (pathname.startsWith('/upload')) return 'upload'
  if (pathname.startsWith('/scan/')) return 'runs'
  if (pathname.startsWith('/scan')) return 'scan'
  if (pathname.startsWith('/dashboard')) return 'dashboard'
  if (pathname.startsWith('/runs')) return 'runs'
  if (pathname.startsWith('/pipeline')) return 'pipeline'
  if (pathname.startsWith('/settings')) return 'settings'
  if (pathname.startsWith('/home')) return 'home'
  return 'home'
}

export function AppShell({ children }: Props) {
  const location = useLocation()
  const navigate = useNavigate()
  const current = useMemo(() => pageFromPath(location.pathname), [location.pathname])
  const stored = getStoredTheme()
  const [dark, setDark] = useState(stored.isDark)
  const [themeName, setThemeName] = useState(stored.themeName)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  useEffect(() => {
    applyTheme(themeName, dark)
  }, [themeName, dark])

  // Sync theme with changes from other pages (e.g., Settings) and other tabs
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === 'accesstest-theme' && e.newValue) {
        setThemeName(e.newValue)
      }
      if (e.key === 'accesstest-dark-mode' && e.newValue !== null) {
        setDark(e.newValue === 'true')
      }
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  return (
    <KeyboardShortcutsProvider
      onNavigate={(page) => navigate(routeMap[page] || '/home')}
      onThemeToggle={() => setDark(d => !d)}
      onToggleSidebar={() => {
        window.dispatchEvent(new CustomEvent('toggle-sidebar'))
      }}
      onNewScan={() => navigate('/scan')}
    >
      <div className="min-h-screen bg-background text-foreground flex">
        <AppSidebar
          currentPage={current}
          onPageChange={(page) => navigate(routeMap[page] || '/home')}
          collapsed={sidebarCollapsed}
          onCollapsedChange={setSidebarCollapsed}
        />
        <div className="flex-1 flex flex-col">
          <TopBar 
            projectName="Accessibility Assistant" 
            theme={dark ? 'dark' : 'light'} 
            onThemeToggle={() => setDark(d => !d)}
          />
          <main className="p-6 flex-1">{children}</main>
        </div>
      </div>
    </KeyboardShortcutsProvider>
  )
}
