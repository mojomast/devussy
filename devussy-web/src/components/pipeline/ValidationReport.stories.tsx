import type { Meta, StoryObj } from '@storybook/react';
import { ValidationReport, ValidationBadge, ValidationReportData, SanityReviewResult } from './ValidationReport';

const meta: Meta<typeof ValidationReport> = {
  title: 'Pipeline/ValidationReport',
  component: ValidationReport,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ValidationReport>;

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
      message: 'Contradictory requirements detected in authentication section',
      location: 'section 2.1',
      suggestion: 'Clarify whether JWT or session-based auth should be used',
      auto_correctable: true,
    },
    {
      check_name: 'completeness',
      severity: 'warning',
      message: 'Missing deployment section for production environment',
      auto_correctable: true,
    },
    {
      check_name: 'scope_alignment',
      severity: 'info',
      message: 'Consider adding monitoring for production readiness',
      auto_correctable: false,
    },
  ],
  checks_passed: ['hallucination_detection', 'over_engineering_detection'],
  checks_failed: ['consistency', 'completeness', 'scope_alignment'],
  auto_correctable_count: 2,
  manual_review_required: false,
};

const severeReport: ValidationReportData = {
  is_valid: false,
  issues: [
    {
      check_name: 'hallucination_detection',
      severity: 'error',
      message: 'Referenced non-existent package "react-super-auth-v5"',
      suggestion: 'Use well-known package like "next-auth" or "passport"',
      auto_correctable: false,
    },
    {
      check_name: 'over_engineering_detection',
      severity: 'error',
      message: 'Microservices architecture is overkill for MVP scope',
      suggestion: 'Start with monolith, split later if needed',
      auto_correctable: false,
    },
    {
      check_name: 'consistency',
      severity: 'error',
      message: 'TypeScript mentioned but JavaScript files in structure',
      auto_correctable: true,
    },
  ],
  checks_passed: ['completeness'],
  checks_failed: ['consistency', 'hallucination_detection', 'over_engineering_detection', 'scope_alignment'],
  auto_correctable_count: 1,
  manual_review_required: true,
};

const sanityReview: SanityReviewResult = {
  is_sane: true,
  confidence: 0.85,
  issues_found: ['Minor terminology inconsistency between sections'],
  suggestions: ['Consider standardizing API naming conventions', 'Add error handling patterns'],
  overall_assessment: 'The design is well-structured and appropriate for the project scope. Minor improvements suggested for consistency.',
};

const failedSanityReview: SanityReviewResult = {
  is_sane: false,
  confidence: 0.42,
  issues_found: [
    'Design complexity exceeds stated requirements',
    'Multiple contradictory decisions in architecture section',
    'Missing critical security considerations',
  ],
  suggestions: [
    'Simplify the architecture to match MVP scope',
    'Resolve auth method contradiction',
    'Add security section covering data protection',
  ],
  overall_assessment: 'The design requires significant revision before proceeding. Multiple fundamental issues need resolution.',
};

export const Valid: Story = {
  args: {
    report: validReport,
    showDetails: true,
  },
};

export const Invalid: Story = {
  args: {
    report: invalidReport,
    showDetails: true,
    onRequestCorrection: () => console.log('Correction requested'),
  },
};

export const SevereIssues: Story = {
  args: {
    report: severeReport,
    showDetails: true,
    onRequestCorrection: () => console.log('Correction requested'),
  },
};

export const WithSanityReview: Story = {
  args: {
    report: validReport,
    sanityReview: sanityReview,
    showDetails: true,
  },
};

export const WithFailedSanityReview: Story = {
  args: {
    report: invalidReport,
    sanityReview: failedSanityReview,
    showDetails: true,
    onRequestCorrection: () => console.log('Correction requested'),
  },
};

export const WithoutDetails: Story = {
  args: {
    report: invalidReport,
    showDetails: false,
  },
};

export const Loading: Story = {
  args: {
    report: validReport,
    isLoading: true,
  },
};

// Badge stories
export const ValidBadge: StoryObj<typeof ValidationBadge> = {
  render: () => <ValidationBadge report={validReport} />,
};

export const InvalidBadge: StoryObj<typeof ValidationBadge> = {
  render: () => <ValidationBadge report={invalidReport} />,
};

export const SevereBadge: StoryObj<typeof ValidationBadge> = {
  render: () => <ValidationBadge report={severeReport} />,
};
