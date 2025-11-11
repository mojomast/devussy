/**
 * API client for project template management
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface ModelConfig {
  provider_credential_id: string;
  model_name: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
}

export interface StageConfig {
  stage: 'design' | 'devplan' | 'handoff';
  llm_config: ModelConfig;
  enabled?: boolean;
  timeout?: number;
  max_retries?: number;
}

export interface ProjectTemplate {
  id: string;
  name: string;
  description: string;
  llm_config?: ModelConfig;
  stage_overrides: Record<string, StageConfig>;
  created_at: string;
  created_from_project_id?: string;
  usage_count: number;
  last_used_at?: string;
  tags: string[];
}

export interface CreateTemplateRequest {
  name: string;
  description: string;
  llm_config?: ModelConfig;
  stage_overrides?: Record<string, StageConfig>;
  tags?: string[];
}

export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  llm_config?: ModelConfig;
  stage_overrides?: Record<string, StageConfig>;
  tags?: string[];
}

export const templatesApi = {
  /**
   * Create a new project template
   */
  createTemplate: async (request: CreateTemplateRequest): Promise<ProjectTemplate> => {
    const response = await axios.post(`${API_BASE_URL}/api/templates`, request);
    return response.data;
  },

  /**
   * List all project templates
   */
  listTemplates: async (): Promise<ProjectTemplate[]> => {
    const response = await axios.get(`${API_BASE_URL}/api/templates`);
    return response.data;
  },

  /**
   * Get a specific template by ID
   */
  getTemplate: async (templateId: string): Promise<ProjectTemplate> => {
    const response = await axios.get(`${API_BASE_URL}/api/templates/${templateId}`);
    return response.data;
  },

  /**
   * Update an existing template
   */
  updateTemplate: async (
    templateId: string,
    request: UpdateTemplateRequest
  ): Promise<ProjectTemplate> => {
    const response = await axios.put(`${API_BASE_URL}/api/templates/${templateId}`, request);
    return response.data;
  },

  /**
   * Delete a template
   */
  deleteTemplate: async (templateId: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/templates/${templateId}`);
  },

  /**
   * Mark a template as used (increments usage count)
   */
  useTemplate: async (templateId: string): Promise<ProjectTemplate> => {
    const response = await axios.post(`${API_BASE_URL}/api/templates/${templateId}/use`);
    return response.data;
  },

  /**
   * Create a template from an existing project
   */
  createTemplateFromProject: async (
    projectId: string,
    request: CreateTemplateRequest
  ): Promise<ProjectTemplate> => {
    const response = await axios.post(
      `${API_BASE_URL}/api/templates/from-project/${projectId}`,
      request
    );
    return response.data;
  },

  /**
   * Export a template as JSON
   */
  exportTemplate: async (templateId: string): Promise<Blob> => {
    const response = await axios.get(`${API_BASE_URL}/api/templates/${templateId}/export`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Import a template from JSON file
   */
  importTemplate: async (file: File): Promise<ProjectTemplate> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_BASE_URL}/api/templates/import`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};
