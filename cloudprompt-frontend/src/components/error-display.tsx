import { useState } from "react"

interface ErrorDisplayProps {
  error: {
    success: false
    error: string
    provider?: string
    received_output?: string
    details?: string
    status?: number
  }
}

export function ErrorDisplay({ error }: ErrorDisplayProps) {
  const [isOutputOpen, setIsOutputOpen] = useState(false)
  
  const getErrorClass = () => {
    if (error.status && error.status >= 500) return "border-red-500 bg-red-50"
    if (!error.status) return "border-red-500 bg-red-50"
    return "border-yellow-500 bg-yellow-50"
  }
  
  const getErrorTitle = () => {
    if (error.status && error.status >= 500) return "Server Error"
    if (!error.status) return "Network Error"
    return "Request Error"
  }

  return (
    <div className="space-y-3">
      <div className={`border-l-4 p-4 rounded ${getErrorClass()}`}>
        <div className="flex items-center gap-2 mb-2">
          <h3 className="font-semibold text-gray-800">
            {getErrorTitle()}
          </h3>
          {error.status && (
            <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded">
              {error.status}
            </span>
          )}
          {error.provider && (
            <span className="px-2 py-1 bg-blue-200 text-blue-700 text-xs rounded">
              {error.provider}
            </span>
          )}
        </div>
        <div className="space-y-2">
          <p className="font-medium text-gray-800">{error.error}</p>
          {error.details && (
            <p className="text-sm text-gray-600">{error.details}</p>
          )}
        </div>
      </div>

      {error.received_output && (
        <div className="border border-gray-200 rounded">
          <button
            onClick={() => setIsOutputOpen(!isOutputOpen)}
            className="w-full flex items-center gap-2 p-3 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-50 transition-colors"
          >
            <span className="transform transition-transform">
              {isOutputOpen ? '▼' : '▶'}
            </span>
            Show raw output from server ({error.received_output.length} characters)
          </button>
          {isOutputOpen && (
            <div className="border-t border-gray-200 bg-gray-50 p-3">
              <pre className="font-mono text-sm overflow-auto max-h-64 whitespace-pre-wrap break-words bg-white p-3 rounded border">
                {error.received_output}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
