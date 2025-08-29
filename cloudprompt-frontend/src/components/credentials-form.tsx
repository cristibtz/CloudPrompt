import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, Plus, Key } from 'lucide-react'
import { api } from '@/services/api'
import { useKeycloak } from '@/auth/KeycloakContext'

interface CredentialData {
  [key: string]: string
}

interface CredentialFormData {
  provider: string
  name: string
  data: CredentialData
}

const PROVIDERS = {
  aws: {
    name: 'AWS',
    fields: [
      { key: 'AWS_ACCESS_KEY', label: 'AWS Access Key ID', type: 'text', placeholder: 'AKIA...' },
      { key: 'AWS_SECRET_ACCESS_KEY', label: 'AWS Secret Access Key', type: 'password', placeholder: 'Your AWS Secret Key' }
    ]
  },
  proxmox: {
    name: 'Proxmox',
    fields: [
      { key: 'host', label: 'Host', type: 'text', placeholder: '192.168.100.203' },
      { key: 'username', label: 'Username', type: 'text', placeholder: 'root' },
      { key: 'password', label: 'Password', type: 'password', placeholder: 'Your password' }
    ]
  },
  azure: {
    name: 'Azure',
    fields: [
      { key: 'AZURE_CLIENT_ID', label: 'Client ID', type: 'text', placeholder: 'Your Azure Client ID' },
      { key: 'AZURE_CLIENT_SECRET', label: 'Client Secret', type: 'password', placeholder: 'Your Azure Client Secret' },
      { key: 'AZURE_TENANT_ID', label: 'Tenant ID', type: 'text', placeholder: 'Your Azure Tenant ID' }
    ]
  },
  gcp: {
    name: 'Google Cloud Platform',
    fields: [
      { key: 'GCP_PROJECT_ID', label: 'Project ID', type: 'text', placeholder: 'your-project-id' },
      { key: 'GCP_SERVICE_ACCOUNT_KEY', label: 'Service Account Key (JSON)', type: 'textarea', placeholder: 'Paste your service account JSON here' }
    ]
  }
}

interface CredentialsFormProps {
  onCredentialsAdded?: () => void
}

