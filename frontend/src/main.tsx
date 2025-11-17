import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/queryClient'
import App from './App'
import './index.css'
import { applyTheme, getStoredTheme } from './utils/themes'
import { Toaster } from 'sonner'

// Apply theme immediately before React renders to prevent flash
const stored = getStoredTheme()
applyTheme(stored.themeName, stored.isDark)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster position="top-right" expand={true} richColors />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)

