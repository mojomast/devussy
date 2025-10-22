import React, { useState, useEffect } from 'react';
import { configApi, GlobalConfig, ProviderCredentials, PipelineStage } from '../../services/configApi';

const GlobalConfigTab: React.FC = () => {
  const [config, setConfig] = useState<GlobalConfig | null>(null);
  const [credentials, setCredentials] = useState<ProviderCredentials[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [globalConfig, creds] = await Promise.all([
        configApi.getGlobalConfig(),
        configApi.listCredentials()
      ]);
      setConfig(globalConfig);
      setCredentials(creds);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!config) return;
    
    try {
      setSaving(true);
      await configApi.updateGlobalConfig(config);
      setSuccessMessage('✅ Configuration saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const updateDefaultModel = (field: string, value: any) => {
    if (!config) return;
    setConfig({
      ...config,
      default_model_config: {
        ...config.default_model_config,
        [field]: value
      }
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading configuration...</p>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-md">
        No global configuration found. Using defaults.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Global Configuration</h2>
        <p className="mt-1 text-sm text-gray-600">
          Set default model configurations that apply to all new projects
        </p>
      </div>

      {/* Success Message */}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
          {successMessage}
        </div>
      )}

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

      {/* Default Model Configuration */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Default Model Settings</h3>
        
        <div className="space-y-4">
          {/* Credential Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Credential *
            </label>
            <select
              value={config.default_model_config.provider_credential_id}
              onChange={(e) => updateDefaultModel('provider_credential_id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a credential...</option>
              {credentials.map((cred) => (
                <option key={cred.id} value={cred.id}>
                  {cred.name} ({cred.provider})
                </option>
              ))}
            </select>
            {credentials.length === 0 && (
              <p className="mt-1 text-xs text-orange-600">
                ⚠️ No credentials configured. Add one in the Credentials tab first.
              </p>
            )}
          </div>

          {/* Model Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Model Name *
            </label>
            <input
              type="text"
              value={config.default_model_config.model_name}
              onChange={(e) => updateDefaultModel('model_name', e.target.value)}
              placeholder="e.g., gpt-4, claude-3-opus-20240229"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Common models: gpt-4-turbo, gpt-3.5-turbo, claude-3-opus-20240229, claude-3-sonnet-20240229
            </p>
          </div>

          {/* Temperature */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Temperature: {config.default_model_config.temperature?.toFixed(2) ?? '0.70'}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={config.default_model_config.temperature ?? 0.7}
              onChange={(e) => updateDefaultModel('temperature', parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0 (Deterministic)</span>
              <span>1 (Balanced)</span>
              <span>2 (Creative)</span>
            </div>
          </div>

          {/* Max Tokens */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Tokens
            </label>
            <input
              type="number"
              min="1"
              max="128000"
              value={config.default_model_config.max_tokens ?? 4096}
              onChange={(e) => updateDefaultModel('max_tokens', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Maximum tokens to generate in response (typical: 4096-8192)
            </p>
          </div>

          {/* Advanced Parameters */}
          <details className="border border-gray-200 rounded-lg p-4">
            <summary className="cursor-pointer font-medium text-gray-700">
              Advanced Parameters (Optional)
            </summary>
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Top P
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={config.default_model_config.top_p ?? ''}
                    onChange={(e) => updateDefaultModel('top_p', e.target.value ? parseFloat(e.target.value) : null)}
                    placeholder="Default (usually 1.0)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Frequency Penalty
                  </label>
                  <input
                    type="number"
                    min="-2"
                    max="2"
                    step="0.1"
                    value={config.default_model_config.frequency_penalty ?? ''}
                    onChange={(e) => updateDefaultModel('frequency_penalty', e.target.value ? parseFloat(e.target.value) : null)}
                    placeholder="Default (0)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Presence Penalty
                </label>
                <input
                  type="number"
                  min="-2"
                  max="2"
                  step="0.1"
                  value={config.default_model_config.presence_penalty ?? ''}
                  onChange={(e) => updateDefaultModel('presence_penalty', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="Default (0)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </details>
        </div>
      </div>

      {/* Stage-Specific Model Configuration */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Pipeline Stage Configuration
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Assign different models to different stages (Design → DevPlan → Handoff).
          Leave empty to use the default model for all stages.
        </p>
        
        <div className="space-y-6">
          {/* Design Stage */}
          <div className="border-l-4 border-blue-500 pl-4">
            <h4 className="font-medium text-gray-900 mb-3">🎨 Design Stage</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model (optional)
                </label>
                <input
                  type="text"
                  placeholder="Use default model"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  placeholder="0.7"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* DevPlan Stage */}
          <div className="border-l-4 border-green-500 pl-4">
            <h4 className="font-medium text-gray-900 mb-3">📋 DevPlan Stage</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model (optional)
                </label>
                <input
                  type="text"
                  placeholder="Use default model"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  placeholder="0.7"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Handoff Stage */}
          <div className="border-l-4 border-purple-500 pl-4">
            <h4 className="font-medium text-gray-900 mb-3">🚀 Handoff Stage</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model (optional)
                </label>
                <input
                  type="text"
                  placeholder="Use default model"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  placeholder="0.7"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* System Settings */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">System Settings</h3>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Concurrent Requests
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={config.max_concurrent_requests}
                onChange={(e) => setConfig({ ...config, max_concurrent_requests: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Output Directory
              </label>
              <input
                type="text"
                value={config.output_dir}
                onChange={(e) => setConfig({ ...config, output_dir: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex gap-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={config.enable_git}
                onChange={(e) => setConfig({ ...config, enable_git: e.target.checked })}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Enable Git integration</span>
            </label>
            
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={config.enable_streaming}
                onChange={(e) => setConfig({ ...config, enable_streaming: e.target.checked })}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Enable streaming responses</span>
            </label>
          </div>
        </div>
      </div>

      {/* Retry Configuration */}
      <details className="bg-white border border-gray-200 rounded-lg p-6">
        <summary className="cursor-pointer font-medium text-gray-900">
          Retry & Error Handling
        </summary>
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Initial Delay (seconds)
            </label>
            <input
              type="number"
              min="0.1"
              step="0.1"
              value={config.retry_initial_delay}
              onChange={(e) => setConfig({ ...config, retry_initial_delay: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Delay (seconds)
            </label>
            <input
              type="number"
              min="1"
              value={config.retry_max_delay}
              onChange={(e) => setConfig({ ...config, retry_max_delay: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Exponential Base
            </label>
            <input
              type="number"
              min="1"
              step="0.1"
              value={config.retry_exponential_base}
              onChange={(e) => setConfig({ ...config, retry_exponential_base: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </details>

      {/* Save Button */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          onClick={loadData}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
        >
          Reset to Saved
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? '⏳ Saving...' : '💾 Save Configuration'}
        </button>
      </div>
    </div>
  );
};

export default GlobalConfigTab;
