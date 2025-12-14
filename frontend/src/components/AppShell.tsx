import { ReactNode, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { AppSidebar } from './AppSidebar'
import { TopBar } from './TopBar'
import { KeyboardShortcutsProvider } from './KeyboardShortcuts'
import { applyTheme, getStoredTheme } from '../utils/themes'

type Props = { children: ReactNode }

const routeMap: Record<string, string> = {
  upload: '/upload',
  dashboard: '/',
  reports: '/reports',
  runs: '/runs',
  settings: '/settings',
  pipeline: '/pipeline',
  'manual-testing': '/manual-testing',
}

function pageFromPath(pathname: string): string {
  if (pathname === '/') return 'dashboard'
  if (pathname.startsWith('/upload')) return 'upload'
  if (pathname.startsWith('/scan/')) return 'runs'
  if (pathname.startsWith('/dashboard')) return 'dashboard'
  if (pathname.startsWith('/reports')) return 'reports'
  if (pathname.startsWith('/runs')) return 'runs'
  if (pathname.startsWith('/pipeline')) return 'pipeline'
  if (pathname.startsWith('/settings')) return 'settings'
  if (pathname.startsWith('/manual-testing')) return 'manual-testing'
  return 'dashboard'
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

  const handleThemeToggle = () => {
    const saved = getStoredTheme()
    const nextIsDark = !saved.isDark
    setThemeName(saved.themeName)
    setDark(nextIsDark)
    applyTheme(saved.themeName, nextIsDark)
  }

  return (
    <KeyboardShortcutsProvider
      onNavigate={(page) => navigate(routeMap[page] || '/')}
      onThemeToggle={handleThemeToggle}
      onToggleSidebar={() => {
        window.dispatchEvent(new CustomEvent('toggle-sidebar'))
      }}
      onNewScan={() => navigate('/upload')}
    >
      <div className="min-h-screen bg-background text-foreground flex flex-col">
        <div className="sticky top-0 z-50 border-b border-sidebar-border bg-background/95 backdrop-blur">
          <div className="flex items-center">
            <div className={`${sidebarCollapsed ? 'w-16' : 'w-64'} h-[var(--app-header-height)] px-6 lg:px-8 flex items-center gap-3`}>
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-3 hover:opacity-90 transition-opacity cursor-pointer"
                title="AccessTest"
              >
                <div className="w-10 h-10 rounded-lg bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">
                  A
                </div>
                {!sidebarCollapsed && (
                  <div className="leading-tight">
                    <div className="text-sidebar-foreground font-semibold">AccessTest</div>
                    <div className="text-xs text-muted-foreground">Accessibility Assistant</div>
                  </div>
                )}
              </button>
            </div>
            <div className="flex-1">
              <TopBar 
                projectName="Accessibility Assistant" 
                theme={dark ? 'dark' : 'light'} 
                onThemeToggle={handleThemeToggle}
              />
            </div>
          </div>
        </div>
        <div className="flex flex-1">
          <AppSidebar
            currentPage={current}
            onPageChange={(page) => navigate(routeMap[page] || '/')}
            collapsed={sidebarCollapsed}
            onCollapsedChange={setSidebarCollapsed}
          />
          <main className="p-6 flex-1">{children}</main>
        </div>
      </div>
    </KeyboardShortcutsProvider>
  )
}
