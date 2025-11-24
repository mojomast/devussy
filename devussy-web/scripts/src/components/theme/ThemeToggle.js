"use strict";
'use client';
Object.defineProperty(exports, "__esModule", { value: true });
exports.ThemeToggle = ThemeToggle;
const jsx_runtime_1 = require("react/jsx-runtime");
const ThemeProvider_1 = require("./ThemeProvider");
const lucide_react_1 = require("lucide-react");
const themes = [
    { value: 'default', label: 'Default', icon: (0, jsx_runtime_1.jsx)(lucide_react_1.Monitor, { className: "w-4 h-4" }) },
    { value: 'terminal', label: 'Terminal', icon: (0, jsx_runtime_1.jsx)(lucide_react_1.Terminal, { className: "w-4 h-4" }) },
    { value: 'bliss', label: 'Bliss', icon: (0, jsx_runtime_1.jsx)(lucide_react_1.Image, { className: "w-4 h-4" }) },
];
function ThemeToggle() {
    const { theme, setTheme } = (0, ThemeProvider_1.useTheme)();
    const cycleTheme = () => {
        const currentIndex = themes.findIndex((t) => t.value === theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        setTheme(themes[nextIndex].value);
    };
    const currentTheme = themes.find((t) => t.value === theme) || themes[0];
    return ((0, jsx_runtime_1.jsxs)("button", { onClick: cycleTheme, className: "flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-border hover:bg-accent transition-colors text-sm font-medium", title: `Current theme: ${currentTheme.label}. Click to cycle.`, children: [currentTheme.icon, (0, jsx_runtime_1.jsx)("span", { children: currentTheme.label })] }));
}
