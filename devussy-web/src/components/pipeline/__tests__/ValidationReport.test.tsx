import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { 
  ValidationReport, 
  ValidationBadge, 
  ValidationReportData, 
  ValidationIssue,
  SanityReviewResult 
} from '../ValidationReport';

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Shield: () => <span data-testid="shield-icon">Shield</span>,
  CheckCircle2: () => <span data-testid="check-circle-icon">CheckCircle2</span>,
  XCircle: () => <span data-testid="x-circle-icon">XCircle</span>,
  AlertTriangle: () => <span data-testid="alert-triangle-icon">AlertTriangle</span>,
  FileCheck: () => <span data-testid="file-check-icon">FileCheck</span>,
  Scale: () => <span data-testid="scale-icon">Scale</span>,
  Search: () => <span data-testid="search-icon">Search</span>,
  Lightbulb: () => <span data-testid="lightbulb-icon">Lightbulb</span>,
  Target: () => <span data-testid="target-icon">Target</span>,
  Wrench: () => <span data-testid="wrench-icon">Wrench</span>,
}));

describe('ValidationReport', () => {
  const validReport: ValidationReportData = {
    is_valid: true,
    issues: [],
    checks_passed: ['consistency', 'completeness', 'scope_alignment', 'hallucination_detection', 'over_engineering_detection'],
    checks_failed: [],
    auto_correctable_count: 0,
    manual_review_required: false,
    timestamp: '2025-11-26T12:00:00Z',
  };

  const invalidReport: ValidationReportData = {
    is_valid: false,
    issues: [
      {
        check_name: 'consistency',
        severity: 'error',
        message: 'Contradictory requirements detected',
        location: 'section 2.1',
        suggestion: 'Clarify the authentication requirements',
        auto_correctable: true,
      },
      {
        check_name: 'completeness',
        severity: 'warning',
        message: 'Missing deployment section',
        auto_correctable: true,
      },
      {
        check_name: 'scope_alignment',
        severity: 'info',
        message: 'Consider adding monitoring for production',
        auto_correctable: false,
      },
    ],
    checks_passed: ['hallucination_detection', 'over_engineering_detection'],
    checks_failed: ['consistency', 'completeness', 'scope_alignment'],
    auto_correctable_count: 2,
    manual_review_required: false,
  };

  const sanityReview: SanityReviewResult = {
    is_sane: true,
    confidence: 0.85,
    issues_found: ['Minor terminology inconsistency'],
    suggestions: ['Consider standardizing API naming conventions'],
    overall_assessment: 'The design is well-structured and appropriate for the project scope.',
  };

  describe('rendering valid report', () => {
    it('shows valid status when report is valid', () => {
      render(<ValidationReport report={validReport} />);
      
      expect(screen.getByText('Valid')).toBeInTheDocument();
      expect(screen.getByText('All validation checks passed')).toBeInTheDocument();
    });

    it('shows all passed checks', () => {
      render(<ValidationReport report={validReport} />);
      
      expect(screen.getByText('Consistency')).toBeInTheDocument();
      expect(screen.getByText('Completeness')).toBeInTheDocument();
      expect(screen.getByText('Scope Alignment')).toBeInTheDocument();
      expect(screen.getByText('Hallucination Detection')).toBeInTheDocument();
      expect(screen.getByText('Over Engineering Detection')).toBeInTheDocument();
    });

    it('does not show auto-correct button when report is valid', () => {
      render(<ValidationReport report={validReport} onRequestCorrection={() => {}} />);
      
      expect(screen.queryByText(/Auto-correct/)).not.toBeInTheDocument();
    });
  });

  describe('rendering invalid report', () => {
    it('shows needs review status when report is invalid', () => {
      render(<ValidationReport report={invalidReport} />);
      
      expect(screen.getByText('Needs Review')).toBeInTheDocument();
      expect(screen.getByText('3 check(s) need attention')).toBeInTheDocument();
    });

    it('shows issue counts by severity', () => {
      render(<ValidationReport report={invalidReport} />);
      
      expect(screen.getByText('1 error')).toBeInTheDocument();
      expect(screen.getByText('1 warning')).toBeInTheDocument();
      expect(screen.getByText('1 info')).toBeInTheDocument();
    });

    it('shows issue details when showDetails is true', () => {
      render(<ValidationReport report={invalidReport} showDetails={true} />);
      
      expect(screen.getByText('Issues (3)')).toBeInTheDocument();
      expect(screen.getByText('Contradictory requirements detected')).toBeInTheDocument();
      expect(screen.getByText('Missing deployment section')).toBeInTheDocument();
      expect(screen.getByText('Consider adding monitoring for production')).toBeInTheDocument();
    });

    it('shows issue location when provided', () => {
      render(<ValidationReport report={invalidReport} showDetails={true} />);
      
      expect(screen.getByText('Location: section 2.1')).toBeInTheDocument();
    });

    it('shows suggestion when provided', () => {
      render(<ValidationReport report={invalidReport} showDetails={true} />);
      
      expect(screen.getByText(/Clarify the authentication requirements/)).toBeInTheDocument();
    });

    it('shows auto-fix badge for auto-correctable issues', () => {
      render(<ValidationReport report={invalidReport} showDetails={true} />);
      
      // Two issues are auto-correctable
      const autoFixBadges = screen.getAllByText('Auto-fix');
      expect(autoFixBadges).toHaveLength(2);
    });

    it('hides issue details when showDetails is false', () => {
      render(<ValidationReport report={invalidReport} showDetails={false} />);
      
      expect(screen.queryByText('Issues (3)')).not.toBeInTheDocument();
      expect(screen.queryByText('Contradictory requirements detected')).not.toBeInTheDocument();
    });
  });

  describe('auto-correct button', () => {
    it('shows auto-correct button when issues are auto-correctable', () => {
      render(<ValidationReport report={invalidReport} onRequestCorrection={() => {}} />);
      
      expect(screen.getByText('Auto-correct (2)')).toBeInTheDocument();
    });

    it('calls onRequestCorrection when clicked', async () => {
      const user = userEvent.setup();
      const onRequestCorrection = jest.fn();
      render(<ValidationReport report={invalidReport} onRequestCorrection={onRequestCorrection} />);
      
      await user.click(screen.getByText('Auto-correct (2)'));
      expect(onRequestCorrection).toHaveBeenCalledTimes(1);
    });

    it('does not show when onRequestCorrection is not provided', () => {
      render(<ValidationReport report={invalidReport} />);
      
      expect(screen.queryByText(/Auto-correct/)).not.toBeInTheDocument();
    });
  });

  describe('manual review indicator', () => {
    it('shows manual review badge when required', () => {
      const manualReviewReport = { ...invalidReport, manual_review_required: true };
      render(<ValidationReport report={manualReviewReport} />);
      
      expect(screen.getByText('Manual review required')).toBeInTheDocument();
    });

    it('does not show manual review badge when not required', () => {
      render(<ValidationReport report={invalidReport} />);
      
      expect(screen.queryByText('Manual review required')).not.toBeInTheDocument();
    });
  });

  describe('loading state', () => {
    it('shows loading skeleton when isLoading is true', () => {
      render(<ValidationReport report={validReport} isLoading={true} />);
      
      expect(screen.queryByText('Design Validation')).not.toBeInTheDocument();
      expect(screen.queryByText('Valid')).not.toBeInTheDocument();
    });
  });

  describe('LLM sanity review section', () => {
    it('shows sanity review when provided', () => {
      render(<ValidationReport report={validReport} sanityReview={sanityReview} />);
      
      expect(screen.getByText('LLM Sanity Review')).toBeInTheDocument();
      expect(screen.getByText('Sane')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('shows overall assessment', () => {
      render(<ValidationReport report={validReport} sanityReview={sanityReview} />);
      
      expect(screen.getByText(sanityReview.overall_assessment)).toBeInTheDocument();
    });

    it('shows issues found', () => {
      render(<ValidationReport report={validReport} sanityReview={sanityReview} />);
      
      expect(screen.getByText('Issues Found:')).toBeInTheDocument();
      expect(screen.getByText('Minor terminology inconsistency')).toBeInTheDocument();
    });

    it('shows suggestions', () => {
      render(<ValidationReport report={validReport} sanityReview={sanityReview} />);
      
      expect(screen.getByText('Suggestions:')).toBeInTheDocument();
      expect(screen.getByText('Consider standardizing API naming conventions')).toBeInTheDocument();
    });

    it('shows needs review when sanity check fails', () => {
      const failedSanityReview = { ...sanityReview, is_sane: false, confidence: 0.4 };
      render(<ValidationReport report={validReport} sanityReview={failedSanityReview} />);
      
      expect(screen.getByText('Needs Review')).toBeInTheDocument();
      expect(screen.getByText('40%')).toBeInTheDocument();
    });

    it('does not show sanity review when not provided', () => {
      render(<ValidationReport report={validReport} />);
      
      expect(screen.queryByText('LLM Sanity Review')).not.toBeInTheDocument();
    });
  });
});

describe('ValidationBadge', () => {
  const validReport: ValidationReportData = {
    is_valid: true,
    issues: [],
    checks_passed: ['consistency', 'completeness'],
    checks_failed: [],
    auto_correctable_count: 0,
    manual_review_required: false,
  };

  const invalidReport: ValidationReportData = {
    is_valid: false,
    issues: [
      { check_name: 'consistency', severity: 'error', message: 'Error', auto_correctable: false },
      { check_name: 'completeness', severity: 'error', message: 'Error', auto_correctable: false },
      { check_name: 'scope', severity: 'warning', message: 'Warning', auto_correctable: false },
    ],
    checks_passed: [],
    checks_failed: ['consistency', 'completeness', 'scope'],
    auto_correctable_count: 0,
    manual_review_required: false,
  };

  it('shows valid status for valid report', () => {
    render(<ValidationBadge report={validReport} />);
    expect(screen.getByText('Valid')).toBeInTheDocument();
  });

  it('shows issues status for invalid report', () => {
    render(<ValidationBadge report={invalidReport} />);
    expect(screen.getByText('Issues')).toBeInTheDocument();
  });

  it('shows error and warning counts for invalid report', () => {
    render(<ValidationBadge report={invalidReport} />);
    expect(screen.getByText('2E')).toBeInTheDocument();
    expect(screen.getByText('1W')).toBeInTheDocument();
  });

  it('applies correct styling for valid report', () => {
    const { container } = render(<ValidationBadge report={validReport} />);
    expect(container.firstChild).toHaveClass('bg-green-500/10');
  });

  it('applies correct styling for invalid report', () => {
    const { container } = render(<ValidationBadge report={invalidReport} />);
    expect(container.firstChild).toHaveClass('bg-yellow-500/10');
  });
});
