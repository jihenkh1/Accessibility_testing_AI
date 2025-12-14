import { Upload, LayoutDashboard, History, Settings, GitBranch, ChevronLeft, ChevronRight, ClipboardCheck, FileText } from 'lucide-react'
import { Button } from './ui/button'
import { useEffect } from 'react'

type Props = {
  currentPage: string
  onPageChange: (page: string) => void
  collapsed: boolean
  onCollapsedChange: (collapsed: boolean) => void
}

const sections = [
  {
    label: 'PROJECT',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { id: 'upload', label: 'Upload', icon: Upload },
      { id: 'reports', label: 'Reports', icon: FileText },
      { id: 'manual-testing', label: 'Manual Testing', icon: ClipboardCheck },
    ],
  },
  {
    label: 'AUTOMATION',
    items: [
      { id: 'pipeline', label: 'Pipeline', icon: GitBranch },
      { id: 'runs', label: 'Runs', icon: History },
    ],
  },
  {
    label: 'ADMIN',
    items: [
      { id: 'settings', label: 'Settings', icon: Settings },
    ],
  },
]

export function AppSidebar({ currentPage, onPageChange, collapsed, onCollapsedChange }: Props) {
  useEffect(() => {
    const handleToggle = () => onCollapsedChange(!collapsed)
    window.addEventListener('toggle-sidebar', handleToggle)
    return () => window.removeEventListener('toggle-sidebar', handleToggle)
  }, [collapsed, onCollapsedChange])

  return (
    <div className={`${collapsed ? 'w-16' : 'w-64'} border-r border-sidebar-border bg-sidebar min-h-screen flex flex-col transition-all duration-300 relative`}>
      {/* Collapse Toggle Button */}
      <Button
        variant="ghost"
        size="sm"
        className="absolute -right-3 top-4 h-6 w-6 rounded-full border border-sidebar-border bg-sidebar shadow-md hover:bg-sidebar-accent z-10 p-0"
        onClick={() => onCollapsedChange(!collapsed)}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? (
          <ChevronRight className="h-3 w-3 text-sidebar-foreground" />
        ) : (
          <ChevronLeft className="h-3 w-3 text-sidebar-foreground" />
        )}
      </Button>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-5">
        {sections.map((section) => (
          <div key={section.label} className="space-y-1">
            {!collapsed && (
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground px-2 pb-1">
                {section.label}
              </div>
            )}
            {section.items.map((item) => {
              const Icon = item.icon
              const active = currentPage === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => onPageChange(item.id)}
                  title={collapsed ? item.label : undefined}
                  className={`relative w-full h-10 rounded-md flex items-center ${collapsed ? 'justify-center px-2' : 'justify-start px-3 gap-3'} text-sm font-medium transition-colors ${
                    active
                      ? 'bg-muted text-foreground font-semibold'
                      : 'text-sidebar-foreground hover:bg-muted hover:text-foreground'
                  }`}
                >
                  {active && <span className="absolute left-0 top-0 h-full w-[3px] bg-primary rounded-r" aria-hidden />}
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </button>
              )
            })}
          </div>
        ))}
      </nav>
    </div>
  )
}
