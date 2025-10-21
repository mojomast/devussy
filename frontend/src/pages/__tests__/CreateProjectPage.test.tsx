import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import CreateProjectPage from '../CreateProjectPage';
import { projectsApi, ProjectStatus } from '../../services/projectsApi';
import { configApi, GlobalConfig } from '../../services/configApi';

// Mock the APIs
vi.mock('../../services/projectsApi', () => ({
  projectsApi: {
    createProject: vi.fn(),
  },
  ProjectStatus: {
    PENDING: 'pending',
    RUNNING: 'running',
    COMPLETED: 'completed',
    FAILED: 'failed',
    CANCELLED: 'cancelled',
  },
}));

vi.mock('../../services/configApi', () => ({
  configApi: {
    getGlobalConfig: vi.fn(),
  },
  ProviderType: {
    OPENAI: 'openai',
    ANTHROPIC: 'anthropic',
    GOOGLE: 'google',
    AZURE_OPENAI: 'azure_openai',
    GENERIC: 'generic',
    REQUESTY: 'requesty',
  },
}));

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    promise: vi.fn((promise, _options) => promise),
    error: vi.fn(),
    success: vi.fn(),
  },
}));

const mockGlobalConfig: GlobalConfig = {
  id: 'global-1',
  default_model_config: {
    provider_credential_id: 'cred-1',
    model_name: 'gpt-4',
    temperature: 0.7,
    max_tokens: 4000,
  },
  stage_overrides: {},
  retry_initial_delay: 1,
  retry_max_delay: 30,
  retry_exponential_base: 2,
  max_concurrent_requests: 3,
  output_dir: './output',
  enable_git: false,
  enable_streaming: true,
};

