import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { 
  CorrectionTimeline, 
  CorrectionBadge, 
  CorrectionHistory,
  CorrectionIteration 
} from '../CorrectionTimeline';

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  History: () => <span data-testid="history-icon">History</span>,
  CheckCircle2: () => <span data-testid="check-circle-icon">CheckCircle2</span>,
  XCircle: () => <span data-testid="x-circle-icon">XCircle</span>,
  AlertTriangle: () => <span data-testid="alert-triangle-icon">AlertTriangle</span>,
  ArrowRight: () => <span data-testid="arrow-right-icon">ArrowRight</span>,
  RefreshCw: () => <span data-testid="refresh-icon">RefreshCw</span>,
  Clock: () => <span data-testid="clock-icon">Clock</span>,
  Wrench: () => <span data-testid="wrench-icon">Wrench</span>,
  Target: () => <span data-testid="target-icon">Target</span>,
  Loader2: () => <span data-testid="loader-icon">Loader2</span>,
}));

describe('CorrectionTimeline', () => {
  const successHistory: CorrectionHistory = {
    total_iterations: 2,
    max_iterations: 3,
    final_status: 'success',
    iterations: [
      {
        iteration_number: 1,
        timestamp: '2025-11-26T12:00:00Z',
        issues_addressed: ['consistency', 'completeness'],
        corrections_applied: ['Fixed contradictory requirements', 'Added deployment section'],
        validation_result: { is_valid: false, remaining_issues: 1 },
        llm_review_confidence: 0.7,
        duration_ms: 1500,
      },
      {
        iteration_number: 2,
        timestamp: '2025-11-26T12:00:02Z',
        issues_addressed: ['scope_alignment'],
        corrections_applied: ['Aligned scope with requirements'],
        validation_result: { is_valid: true, remaining_issues: 0 },
        llm_review_confidence: 0.95,
        duration_ms: 1200,
      },
    ],
    started_at: '2025-11-26T12:00:00Z',
    completed_at: '2025-11-26T12:00:03Z',
  };

  const maxIterationsHistory: CorrectionHistory = {
    total_iterations: 3,
    max_iterations: 3,
    final_status: 'max_iterations_reached',
    iterations: [
      {
        iteration_number: 1,
        issues_addressed: ['consistency'],
        corrections_applied: ['Attempt 1'],
        validation_result: { is_valid: false, remaining_issues: 2 },
        llm_review_confidence: 0.5,
        duration_ms: 1000,
      },
      {
        iteration_number: 2,
        issues_addressed: ['consistency'],
        corrections_applied: ['Attempt 2'],
        validation_result: { is_valid: false, remaining_issues: 1 },
        llm_review_confidence: 0.6,
        duration_ms: 1000,
      },
      {
        iteration_number: 3,
        issues_addressed: ['consistency'],
        corrections_applied: ['Attempt 3'],
        validation_result: { is_valid: false, remaining_issues: 1 },
        llm_review_confidence: 0.65,
        duration_ms: 1000,
      },
    ],
  };

  const manualReviewHistory: CorrectionHistory = {
    total_iterations: 1,
    max_iterations: 3,
    final_status: 'manual_review_required',
    iterations: [
      {
        iteration_number: 1,
        issues_addressed: [],
        corrections_applied: [],
        validation_result: { is_valid: false, remaining_issues: 3 },
        llm_review_confidence: 0.3,
        duration_ms: 500,
      },
    ],
  };

  const emptyHistory: CorrectionHistory = {
    total_iterations: 0,
    max_iterations: 3,
    final_status: 'success',
    iterations: [],
  };

  describe('header rendering', () => {
    it('renders correction timeline title', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('Correction Timeline')).toBeInTheDocument();
    });

    it('shows iteration count', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('2 of 3 iterations')).toBeInTheDocument();
    });

    it('shows success status', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('Completed Successfully')).toBeInTheDocument();
    });

    it('shows max iterations reached status', () => {
      render(<CorrectionTimeline history={maxIterationsHistory} />);
      expect(screen.getByText('Max Iterations Reached')).toBeInTheDocument();
    });

    it('shows manual review required status', () => {
      render(<CorrectionTimeline history={manualReviewHistory} />);
      expect(screen.getByText('Manual Review Required')).toBeInTheDocument();
    });

    it('shows in progress status when running', () => {
      render(<CorrectionTimeline history={successHistory} isRunning={true} />);
      expect(screen.getByText('In Progress')).toBeInTheDocument();
    });
  });

  describe('progress bar', () => {
    it('shows progress label', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('Progress')).toBeInTheDocument();
    });

    it('shows iteration count in progress', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('2 / 3')).toBeInTheDocument();
    });
  });

  describe('iteration nodes', () => {
    it('renders all iterations', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('Iteration 1')).toBeInTheDocument();
      expect(screen.getByText('Iteration 2')).toBeInTheDocument();
    });

    it('shows duration for each iteration', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('1.5s')).toBeInTheDocument();
      expect(screen.getByText('1.2s')).toBeInTheDocument();
    });

    it('shows confidence for each iteration', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('70% confidence')).toBeInTheDocument();
      expect(screen.getByText('95% confidence')).toBeInTheDocument();
    });

    it('shows issues addressed when showDetails is true', () => {
      render(<CorrectionTimeline history={successHistory} showDetails={true} />);
      // Multiple "Issues Addressed:" labels exist (one per iteration)
      expect(screen.getAllByText('Issues Addressed:').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('consistency')).toBeInTheDocument();
      expect(screen.getByText('completeness')).toBeInTheDocument();
    });

    it('shows corrections applied when showDetails is true', () => {
      render(<CorrectionTimeline history={successHistory} showDetails={true} />);
      // Multiple "Corrections Applied:" labels exist (one per iteration)
      expect(screen.getAllByText('Corrections Applied:').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Fixed contradictory requirements')).toBeInTheDocument();
      expect(screen.getByText('Added deployment section')).toBeInTheDocument();
    });

    it('shows validation result for each iteration', () => {
      render(<CorrectionTimeline history={successHistory} showDetails={true} />);
      expect(screen.getByText('1 issue(s) remaining')).toBeInTheDocument();
      expect(screen.getByText('All checks passed')).toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('shows no corrections needed message', () => {
      render(<CorrectionTimeline history={emptyHistory} />);
      expect(screen.getByText('No corrections needed')).toBeInTheDocument();
      expect(screen.getByText('Design passed all validation checks')).toBeInTheDocument();
    });
  });

  describe('summary section', () => {
    it('shows total iterations', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('Iterations')).toBeInTheDocument();
    });

    it('shows total corrections count', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('Corrections')).toBeInTheDocument();
    });

    it('shows final confidence', () => {
      render(<CorrectionTimeline history={successHistory} />);
      expect(screen.getByText('Final Confidence')).toBeInTheDocument();
    });
  });

  describe('running state', () => {
    it('highlights current iteration when running', () => {
      render(
        <CorrectionTimeline 
          history={successHistory} 
          isRunning={true} 
          currentIteration={1} 
        />
      );
      // Should show loader for current iteration (tested via icon mock)
      expect(screen.getByTestId('loader-icon')).toBeInTheDocument();
    });
  });
});

