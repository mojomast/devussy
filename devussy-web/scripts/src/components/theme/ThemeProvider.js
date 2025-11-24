"use strict";
'use client';
Object.defineProperty(exports, "__esModule", { value: true });
exports.ThemeProvider = ThemeProvider;
exports.useTheme = useTheme;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const ThemeContext = (0, react_1.createContext)(undefined);
function ThemeProvider({ children }) {
    const [theme, setThemeState] = (0, react_1.useState)('default');
    const [mounted, setMounted] = (0, react_1.useState)(false);
    (0, react_1.useEffect)(() => {
        setMounted(true);
        // Load theme from localStorage
        const savedTheme = localStorage.getItem('devussy-theme');
        if (savedTheme && ['default', 'terminal', 'bliss'].includes(savedTheme)) {
            setThemeState(savedTheme);
            document.documentElement.setAttribute('data-theme', savedTheme);
        }
    }, []);
    const setTheme = (newTheme) => {
        setThemeState(newTheme);
        localStorage.setItem('devussy-theme', newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
    };
    return ((0, jsx_runtime_1.jsx)(ThemeContext.Provider, { value: { theme, setTheme }, children: children }));
}
function useTheme() {
    const context = (0, react_1.useContext)(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}