const mockProject = {
  id: '123',
  name: 'Test Project',
  description: 'A test project',
  status: 'pending' as ProjectStatus,
  progress: 0,
  current_stage: undefined,
  created_at: '2025-10-21T10:00:00Z',
  updated_at: '2025-10-21T10:00:00Z',
  completed_at: undefined,
  output_dir: '/output/123',
  files: {},
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('CreateProjectPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the form with all fields', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/project description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/enable git integration/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/enable streaming/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create project/i })).toBeInTheDocument();
    });
  });

  it('should load and display global config status', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByText(/configuration active/i)).toBeInTheDocument();
      expect(screen.getByText(/using global configuration/i)).toBeInTheDocument();
    });
  });

  it('should show warning when no global config exists', async () => {
    vi.mocked(configApi.getGlobalConfig).mockRejectedValue(new Error('Not found'));

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByText(/no configuration found/i)).toBeInTheDocument();
      expect(screen.getByText(/please set up your api credentials/i)).toBeInTheDocument();
    });
  });

  it('should disable submit button when no config exists', async () => {
    vi.mocked(configApi.getGlobalConfig).mockRejectedValue(new Error('Not found'));

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /create project/i });
      expect(submitButton).toBeDisabled();
    });
  });

  it('should update form fields when user types', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/project name/i) as HTMLInputElement;
    const descInput = screen.getByLabelText(/project description/i) as HTMLTextAreaElement;

    fireEvent.change(nameInput, { target: { value: 'My New Project' } });
    fireEvent.change(descInput, { target: { value: 'A great description' } });

    expect(nameInput.value).toBe('My New Project');
    expect(descInput.value).toBe('A great description');
  });

  it('should toggle checkboxes correctly', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/enable git integration/i)).toBeInTheDocument();
    });

    const gitCheckbox = screen.getByLabelText(/enable git integration/i) as HTMLInputElement;
    const streamingCheckbox = screen.getByLabelText(/enable streaming/i) as HTMLInputElement;

    expect(gitCheckbox.checked).toBe(false);
    expect(streamingCheckbox.checked).toBe(true); // Default is true

    fireEvent.click(gitCheckbox);
    expect(gitCheckbox.checked).toBe(true);

    fireEvent.click(streamingCheckbox);
    expect(streamingCheckbox.checked).toBe(false);
  });

  it('should validate name field is required', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create project/i })).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/project name/i) as HTMLInputElement;
    expect(nameInput).toHaveAttribute('required');
    expect(projectsApi.createProject).not.toHaveBeenCalled();
  });

  it('should validate description field is required', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    });

    const descInput = screen.getByLabelText(/project description/i) as HTMLTextAreaElement;
    expect(descInput).toHaveAttribute('required');
  });

  it('should create project successfully with valid data', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);
    vi.mocked(projectsApi.createProject).mockResolvedValue(mockProject);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/project name/i);
    const descInput = screen.getByLabelText(/project description/i);

    fireEvent.change(nameInput, { target: { value: 'Test Project' } });
    fireEvent.change(descInput, { target: { value: 'A test description' } });

    const submitButton = screen.getByRole('button', { name: /create project/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(projectsApi.createProject).toHaveBeenCalledWith({
        name: 'Test Project',
        description: 'A test description',
        options: {
          enable_git: false,
          enable_streaming: true,
        },
      });
    });
  });

  it('should navigate to project detail page after successful creation', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);
    vi.mocked(projectsApi.createProject).mockResolvedValue(mockProject);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/project name/i);
    const descInput = screen.getByLabelText(/project description/i);

    fireEvent.change(nameInput, { target: { value: 'Test Project' } });
    fireEvent.change(descInput, { target: { value: 'A test description' } });

    const submitButton = screen.getByRole('button', { name: /create project/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/projects/123');
    }, { timeout: 3000 });
  });

  it('should show loading state during submission', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);
    vi.mocked(projectsApi.createProject).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockProject), 100))
    );

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/project name/i);
    const descInput = screen.getByLabelText(/project description/i);

    fireEvent.change(nameInput, { target: { value: 'Test Project' } });
    fireEvent.change(descInput, { target: { value: 'A test description' } });

    const submitButton = screen.getByRole('button', { name: /create project/i });
    fireEvent.click(submitButton);

    // Should show loading state
    expect(screen.getByText(/creating project/i)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  it('should display error message when creation fails', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);
    vi.mocked(projectsApi.createProject).mockRejectedValue({
      response: { data: { detail: 'Failed to create project' } },
    });

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/project name/i);
    const descInput = screen.getByLabelText(/project description/i);

    fireEvent.change(nameInput, { target: { value: 'Test Project' } });
    fireEvent.change(descInput, { target: { value: 'A test description' } });

    const submitButton = screen.getByRole('button', { name: /create project/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/failed to create project/i)).toBeInTheDocument();
    });

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('should handle cancel button click', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockNavigate).toHaveBeenCalledWith('/projects');
  });

  it('should include options in create request when checkboxes are changed', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);
    vi.mocked(projectsApi.createProject).mockResolvedValue(mockProject);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/project name/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/project name/i);
    const descInput = screen.getByLabelText(/project description/i);
    const gitCheckbox = screen.getByLabelText(/enable git integration/i);
    const streamingCheckbox = screen.getByLabelText(/enable streaming/i);

    fireEvent.change(nameInput, { target: { value: 'Test Project' } });
    fireEvent.change(descInput, { target: { value: 'A test description' } });
    fireEvent.click(gitCheckbox); // Enable git
    fireEvent.click(streamingCheckbox); // Disable streaming

    const submitButton = screen.getByRole('button', { name: /create project/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(projectsApi.createProject).toHaveBeenCalledWith({
        name: 'Test Project',
        description: 'A test description',
        options: {
          enable_git: true,
          enable_streaming: false,
        },
      });
    });
  });

  it('should render settings link in warning message', async () => {
    vi.mocked(configApi.getGlobalConfig).mockRejectedValue(new Error('Not found'));

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      const settingsLinks = screen.getAllByRole('link', { name: /settings/i });
      expect(settingsLinks.length).toBeGreaterThan(0);
      expect(settingsLinks[0]).toHaveAttribute('href', '/settings');
    });
  });

  it('should render settings link in info message', async () => {
    vi.mocked(configApi.getGlobalConfig).mockResolvedValue(mockGlobalConfig);

    renderWithRouter(<CreateProjectPage />);

    await waitFor(() => {
      const settingsLinks = screen.getAllByRole('link', { name: /settings/i });
      expect(settingsLinks.length).toBeGreaterThan(0);
      expect(settingsLinks[0]).toHaveAttribute('href', '/settings');
    });
  });
});
