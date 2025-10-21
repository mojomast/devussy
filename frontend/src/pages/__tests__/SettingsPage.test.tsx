import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import SettingsPage from '../SettingsPage';

// Mock the config components
vi.mock('../../components/config/CredentialsTab', () => ({
  default: () => <div data-testid="credentials-tab">Credentials Tab Content</div>,
}));

vi.mock('../../components/config/GlobalConfigTab', () => ({
  default: () => <div data-testid="global-config-tab">Global Config Tab Content</div>,
}));

vi.mock('../../components/config/PresetsTab', () => ({
  default: () => <div data-testid="presets-tab">Presets Tab Content</div>,
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('SettingsPage', () => {
  it('should render the settings page with header', () => {
    renderWithRouter(<SettingsPage />);

    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(
      screen.getByText(/configure api credentials, model defaults, and presets/i)
    ).toBeInTheDocument();
  });

  it('should render all three tabs', () => {
    renderWithRouter(<SettingsPage />);

    expect(screen.getByText('API Credentials')).toBeInTheDocument();
    expect(screen.getByText('Global Configuration')).toBeInTheDocument();
    expect(screen.getByText('Presets')).toBeInTheDocument();
  });

  it('should display tab icons', () => {
    renderWithRouter(<SettingsPage />);

    expect(screen.getByText('🔑')).toBeInTheDocument(); // Credentials
    expect(screen.getByText('⚙️')).toBeInTheDocument(); // Global Config
    expect(screen.getByText('⭐')).toBeInTheDocument(); // Presets
  });

  it('should show credentials tab by default', () => {
    renderWithRouter(<SettingsPage />);

    expect(screen.getByTestId('credentials-tab')).toBeInTheDocument();
    expect(screen.queryByTestId('global-config-tab')).not.toBeInTheDocument();
    expect(screen.queryByTestId('presets-tab')).not.toBeInTheDocument();
  });

  it('should highlight active tab with blue border and text', () => {
    renderWithRouter(<SettingsPage />);

    const credentialsTab = screen.getByRole('button', { name: /api credentials/i });
    
    expect(credentialsTab).toHaveClass('border-blue-500');
    expect(credentialsTab).toHaveClass('text-blue-600');
  });

  it('should switch to global config tab when clicked', () => {
    renderWithRouter(<SettingsPage />);

    const globalConfigTab = screen.getByRole('button', { name: /global configuration/i });
    fireEvent.click(globalConfigTab);

    expect(screen.getByTestId('global-config-tab')).toBeInTheDocument();
    expect(screen.queryByTestId('credentials-tab')).not.toBeInTheDocument();
    expect(screen.queryByTestId('presets-tab')).not.toBeInTheDocument();
  });

  it('should switch to presets tab when clicked', () => {
    renderWithRouter(<SettingsPage />);

    const presetsTab = screen.getByRole('button', { name: /presets/i });
    fireEvent.click(presetsTab);

    expect(screen.getByTestId('presets-tab')).toBeInTheDocument();
    expect(screen.queryByTestId('credentials-tab')).not.toBeInTheDocument();
    expect(screen.queryByTestId('global-config-tab')).not.toBeInTheDocument();
  });

  it('should update active tab styling when switching tabs', () => {
    renderWithRouter(<SettingsPage />);

    const credentialsTab = screen.getByRole('button', { name: /api credentials/i });
    const globalConfigTab = screen.getByRole('button', { name: /global configuration/i });

    // Initially, credentials tab is active
    expect(credentialsTab).toHaveClass('border-blue-500', 'text-blue-600');
    expect(globalConfigTab).toHaveClass('border-transparent', 'text-gray-500');

    // Click global config tab
    fireEvent.click(globalConfigTab);

    // Now global config tab should be active
    expect(globalConfigTab).toHaveClass('border-blue-500', 'text-blue-600');
    expect(credentialsTab).toHaveClass('border-transparent', 'text-gray-500');
  });

  it('should switch between all tabs correctly', () => {
    renderWithRouter(<SettingsPage />);

    const credentialsTab = screen.getByRole('button', { name: /api credentials/i });
    const globalConfigTab = screen.getByRole('button', { name: /global configuration/i });
    const presetsTab = screen.getByRole('button', { name: /presets/i });

    // Start with credentials
    expect(screen.getByTestId('credentials-tab')).toBeInTheDocument();

    // Switch to global config
    fireEvent.click(globalConfigTab);
    expect(screen.getByTestId('global-config-tab')).toBeInTheDocument();
    expect(screen.queryByTestId('credentials-tab')).not.toBeInTheDocument();

    // Switch to presets
    fireEvent.click(presetsTab);
    expect(screen.getByTestId('presets-tab')).toBeInTheDocument();
    expect(screen.queryByTestId('global-config-tab')).not.toBeInTheDocument();

    // Switch back to credentials
    fireEvent.click(credentialsTab);
    expect(screen.getByTestId('credentials-tab')).toBeInTheDocument();
    expect(screen.queryByTestId('presets-tab')).not.toBeInTheDocument();
  });

  it('should render tabs in a flex container with proper styling', () => {
    renderWithRouter(<SettingsPage />);

    const tabContainer = screen.getByRole('button', { name: /api credentials/i }).parentElement;
    
    expect(tabContainer).toHaveClass('flex');
    expect(tabContainer).toHaveClass('-mb-px');
  });

  it('should render white background container for tabs', () => {
    const { container } = renderWithRouter(<SettingsPage />);

    const whiteContainer = container.querySelector('.bg-white.rounded-lg.shadow');
    expect(whiteContainer).toBeInTheDocument();
  });

  it('should render tabs with proper button styling', () => {
    renderWithRouter(<SettingsPage />);

    const credentialsTab = screen.getByRole('button', { name: /api credentials/i });
    
    expect(credentialsTab).toHaveClass('flex', 'items-center', 'gap-2');
    expect(credentialsTab).toHaveClass('px-6', 'py-4');
    expect(credentialsTab).toHaveClass('text-sm', 'font-medium');
    expect(credentialsTab).toHaveClass('border-b-2');
  });
});
