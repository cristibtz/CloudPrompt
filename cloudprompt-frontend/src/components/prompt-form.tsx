import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
} from "@/components/ui/form"

const FormSchema = z.object({
  prompt: z.string().min(1, {
    message: "Prompt must not be empty",
  }),
})

interface PromptInputProps {
  onSubmit: (prompt: string) => Promise<void>
  apiStatus?: boolean | null
}

export function PromptInput({ onSubmit, apiStatus }: PromptInputProps) {
  const [isSubmitted, setIsSubmitted] = useState(false)
  
  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      prompt: "",
    },
  })

  async function handleSubmit(data: z.infer<typeof FormSchema>) {
    console.log("Form submitted:", data) // Debug log
    setIsSubmitted(true)
    
    try {
      await onSubmit(data.prompt)

    } catch (error) {
      console.error("Form submission error:", error)
    }
    
    // Reset form after submission
    form.reset()
    
    // Reset submitted state after 3 seconds
    setTimeout(() => setIsSubmitted(false), 3000)
  }

  return (
    <div className="bg-white rounded-lg shadow-lg border border-[#B0BEC5]/20 p-6 w-full max-w-4xl">
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-[#0B1C37] mb-2">
          Cloud<span className="text-[#2196F3]">Prompt</span> Assistant
        </h2>
        <p className="text-[#B0BEC5] text-sm">
          Enter your cloud management commands using natural language
        </p>
      </div>
      
      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="prompt"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <div className="relative">
                    <textarea
                      {...field}
                      placeholder="e.g., 'List all my EC2 instances in us-east-1' or 'Create a new S3 bucket called my-data-bucket'"
                      className="w-full min-h-[120px] p-4 text-lg border-2 border-[#B0BEC5]/30 rounded-lg resize-none focus:border-[#2196F3] focus:outline-none focus:ring-2 focus:ring-[#2196F3]/20 transition-all duration-300"
                      rows={4}
                      onKeyDown={(e) => {
                        if (e.ctrlKey && e.key === 'Enter') {
                          e.preventDefault()
                          form.handleSubmit(handleSubmit)()
                        }
                      }}
                    />
                    <div className="absolute bottom-3 right-3 text-xs text-[#B0BEC5]">
                      {field.value?.length || 0} characters
                    </div>
                  </div>
                </FormControl>
                {form.formState.errors.prompt && (
                  <p className="text-red-500 text-sm mt-2">
                    {form.formState.errors.prompt.message}
                  </p>
                )}
              </FormItem>
            )}
          />
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Button 
                type="submit" 
                className="bg-[#2196F3] hover:bg-[#64B5F6] text-white px-8 py-3 rounded-lg font-semibold transition-all duration-300 cursor-pointer hover:scale-105 hover:shadow-lg text-lg"
                disabled={form.formState.isSubmitting}
              >
                {form.formState.isSubmitting ? (
                  <div className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </div>
                ) : (
                  "Execute Command"
                )}
              </Button>
              
              {/* API Status Indicator */}
              <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    apiStatus === true ? 'bg-green-500 animate-pulse' : 
                    apiStatus === false ? 'bg-red-500' : 
                    'bg-yellow-500 animate-pulse'
                  }`}></div>
                  <span className="text-sm text-[#B0BEC5]">
                    {apiStatus === true ? 'API Connected' : 
                        apiStatus === false ? 'API Offline' : 
                        'Checking API...'}
                  </span>
              </div>


              {isSubmitted && (
                <div className="flex items-center text-green-500 transition-opacity duration-500 ease-in-out">
                  <svg 
                    className="w-6 h-6 mr-1" 
                    fill="currentColor" 
                    viewBox="0 0 20 20"
                  >
                    <path 
                      fillRule="evenodd" 
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" 
                      clipRule="evenodd" 
                    />
                  </svg>
                  <span className="text-sm font-medium">Command Executed!</span>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2 text-sm text-[#B0BEC5]">
              <kbd className="px-2 py-1 bg-[#B0BEC5]/10 rounded border text-xs">Ctrl</kbd>
              <span>+</span>
              <kbd className="px-2 py-1 bg-[#B0BEC5]/10 rounded border text-xs">Enter</kbd>
              <span>to submit</span>
            </div>
          </div>
        </form>
      </Form>
    </div>
  )
}