export function CredentialsForm({ onCredentialsAdded }: CredentialsFormProps) {
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [credentialName, setCredentialName] = useState<string>('')
  const [formData, setFormData] = useState<CredentialData>({})
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  // Get token from Keycloak context
  const { token } = useKeycloak()

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider)
    setFormData({})
    setCredentialName('')
    setMessage(null)
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setMessage(null)

    try {
      const credentialPayload: CredentialFormData = {
        provider: selectedProvider,
        name: credentialName,
        data: formData
      }

      const result = await api.addCredentials(credentialPayload, token)
      
      setMessage({ type: 'success', text: result.message || 'Credentials added successfully!' })
      setFormData({})
      setCredentialName('')
      setSelectedProvider('')
      
      // Trigger credentials refresh
      onCredentialsAdded?.()
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.message || 'Failed to add credentials. Please try again.' 
      })
    } finally {
      setIsLoading(false)
    }
  }

  const isFormValid = () => {
    if (!selectedProvider || !credentialName.trim()) return false
    const provider = PROVIDERS[selectedProvider as keyof typeof PROVIDERS]
    if (!provider) return false
    
    return provider.fields.every(field => formData[field.key]?.trim())
  }

  const selectedProviderConfig = selectedProvider ? PROVIDERS[selectedProvider as keyof typeof PROVIDERS] : null

  return (
    <div className="bg-white rounded-lg shadow-lg border border-[#6565fc]/30 p-4 sm:p-6 w-full">
      <div className="mb-4">
        <h2 className="text-lg sm:text-xl font-bold text-[#0B1C37] mb-2 flex items-center gap-2">
          <div className="h-6 w-6 bg-[#6565fc] rounded-lg flex items-center justify-center">
            <Key className="h-3 w-3 text-white" />
          </div>
          Cloud Credentials
        </h2>
        <p className="text-[#B0BEC5] text-xs sm:text-sm">
          Add your cloud provider credentials
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Provider Selection */}
        <div className="space-y-2">
          <label htmlFor="provider" className="block text-sm font-medium text-[#0B1C37]">Provider</label>
          <Select value={selectedProvider} onValueChange={handleProviderChange}>
            <SelectTrigger className="w-full p-2 border-2 border-[#B0BEC5]/30 rounded-lg focus:border-[#6565fc] focus:outline-none focus:ring-2 focus:ring-[#6565fc]/20 transition-all duration-300">
              <SelectValue placeholder="Select provider" />
            </SelectTrigger>
            <SelectContent className="bg-white border-2 border-[#B0BEC5]/30 shadow-lg">
              {Object.entries(PROVIDERS).map(([key, provider]) => (
                <SelectItem key={key} value={key}>
                  {provider.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Credential Name */}
        {selectedProvider && (
          <div className="space-y-2">
            <label htmlFor="credentialName" className="block text-sm font-medium text-[#0B1C37]">
              Credential Name
            </label>
            <input
              id="credentialName"
              type="text"
              value={credentialName}
              onChange={(e) => setCredentialName(e.target.value)}
              placeholder={`My ${PROVIDERS[selectedProvider as keyof typeof PROVIDERS]?.name} Account`}
              className="w-full p-2 border-2 border-[#B0BEC5]/30 rounded-lg focus:border-[#2196F3] focus:outline-none focus:ring-2 focus:ring-[#2196F3]/20 transition-all duration-300 text-sm"
              required
            />
          </div>
        )}

        {/* Dynamic Fields Based on Provider */}
        {selectedProviderConfig && (
          <div className="space-y-3">
            <div className="border-t border-[#B0BEC5]/20 pt-3">
              <h3 className="text-sm font-medium text-[#0B1C37] mb-3">
                {selectedProviderConfig.name} Credentials
              </h3>
              <div className="space-y-3">
                {selectedProviderConfig.fields.map((field) => (
                  <div key={field.key} className="space-y-1">
                    <label htmlFor={field.key} className="block text-sm font-medium text-[#0B1C37]">
                      {field.label}
                    </label>
                    {field.type === 'textarea' ? (
                      <textarea
                        id={field.key}
                        value={formData[field.key] || ''}
                        onChange={(e) => handleInputChange(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        className="w-full p-2 border-2 border-[#B0BEC5]/30 rounded-lg focus:border-[#2196F3] focus:outline-none focus:ring-2 focus:ring-[#2196F3]/20 transition-all duration-300 resize-none text-sm"
                        rows={3}
                        required
                      />
                    ) : (
                      <input
                        id={field.key}
                        type={field.type}
                        value={formData[field.key] || ''}
                        onChange={(e) => handleInputChange(field.key, e.target.value)}
                        placeholder={field.placeholder}
                        className="w-full p-2 border-2 border-[#B0BEC5]/30 rounded-lg focus:border-[#2196F3] focus:outline-none focus:ring-2 focus:ring-[#2196F3]/20 transition-all duration-300 text-sm"
                        required
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Submit Button */}
        {selectedProvider && (
          <Button 
            type="submit" 
            disabled={!isFormValid() || isLoading}
            className="w-full bg-[#6565fc] hover:bg-[#512DA8] text-white px-4 py-2 rounded-lg font-semibold transition-all duration-300 cursor-pointer hover:scale-105 hover:shadow-lg text-sm"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Adding...
              </div>
            ) : (
              <div className="flex items-center justify-center">
                <Plus className="mr-2 h-4 w-4" />
                Add Credentials
              </div>
            )}
          </Button>
        )}

        {/* Success/Error Messages */}
        {message && (
          <div className={`p-3 rounded-lg border-2 transition-all duration-300 ${
            message.type === 'error' 
              ? 'border-red-200 bg-red-50 text-red-700' 
              : 'border-green-200 bg-green-50 text-green-700'
          }`}>
            <p className="text-sm font-medium">
              {message.text}
            </p>
          </div>
        )}
      </form>
    </div>
  )
}

export default CredentialsForm
