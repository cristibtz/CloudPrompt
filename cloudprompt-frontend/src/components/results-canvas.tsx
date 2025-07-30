import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"

interface ResultsCanvasProps {
  results: string | null
  isLoading: boolean
}

export function ResultsCanvas({ results, isLoading }: ResultsCanvasProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const resultsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (results && resultsRef.current) {
      resultsRef.current.scrollTop = resultsRef.current.scrollHeight
    }
  }, [results])

  const copyToClipboard = () => {
    if (results) {
      navigator.clipboard.writeText(results)

      toast.success("Results copied to clipboard!", {
        description: "You can now paste the results anywhere.",
      })
    }
  }

  if (!results && !isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg border border-[#B0BEC5]/20 p-6 w-full max-w-4xl">
        <div className="text-center py-12">
          <div className="w-16 h-16 mx-auto mb-4 bg-[#2196F3]/10 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-[#2196F3]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-[#0B1C37] mb-2">Ready to Execute</h3>
          <p className="text-[#B0BEC5]">Enter a command above to see results here</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg border border-[#B0BEC5]/20 p-6 w-full max-w-4xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-[#0B1C37] flex items-center">
          <span className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></span>
          Command Results
        </h3>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={copyToClipboard}
            className="text-[#2196F3] border-[#2196F3] hover:bg-[#2196F3] hover:text-white"
            disabled={!results}
          >
            📋 Copy
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[#2196F3] border-[#2196F3] hover:bg-[#2196F3] hover:text-white"
          >
            {isExpanded ? "📉 Collapse" : "📈 Expand"}
          </Button>
        </div>
      </div>

      <div 
        ref={resultsRef}
        className={`bg-[#0B1C37] rounded-lg p-4 font-mono text-sm text-green-400 overflow-auto transition-all duration-300 ${
          isExpanded ? "max-h-96" : "max-h-64"
        }`}
      >
        {isLoading ? (
          <div className="flex items-center space-x-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-[#2196F3] rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-[#2196F3] rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-[#2196F3] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <span className="text-[#2196F3]">Executing command...</span>
          </div>
        ) : (
          <div className="whitespace-pre-wrap">
            {results}
            <div className="text-[#B0BEC5] mt-2 text-xs">
              Command completed at {new Date().toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>

      {results && (
        <div className="mt-4 flex items-center justify-between text-sm text-[#B0BEC5]">
          <div className="flex items-center space-x-4">
            <span>✅ Command executed successfully</span>
            <span>📊 {results.split('\n').length} lines</span>
            <span>📝 {results.length} characters</span>
          </div>
          <div className="text-xs">
            {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  )
}
