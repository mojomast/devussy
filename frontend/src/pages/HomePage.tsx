import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi, ProjectResponse } from '../services/projectsApi';
import { configApi, ProviderCredentials } from '../services/configApi';

const HomePage: React.FC = () => {
  const [recentProjects, setRecentProjects] = useState<ProjectResponse[]>([]);
  const [allProjects, setAllProjects] = useState<ProjectResponse[]>([]);
  const [credentials, setCredentials] = useState<ProviderCredentials[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [projectsData, allProjectsData, credentialsData] = await Promise.all([
        projectsApi.listProjects(undefined, 3, 0),
        projectsApi.listProjects(undefined),
        configApi.listCredentials(),
      ]);
      setRecentProjects(projectsData.projects);
      setAllProjects(allProjectsData.projects);
      setCredentials(credentialsData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const hasCredentials = credentials.length > 0;

  // Calculate statistics
  const stats = {
    total: allProjects.length,
    completed: allProjects.filter((p) => p.status === 'completed').length,
    running: allProjects.filter((p) => p.status === 'running').length,
    failed: allProjects.filter((p) => p.status === 'failed').length,
    cancelled: allProjects.filter((p) => p.status === 'cancelled').length,
  };

  const successRate = stats.total > 0
    ? ((stats.completed / (stats.total - stats.running)) * 100).toFixed(1)
    : '0';


  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <h1 className="text-6xl font-bold text-gray-900 dark:text-white mb-4">🎯 DevUssY</h1>
        <p className="text-2xl text-gray-600 dark:text-gray-300 mb-2">AI-Powered Development Plan Orchestrator</p>
        <p className="text-gray-500 dark:text-gray-400 mb-8">
          Generate comprehensive project documentation with multi-stage AI pipeline
        </p>

        <div className="flex gap-4 justify-center">
          <Link
            to="/create"
            className="px-8 py-4 bg-blue-600 text-white text-lg rounded-lg hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
          >
            🚀 Create New Project
          </Link>
          <Link
            to="/projects"
            className="px-8 py-4 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-lg rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors border-2 border-gray-200 dark:border-gray-700"
          >
            📁 View All Projects
          </Link>
        </div>
      </div>

      {/* Configuration Status */}
      {!loading && !hasCredentials && (
        <div className="mb-12 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border-2 border-yellow-300 dark:border-yellow-700 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <svg
              className="w-8 h-8 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-1"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-yellow-900 dark:text-yellow-200 mb-2">⚠️ Setup Required</h3>
              <p className="text-yellow-800 dark:text-yellow-300 mb-4">
                Before you can create projects, you need to configure your API credentials.
              </p>
              <Link
                to="/settings"
                className="inline-block px-6 py-3 bg-yellow-600 dark:bg-yellow-700 text-white font-medium rounded-lg hover:bg-yellow-700 dark:hover:bg-yellow-600 transition-colors"
              >
                Go to Settings →
              </Link>
            </div>
          </div>
        </div>
      )}

      {hasCredentials && (
        <div className="mb-12 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-green-800 dark:text-green-300">
              ✓ Configuration ready! You have {credentials.length} API credential
              {credentials.length !== 1 ? 's' : ''} configured.
            </p>
          </div>
        </div>
      )}

      {/* Analytics/Statistics */}
      {!loading && stats.total > 0 && (
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">📊 Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {/* Total Projects */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 transition-colors">
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-1">{stats.total}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Projects</div>
            </div>

            {/* Completed */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 transition-colors">
              <div className="text-3xl font-bold text-green-600 dark:text-green-400 mb-1">{stats.completed}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Completed</div>
            </div>

            {/* Running */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 transition-colors">
              <div className="text-3xl font-bold text-blue-500 dark:text-blue-300 mb-1">{stats.running}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Running</div>
            </div>

            {/* Failed */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 transition-colors">
              <div className="text-3xl font-bold text-red-600 dark:text-red-400 mb-1">{stats.failed}</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Failed</div>
            </div>

            {/* Success Rate */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 transition-colors">
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-1">{successRate}%</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Success Rate</div>
            </div>
          </div>
        </div>
      )}

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 transition-colors">
          <div className="text-4xl mb-4">🎨</div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Design Stage</h3>
          <p className="text-gray-600 dark:text-gray-400">
            Generate architectural designs and system specifications based on your project
            description.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 transition-colors">
          <div className="text-4xl mb-4">📋</div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">DevPlan Stage</h3>
          <p className="text-gray-600 dark:text-gray-400">
            Create detailed development plans with tasks, timelines, and technical requirements.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 transition-colors">
          <div className="text-4xl mb-4">🤝</div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Handoff Stage</h3>
          <p className="text-gray-600 dark:text-gray-400">
            Generate comprehensive handoff documentation for seamless team transitions.
          </p>
        </div>
      </div>

      {/* Recent Projects */}
      {!loading && recentProjects.length > 0 && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Recent Projects</h2>
            <Link to="/projects" className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium">
              View All →
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {recentProjects.map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-lg transition-all"
              >
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">{project.name}</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-2">{project.description}</p>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                  <span
                    className={`px-2 py-1 text-xs rounded-full capitalize ${
                      project.status === 'completed'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                        : project.status === 'running'
                        ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300'
                        : project.status === 'failed'
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                    }`}
                  >
                    {project.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Quick Links */}
      <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-6 transition-colors">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">📚 Documentation</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Learn how to configure multi-LLM setups and advanced features.
          </p>
          <a
            href="https://github.com/yourusername/devussy"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
          >
            Read the Docs →
          </a>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-700 rounded-lg p-6 transition-colors">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">⚙️ Settings</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Configure API credentials, default models, and pipeline settings.
          </p>
          <Link
            to="/settings"
            className="text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium"
          >
            Open Settings →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
