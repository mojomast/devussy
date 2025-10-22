/**
 * Configuration API Client
 * Handles all API calls for credential management, global config, and presets
 */

import axios from 'axios';

const API_BASE = '/api/config';

// Types matching backend Pydantic models
export enum ProviderType {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  AZURE_OPENAI = 'azure_openai',
  GENERIC = 'generic',
  REQUESTY = 'requesty'
}

export enum PipelineStage {
  DESIGN = 'DESIGN',
  DEVPLAN = 'DEVPLAN',
  HANDOFF = 'HANDOFF'
}

export interface ProviderCredentials {
  id: string;
  name: string;
  provider: ProviderType;
  api_key_encrypted: string; // Always masked in responses
  api_base?: string;
  organization_id?: string;
  created_at: string;
  last_tested?: string;
  is_valid: boolean;
}

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
  stage: PipelineStage;
  model_config: ModelConfig;
  enabled: boolean;
  timeout: number;
  max_retries: number;
}

export interface GlobalConfig {
  id: string;
  default_model_config: ModelConfig;
  stage_overrides: Record<string, StageConfig>;
  retry_initial_delay: number;
  retry_max_delay: number;
  retry_exponential_base: number;
  max_concurrent_requests: number;
  output_dir: string;
  enable_git: boolean;
  enable_streaming: boolean;
}

export interface ConfigPreset {
  id: string;
  name: string;
  description: string;
  default_model_config: ModelConfig;
  stage_overrides: Record<string, StageConfig>;
}

export interface CreateCredentialRequest {
  name: string;
  provider: ProviderType;
  api_key: string;
  api_base?: string;
  organization_id?: string;
}

export interface UpdateCredentialRequest {
  name?: string;
  api_key?: string;
  api_base?: string;
  organization_id?: string;
}

export interface TestCredentialResponse {
  success: boolean;
  message: string;
  details?: any;
}

/**
 * Configuration API Client
 */
export const configApi = {
  // ============ Credentials Management ============

  /**
   * Create a new credential (API key)
   */
  async createCredential(data: CreateCredentialRequest): Promise<ProviderCredentials> {
    const response = await axios.post(`${API_BASE}/credentials`, data);
    return response.data;
  },

  /**
   * List all credentials (API keys masked)
   */
  async listCredentials(): Promise<ProviderCredentials[]> {
    const response = await axios.get(`${API_BASE}/credentials`);
    return response.data;
  },

  /**
   * Get a specific credential by ID
   */
  async getCredential(id: string): Promise<ProviderCredentials> {
    const response = await axios.get(`${API_BASE}/credentials/${id}`);
    return response.data;
  },

  /**
   * Update a credential
   */
  async updateCredential(id: string, data: UpdateCredentialRequest): Promise<ProviderCredentials> {
    const response = await axios.put(`${API_BASE}/credentials/${id}`, data);
    return response.data;
  },

  /**
   * Delete a credential
   */
  async deleteCredential(id: string): Promise<void> {
    await axios.delete(`${API_BASE}/credentials/${id}`);
  },

  /**
   * Test a credential to verify it works
   */
  async testCredential(id: string): Promise<TestCredentialResponse> {
    const response = await axios.post(`${API_BASE}/credentials/${id}/test`);
    return response.data;
  },

  /**
   * Find credentials by provider type
   */
  async findCredentialsByProvider(provider: ProviderType): Promise<ProviderCredentials[]> {
    const response = await axios.get(`${API_BASE}/credentials/provider/${provider}`);
    return response.data;
  },

  // ============ Global Configuration ============

  /**
   * Get the current global configuration
   */
  async getGlobalConfig(): Promise<GlobalConfig> {
    const response = await axios.get(`${API_BASE}/global`);
    return response.data;
  },

  /**
   * Update the global configuration
   */
  async updateGlobalConfig(config: GlobalConfig): Promise<GlobalConfig> {
    const response = await axios.put(`${API_BASE}/global`, config);
    return response.data;
  },

  // ============ Presets ============

  /**
   * List all available presets
   */
  async listPresets(): Promise<ConfigPreset[]> {
    const response = await axios.get(`${API_BASE}/presets`);
    return response.data;
  },

  /**
   * Get a specific preset by ID
   */
  async getPreset(id: string): Promise<ConfigPreset> {
    const response = await axios.get(`${API_BASE}/presets/${id}`);
    return response.data;
  },

  /**
   * Apply a preset to global configuration
   */
  async applyPreset(presetId: string): Promise<GlobalConfig> {
    const response = await axios.post(`${API_BASE}/presets/apply/${presetId}`);
    return response.data;
  },

  // ============ Project Overrides ============

  /**
   * Get project-specific configuration overrides
   */
  async getProjectConfig(projectId: string): Promise<any> {
    const response = await axios.get(`${API_BASE}/projects/${projectId}`);
    return response.data;
  },

  /**
   * Set project-specific configuration overrides
   */
  async setProjectConfig(projectId: string, config: any): Promise<any> {
    const response = await axios.put(`${API_BASE}/projects/${projectId}`, config);
    return response.data;
  },

  // ============ Model Discovery ============

  /**
   * List available models for a credential
   */
  async listAvailableModels(credentialId: string): Promise<AvailableModel[]> {
    const response = await axios.get(`${API_BASE}/credentials/${credentialId}/models`);
    return response.data.models || [];
  }
};

export interface AvailableModel {
  id: string;
  name: string;
  description: string;
  context_window: number;
}

export default configApi;
