import React, { useState, useEffect } from 'react';
import { configApi, ConfigPreset } from '../../services/configApi';

const PresetsTab: React.FC = () => {
  const [presets, setPresets] = useState<ConfigPreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<ConfigPreset | null>(null);

  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = async () => {
    try {
      setLoading(true);
      const presetsList = await configApi.listPresets();
      setPresets(presetsList);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load presets');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyPreset = async (presetId: string) => {
    if (!confirm('This will update your global configuration. Continue?')) {
      return;
    }

    try {
      setApplying(presetId);
      await configApi.applyPreset(presetId);
      setSuccessMessage('✅ Preset applied successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to apply preset');
    } finally {
      setApplying(null);
    }
  };

  const handleViewDetails = (preset: ConfigPreset) => {
    setSelectedPreset(selectedPreset?.id === preset.id ? null : preset);
  };

  const getPresetIcon = (presetId: string): string => {
    const icons: Record<string, string> = {
      'cost_optimized': '💰',
      'max_quality': '⭐',
      'anthropic_claude': '🧠',
      'fast_turnaround': '⚡',
      'balanced': '⚖️'
    };
    return icons[presetId] || '⚙️';
  };

  const getPresetColor = (presetId: string): string => {
    const colors: Record<string, string> = {
      'cost_optimized': 'green',
      'max_quality': 'blue',
      'anthropic_claude': 'purple',
      'fast_turnaround': 'yellow',
      'balanced': 'gray'
    };
    return colors[presetId] || 'gray';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading presets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Configuration Presets</h2>
        <p className="mt-1 text-sm text-gray-600">
          Quick-start configurations optimized for different use cases
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

      {/* Presets Grid */}
      {presets.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <p className="text-xl mb-2">⚙️</p>
          <p className="text-gray-600">No presets available</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {presets.map((preset) => {
            const color = getPresetColor(preset.id);
            const isSelected = selectedPreset?.id === preset.id;
            
            return (
              <div
                key={preset.id}
                className={`
                  bg-white border-2 rounded-lg p-6 transition-all cursor-pointer
                  ${isSelected ? `border-${color}-500 shadow-lg` : 'border-gray-200 hover:shadow-md'}
                `}
                onClick={() => handleViewDetails(preset)}
              >
                {/* Preset Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{getPresetIcon(preset.id)}</span>
                    <div>
                      <h3 className="font-semibold text-gray-900">{preset.name}</h3>
                      <p className="text-xs text-gray-500 mt-0.5">{preset.id}</p>
                    </div>
                  </div>
                </div>

                {/* Description */}
                <p className="text-sm text-gray-600 mb-4">{preset.description}</p>

                {/* Model Info */}
                <div className="bg-gray-50 rounded-md p-3 mb-4 text-sm">
                  <div className="font-medium text-gray-700 mb-1">Default Model:</div>
                  <code className="text-xs bg-white px-2 py-1 rounded border border-gray-200">
                    {preset.default_model_config.model_name}
                  </code>
                  
                  {Object.keys(preset.stage_overrides || {}).length > 0 && (
                    <div className="mt-2">
                      <div className="font-medium text-gray-700 mb-1">Stage Overrides:</div>
                      <div className="space-y-1">
                        {Object.entries(preset.stage_overrides).map(([stage, config]) => (
                          <div key={stage} className="text-xs">
                            <span className="font-medium">{stage}:</span>{' '}
                            <code className="bg-white px-1.5 py-0.5 rounded border border-gray-200">
                              {config.model_config.model_name}
                            </code>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Details Toggle */}
                {isSelected && (
                  <div className="border-t border-gray-200 pt-4 mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Configuration Details:</h4>
                    <pre className="text-xs bg-gray-900 text-gray-100 p-3 rounded-md overflow-auto max-h-60">
                      {JSON.stringify(preset, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Apply Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleApplyPreset(preset.id);
                  }}
                  disabled={applying === preset.id}
                  className={`
                    w-full px-4 py-2 rounded-md font-medium transition-colors
                    ${applying === preset.id
                      ? 'bg-gray-400 text-white cursor-not-allowed'
                      : `bg-${color}-600 text-white hover:bg-${color}-700`
                    }
                  `}
                  style={{
                    backgroundColor: applying === preset.id ? undefined : 
                      color === 'green' ? '#16a34a' :
                      color === 'blue' ? '#2563eb' :
                      color === 'purple' ? '#9333ea' :
                      color === 'yellow' ? '#ca8a04' : '#6b7280'
                  }}
                  onMouseEnter={(e) => {
                    if (applying !== preset.id) {
                      const bg = 
                        color === 'green' ? '#15803d' :
                        color === 'blue' ? '#1d4ed8' :
                        color === 'purple' ? '#7e22ce' :
                        color === 'yellow' ? '#a16207' : '#4b5563';
                      (e.target as HTMLButtonElement).style.backgroundColor = bg;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (applying !== preset.id) {
                      const bg = 
                        color === 'green' ? '#16a34a' :
                        color === 'blue' ? '#2563eb' :
                        color === 'purple' ? '#9333ea' :
                        color === 'yellow' ? '#ca8a04' : '#6b7280';
                      (e.target as HTMLButtonElement).style.backgroundColor = bg;
                    }
                  }}
                >
                  {applying === preset.id ? '⏳ Applying...' : '✨ Apply This Preset'}
                </button>

                {/* Click to view hint */}
                <p className="text-center text-xs text-gray-400 mt-2">
                  {isSelected ? 'Click again to hide details' : 'Click card to view details'}
                </p>
              </div>
            );
          })}
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex gap-3">
          <span className="text-2xl">💡</span>
          <div className="flex-1">
            <h4 className="font-medium text-blue-900 mb-1">About Presets</h4>
            <p className="text-sm text-blue-700">
              Presets are pre-configured settings optimized for specific use cases. 
              Applying a preset will update your global configuration with the preset's settings. 
              You can always customize the settings afterward in the Global Configuration tab.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PresetsTab;
