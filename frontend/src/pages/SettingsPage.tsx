import React, { useState } from 'react';
import CredentialsTab from '../components/config/CredentialsTab';
import GlobalConfigTab from '../components/config/GlobalConfigTab';
import PresetsTab from '../components/config/PresetsTab';

type TabName = 'credentials' | 'global' | 'presets';

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabName>('credentials');

  const tabs = [
    { id: 'credentials' as TabName, label: 'API Credentials', icon: '🔑' },
    { id: 'global' as TabName, label: 'Global Configuration', icon: '⚙️' },
    { id: 'presets' as TabName, label: 'Presets', icon: '⭐' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="mt-2 text-gray-600">
            Configure API credentials, model defaults, and presets for your projects
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span className="text-lg">{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'credentials' && <CredentialsTab />}
            {activeTab === 'global' && <GlobalConfigTab />}
            {activeTab === 'presets' && <PresetsTab />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
