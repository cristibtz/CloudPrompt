import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { api } from '@/services/api'
import { useKeycloak } from '@/auth/KeycloakContext'
import { toast } from 'sonner'
import { Trash2, Send, User, Bot, BookmarkPlus } from 'lucide-react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface Credential {
  id: string
  name: string
  provider: string
}

interface ConversationProps {
  credentialsRefreshTrigger: number
  onPromptSaved?: () => void
}

export function Conversation({ credentialsRefreshTrigger, onPromptSaved }: ConversationProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [provider, setProvider] = useState('aws')
  const [credentialsName, setCredentialsName] = useState('')
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [lastExchange, setLastExchange] = useState<{prompt: string, response: string} | null>(null)
  const { token } = useKeycloak()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

    // Load credentials
  useEffect(() => {
    const loadCredentials = async () => {
      if (!token) return
      
      try {
        const credentialsData = await api.getUserCredentials(token)
        console.log('Loaded credentials:', credentialsData)
        setCredentials(credentialsData || [])
        
        // Auto-select first credential for the current provider if available
        if (credentialsData && credentialsData.length > 0) {
          const providerCredentials = credentialsData.filter((cred: { provider: string }) => cred.provider === provider)
          if (providerCredentials.length > 0) {
            setCredentialsName(providerCredentials[0].name)
          } else if (credentialsData.length > 0) {
            // If no credentials for current provider, select first available and switch provider
            setCredentialsName(credentialsData[0].name)
            setProvider(credentialsData[0].provider)
          }
        }
      } catch (error) {
        console.error('Failed to load credentials:', error)
        toast.error('Failed to load credentials. Please add credentials first.')
      }
    }

    loadCredentials()
  }, [token, credentialsRefreshTrigger, provider])

  const handleSendMessage = async () => {
    if (!currentMessage.trim() || !credentialsName || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: currentMessage.trim(),
      timestamp: new Date()
    }

    const userPrompt = currentMessage.trim()
    setMessages(prev => [...prev, userMessage])
    setCurrentMessage('')
    setIsLoading(true)

    try {
      const response = await api.executeCommand(userPrompt, provider, credentialsName, token)
      const responseText = response?.message ? response.message : JSON.stringify(response, null, 2)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: responseText,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Store the last exchange for saving
      setLastExchange({
        prompt: userPrompt,
        response: responseText
      })
      
      toast.success('Message sent successfully!')

    } catch (err: any) {
      console.error('Message failed:', err)
      
      let errorMessage = 'Unknown error occurred'
      if (err.message) {
        errorMessage = err.message
      } else if (err.response?.data?.error?.message) {
        errorMessage = err.response.data.error.message
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      }

      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `❌ Error: ${errorMessage}`,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, errorMsg])
      toast.error('Message failed', { description: errorMessage })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveLastPrompt = async () => {
    if (!lastExchange || !token) {
      toast.error('No prompt to save')
      return
    }

    try {
      const promptData = {
        prompt: lastExchange.prompt,
        provider: provider,
        response: lastExchange.response
      }
      
      await api.savePrompt(promptData, token)
      onPromptSaved?.()
      toast.success('Prompt saved successfully!')
    } catch (err: any) {
      toast.error('Failed to save prompt', {
        description: err.message
      })
    }
  }

  const handleClearSession = async () => {
    try {
      await api.clearSession(token)
      setMessages([])
      toast.success('Session and conversation history cleared!')
    } catch (error: any) {
      toast.error('Failed to clear session', { 
        description: error.message 
      })
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <Card className="h-[80vh] flex flex-col">
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            CloudPrompt Assistant
          </CardTitle>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleClearSession}
            className="flex items-center gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Clear Session
          </Button>
        </div>
        
        {/* Provider and Credentials Selection */}
        <div className="flex gap-2 mt-4">
          <Select value={provider} onValueChange={setProvider}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Provider" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="aws">AWS</SelectItem>
              <SelectItem value="azure">Azure</SelectItem>
              <SelectItem value="gcp">GCP</SelectItem>
              <SelectItem value="proxmox">Proxmox</SelectItem>
            </SelectContent>
          </Select>

          <Select value={credentialsName} onValueChange={setCredentialsName}>
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Select credentials" />
            </SelectTrigger>
            <SelectContent>
              {credentials
                .filter(cred => cred.provider === provider)
                .map((cred) => (
                  <SelectItem key={cred.id} value={cred.name}>
                    {cred.name}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col gap-4 p-4">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto space-y-4 min-h-0">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Start a conversation with CloudPrompt!</p>
                <p className="text-sm mt-2">Try: "create an EC2 instance" or "list my S3 buckets"</p>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex gap-2 max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {message.type === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>
                  <div className={`rounded-lg px-4 py-2 ${
                    message.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                    <pre className="whitespace-pre-wrap font-sans text-sm">
                      {message.content}
                    </pre>
                    <div className={`text-xs mt-1 opacity-70`}>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="flex gap-2">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="bg-gray-100 text-gray-900 rounded-lg px-4 py-2">
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="space-y-3">
          {/* Save Button Row */}
          {lastExchange && (
            <div className="flex justify-center">
              <Button 
                variant="outline"
                size="sm"
                onClick={handleSaveLastPrompt}
                className="flex items-center gap-2"
              >
                <BookmarkPlus className="h-4 w-4" />
                Save Last Exchange
              </Button>
            </div>
          )}
          
          {/* Message Input Row */}
          <div className="flex gap-2 border-t pt-4">
            <Input
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={credentialsName ? "Type your message..." : "Select credentials first..."}
              disabled={isLoading}
              className="flex-1"
            />
            <Button 
              onClick={handleSendMessage}
              disabled={isLoading || !currentMessage.trim() || !credentialsName}
              className="flex items-center gap-2"
            >
              <Send className="h-4 w-4" />
              Send
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
