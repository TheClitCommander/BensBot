import { useState } from 'react'
import './App.css'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Layout components
import MainContent from './components/MainContent'
import { AICoPilot } from './components/AICoPilot'

// Create a client
const queryClient = new QueryClient()

function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')

  return (
    <QueryClientProvider client={queryClient}>
      <div className={`app ${theme} text-white`}>
        <div className="h-screen overflow-hidden bg-background">
          {/* Main Content */}
          <MainContent />
          
          {/* AI Co-Pilot */}
          <AICoPilot />
        </div>
      </div>
    </QueryClientProvider>
  )
}

export default App 