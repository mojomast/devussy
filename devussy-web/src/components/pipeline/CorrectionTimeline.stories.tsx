import type { Meta, StoryObj } from '@storybook/react';
import { CorrectionTimeline, CorrectionBadge, CorrectionHistory } from './CorrectionTimeline';

const meta: Meta<typeof CorrectionTimeline> = {
  title: 'Pipeline/CorrectionTimeline',
  component: CorrectionTimeline,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof CorrectionTimeline>;

const successHistory: CorrectionHistory = {
  total_iterations: 2,
  max_iterations: 3,
  final_status: 'success',
  iterations: [
    {
      iteration_number: 1,
      timestamp: '2025-11-26T12:00:00Z',
      issues_addressed: ['consistency', 'completeness'],
      corrections_applied: [
        'Resolved JWT vs session auth contradiction',
        'Added deployment section with Docker configuration',
      ],
      validation_result: { is_valid: false, remaining_issues: 1 },
      llm_review_confidence: 0.72,
      duration_ms: 1500,
    },
    {
      iteration_number: 2,
      timestamp: '2025-11-26T12:00:02Z',
      issues_addressed: ['scope_alignment'],
      corrections_applied: ['Aligned architecture complexity with MVP scope'],
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
      corrections_applied: ['Attempt to resolve auth contradiction'],
      validation_result: { is_valid: false, remaining_issues: 2 },
      llm_review_confidence: 0.5,
      duration_ms: 1000,
    },
    {
      iteration_number: 2,
      issues_addressed: ['consistency', 'completeness'],
      corrections_applied: ['Further refinement of auth section', 'Added basic deployment notes'],
      validation_result: { is_valid: false, remaining_issues: 1 },
      llm_review_confidence: 0.6,
      duration_ms: 1100,
    },
    {
      iteration_number: 3,
      issues_addressed: ['scope_alignment'],
      corrections_applied: ['Attempted scope reduction'],
      validation_result: { is_valid: false, remaining_issues: 1 },
      llm_review_confidence: 0.68,
      duration_ms: 950,
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
      validation_result: { is_valid: false, remaining_issues: 4 },
      llm_review_confidence: 0.25,
      duration_ms: 800,
    },
  ],
};

const inProgressHistory: CorrectionHistory = {
  total_iterations: 1,
  max_iterations: 3,
  final_status: 'in_progress',
  iterations: [
    {
      iteration_number: 1,
      issues_addressed: ['consistency'],
      corrections_applied: ['Resolved auth contradiction'],
      validation_result: { is_valid: false, remaining_issues: 2 },
      llm_review_confidence: 0.65,
      duration_ms: 1200,
    },
  ],
};

const emptyHistory: CorrectionHistory = {
  total_iterations: 0,
  max_iterations: 3,
  final_status: 'success',
  iterations: [],
};

export const Success: Story = {
  args: {
    history: successHistory,
    showDetails: true,
  },
};

export const MaxIterationsReached: Story = {
  args: {
    history: maxIterationsHistory,
    showDetails: true,
  },
};

export const ManualReviewRequired: Story = {
  args: {
    history: manualReviewHistory,
    showDetails: true,
  },
};

export const InProgress: Story = {
  args: {
    history: inProgressHistory,
    isRunning: true,
    currentIteration: 2,
    showDetails: true,
  },
};

export const NoCorrectionsNeeded: Story = {
  args: {
    history: emptyHistory,
    showDetails: true,
  },
};

export const WithoutDetails: Story = {
  args: {
    history: successHistory,
    showDetails: false,
  },
};

// Badge stories
export const SuccessBadge: StoryObj<typeof CorrectionBadge> = {
  render: () => <CorrectionBadge history={successHistory} />,
};

export const MaxIterationsBadge: StoryObj<typeof CorrectionBadge> = {
  render: () => <CorrectionBadge history={maxIterationsHistory} />,
};

export const ManualReviewBadge: StoryObj<typeof CorrectionBadge> = {
  render: () => <CorrectionBadge history={manualReviewHistory} />,
};

export const InProgressBadge: StoryObj<typeof CorrectionBadge> = {
  render: () => <CorrectionBadge history={inProgressHistory} isRunning={true} />,
};