describe('CorrectionBadge', () => {
  const successHistory: CorrectionHistory = {
    total_iterations: 2,
    max_iterations: 3,
    final_status: 'success',
    iterations: [],
  };

  const inProgressHistory: CorrectionHistory = {
    total_iterations: 1,
    max_iterations: 3,
    final_status: 'in_progress',
    iterations: [],
  };

  const maxIterationsHistory: CorrectionHistory = {
    total_iterations: 3,
    max_iterations: 3,
    final_status: 'max_iterations_reached',
    iterations: [],
  };

  it('shows iteration count', () => {
    render(<CorrectionBadge history={successHistory} />);
    expect(screen.getByText('2/3')).toBeInTheDocument();
  });

  it('shows completed status for success', () => {
    render(<CorrectionBadge history={successHistory} />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('shows in progress status when running', () => {
    render(<CorrectionBadge history={inProgressHistory} isRunning={true} />);
    expect(screen.getByText('In')).toBeInTheDocument();
  });

  it('shows max status when max iterations reached', () => {
    render(<CorrectionBadge history={maxIterationsHistory} />);
    expect(screen.getByText('Max')).toBeInTheDocument();
  });

  it('applies success styling', () => {
    const { container } = render(<CorrectionBadge history={successHistory} />);
    expect(container.firstChild).toHaveClass('bg-green-500/10');
  });

  it('applies in progress styling when running', () => {
    const { container } = render(<CorrectionBadge history={inProgressHistory} isRunning={true} />);
    expect(container.firstChild).toHaveClass('bg-blue-500/10');
  });

  it('applies warning styling for max iterations', () => {
    const { container } = render(<CorrectionBadge history={maxIterationsHistory} />);
    expect(container.firstChild).toHaveClass('bg-yellow-500/10');
  });
});
