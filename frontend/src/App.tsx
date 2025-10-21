import { Routes, Route, Navigate } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import Settings from './pages/Settings'
import { AppShell } from './components/AppShell'

// Code-split heavy pages
const Home = lazy(() => import('./pages/HomeNew'))
const UploadScan = lazy(() => import('./pages/UploadNew'))
const ScanNew = lazy(() => import('./pages/ScanNew'))
const Dashboard = lazy(() => import('./pages/DashboardNew'))
const ScanDetail = lazy(() => import('./pages/ScanDetail'))
const RunIssues = lazy(() => import('./pages/RunIssues'))
const Pipeline = lazy(() => import('./pages/Pipeline'))
const Runs = lazy(() => import('./pages/Runs'))

export default function App() {
  return (
    <AppShell>
      <Suspense fallback={<div className="p-6 text-sm text-muted-foreground">Loading...</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<Home />} />
          <Route path="/upload" element={<UploadScan />} />
          <Route path="/scan" element={<ScanNew />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/scan/:id" element={<ScanDetail />} />
          <Route path="/scan/:id/issues" element={<RunIssues />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </AppShell>
  )
}

