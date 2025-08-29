import { useState, useEffect } from "react"
import { ChevronDown, ChevronUp, Trash2, RefreshCw, User, Copy } from "lucide-react"
import { Button } from "@/components/ui/button"
import { api } from "@/services/api"
import { useKeycloak } from "@/auth/KeycloakContext"
import { toast } from "sonner"

interface SavedPrompt {
  id: number
  prompt: string
  response: string
  provider: string
  created_at: string
}

interface SavedPromptsProps {
  refreshTrigger?: number
}

export function SavedPrompts({ refreshTrigger }: SavedPromptsProps) {
  const [prompts, setPrompts] = useState<SavedPrompt[]>([])
  const [expandedPrompts, setExpandedPrompts] = useState<Set<number>>(new Set())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const { token } = useKeycloak()

  const fetchPrompts = async () => {
    if (!token) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const promptsData = await api.getUserPrompts(token)
      setPrompts(promptsData || [])
    } catch (err: any) {
      setError(err.message || 'Failed to load prompts')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeletePrompt = async (promptId: number, event: React.MouseEvent) => {
    event.stopPropagation()
    if (!token) return
    
    try {
      await api.deletePrompt(promptId, token)
      setPrompts(prompts.filter(p => p.id !== promptId))
      setExpandedPrompts(prev => {
        const next = new Set(prev)
        next.delete(promptId)
        return next
      })
    } catch (err: any) {
      setError(err.message || 'Failed to delete prompt')
    }
  }

  const toggleExpanded = (promptId: number, event: React.MouseEvent) => {
    event.stopPropagation()
    setExpandedPrompts(prev => {
      const next = new Set(prev)
      if (next.has(promptId)) {
        next.delete(promptId)
      } else {
        next.add(promptId)
      }
      return next
    })
  }

  const handlePromptClick = (prompt: SavedPrompt, event: React.MouseEvent) => {
    // Only copy prompt when clicking on the prompt text area, not buttons
    const target = event.target as HTMLElement
    if (!target.closest('button')) {
      copyToClipboard(prompt.prompt, 'prompt', event)
    }
  }

  const copyToClipboard = async (text: string, type: 'prompt' | 'response', event: React.MouseEvent) => {
    event.stopPropagation()
    try {
      await navigator.clipboard.writeText(text)
      toast.success(`${type === 'prompt' ? 'Prompt' : 'Response'} copied to clipboard!`)
    } catch (err) {
      toast.error('Failed to copy to clipboard')
    }
  }

  const truncateText = (text: string, maxLength: number = 100) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + "..."
  }

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return {
      date: date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      }),
      time: date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }),
      dateTime: date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      }) + ' at ' + date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    }
  }

  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      aws: 'bg-orange-100 text-orange-800 border-orange-200',
      azure: 'bg-blue-100 text-blue-800 border-blue-200',
      gcp: 'bg-green-100 text-green-800 border-green-200',
      proxmox: 'bg-purple-100 text-purple-800 border-purple-200'
    }
    return colors[provider] || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  useEffect(() => {
    fetchPrompts()
  }, [token, refreshTrigger])

  if (isLoading) {
    return (
      <div className="w-full h-full">
        <div className="bg-white rounded-lg shadow-lg border border-[#B0BEC5]/20 p-6 h-full">
          <div className="flex items-center gap-3 text-[#0B1C37]">
            <RefreshCw className="h-5 w-5 animate-spin" />
            <span className="text-xl font-bold">Loading Saved Prompts...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full">
      <div className="bg-white rounded-lg shadow-lg border border-[#6565fc]/30 p-6 h-full flex flex-col">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-2xl font-bold text-[#0B1C37] flex items-center gap-3">
              <div className="h-8 w-8 bg-[#6565fc] rounded-lg flex items-center justify-center">
                <User className="h-4 w-4 text-white" />
              </div>
              Saved Prompts
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchPrompts}
              disabled={isLoading}
              className="h-10 w-10 p-0 hover:bg-[#6565fc]/10 rounded-full border border-[#6565fc]/20"
              title="Refresh prompts"
            >
              <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''} text-[#6565fc]`} />
            </Button>
          </div>
          <div className="flex items-center gap-4 text-sm text-[#B0BEC5]">
            <span className="flex items-center gap-1">
              <span className="font-medium">{prompts.length}</span> 
              {prompts.length === 1 ? 'prompt' : 'prompts'} saved
            </span>
            <span className="text-xs">Click any prompt to reuse it</span>
          </div>
        </div>
        
        {/* Error Display */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm font-medium">{error}</p>
          </div>
        )}
        
        {/* Empty State */}
        {prompts.length === 0 && !isLoading && (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-12">
            <User className="h-16 w-16 text-[#B0BEC5] mb-4" />
            <h3 className="text-lg font-medium text-[#B0BEC5] mb-2">No saved prompts yet</h3>
            <p className="text-sm text-[#B0BEC5] max-w-sm">
              Execute a prompt and save it to build your personal prompt library
            </p>
          </div>
        )}

        {/* Prompts List */}
        <div className="flex-1 overflow-hidden">
          <div className="space-y-4 h-full overflow-y-auto pr-2">
            {prompts.map((prompt) => {
              const isExpanded = expandedPrompts.has(prompt.id)
              const dateTime = formatDateTime(prompt.created_at)
              
              return (
                <div
                  key={prompt.id}
                  className="border border-[#B0BEC5]/20 rounded-lg p-4 hover:border-[#2196F3]/40 hover:shadow-md transition-all duration-200 bg-white group"
                >
                  {/* Main Content */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div 
                      className="flex-1 min-w-0 cursor-pointer" 
                      onClick={(e) => handlePromptClick(prompt, e)}
                    >
                      <h4 className="font-semibold text-[#0B1C37] text-base leading-relaxed mb-2 group-hover:text-[#2196F3] transition-colors">
                        {isExpanded ? prompt.prompt : truncateText(prompt.prompt, 120)}
                      </h4>
                      
                      {/* Metadata Row */}
                      <div className="flex items-center flex-wrap gap-3 mb-2">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getProviderColor(prompt.provider)}`}>
                          {prompt.provider.toUpperCase()}
                        </span>
                      </div>
                      
                      {/* Response Preview */}
                      <div className="text-sm text-[#B0BEC5]">
                        <span className="font-medium">Response: </span>
                        {truncateText(prompt.response, 80)}
                      </div>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => copyToClipboard(prompt.prompt, 'prompt', e)}
                        className="h-8 w-8 p-0 hover:bg-[#2196F3]/10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Copy prompt"
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => toggleExpanded(prompt.id, e)}
                        className="h-8 w-8 p-0 hover:bg-[#2196F3]/10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        title={isExpanded ? "Collapse details" : "Expand details"}
                      >
                        {isExpanded ? (
                          <ChevronUp className="h-3 w-3" />
                        ) : (
                          <ChevronDown className="h-3 w-3" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => handleDeletePrompt(prompt.id, e)}
                        className="h-8 w-8 p-0 hover:bg-red-100 hover:text-red-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Delete prompt"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  
                  {/* Expanded Details */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-[#B0BEC5]/20">
                      <div className="space-y-4">
                        {/* Full Prompt */}
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="text-sm font-semibold text-[#0B1C37] flex items-center gap-2">
                              Complete Prompt
                            </h5>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => copyToClipboard(prompt.prompt, 'prompt', e)}
                              className="h-6 px-2 text-xs hover:bg-[#2196F3]/10"
                              title="Copy prompt"
                            >
                              <Copy className="h-3 w-3 mr-1" />
                              Copy
                            </Button>
                          </div>
                          <div className="text-sm text-[#0B1C37] bg-gray-50 p-4 rounded-lg border border-[#B0BEC5]/20 leading-relaxed">
                            {prompt.prompt}
                          </div>
                        </div>
                        
                        {/* Full Response */}
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="text-sm font-semibold text-[#0B1C37]">Response</h5>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => copyToClipboard(prompt.response, 'response', e)}
                              className="h-6 px-2 text-xs hover:bg-[#2196F3]/10"
                              title="Copy response"
                            >
                              <Copy className="h-3 w-3 mr-1" />
                              Copy
                            </Button>
                          </div>
                          <div className="text-sm text-[#B0BEC5] bg-gray-50 p-4 rounded-lg border border-[#B0BEC5]/20 max-h-48 overflow-y-auto leading-relaxed">
                            <pre className="whitespace-pre-wrap font-sans">{prompt.response}</pre>
                          </div>
                        </div>
                        
                        {/* Additional Details */}
                        <div className="grid grid-cols-2 gap-4 pt-3 border-t border-[#B0BEC5]/10">
                          <div className="text-xs">
                            <span className="font-medium text-[#0B1C37]">Created:</span>
                            <div className="text-[#B0BEC5] mt-1">
                              {dateTime.dateTime}
                            </div>
                          </div>
                          <div className="text-xs">
                            <span className="font-medium text-[#0B1C37]">Prompt ID:</span>
                            <div className="text-[#B0BEC5] mt-1 font-mono">#{prompt.id}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

