import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import './quotation-print-fix.css'
import './crm-filter-standard.css'
import './crm-compact-layout.css'
import './dashboard-polish.css'
import './dashboard-reference.css'
import './dashboard-final.css'
import './dashboard-kpi-fix.css'
import './dashboard-auto-repair.css'
import './dashboard-cleanup.css'
import './pipeline-premium.css'
import './pipeline-analytics.css'
import './pipeline-analytics-enhancer'
import './pipeline-compact-override.css'
import './crm-customer-pipeline-table-fix.css'
import './settings-matrix-polish.css'
import './dashboard-welcome-dynamic.css'
import './dashboard-welcome-sync'
import './dashboard-business-performance'
import './customer-source-other'
import App from './App.tsx'
import { queryClient } from './lib/queryClient'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
