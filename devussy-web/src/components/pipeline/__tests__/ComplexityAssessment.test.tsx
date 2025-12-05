import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { ComplexityAssessment, ComplexityBadge, ComplexityProfile } from '../ComplexityAssessment';

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Gauge: () => <span data-testid="gauge-icon">Gauge</span>,
  Layers: () => <span data-testid="layers-icon">Layers</span>,
  Microscope: () => <span data-testid="microscope-icon">Microscope</span>,
  ShieldCheck: () => <span data-testid="shield-check-icon">ShieldCheck</span>,
  AlertTriangle: () => <span data-testid="alert-triangle-icon">AlertTriangle</span>,
  CheckCircle2: () => <span data-testid="check-circle-icon">CheckCircle2</span>,
  Clock: () => <span data-testid="clock-icon">Clock</span>,
  Users: () => <span data-testid="users-icon">Users</span>,
  Boxes: () => <span data-testid="boxes-icon">Boxes</span>,
}));

describe('ComplexityAssessment', () => {
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
    score: 7.5,
    estimated_phase_count: 7,
    depth_level: 'standard',
    confidence: 0.75,
  };

  const detailedProfile: ComplexityProfile = {
    project_type_bucket: 'saas',
    technical_complexity_bucket: 'multi_region',
    integration_bucket: '6_plus_services',
    team_size_bucket: '7_plus',
    score: 18.0,
    estimated_phase_count: 13,
    depth_level: 'detailed',
    confidence: 0.55,
  };

  describe('rendering', () => {
    it('renders complexity score correctly for minimal profile', () => {
      render(<ComplexityAssessment profile={minimalProfile} />);
      
      expect(screen.getByText('1.5')).toBeInTheDocument();
      expect(screen.getByText('/ 20')).toBeInTheDocument();
      expect(screen.getByText('Complexity Assessment')).toBeInTheDocument();
    });

    it('renders depth level correctly for each tier', () => {
      const { rerender } = render(<ComplexityAssessment profile={minimalProfile} />);
      expect(screen.getByText('Minimal')).toBeInTheDocument();
      
      rerender(<ComplexityAssessment profile={standardProfile} />);
      expect(screen.getByText('Standard')).toBeInTheDocument();
      
      rerender(<ComplexityAssessment profile={detailedProfile} />);
      expect(screen.getByText('Detailed')).toBeInTheDocument();
    });

    it('renders estimated phase count', () => {
      render(<ComplexityAssessment profile={standardProfile} />);
      expect(screen.getByText('7')).toBeInTheDocument();
      expect(screen.getByText('Estimated Phases')).toBeInTheDocument();
    });

    it('renders confidence percentage', () => {
      render(<ComplexityAssessment profile={standardProfile} />);
      expect(screen.getByText('75%')).toBeInTheDocument();
      expect(screen.getByText('Confidence')).toBeInTheDocument();
    });

    it('renders project scale based on score', () => {
      const { rerender } = render(<ComplexityAssessment profile={minimalProfile} />);
      expect(screen.getByText('Simple')).toBeInTheDocument();
      
      // Score 7.5 is in Complex range (> 7)
      rerender(<ComplexityAssessment profile={standardProfile} />);
      expect(screen.getByText('Complex')).toBeInTheDocument();
      
      // Score 5 is in Moderate range (> 3 and <= 7)
      const moderateProfile = { ...standardProfile, score: 5 };
      rerender(<ComplexityAssessment profile={moderateProfile} />);
      expect(screen.getByText('Moderate')).toBeInTheDocument();
      
      rerender(<ComplexityAssessment profile={detailedProfile} />);
      expect(screen.getByText('Enterprise')).toBeInTheDocument();
    });
  });

  describe('details section', () => {
    it('shows complexity factors when showDetails is true', () => {
      render(<ComplexityAssessment profile={minimalProfile} showDetails={true} />);
      
      expect(screen.getByText('Complexity Factors')).toBeInTheDocument();
      expect(screen.getByText('Cli Tool')).toBeInTheDocument();
      expect(screen.getByText('Simple Crud')).toBeInTheDocument();
      expect(screen.getByText('Standalone')).toBeInTheDocument();
      expect(screen.getByText('Solo')).toBeInTheDocument();
    });

    it('hides complexity factors when showDetails is false', () => {
      render(<ComplexityAssessment profile={minimalProfile} showDetails={false} />);
      
      expect(screen.queryByText('Complexity Factors')).not.toBeInTheDocument();
    });

    it('formats bucket names correctly', () => {
      render(<ComplexityAssessment profile={standardProfile} showDetails={true} />);
      
      expect(screen.getByText('Web App')).toBeInTheDocument();
      expect(screen.getByText('Auth Db')).toBeInTheDocument();
      expect(screen.getByText('3 5 Services')).toBeInTheDocument();
    });
  });

  describe('loading state', () => {
    it('shows loading skeleton when isLoading is true', () => {
      render(<ComplexityAssessment profile={minimalProfile} isLoading={true} />);
      
      // Should not show actual content
      expect(screen.queryByText('1.5')).not.toBeInTheDocument();
      expect(screen.queryByText('Complexity Assessment')).not.toBeInTheDocument();
    });
  });

  describe('refresh callback', () => {
    it('shows refresh button when onRefresh is provided', () => {
      const onRefresh = jest.fn();
      render(<ComplexityAssessment profile={minimalProfile} onRefresh={onRefresh} />);
      
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    it('calls onRefresh when refresh button is clicked', async () => {
      const user = userEvent.setup();
      const onRefresh = jest.fn();
      render(<ComplexityAssessment profile={minimalProfile} onRefresh={onRefresh} />);
      
      await user.click(screen.getByText('Refresh'));
      expect(onRefresh).toHaveBeenCalledTimes(1);
    });

    it('does not show refresh button when onRefresh is not provided', () => {
      render(<ComplexityAssessment profile={minimalProfile} />);
      
      expect(screen.queryByText('Refresh')).not.toBeInTheDocument();
    });
  });

  describe('confidence indicators', () => {
    it('shows high confidence indicator for >= 0.8', () => {
      const highConfidenceProfile = { ...minimalProfile, confidence: 0.9 };
      render(<ComplexityAssessment profile={highConfidenceProfile} />);
      
      expect(screen.getByText('High confidence')).toBeInTheDocument();
    });

    it('shows medium confidence indicator for >= 0.6', () => {
      const mediumConfidenceProfile = { ...minimalProfile, confidence: 0.7 };
      render(<ComplexityAssessment profile={mediumConfidenceProfile} />);
      
      expect(screen.getByText('Medium confidence')).toBeInTheDocument();
    });

    it('shows low confidence indicator for < 0.6', () => {
      const lowConfidenceProfile = { ...minimalProfile, confidence: 0.4 };
      render(<ComplexityAssessment profile={lowConfidenceProfile} />);
      
      expect(screen.getByText('Low confidence')).toBeInTheDocument();
    });
  });
});

describe('ComplexityBadge', () => {
  const profile: ComplexityProfile = {
    project_type_bucket: 'web_app',
    technical_complexity_bucket: 'auth_db',
    integration_bucket: '3_5_services',
    team_size_bucket: '2_3',
    score: 7.5,
    estimated_phase_count: 7,
    depth_level: 'standard',
    confidence: 0.75,
  };

  it('renders score correctly', () => {
    render(<ComplexityBadge profile={profile} />);
    expect(screen.getByText('7.5')).toBeInTheDocument();
  });

  it('renders phase count', () => {
    render(<ComplexityBadge profile={profile} />);
    expect(screen.getByText('7 phases')).toBeInTheDocument();
  });

  it('renders depth level label', () => {
    render(<ComplexityBadge profile={profile} />);
    expect(screen.getByText('Standard')).toBeInTheDocument();
  });

  it('renders different styles for each depth level', () => {
    const { rerender, container } = render(<ComplexityBadge profile={profile} />);
    
    // Standard should have blue styling
    expect(container.firstChild).toHaveClass('bg-blue-500/10');
    
    // Minimal should have green styling
    const minimalProfile = { ...profile, depth_level: 'minimal' as const };
    rerender(<ComplexityBadge profile={minimalProfile} />);
    expect(container.firstChild).toHaveClass('bg-green-500/10');
    
    // Detailed should have purple styling
    const detailedProfile = { ...profile, depth_level: 'detailed' as const };
    rerender(<ComplexityBadge profile={detailedProfile} />);
    expect(container.firstChild).toHaveClass('bg-purple-500/10');
  });
});
