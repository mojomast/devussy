import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { projectsApi, ProjectCreateRequest } from '../services/projectsApi';
import { configApi, GlobalConfig, ProviderCredentials, AvailableModel } from '../services/configApi';
import { extractErrorMessage } from '../utils/errorHandler';

const CreateProjectPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<ProjectCreateRequest>({
    name: '',
    description: '',
    options: {
      enable_git: false,
      enable_streaming: true,
    },
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [globalConfig, setGlobalConfig] = useState<GlobalConfig | null>(null);
  const [credentials, setCredentials] = useState<ProviderCredentials[]>([]);
  const [availableModels, setAvailableModels] = useState<Record<string, AvailableModel[]>>({});
  const [loadingModels, setLoadingModels] = useState<boolean>(false);
  const [selectedCredential, setSelectedCredential] = useState<string>('');

  useEffect(() => {
    loadConfigAndCredentials();
  }, []);

  const loadConfigAndCredentials = async () => {
    try {
      const [config, creds] = await Promise.all([
        configApi.getGlobalConfig().catch(() => null),
        configApi.listCredentials().catch(() => [])
      ]);
      setGlobalConfig(config);
      setCredentials(creds);
      
      // Auto-select first valid credential
      const validCred = creds.find(c => c.is_valid);
      if (validCred) {
        setSelectedCredential(validCred.id);
        loadModelsForCredential(validCred.id);
      }
    } catch (err) {
      console.error('Failed to load configuration:', err);
    }
  };

  const loadModelsForCredential = async (credentialId: string) => {
    if (availableModels[credentialId]) return; // Already loaded
    
    try {
      setLoadingModels(true);
      const models = await configApi.listAvailableModels(credentialId);
      setAvailableModels(prev => ({ ...prev, [credentialId]: models }));
    } catch (err) {
      console.error('Failed to load models:', err);
    } finally {
      setLoadingModels(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      const errorMsg = 'Project name is required';
      setError(errorMsg);
      toast.error(errorMsg);
      return;
    }

    if (!formData.description.trim()) {
      const errorMsg = 'Project description is required';
      setError(errorMsg);
      toast.error(errorMsg);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // Add selected credential to the request
      const projectRequest = {
        ...formData,
        credential_id: selectedCredential || undefined,
      };
      
      const createPromise = projectsApi.createProject(projectRequest);
      
      toast.promise(createPromise, {
        loading: 'Creating project...',
        success: 'Project created successfully! Redirecting...',
        error: (err: any) => extractErrorMessage(err),
      });
      
      const project = await createPromise;
      setTimeout(() => navigate(`/projects/${project.id}`), 500);
    } catch (err: any) {
      const errorMessage = extractErrorMessage(err);
      setError(errorMessage);
      setLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      options: {
        ...prev.options,
        [name]: checked,
      },
    }));
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Create New Project</h1>
        <p className="text-lg text-gray-600 dark:text-gray-300 mt-2">
          Generate comprehensive documentation for your development project
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-base text-red-800 font-medium">{error}</p>
        </div>
      )}

      {/* Configuration Status */}
      {(globalConfig || credentials.length > 0) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-blue-600 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h3 className="font-semibold text-blue-900 text-base">✅ Configuration Active</h3>
              <p className="text-base text-blue-800 mt-1 leading-relaxed">
                {credentials.length} credential(s) available. You can configure different models for each phase below.
              </p>
            </div>
          </div>
        </div>
      )}

      {!globalConfig && credentials.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-yellow-600 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h3 className="font-semibold text-yellow-900 text-base">⚠️ No Credentials Found</h3>
              <p className="text-base text-yellow-800 mt-1 leading-relaxed">
                Please set up your API credentials in{' '}
                <a href="/settings" className="underline font-bold hover:text-yellow-900">
                  Settings
                </a>{' '}
                before creating a project.
              </p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6">
        {/* Project Name */}
        <div className="mb-6">
          <label htmlFor="name" className="block text-base font-semibold text-gray-900 dark:text-white mb-2">
            Project Name *
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            placeholder="My Awesome Project"
            className="w-full px-4 py-3 text-base bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            A clear, descriptive name for your project
          </p>
        </div>

        {/* Project Description */}
        <div className="mb-6">
          <label
            htmlFor="description"
            className="block text-base font-semibold text-gray-900 dark:text-white mb-2"
          >
            Project Description *
          </label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
            placeholder="A web application that helps users manage their tasks with AI-powered suggestions..."
            rows={6}
            className="w-full px-4 py-3 text-base bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 leading-relaxed"
            required
          />
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 leading-relaxed">
            Describe your project's purpose, features, and technical requirements. The more detail
            you provide, the better the generated documentation.
          </p>
        </div>

        {/* Options */}
        <div className="mb-6">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-3">Options</h3>
          <div className="space-y-4">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                name="enable_git"
                checked={formData.options?.enable_git || false}
                onChange={handleCheckboxChange}
                className="w-5 h-5 mt-0.5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div>
                <span className="text-base font-medium text-gray-900 dark:text-white">Enable Git Integration</span>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Automatically initialize a Git repository and commit generated files
                </p>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                name="enable_streaming"
                checked={formData.options?.enable_streaming !== false}
                onChange={handleCheckboxChange}
                className="w-5 h-5 mt-0.5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <div>
                <span className="text-base font-medium text-gray-900 dark:text-white">Enable Streaming</span>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Show real-time progress updates during generation
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Per-Stage Model Selection */}
        {credentials.length > 0 && (
          <div className="mb-6">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-3">🎯 Model Configuration Per Phase</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 leading-relaxed">
              Optionally select different models for each phase of your project generation. Leave blank to use defaults.
            </p>
            
            {/* Credential Selector */}
            <div className="mb-4">
              <label className="block text-base font-medium text-gray-900 dark:text-white mb-2">
                API Credential
              </label>
              <select
                value={selectedCredential}
                onChange={(e) => {
                  setSelectedCredential(e.target.value);
                  loadModelsForCredential(e.target.value);
                }}
                className="w-full px-4 py-3 text-base bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- Use Global Default --</option>
                {credentials.map(cred => (
                  <option key={cred.id} value={cred.id}>
                    {cred.name} ({cred.provider}) {cred.is_valid ? '✓' : '⚠️ Not Tested'}
                  </option>
                ))}
              </select>
              
              {/* Requesty Model Format Help */}
              {selectedCredential && credentials.find(c => c.id === selectedCredential)?.provider.toLowerCase() === 'requesty' && (
                <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
                  <p className="text-sm text-blue-800 dark:text-blue-300">
                    <strong>💡 Requesty Model Format:</strong> Model names must use{' '}
                    <code className="bg-blue-100 dark:bg-blue-800 px-1 py-0.5 rounded text-xs font-mono">
                      provider/model
                    </code>{' '}
                    format (e.g., <code className="bg-blue-100 dark:bg-blue-800 px-1 py-0.5 rounded text-xs font-mono">openai/gpt-4o</code>
                    , <code className="bg-blue-100 dark:bg-blue-800 px-1 py-0.5 rounded text-xs font-mono">anthropic/claude-3-5-sonnet</code>).{' '}
                    <a 
                      href="https://docs.requesty.ai/models" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="underline hover:text-blue-600 dark:hover:text-blue-200"
                    >
                      View available models →
                    </a>
                  </p>
                </div>
              )}
            </div>

            {/* Model Selection Grid */}
            {selectedCredential && availableModels[selectedCredential] && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Design Phase */}
                <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-900 mb-3 text-base">🎨 Design Phase</h4>
                  <select
                    value={formData.design_model || ''}
                    onChange={(e) => setFormData({ ...formData, design_model: e.target.value })}
                    className="w-full px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-blue-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">-- Default Model --</option>
                    {availableModels[selectedCredential].map(model => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                  <p className="text-sm text-blue-700 mt-3 leading-relaxed">Creates initial project architecture</p>
                </div>

                {/* DevPlan Phase */}
                <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                  <h4 className="font-semibold text-green-900 mb-3 text-base">📋 DevPlan Phase</h4>
                  <select
                    value={formData.devplan_model || ''}
                    onChange={(e) => setFormData({ ...formData, devplan_model: e.target.value })}
                    className="w-full px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-green-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    <option value="">-- Default Model --</option>
                    {availableModels[selectedCredential].map(model => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                  <p className="text-sm text-green-700 mt-3 leading-relaxed">Generates detailed development plan</p>
                </div>

                {/* Handoff Phase */}
                <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
                  <h4 className="font-semibold text-purple-900 mb-3 text-base">🚀 Handoff Phase</h4>
                  <select
                    value={formData.handoff_model || ''}
                    onChange={(e) => setFormData({ ...formData, handoff_model: e.target.value })}
                    className="w-full px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-purple-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">-- Default Model --</option>
                    {availableModels[selectedCredential].map(model => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                  <p className="text-sm text-purple-700 mt-3 leading-relaxed">Creates handoff documentation</p>
                </div>
              </div>
            )}

            {loadingModels && selectedCredential && (
              <div className="text-center py-4">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="text-base text-gray-600 dark:text-gray-400 mt-3 font-medium">Loading available models...</p>
              </div>
            )}
          </div>
        )}

        {/* Submit Button */}
        <div className="flex gap-4">
          <button
            type="submit"
            disabled={loading || (credentials.length === 0 && !globalConfig)}
            className="flex-1 px-6 py-4 text-lg bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed font-semibold shadow-md hover:shadow-lg"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-3">
                <svg
                  className="animate-spin h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Creating Project...
              </span>
            ) : (
              'Create Project'
            )}
          </button>
          <button
            type="button"
            onClick={() => navigate('/projects')}
            className="px-6 py-4 text-lg bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-semibold"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateProjectPage;
