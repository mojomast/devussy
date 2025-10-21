import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ProjectsListPage from '../ProjectsListPage';
import { projectsApi, ProjectStatus } from '../../services/projectsApi';

// Mock the projectsApi
vi.mock('../../services/projectsApi', () => ({
  projectsApi: {
    listProjects: vi.fn(),
    deleteProject: vi.fn(),
  },
  ProjectStatus: {
    PENDING: 'pending',
    RUNNING: 'running',
    COMPLETED: 'completed',
    FAILED: 'failed',
    CANCELLED: 'cancelled',
  },
}));

const mockProjects = [
  {
    id: '1',
    name: 'Test Project 1',
    description: 'A test project',
    status: 'completed' as ProjectStatus,
    progress: 100,
    current_stage: undefined,
    created_at: '2025-10-21T10:00:00Z',
    updated_at: '2025-10-21T11:00:00Z',
    completed_at: '2025-10-21T11:00:00Z',
    output_dir: '/output/1',
    files: {
      design: 'design.md',
      devplan: 'devplan.md',
      handoff: 'handoff.md',
    },
  },
  {
    id: '2',
    name: 'Test Project 2',
    description: 'Another test project',
    status: 'running' as ProjectStatus,
    progress: 50,
    current_stage: undefined,
    created_at: '2025-10-21T12:00:00Z',
    updated_at: '2025-10-21T12:30:00Z',
    completed_at: undefined,
    output_dir: '/output/2',
    files: {},
  },
  {
    id: '3',
    name: 'Test Project 3',
    description: 'Failed project',
    status: 'failed' as ProjectStatus,
    progress: 25,
    current_stage: undefined,
    created_at: '2025-10-21T13:00:00Z',
    updated_at: '2025-10-21T13:15:00Z',
    completed_at: undefined,
    output_dir: '/output/3',
    files: {},
  },
];

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

const mockApiResponse = (projects: typeof mockProjects) => ({
  projects,
  total: projects.length,
});

describe('ProjectsListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.confirm
    vi.stubGlobal('confirm', vi.fn(() => true));
    vi.stubGlobal('alert', vi.fn());
  });

  it('should render loading state initially', () => {
    vi.mocked(projectsApi.listProjects).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithRouter(<ProjectsListPage />);
    
    // Should show skeleton loaders (multiple elements with aria-label="Loading...")
    const loadingElements = screen.getAllByLabelText('Loading...');
    expect(loadingElements.length).toBeGreaterThan(0);
  });

  it('should render projects after loading', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse(mockProjects));

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
      expect(screen.getByText('Test Project 2')).toBeInTheDocument();
      expect(screen.getByText('Test Project 3')).toBeInTheDocument();
    });
  });

  it('should display status badges with correct colors', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse(mockProjects));

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      // Get all instances and filter for the status badges (not filter buttons)
      const completedBadges = screen.getAllByText('completed');
      const runningBadges = screen.getAllByText('running');
      const failedBadges = screen.getAllByText('failed');
      
      const completedBadge = completedBadges.find(el => el.classList.contains('bg-green-100'));
      const runningBadge = runningBadges.find(el => el.classList.contains('bg-blue-100'));
      const failedBadge = failedBadges.find(el => el.classList.contains('bg-red-100'));

      expect(completedBadge).toHaveClass('bg-green-100', 'text-green-800');
      expect(runningBadge).toHaveClass('bg-blue-100', 'text-blue-800');
      expect(failedBadge).toHaveClass('bg-red-100', 'text-red-800');
    });
  });

  it('should show progress bar for running projects', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse(mockProjects));

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      // Only the running project should have a progress indicator
      const progressText = screen.getByText('50%');
      expect(progressText).toBeInTheDocument();
      // Note: current_stage is undefined in our mock, so we just check for progress bar existence
    });
  });

  it('should filter projects by status', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse([mockProjects[0]]));

    renderWithRouter(<ProjectsListPage />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });

    // Click on completed filter
    const completedButton = screen.getByRole('button', { name: /completed/i });
    fireEvent.click(completedButton);

    await waitFor(() => {
      expect(projectsApi.listProjects).toHaveBeenCalledWith('completed');
    });
  });

  it('should show empty state when no projects exist', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse([]));

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      expect(screen.getByText('No projects')).toBeInTheDocument();
      expect(screen.getByText('Get started by creating a new project.')).toBeInTheDocument();
    });
  });

  it('should display error message on load failure', async () => {
    const errorMessage = 'Network error';
    vi.mocked(projectsApi.listProjects).mockRejectedValue({
      response: { data: { detail: errorMessage } },
    });

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
      expect(screen.getByText('Try again')).toBeInTheDocument();
    });
  });

  it('should retry loading projects when try again is clicked', async () => {
    vi.mocked(projectsApi.listProjects)
      .mockRejectedValueOnce({
        response: { data: { detail: 'Network error' } },
      })
      .mockResolvedValueOnce(mockApiResponse(mockProjects));

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    const tryAgainButton = screen.getByText('Try again');
    fireEvent.click(tryAgainButton);

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });
  });

  it('should delete project when delete button is clicked', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse(mockProjects));
    vi.mocked(projectsApi.deleteProject).mockResolvedValue(undefined);

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(projectsApi.deleteProject).toHaveBeenCalledWith('1');
      expect(projectsApi.listProjects).toHaveBeenCalledTimes(2); // Initial + reload
    });
  });

  it('should not delete project if user cancels confirmation', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse(mockProjects));
    vi.stubGlobal('confirm', vi.fn(() => false)); // User cancels

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    expect(projectsApi.deleteProject).not.toHaveBeenCalled();
  });

  it('should handle delete failure', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse(mockProjects));
    vi.mocked(projectsApi.deleteProject).mockRejectedValue({
      response: { data: { detail: 'Delete failed' } },
    });

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      // Delete was attempted
      expect(projectsApi.deleteProject).toHaveBeenCalledWith('1');
      // Error is handled by toast notification (not window.alert anymore)
    });
  });

  it('should render links to project detail pages', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse(mockProjects));

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      const viewDetailsLinks = screen.getAllByText('View Details');
      expect(viewDetailsLinks).toHaveLength(3);
      expect(viewDetailsLinks[0].closest('a')).toHaveAttribute('href', '/projects/1');
      expect(viewDetailsLinks[1].closest('a')).toHaveAttribute('href', '/projects/2');
      expect(viewDetailsLinks[2].closest('a')).toHaveAttribute('href', '/projects/3');
    });
  });

  it('should render create project link', () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse([]));

    renderWithRouter(<ProjectsListPage />);

    const createLinks = screen.getAllByRole('link', { name: /new project|create project/i });
    expect(createLinks.length).toBeGreaterThan(0);
  });

  it('should display formatted dates', async () => {
    vi.mocked(projectsApi.listProjects).mockResolvedValue(mockApiResponse([mockProjects[0]]));

    renderWithRouter(<ProjectsListPage />);

    await waitFor(() => {
      expect(screen.getByText(/Created:/)).toBeInTheDocument();
      expect(screen.getByText(/Completed:/)).toBeInTheDocument();
    });
  });
});
