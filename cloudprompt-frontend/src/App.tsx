import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState } from "react"
import { Header } from "@/components/header"
import { CredentialsForm } from "@/components/credentials-form"
import { SavedPrompts } from "@/components/saved-prompts"
import { Conversation } from "@/components/conversation"
import { KeycloakProvider } from "./auth/KeycloakProvider"
import LoginPage from "./components/LoginPage"
import ProtectedRoute from "./components/ProtectedRoute"
import { toast } from "sonner"

function MainApp() {
  const [credentialsRefreshTrigger, setCredentialsRefreshTrigger] = useState(0)
  const [promptRefreshTrigger, setPromptRefreshTrigger] = useState(0)

  const handleCredentialsAdded = () => {
    setCredentialsRefreshTrigger(prev => prev + 1)
    toast.success('Credentials added successfully!')
  }

  const handlePromptSaved = () => {
    setPromptRefreshTrigger(prev => prev + 1)
    toast.success('Prompt saved successfully!')
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-[#E3F2FD] via-white to-[#F3E5F5]">
      <Header />

      <main className="flex-1 max-w-full px-2 sm:px-4 py-4 sm:py-6">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 h-full max-w-[98vw] mx-auto">
          
          {/* Left side - Saved Prompts */}
          <div className="lg:col-span-1 order-3 lg:order-1">
            <div className="sticky top-6">
              <SavedPrompts 
                refreshTrigger={promptRefreshTrigger}
              />
            </div>
          </div>

          {/* Main Conversation Area */}
          <div className="lg:col-span-3 order-1 lg:order-2">
            <Conversation 
              credentialsRefreshTrigger={credentialsRefreshTrigger}
              onPromptSaved={handlePromptSaved}
            />
          </div>

          {/* Right side - Credentials form */}
          <div className="lg:col-span-1 order-2 lg:order-3">
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