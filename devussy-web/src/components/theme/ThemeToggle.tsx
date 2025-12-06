'use client';

import { useTheme, Theme } from './ThemeProvider';
import { Monitor, Terminal, Image, Cpu, Ghost } from 'lucide-react';

const themes: { value: Theme; label: string; icon: React.ReactNode }[] = [
    { value: 'default', label: 'Default', icon: <Monitor className="w-4 h-4" /> },
    { value: 'terminal', label: 'Terminal', icon: <Terminal className="w-4 h-4" /> },
    { value: 'bliss', label: 'Bliss', icon: <Image className="w-4 h-4" /> },
    { value: 'cyberpunk', label: 'Cyberpunk', icon: <Cpu className="w-4 h-4" /> },
    { value: 'retro', label: 'Retro', icon: <Ghost className="w-4 h-4" /> },
];

export function ThemeToggle() {
    const { theme, setTheme } = useTheme();

    const cycleTheme = () => {
        const currentIndex = themes.findIndex((t) => t.value === theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        setTheme(themes[nextIndex].value);
    };

    const currentTheme = themes.find((t) => t.value === theme) || themes[0];

    return (
        <button
            onClick={cycleTheme}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-border hover:bg-accent transition-colors text-sm font-medium"
            title={`Current theme: ${currentTheme.label}. Click to cycle.`}
        >
            {currentTheme.icon}
            <span>{currentTheme.label}</span>
        </button>
    );
}
