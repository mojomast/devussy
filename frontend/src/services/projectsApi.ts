/**
 * Projects API Client
 * Handles all API calls for project management
 */

import axios from 'axios';

const API_BASE = '/api/projects';

// Types matching backend Pydantic models
export enum ProjectStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  AWAITING_USER_INPUT = 'awaiting_user_input', // NEW
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum PipelineStage {
  DESIGN = 'design',
  BASIC_DEVPLAN = 'basic_devplan',
  DETAILED_DEVPLAN = 'detailed_devplan',
  REFINED_DEVPLAN = 'refined_devplan', // NEW
  HANDOFF = 'handoff'
}

export interface ProjectCreateRequest {
  name: string;
  description: string;
  config_id?: string;
  options?: {
    enable_git?: boolean;
    enable_streaming?: boolean;
    output_dir?: string;
  };
  // LLM Configuration
  credential_id?: string;  // Phase 20: Credential selection
  provider?: string;
  model?: string;
  // Per-stage model configuration
  design_model?: string;
  devplan_model?: string;
  handoff_model?: string;
}

export interface ProjectResponse {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  current_stage?: PipelineStage;
  progress: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error?: string;
  output_dir: string;
  config_id?: string;
  files: {
    design?: string;
    devplan?: string;
    handoff?: string;
  };
  // NEW: Iteration fields
  current_iteration?: number;
  awaiting_user_input?: boolean;
  iteration_prompt?: string;
  current_stage_output?: string;
}

export interface ProjectListResponse {
  projects: ProjectResponse[];
  total: number;
}

export interface WebSocketMessage {
  type: 'progress' | 'stage' | 'output' | 'error' | 'complete' | 'awaiting_input' | 'regenerated';
  data: any;
}

// NEW: Iteration types
export interface IterationRequest {
  feedback: string;
  regenerate?: boolean;
}

export interface StageApproval {
  approved?: boolean;
  notes?: string;
}

/**
 * Projects API Client
 */
export const projectsApi = {
  /**
   * Create a new project and start the pipeline
   */
  async createProject(data: ProjectCreateRequest): Promise<ProjectResponse> {
    const response = await axios.post(API_BASE, data);
    return response.data;
  },

  /**
   * List all projects with optional filtering
   */
  async listProjects(
    status?: ProjectStatus,
    limit: number = 50,
    offset: number = 0
  ): Promise<ProjectListResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response = await axios.get(`${API_BASE}?${params.toString()}`);
    return response.data;
  },

  /**
   * Get details for a specific project
   */
  async getProject(projectId: string): Promise<ProjectResponse> {
    const response = await axios.get(`${API_BASE}/${projectId}`);
    return response.data;
  },

  /**
   * Delete a project and its files
   */
  async deleteProject(projectId: string): Promise<void> {
    await axios.delete(`${API_BASE}/${projectId}`);
  },

  /**
   * Cancel a running project
   */
  async cancelProject(projectId: string): Promise<ProjectResponse> {
    const response = await axios.post(`${API_BASE}/${projectId}/cancel`);
    return response.data;
  },

  /**
   * Create a WebSocket connection for real-time project updates
   */
  createWebSocket(projectId: string): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.hostname}:8000/api/ws/projects/${projectId}`;
    return new WebSocket(wsUrl);
  },

  /**
   * Get the content of a generated file
   */
  async getFileContent(projectId: string, filename: string): Promise<string> {
    const response = await axios.get(`${API_BASE}/${projectId}/files/${filename}`);
    return response.data;
  },
  
  // NEW: Iteration support methods
  
  /**
   * Submit feedback to iterate on current stage
   */
  async iterateStage(projectId: string, data: IterationRequest): Promise<ProjectResponse> {
    const response = await axios.post(`${API_BASE}/${projectId}/iterate`, data);
    return response.data;
  },
  
  /**
   * Approve current stage and move to next
   */
  async approveStage(projectId: string, data: StageApproval): Promise<ProjectResponse> {
    const response = await axios.post(`${API_BASE}/${projectId}/approve`, data);
    return response.data;
  }
};

export default projectsApi;
