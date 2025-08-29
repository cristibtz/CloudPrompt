import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState } from "react"
import { Header } from "@/components/header"
import { PromptInput } from "@/components/prompt-form"
import { ResultsCanvas } from "@/components/results-canvas"
import { CredentialsForm } from "@/components/credentials-form"
import { SavedPrompts } from "@/components/saved-prompts"
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
  const [lastExecutedPrompt, setLastExecutedPrompt] = useState<{
    prompt: string
    provider: string
    response: string
  } | null>(null)
  const [promptRefreshTrigger, setPromptRefreshTrigger] = useState(0)
  const [credentialsRefreshTrigger, setCredentialsRefreshTrigger] = useState(0)
  
  // Get token from Keycloak context
  const { token } = useKeycloak()

  const handlePromptSubmit = async (prompt: string, provider: string, credentialsName: string) => {
    setIsLoading(true)
    setResults(null)
    setError(null)

    try {
      console.log('Submitting prompt:', prompt, 'Provider:', provider, 'Credentials:', credentialsName)

      const response = await api.executeCommand(prompt, provider, credentialsName, token)

      const responseText = response?.message ? response.message : JSON.stringify(response, null, 2)
      setResults(responseText)
      
      // Store the executed prompt for potential saving
      setLastExecutedPrompt({
        prompt,
        provider,
        response: responseText
      })
      
      toast.success('Prompt executed successfully!')

    } catch (err: any) {
      console.error('Command execution failed:', err)
      
      let errorMessage = 'Unknown error occurred'
      
      if (err.message) {
        errorMessage = err.message
      } else if (err.response?.data?.error?.message) {
        errorMessage = err.response.data.error.message
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      }
      
      setError(errorMessage)
      toast.error('Command failed', {
        description: errorMessage,
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSavePrompt = async () => {
    if (!lastExecutedPrompt || !token) {
      toast.error('No prompt to save')
      return
    }

    try {
      await api.savePrompt(lastExecutedPrompt, token)
      toast.success('Prompt saved successfully!')
      setPromptRefreshTrigger(prev => prev + 1)
    } catch (err: any) {
      toast.error('Failed to save prompt', {
        description: err.message
      })
    }
  }

  const handleCredentialsAdded = () => {
    setCredentialsRefreshTrigger(prev => prev + 1)
    toast.success('Credentials added successfully!')
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-[#E3F2FD] via-white to-[#F3E5F5]">
      <Header />

      <main className="flex-1 max-w-full px-2 sm:px-4 py-4 sm:py-6">
        <div className="grid grid-cols-1 xl:grid-cols-7 gap-3 sm:gap-4 h-full max-w-[98vw] mx-auto">
          {/* Left side - Saved Prompts */}
          <div className="xl:col-span-2 order-2 xl:order-1">
            <div className="sticky top-6">
              <SavedPrompts 
                refreshTrigger={promptRefreshTrigger}
              />
            </div>
          </div>
          
          {/* Center - Main content - Bigger space for prompt form */}
          <div className="xl:col-span-3 order-1 xl:order-2 space-y-4 sm:space-y-6">
            <PromptInput 
              onSubmit={handlePromptSubmit}
              onSave={handleSavePrompt}
              canSave={!!lastExecutedPrompt}
              credentialsRefreshTrigger={credentialsRefreshTrigger}
            />
            
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

          {/* Right side - Credentials form */}
          <div className="xl:col-span-2 order-3">
            <div className="sticky top-6">
              <CredentialsForm onCredentialsAdded={handleCredentialsAdded} />
            </div>
          </div>
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