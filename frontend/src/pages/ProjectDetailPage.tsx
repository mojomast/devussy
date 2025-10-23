import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import JSZip from 'jszip';
import toast from 'react-hot-toast';
import { projectsApi, ProjectResponse, ProjectStatus, PipelineStage } from '../services/projectsApi';
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
  
  // NEW: Iteration state
  const [iterationFeedback, setIterationFeedback] = useState('');
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  
  // NEW: Verbose API logging
  const [apiLogs, setApiLogs] = useState<Array<{
    timestamp: string;
    method: string;
    url: string;
    status?: number;
    request?: any;
    response?: any;
    error?: string;
  }>>([]);
  const apiLogsEndRef = useRef<HTMLDivElement>(null);
  
  const addApiLog = (log: typeof apiLogs[0]) => {
    setApiLogs(prev => [...prev, log]);
    setTimeout(() => apiLogsEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  };

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
    
    const logEntry = {
      timestamp: new Date().toLocaleTimeString(),
      method: 'GET',
      url: `/api/projects/${projectId}`,
    };
    
    try {
      setLoading(true);
      setError(null);
      const data = await projectsApi.getProject(projectId);
      setProject(data);
      addApiLog({ ...logEntry, status: 200, response: data });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to load project';
      setError(errorMsg);
      addApiLog({ 
        ...logEntry, 
        status: err.response?.status || 500, 
        error: errorMsg,
        response: err.response?.data 
      });
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
      case 'awaiting_input':
        setProject((prev) =>
          prev ? { 
            ...prev, 
            status: ProjectStatus.AWAITING_USER_INPUT,
            awaiting_user_input: true,
            iteration_prompt: message.data.prompt
          } : prev
        );
        addLog(`Awaiting user input: ${message.data.prompt}`);
        toast.success('Stage complete! Please review and provide feedback.', { duration: 5000 });
        loadProject(); // Reload to get current_stage_output
        break;
      case 'regenerated':
        addLog(`Stage regenerated (iteration ${message.data.iteration})`);
        toast.success('Content regenerated with your feedback!');
        loadProject();
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
  
  // NEW: Iteration handlers
  const handleApproveStage = async () => {
    if (!projectId) return;
    
    setIsSubmittingFeedback(true);
    try {
      await projectsApi.approveStage(projectId, {
        approved: true,
        notes: iterationFeedback || undefined
      });
      
      toast.success('Stage approved! Moving to next phase...');
      setIterationFeedback('');
      
      // Reload project to see updates
      setTimeout(() => loadProject(), 1000);
    } catch (err: any) {
      console.error('Failed to approve stage:', err);
      toast.error(err.response?.data?.detail || 'Failed to approve stage');
    } finally {
      setIsSubmittingFeedback(false);
    }
  };
  
  const handleRegenerateWithFeedback = async () => {
    if (!projectId) return;
    
    if (!iterationFeedback.trim()) {
      toast.error('Please provide feedback for regeneration');
      return;
    }
    
    setIsSubmittingFeedback(true);
    try {
      await projectsApi.iterateStage(projectId, {
        feedback: iterationFeedback,
        regenerate: true
      });
      
      toast.success('Regenerating with your feedback...');
      setIterationFeedback('');
      
      // Reload project
      setTimeout(() => loadProject(), 1000);
    } catch (err: any) {
      console.error('Failed to iterate:', err);
      toast.error(err.response?.data?.detail || 'Failed to iterate on stage');
    } finally {
      setIsSubmittingFeedback(false);
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

      {/* NEW: Phase Progress Indicator */}
      {project.current_stage && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Pipeline Progress</h2>
          <div className="flex items-center justify-between relative">
            {/* Progress Line */}
            <div className="absolute top-5 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700 -z-10">
              <div
                className="h-full bg-blue-600 transition-all duration-500"
                style={{
                  width: `${
                    project.current_stage === PipelineStage.DESIGN ? '0%' :
                    project.current_stage === PipelineStage.BASIC_DEVPLAN ? '25%' :
                    project.current_stage === PipelineStage.DETAILED_DEVPLAN ? '50%' :
                    project.current_stage === PipelineStage.REFINED_DEVPLAN ? '75%' :
                    project.current_stage === PipelineStage.HANDOFF ? '100%' : '0%'
                  }`
                }}
              />
            </div>

            {/* Stage Dots */}
            {[
              { stage: PipelineStage.DESIGN, label: 'Design', icon: '🎨' },
              { stage: PipelineStage.BASIC_DEVPLAN, label: 'Basic Plan', icon: '📋' },
              { stage: PipelineStage.DETAILED_DEVPLAN, label: 'Detailed Plan', icon: '📝' },
              { stage: PipelineStage.REFINED_DEVPLAN, label: 'Refined Plan', icon: '✨' },
              { stage: PipelineStage.HANDOFF, label: 'Handoff', icon: '🚀' },
            ].map((item) => {
              const isActive = project.current_stage === item.stage;
              const isPast = 
                (item.stage === PipelineStage.DESIGN && project.current_stage !== PipelineStage.DESIGN) ||
                (item.stage === PipelineStage.BASIC_DEVPLAN && [PipelineStage.DETAILED_DEVPLAN, PipelineStage.REFINED_DEVPLAN, PipelineStage.HANDOFF].includes(project.current_stage!)) ||
                (item.stage === PipelineStage.DETAILED_DEVPLAN && [PipelineStage.REFINED_DEVPLAN, PipelineStage.HANDOFF].includes(project.current_stage!)) ||
                (item.stage === PipelineStage.REFINED_DEVPLAN && project.current_stage === PipelineStage.HANDOFF);
              
              return (
                <div key={item.stage} className="flex flex-col items-center relative bg-white dark:bg-gray-800 px-2">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-xl transition-all duration-300 ${
                      isActive
                        ? 'bg-blue-600 ring-4 ring-blue-200 dark:ring-blue-900 scale-110'
                        : isPast
                        ? 'bg-green-600'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    {isPast ? '✓' : item.icon}
                  </div>
                  <span
                    className={`mt-2 text-xs font-medium text-center ${
                      isActive
                        ? 'text-blue-600 dark:text-blue-400 font-bold'
                        : isPast
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    {item.label}
                  </span>
                  {isActive && project.current_iteration !== undefined && project.current_iteration > 0 && (
                    <span className="mt-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded-full">
                      Iter {project.current_iteration}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

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

      {/* NEW: Iteration Feedback Section */}
      {project.status === ProjectStatus.AWAITING_USER_INPUT && project.awaiting_user_input && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border-2 border-yellow-400 dark:border-yellow-600 rounded-lg p-6 mb-6 animate-pulse-slow">
          <div className="flex items-start gap-3 mb-4">
            <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-800 dark:text-yellow-300 text-lg mb-2">
                User Review Required - {project.current_stage?.replace(/_/g, ' ').toUpperCase()}
              </h3>
              <p className="text-yellow-700 dark:text-yellow-400 mb-2">
                {project.iteration_prompt || 'Please review the current stage output and provide feedback.'}
              </p>
              {project.current_iteration !== undefined && project.current_iteration > 0 && (
                <p className="text-sm text-yellow-600 dark:text-yellow-500">
                  Current iteration: {project.current_iteration}
                </p>
              )}
            </div>
          </div>

          {/* Current Stage Output Preview */}
          {project.current_stage_output && (
            <div className="mb-4 bg-white dark:bg-gray-800 border border-yellow-300 dark:border-yellow-700 rounded p-4 max-h-64 overflow-y-auto">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Current Output:</h4>
              <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                {project.current_stage_output.substring(0, 500)}
                {project.current_stage_output.length > 500 && '...\n\n(See full output in files section)'}
              </pre>
            </div>
          )}

          {/* Feedback Textarea */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Your Feedback (optional for approval, required for regeneration):
            </label>
            <textarea
              value={iterationFeedback}
              onChange={(e) => setIterationFeedback(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent"
              placeholder="e.g., 'Add more details about the database schema' or 'Include Redis for caching'"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleApproveStage}
              disabled={isSubmittingFeedback}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              {isSubmittingFeedback ? 'Processing...' : 'Approve & Continue to Next Stage'}
            </button>
            
            <button
              onClick={handleRegenerateWithFeedback}
              disabled={isSubmittingFeedback || !iterationFeedback.trim()}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {isSubmittingFeedback ? 'Processing...' : 'Regenerate with Feedback'}
            </button>
          </div>
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

      {/* Logs Section - Collapsible */}
      <div className="mt-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 transition-colors">
        <details className="group">
          <summary className="text-lg font-semibold text-gray-900 dark:text-white mb-4 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 flex items-center gap-2">
            <span className="group-open:rotate-90 transition-transform">▶</span>
            Live Logs {logs.length > 0 && <span className="text-sm text-gray-500">({logs.length})</span>}
          </summary>
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
        </details>
      </div>

      {/* Verbose API Console */}
      <div className="mt-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 transition-colors">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          API Console (Verbose) 🔍
        </h2>
        <div className="bg-gray-900 dark:bg-black text-gray-100 dark:text-gray-300 rounded p-4 h-96 overflow-y-auto font-mono text-xs border border-gray-700">
          {apiLogs.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400">No API calls yet...</p>
          ) : (
            <div className="space-y-3">
              {apiLogs.map((log, index) => (
                <div key={index} className="border-b border-gray-700 pb-2">
                  {/* Request Header */}
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-gray-400">[{log.timestamp}]</span>
                    <span className="font-bold text-blue-400">{log.method}</span>
                    <span className="text-gray-300">{log.url}</span>
                    {log.status && (
                      <span className={`ml-auto px-2 py-0.5 rounded text-xs font-bold ${
                        log.status >= 400 ? 'bg-red-600 text-white' : 
                        log.status >= 300 ? 'bg-yellow-600 text-white' :
                        'bg-green-600 text-white'
                      }`}>
                        {log.status}
                      </span>
                    )}
                  </div>
                  
                  {/* Request Body */}
                  {log.request && (
                    <details className="ml-4 mt-1">
                      <summary className="text-cyan-400 cursor-pointer hover:text-cyan-300">
                        📤 Request Body
                      </summary>
                      <pre className="text-gray-400 ml-4 mt-1 text-[10px] overflow-x-auto">
                        {JSON.stringify(log.request, null, 2)}
                      </pre>
                    </details>
                  )}
                  
                  {/* Response Body */}
                  {log.response && (
                    <details className="ml-4 mt-1">
                      <summary className="text-green-400 cursor-pointer hover:text-green-300">
                        📥 Response Body
                      </summary>
                      <pre className="text-gray-300 ml-4 mt-1 text-[10px] overflow-x-auto">
                        {JSON.stringify(log.response, null, 2)}
                      </pre>
                    </details>
                  )}
                  
                  {/* Error */}
                  {log.error && (
                    <div className="ml-4 mt-1 text-red-400">
                      ❌ Error: {log.error}
                    </div>
                  )}
                </div>
              ))}
              <div ref={apiLogsEndRef} />
            </div>
          )}
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
