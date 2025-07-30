import { useState, useEffect } from "react"
import { Header } from "@/components/header"
import { PromptInput } from "@/components/prompt-form"
import { ResultsCanvas } from "@/components/results-canvas"
import { api } from "@/services/api"
import { config } from "@/config/env"
import { toast } from "sonner"

function App() {
  const [results, setResults] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isApiHealthy, setIsApiHealthy] = useState<boolean | null>(null)

  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        await api.healthCheck()
        setIsApiHealthy(true)
        console.log('API is healthy')
      } catch (error) {
        setIsApiHealthy(false)
        console.error('API health check failed:', error)
        toast.error('Backend API is not available', {
          description: `Please ensure the backend is reachable at ${config.apiBaseUrl}`,
        })
      }
    }
    
    checkApiHealth()
    const interval = setInterval(checkApiHealth, 30000) 
    return () => clearInterval(interval)
    
  }, [])

  const handlePromptSubmit = async (prompt: string) => {
    setIsLoading(true)
    setResults(null)
    
    try {
      console.log('Submitting prompt:', prompt)
      
      const response = await api.executeCommand(prompt)
      
      // Display the raw JSON response
      setResults(JSON.stringify(response, null, 2))
      
      toast.success('Command executed successfully!')
      
    } catch (error: any) {
      console.error('Command execution failed:', error)
      
      const errorMessage = error.response?.data?.message || error.message || 'Unknown error occurred'
      setResults(`Error: ${errorMessage}`)
      
      toast.error('Command execution failed', {
        description: errorMessage,
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-[#E3F2FD] via-white to-[#F3E5F5]">
      <Header />

      <main className="flex-1 container mx-auto p-4 sm:p-6 flex flex-col items-center space-y-4 sm:space-y-6">
        <div className="w-full max-w-4xl space-y-4 sm:space-y-6">
          <PromptInput onSubmit={handlePromptSubmit} apiStatus={isApiHealthy} />
          <ResultsCanvas results={results} isLoading={isLoading} />
        </div>
      </main>
    </div>
  )
}

export default App