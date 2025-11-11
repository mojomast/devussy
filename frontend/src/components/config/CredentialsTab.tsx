import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { configApi, ProviderCredentials, ProviderType, CreateCredentialRequest, AvailableModel } from '../../services/configApi';

const CredentialsTab: React.FC = () => {
  const [credentials, setCredentials] = useState<ProviderCredentials[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [loadingModelsId, setLoadingModelsId] = useState<string | null>(null);
  const [availableModels, setAvailableModels] = useState<Record<string, AvailableModel[]>>({});
  
  // Form state
  const [formData, setFormData] = useState<CreateCredentialRequest>({
    name: '',
    provider: ProviderType.OPENAI,
    api_key: '',
    api_base: '',
    organization_id: ''
  });

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    try {
      setLoading(true);
      const creds = await configApi.listCredentials();
      setCredentials(creds);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const createPromise = configApi.createCredential(formData);
    
    toast.promise(createPromise, {
      loading: 'Creating credential...',
      success: 'Credential created successfully!',
      error: (err: any) => err.response?.data?.detail || 'Failed to create credential',
    });
    
    try {
      await createPromise;
      setShowForm(false);
      setFormData({
        name: '',
        provider: ProviderType.OPENAI,
        api_key: '',
        api_base: '',
        organization_id: ''
      });
      await loadCredentials();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create credential');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this credential?')) {
      return;
    }
    
    const deletePromise = configApi.deleteCredential(id);
    
    toast.promise(deletePromise, {
      loading: 'Deleting credential...',
      success: 'Credential deleted successfully!',
      error: (err: any) => err.response?.data?.detail || 'Failed to delete credential',
    });
    
    try {
      await deletePromise;
      await loadCredentials();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete credential');
    }
  };

  const handleTest = async (id: string) => {
    const testPromise = configApi.testCredential(id);
    
    setTestingId(id);
    
    toast.promise(testPromise, {
      loading: 'Testing credential...',
      success: (result) => result.success ? `✅ ${result.message}` : `❌ ${result.message}`,
      error: (err: any) => `❌ Test failed: ${err.response?.data?.detail || err.message}`,
    });
    
    try {
      const result = await testPromise;
      // Reload to get updated is_valid status
      await loadCredentials();
      
      // If test was successful, automatically fetch available models
      if (result.success) {
        await handleLoadModels(id);
      }
    } catch (err: any) {
      // Error already handled by toast.promise
    } finally {
      setTestingId(null);
    }
  };

  const handleLoadModels = async (id: string) => {
    setLoadingModelsId(id);
    try {
      const models = await configApi.listAvailableModels(id);
      setAvailableModels(prev => ({ ...prev, [id]: models }));
      toast.success(`✅ Loaded ${models.length} available models`);
    } catch (err: any) {
      toast.error(`Failed to load models: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoadingModelsId(null);
    }
  };

  const getProviderIcon = (provider: ProviderType) => {
    const icons: Record<ProviderType, string> = {
      [ProviderType.OPENAI]: '🤖',
      [ProviderType.ANTHROPIC]: '🧠',
      [ProviderType.GOOGLE]: '🔍',
      [ProviderType.AZURE_OPENAI]: '☁️',
      [ProviderType.GENERIC]: '⚙️',
      [ProviderType.REQUESTY]: '📡'
    };
    return icons[provider] || '🔑';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading credentials...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">API Credentials</h2>
          <p className="mt-1 text-sm text-gray-600">
            Manage your LLM provider API keys. Keys are encrypted and stored securely.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          {showForm ? '✕ Cancel' : '+ Add Credential'}
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          <div className="flex items-center gap-2">
            <span className="text-lg">❌</span>
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Add Credential Form */}
      {showForm && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Credential</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., OpenAI Production"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Provider *
                </label>
                <select
                  required
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value as ProviderType })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={ProviderType.OPENAI}>OpenAI</option>
                  <option value={ProviderType.ANTHROPIC}>Anthropic (Claude)</option>
                  <option value={ProviderType.GOOGLE}>Google</option>
                  <option value={ProviderType.AZURE_OPENAI}>Azure OpenAI</option>
                  <option value={ProviderType.GENERIC}>Generic</option>
                  <option value={ProviderType.REQUESTY}>Requesty</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API Key *
              </label>
              <input
                type="password"
                required
                value={formData.api_key}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                placeholder="sk-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Your API key is encrypted before storage and never exposed in responses
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Custom Endpoint (Optional)
                </label>
                <input
                  type="text"
                  value={formData.api_base}
                  onChange={(e) => setFormData({ ...formData, api_base: e.target.value })}
                  placeholder="https://..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Organization ID (Optional)
                </label>
                <input
                  type="text"
                  value={formData.organization_id}
                  onChange={(e) => setFormData({ ...formData, organization_id: e.target.value })}
                  placeholder="org-..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Save Credential
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Credentials List */}
      {credentials.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <p className="text-xl mb-2">🔑</p>
          <p className="text-gray-600 mb-4">No credentials configured yet</p>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Add Your First Credential
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {credentials.map((cred) => (
            <div
              key={cred.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <span className="text-2xl">{getProviderIcon(cred.provider)}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-gray-900">{cred.name}</h3>
                      {cred.is_valid ? (
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                          ✓ Tested
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                          Not tested
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      Provider: <span className="font-medium">{cred.provider}</span>
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      API Key: <code className="bg-gray-100 px-2 py-0.5 rounded">{cred.api_key_encrypted}</code>
                    </p>
                    {cred.api_base && (
                      <p className="text-sm text-gray-500 mt-1">
                        Endpoint: <span className="font-mono text-xs">{cred.api_base}</span>
                      </p>
                    )}
                    <p className="text-xs text-gray-400 mt-2">
                      Created: {new Date(cred.created_at).toLocaleString()}
                      {cred.last_tested && ` • Last tested: ${new Date(cred.last_tested).toLocaleString()}`}
                    </p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleTest(cred.id)}
                    disabled={testingId === cred.id}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {testingId === cred.id ? '⏳ Testing...' : '🔍 Test'}
                  </button>
                  {cred.is_valid && (
                    <button
                      onClick={() => handleLoadModels(cred.id)}
                      disabled={loadingModelsId === cred.id}
                      className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {loadingModelsId === cred.id ? '⏳ Loading...' : '📋 List Models'}
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(cred.id)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
              
              {/* Available Models Section */}
              {availableModels[cred.id] && availableModels[cred.id].length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Available Models ({availableModels[cred.id].length})</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {availableModels[cred.id].map((model) => (
                      <div
                        key={model.id}
                        className="p-2 bg-gray-50 rounded border border-gray-200 hover:bg-gray-100 transition-colors"
                      >
                        <div className="font-mono text-xs text-blue-600">{model.id}</div>
                        <div className="text-xs text-gray-600 mt-1">{model.name}</div>
                        {model.context_window > 0 && (
                          <div className="text-xs text-gray-500 mt-1">
                            Context: {model.context_window.toLocaleString()} tokens
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CredentialsTab;
