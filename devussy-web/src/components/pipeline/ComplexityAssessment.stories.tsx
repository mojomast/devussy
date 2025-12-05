import type { Meta, StoryObj } from '@storybook/react';
import { ComplexityAssessment, ComplexityBadge, ComplexityProfile } from './ComplexityAssessment';

const meta: Meta<typeof ComplexityAssessment> = {
  title: 'Pipeline/ComplexityAssessment',
  component: ComplexityAssessment,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ComplexityAssessment>;

const minimalProfile: ComplexityProfile = {
  project_type_bucket: 'cli_tool',
  technical_complexity_bucket: 'simple_crud',
  integration_bucket: 'standalone',
  team_size_bucket: 'solo',
  score: 1.5,
  estimated_phase_count: 3,
  depth_level: 'minimal',
  confidence: 0.95,
};

const standardProfile: ComplexityProfile = {
  project_type_bucket: 'web_app',
  technical_complexity_bucket: 'auth_db',
  integration_bucket: '3_5_services',
  team_size_bucket: '2_3',
  score: 6.0,
  estimated_phase_count: 5,
  depth_level: 'standard',
  confidence: 0.82,
};

const detailedProfile: ComplexityProfile = {
  project_type_bucket: 'saas',
  technical_complexity_bucket: 'multi_region',
  integration_bucket: '6_plus_services',
  team_size_bucket: '7_plus',
  score: 18.0,
  estimated_phase_count: 13,
  depth_level: 'detailed',
  confidence: 0.65,
};

export const Minimal: Story = {
  args: {
    profile: minimalProfile,
    showDetails: true,
  },
};

export const Standard: Story = {
  args: {
    profile: standardProfile,
    showDetails: true,
  },
};

export const Detailed: Story = {
  args: {
    profile: detailedProfile,
    showDetails: true,
  },
};

export const WithoutDetails: Story = {
  args: {
    profile: standardProfile,
    showDetails: false,
  },
};

export const Loading: Story = {
  args: {
    profile: standardProfile,
    isLoading: true,
  },
};

export const WithRefresh: Story = {
  args: {
    profile: standardProfile,
    showDetails: true,
    onRefresh: () => console.log('Refresh clicked'),
  },
};

export const LowConfidence: Story = {
  args: {
    profile: {
      ...standardProfile,
      confidence: 0.45,
    },
    showDetails: true,
  },
};

// Badge stories
export const MinimalBadge: StoryObj<typeof ComplexityBadge> = {
  render: () => <ComplexityBadge profile={minimalProfile} />,
};

export const StandardBadge: StoryObj<typeof ComplexityBadge> = {
  render: () => <ComplexityBadge profile={standardProfile} />,
};

export const DetailedBadge: StoryObj<typeof ComplexityBadge> = {
  render: () => <ComplexityBadge profile={detailedProfile} />,
};
