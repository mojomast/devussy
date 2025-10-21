import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import JSZip from 'jszip';
import toast from 'react-hot-toast';
import { projectsApi, ProjectResponse, ProjectStatus } from '../services/projectsApi';
import { templatesApi } from '../services/templatesApi';
import FileViewer from '../components/FileViewer';

const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [templateTags, setTemplateTags] = useState('');
  const [savingTemplate, setSavingTemplate] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!projectId) return;
    loadProject();
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [projectId]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const loadProject = async () => {
    if (!projectId) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await projectsApi.getProject(projectId);
      setProject(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    if (!projectId) return;

    try {
      const ws = projectsApi.createWebSocket(projectId);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        addLog('Connected to project stream');
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addLog('Connection error occurred');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        addLog('Disconnected from project stream');
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
    }
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'progress':
        setProject((prev) =>
          prev ? { ...prev, progress: message.data.progress } : prev
        );
        break;
      case 'stage':
        setProject((prev) =>
          prev ? { ...prev, current_stage: message.data.stage } : prev
        );
        addLog(`Stage: ${message.data.stage}`);
        break;
      case 'output':
        addLog(message.data.text);
        break;
      case 'error':
        addLog(`Error: ${message.data.error}`);
        setProject((prev) =>
          prev ? { ...prev, status: ProjectStatus.FAILED, error: message.data.error } : prev
        );
        break;
      case 'complete':
        addLog('Project completed successfully!');
        setProject((prev) =>
          prev ? { ...prev, status: ProjectStatus.COMPLETED, progress: 100 } : prev
        );
        loadProject(); // Reload to get file paths
        break;
    }
  };

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, `[${timestamp}] ${message}`]);
  };

  const handleCancel = async () => {
    if (!projectId || !confirm('Are you sure you want to cancel this project?')) return;

    try {
      await projectsApi.cancelProject(projectId);
      loadProject();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to cancel project');
    }
  };

  const handleDelete = async () => {
    if (!projectId || !confirm('Are you sure you want to delete this project?')) return;

    try {
      await projectsApi.deleteProject(projectId);
      navigate('/projects');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete project');
    }
  };

  const loadFileContent = async (filename: string) => {
    if (!projectId) return;

    try {
      const content = await projectsApi.getFileContent(projectId, filename);
      setFileContent(content);
      setSelectedFile(filename);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to load file content');
    }
  };

  const handleDownloadAll = async () => {
    if (!project || !projectId) return;

    try {
      const zip = new JSZip();
      const fileEntries = Object.entries(project.files);

      if (fileEntries.length === 0) {
        alert('No files to download');
        return;
      }

      // Fetch all files and add to ZIP
      for (const [key, filepath] of fileEntries) {
        try {
          const content = await projectsApi.getFileContent(projectId, filepath as string);
          const filename = (filepath as string).split('/').pop() || `${key}.md`;
          zip.file(filename, content);
        } catch (err) {
          console.error(`Failed to load ${key}:`, err);
        }
      }

      // Generate and download ZIP
      const blob = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project.name.replace(/\s+/g, '_')}_files.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Failed to download files:', err);
      alert('Failed to download files');
    }
  };

  const handleSaveAsTemplate = async () => {
    if (!projectId || !templateName.trim()) {
      toast.error('Template name is required');
      return;
    }

    setSavingTemplate(true);
    try {
      const tags = templateTags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      await templatesApi.createTemplateFromProject(projectId, {
        name: templateName.trim(),
        description: templateDescription.trim(),
        tags,
      });

      toast.success('Template saved successfully!');
      setShowTemplateModal(false);
      setTemplateName('');
      setTemplateDescription('');
      setTemplateTags('');
    } catch (err: any) {
      console.error('Failed to save template:', err);
      toast.error(err.response?.data?.detail || 'Failed to save template');
    } finally {
      setSavingTemplate(false);
    }
  };

  const getStatusColor = (status: ProjectStatus) => {
    switch (status) {
      case ProjectStatus.COMPLETED:
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300';
      case ProjectStatus.RUNNING:
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300';
      case ProjectStatus.FAILED:
        return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300';
      case ProjectStatus.CANCELLED:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
      default:
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300';
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-red-800 dark:text-red-300 mb-2">Error</h2>
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <div className="mt-4 flex gap-4">
            <button
              onClick={loadProject}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Try Again
            </button>
            <Link
              to="/projects"
              className="px-4 py-2 bg-gray-600 dark:bg-gray-700 text-white rounded hover:bg-gray-700 dark:hover:bg-gray-600"
            >
              Back to Projects
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!project) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <Link to="/projects" className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300">
            ← Back to Projects
          </Link>
        </div>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">{project.name}</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">{project.description}</p>
          </div>
          <span
            className={`px-3 py-1 text-sm font-medium rounded-full capitalize ${getStatusColor(
              project.status
            )}`}
          >
            {project.status}
          </span>
        </div>
      </div>

      {/* Progress Section */}
      {project.status === ProjectStatus.RUNNING && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6 transition-colors">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Progress</h2>
            <span className="text-sm text-gray-600 dark:text-gray-400">{project.current_stage}</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 mb-2">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all flex items-center justify-end pr-2"
              style={{ width: `${project.progress}%` }}
            >
              <span className="text-xs text-white font-medium">
                {Math.round(project.progress)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {project.error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-red-800 dark:text-red-300 mb-2">Error</h3>
          <p className="text-red-600 dark:text-red-400">{project.error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Files Section */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 transition-colors">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Generated Files</h2>
          {Object.entries(project.files).length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-sm">No files generated yet</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(project.files).map(([key, filepath]) => (
                <button
                  key={key}
                  onClick={() => loadFileContent(filepath as string)}
                  className={`w-full text-left px-4 py-2 rounded border transition-colors ${
                    selectedFile === filepath
                      ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-600'
                      : 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'
                  }`}
                >
                  <div className="font-medium text-gray-900 dark:text-white capitalize">{key}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{filepath}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Actions Section */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 transition-colors">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Actions</h2>
          <div className="space-y-2">
            {project.status === ProjectStatus.RUNNING && (
              <button
                onClick={handleCancel}
                className="w-full px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
              >
                Cancel Project
              </button>
            )}
            {project.status === ProjectStatus.COMPLETED && (
              <button
                onClick={() => setShowTemplateModal(true)}
                className="w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                Save as Template
              </button>
            )}
            {Object.entries(project.files).length > 0 && (
              <button
                onClick={handleDownloadAll}
                className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download All Files (ZIP)
              </button>
            )}
            <button
              onClick={loadProject}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Refresh
            </button>
            <button
              onClick={handleDelete}
              className="w-full px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Delete Project
            </button>
          </div>
        </div>
      </div>

      {/* Logs Section */}
      <div className="mt-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 transition-colors">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Live Logs</h2>
        <div className="bg-gray-900 dark:bg-black text-gray-100 dark:text-gray-300 rounded p-4 h-64 overflow-y-auto font-mono text-sm border border-gray-700">
          {logs.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400">No logs yet...</p>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="mb-1">
                {log}
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Save as Template Modal */}
      {showTemplateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Save as Template
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Save this project's configuration as a reusable template for future projects.
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Template Name *
                </label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="e.g., E-commerce Setup"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={templateDescription}
                  onChange={(e) => setTemplateDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Describe when to use this template..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={templateTags}
                  onChange={(e) => setTemplateTags(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="e.g., web, api, python"
                />
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={handleSaveAsTemplate}
                disabled={savingTemplate || !templateName.trim()}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {savingTemplate ? 'Saving...' : 'Save Template'}
              </button>
              <button
                onClick={() => {
                  setShowTemplateModal(false);
                  setTemplateName('');
                  setTemplateDescription('');
                  setTemplateTags('');
                }}
                disabled={savingTemplate}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* File Viewer */}
      {selectedFile && fileContent && (
        <FileViewer
          filename={selectedFile.split('/').pop() || selectedFile}
          content={fileContent}
          onClose={() => {
            setSelectedFile(null);
            setFileContent('');
          }}
        />
      )}
    </div>
  );
};

export default ProjectDetailPage;
