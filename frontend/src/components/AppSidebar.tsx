import { Home, Upload, Scan, LayoutDashboard, History, Settings, GitBranch, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { useEffect } from 'react'

type Props = {
  currentPage: string
  onPageChange: (page: string) => void
  collapsed: boolean
  onCollapsedChange: (collapsed: boolean) => void
}

export function AppSidebar({ currentPage, onPageChange, collapsed, onCollapsedChange }: Props) {
  // Listen for keyboard shortcut toggle
  useEffect(() => {
    const handleToggle = () => onCollapsedChange(!collapsed)
    window.addEventListener('toggle-sidebar', handleToggle)
    return () => window.removeEventListener('toggle-sidebar', handleToggle)
  }, [collapsed, onCollapsedChange])
  const menu = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'upload', label: 'Upload', icon: Upload },
    { id: 'scan', label: 'Scan', icon: Scan },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'pipeline', label: 'Pipeline', icon: GitBranch, badge: 'New' },
    { id: 'runs', label: 'Runs', icon: History },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]

  return (
    <div className={`${collapsed ? 'w-16' : 'w-64'} border-r border-sidebar-border bg-sidebar min-h-screen flex flex-col transition-all duration-300 relative`}>
      <div className="h-16 px-6 border-b border-sidebar-border flex items-center">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center flex-shrink-0">
            <span className="text-primary-foreground text-sm font-semibold">A</span>
          </div>
          {!collapsed && (
            <div>
              <h3 className="text-sidebar-foreground font-semibold">AccessTest</h3>
            </div>
          )}
        </div>
      </div>
      
      {/* Collapse Toggle Button */}
      <Button
        variant="ghost"
        size="sm"
        className="absolute -right-3 top-20 h-6 w-6 rounded-full border border-sidebar-border bg-sidebar shadow-md hover:bg-sidebar-accent z-10 p-0"
        onClick={() => onCollapsedChange(!collapsed)}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? (
          <ChevronRight className="h-3 w-3 text-sidebar-foreground" />
        ) : (
          <ChevronLeft className="h-3 w-3 text-sidebar-foreground" />
        )}
      </Button>
      <nav className="flex-1 p-4 space-y-1">
        {menu.map(item => {
          const Icon = item.icon
          const active = currentPage === item.id
          return (
            <Button
              key={item.id}
              variant={active ? 'secondary' : 'ghost'}
              className={`w-full ${collapsed ? 'justify-center px-2' : 'justify-start'} ${active ? 'bg-sidebar-accent text-sidebar-accent-foreground' : 'text-sidebar-foreground hover:bg-sidebar-accent/50'}`}
              onClick={() => onPageChange(item.id)}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={`h-4 w-4 ${collapsed ? '' : 'mr-3'} flex-shrink-0`} />
              {!collapsed && (
                <>
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge && <Badge variant="secondary" className="ml-auto text-xs">{item.badge}</Badge>}
                </>
              )}
            </Button>
          )
        })}
      </nav>
    </div>
  )
}
