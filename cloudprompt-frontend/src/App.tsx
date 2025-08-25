import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState } from "react"
import { Header } from "@/components/header"
import { PromptInput } from "@/components/prompt-form"
import { ResultsCanvas } from "@/components/results-canvas"
import { api } from "@/services/api"
import { toast } from "sonner"
import { KeycloakProvider } from "./auth/KeycloakProvider"
import { useKeycloak } from './auth/KeycloakContext'
import LoginPage from "./components/LoginPage"
import ProtectedRoute from "./components/ProtectedRoute"

function MainApp() {
  const [results, setResults] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  
  // Get token from Keycloak context
  const { token } = useKeycloak()

  const handlePromptSubmit = async (prompt: string, provider: string) => {
    setIsLoading(true)
    setResults(null)
    setError(null)

    try {
      console.log('Submitting prompt:', prompt, 'Provider:', provider)

      const response = await api.executeCommand(prompt, provider, token)

      // Handle plain text responses
      if (response.is_plain_text && response.response?.message) {
        setResults(response.response.message)
      } else {
        // Display JSON response
        setResults(JSON.stringify(response, null, 2))
      }
      
      toast.success('Command executed successfully!')

    } catch (err: any) {
      console.error('Command execution failed:', err)
      
      let errorMessage = 'Unknown error occurred'
      
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail.error || err.response.data.detail.message || errorMessage
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      toast.error('Command failed', {
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
          <PromptInput onSubmit={handlePromptSubmit} />
          
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Command Error</h3>
                  <p className="mt-1 text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}
          
          <ResultsCanvas results={results} isLoading={isLoading} />
        </div>
      </main>
    </div>
  )
}

function App() {
  return (
    <KeycloakProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <MainApp />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </Router>
    </KeycloakProvider>
  )
}

export default App