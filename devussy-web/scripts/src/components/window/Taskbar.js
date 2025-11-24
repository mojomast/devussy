"use strict";
"use client";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Taskbar = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const utils_1 = require("@/utils");
const lucide_react_1 = require("lucide-react");
const ThemeProvider_1 = require("@/components/theme/ThemeProvider");
const ThemeToggle_1 = require("@/components/theme/ThemeToggle");
const CheckpointManager_1 = require("@/components/pipeline/CheckpointManager");
const AppRegistry_1 = require("@/apps/AppRegistry");
const Taskbar = ({ windows, activeWindowId, minimizedWindowIds, onWindowClick, onNewProject, onHelp, onOpenModelSettings, onOpenIrc, currentState, onLoadCheckpoint, modelConfigs, onModelConfigsChange, activeStage, onOpenApp, ircNick = 'Guest' }) => {
    const { theme } = (0, ThemeProvider_1.useTheme)();
    const [isStartMenuOpen, setIsStartMenuOpen] = (0, react_1.useState)(false);
    const startMenuRef = (0, react_1.useRef)(null);
    const startButtonRef = (0, react_1.useRef)(null);
    // Close start menu when clicking outside
    (0, react_1.useEffect)(() => {
        const handleClickOutside = (event) => {
            if (isStartMenuOpen &&
                startMenuRef.current &&
                !startMenuRef.current.contains(event.target) &&
                startButtonRef.current &&
                !startButtonRef.current.contains(event.target)) {
                setIsStartMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isStartMenuOpen]);
    // Bliss Theme (Windows XP) Taskbar
    if (theme === 'bliss') {
        return ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [isStartMenuOpen && ((0, jsx_runtime_1.jsxs)("div", { ref: startMenuRef, className: "fixed bottom-[32px] left-0 z-[10000] flex flex-col rounded-tr-lg overflow-hidden shadow-xl animate-in slide-in-from-bottom-2 fade-in duration-200", style: {
                        width: '380px',
                        height: '480px',
                        background: '#fff',
                        border: '1px solid #0054e3',
                        borderBottom: 'none',
                        boxShadow: '2px -2px 10px rgba(0,0,0,0.3)'
                    }, children: [(0, jsx_runtime_1.jsxs)("div", { className: "h-16 flex items-center px-4 gap-3", style: {
                                background: 'linear-gradient(to bottom, #1565DE 0%, #1C6CE1 100%)',
                                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)'
                            }, children: [(0, jsx_runtime_1.jsx)("div", { className: "h-10 w-10 rounded-full bg-white border-2 border-white/40 overflow-hidden flex items-center justify-center", children: (0, jsx_runtime_1.jsx)("img", { src: "/devussy_logo_minimal.png", alt: "User", className: "h-8 w-8 object-contain" }) }), (0, jsx_runtime_1.jsx)("span", { className: "text-white font-bold text-lg drop-shadow-md", children: ircNick })] }), (0, jsx_runtime_1.jsxs)("div", { className: "flex-1 flex bg-white", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex-1 p-2 flex flex-col gap-1 bg-white", children: [(0, jsx_runtime_1.jsx)("div", { className: "text-xs text-gray-500 font-bold px-2 mb-1 uppercase tracking-wider", children: "Most Used" }), (0, jsx_runtime_1.jsxs)("button", { onClick: () => { if (onOpenApp) {
                                                onOpenApp('init');
                                            }
                                            else {
                                                onNewProject === null || onNewProject === void 0 ? void 0 : onNewProject();
                                            } setIsStartMenuOpen(false); }, className: "flex items-center gap-2 p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors text-left", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Plus, { className: "h-8 w-8 text-gray-600 group-hover:text-white" }), (0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col", children: [(0, jsx_runtime_1.jsx)("span", { className: "font-bold text-sm", children: "New Project" }), (0, jsx_runtime_1.jsx)("span", { className: "text-[10px] text-gray-500 group-hover:text-white/80", children: "Start a new creation" })] })] }), (0, jsx_runtime_1.jsxs)("button", { onClick: () => { if (onOpenApp) {
                                                onOpenApp('help');
                                            }
                                            else {
                                                onHelp === null || onHelp === void 0 ? void 0 : onHelp();
                                            } setIsStartMenuOpen(false); }, className: "flex items-center gap-2 p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors text-left", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.HelpCircle, { className: "h-8 w-8 text-blue-600 group-hover:text-white" }), (0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col", children: [(0, jsx_runtime_1.jsx)("span", { className: "font-bold text-sm", children: "Help & Support" }), (0, jsx_runtime_1.jsx)("span", { className: "text-[10px] text-gray-500 group-hover:text-white/80", children: "Get assistance" })] })] }), (0, jsx_runtime_1.jsxs)("button", { onClick: () => { if (onOpenApp) {
                                                onOpenApp('irc');
                                            }
                                            else {
                                                onOpenIrc === null || onOpenIrc === void 0 ? void 0 : onOpenIrc();
                                            } setIsStartMenuOpen(false); }, className: "flex items-center gap-2 p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors text-left", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.MessageSquare, { className: "h-8 w-8 text-green-600 group-hover:text-white" }), (0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col", children: [(0, jsx_runtime_1.jsx)("span", { className: "font-bold text-sm", children: "IRC Chat" }), (0, jsx_runtime_1.jsx)("span", { className: "text-[10px] text-gray-500 group-hover:text-white/80", children: "Chat with #devussy" })] })] }), (0, jsx_runtime_1.jsxs)("div", { className: "mt-auto border-t border-gray-200 pt-2", children: [(0, jsx_runtime_1.jsx)("div", { className: "text-xs text-gray-500 font-bold px-2 mb-1 uppercase tracking-wider", children: "All Programs" }), (0, jsx_runtime_1.jsx)("div", { className: "max-h-[220px] overflow-y-auto pr-1", children: Object.values(AppRegistry_1.AppRegistry)
                                                        .filter(app => app.startMenuCategory && app.startMenuCategory !== "Most Used")
                                                        .sort((a, b) => {
                                                        const aCat = a.startMenuCategory || "";
                                                        const bCat = b.startMenuCategory || "";
                                                        if (aCat === bCat) {
                                                            return a.name.localeCompare(b.name);
                                                        }
                                                        return aCat.localeCompare(bCat);
                                                    })
                                                        .map(app => ((0, jsx_runtime_1.jsxs)("button", { onClick: () => {
                                                            if (onOpenApp) {
                                                                onOpenApp(app.id);
                                                            }
                                                            else {
                                                                if (app.id === 'init') {
                                                                    onNewProject === null || onNewProject === void 0 ? void 0 : onNewProject();
                                                                }
                                                                else if (app.id === 'help') {
                                                                    onHelp === null || onHelp === void 0 ? void 0 : onHelp();
                                                                }
                                                                else if (app.id === 'irc') {
                                                                    onOpenIrc === null || onOpenIrc === void 0 ? void 0 : onOpenIrc();
                                                                }
                                                            }
                                                            setIsStartMenuOpen(false);
                                                        }, className: "w-full flex items-center gap-2 px-2 py-1 rounded hover:bg-[#316AC5] hover:text-white text-left text-xs text-gray-800 transition-colors", children: [(0, jsx_runtime_1.jsx)("div", { className: "h-6 w-6 flex items-center justify-center text-gray-600", children: app.icon }), (0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col", children: [(0, jsx_runtime_1.jsx)("span", { className: "font-medium", children: app.name }), app.startMenuCategory && ((0, jsx_runtime_1.jsx)("span", { className: "text-[10px] text-gray-500", children: app.startMenuCategory }))] })] }, app.id))) })] })] }), (0, jsx_runtime_1.jsxs)("div", { className: "w-[160px] bg-[#D3E5FA] border-l border-[#95BDE7] p-2 flex flex-col gap-1", children: [(0, jsx_runtime_1.jsx)("div", { className: "text-xs text-[#1A3E78] font-bold px-2 mb-1", children: "Settings" }), (0, jsx_runtime_1.jsxs)("div", { className: "p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors cursor-pointer flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)("div", { className: "scale-75 origin-left", children: (0, jsx_runtime_1.jsx)(ThemeToggle_1.ThemeToggle, {}) }), (0, jsx_runtime_1.jsx)("span", { className: "text-xs font-medium text-[#1A3E78] group-hover:text-white", children: "Theme" })] }), currentState && onLoadCheckpoint && ((0, jsx_runtime_1.jsxs)("div", { className: "p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors cursor-pointer flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)("div", { className: "scale-75 origin-left", children: (0, jsx_runtime_1.jsx)(CheckpointManager_1.CheckpointManager, { currentState: currentState, onLoad: onLoadCheckpoint }) }), (0, jsx_runtime_1.jsx)("span", { className: "text-xs font-medium text-[#1A3E78] group-hover:text-white", children: "Save/Load" })] })), (0, jsx_runtime_1.jsxs)("button", { onClick: () => { onOpenModelSettings === null || onOpenModelSettings === void 0 ? void 0 : onOpenModelSettings(); setIsStartMenuOpen(false); }, className: "flex items-center gap-2 p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors cursor-pointer text-left", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Settings, { className: "h-8 w-8 text-gray-600 group-hover:text-white" }), (0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col", children: [(0, jsx_runtime_1.jsx)("span", { className: "font-bold text-sm", children: "AI Models" }), (0, jsx_runtime_1.jsx)("span", { className: "text-[10px] text-gray-500 group-hover:text-white/80", children: "Configure models" })] })] })] })] }), (0, jsx_runtime_1.jsx)("div", { className: "h-10 bg-[#1C6CE1] flex items-center justify-end px-3 gap-2", style: {
                                background: 'linear-gradient(to bottom, #1C6CE1 0%, #1565DE 100%)',
                                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)'
                            }, children: (0, jsx_runtime_1.jsxs)("button", { className: "flex items-center gap-1 px-2 py-1 hover:bg-[#1565DE] rounded text-white text-xs", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Power, { className: "h-4 w-4" }), (0, jsx_runtime_1.jsx)("span", { children: "Turn Off Computer" })] }) })] })), (0, jsx_runtime_1.jsxs)("div", { className: "fixed bottom-0 left-0 right-0 w-full h-[32px] bg-[#245DDA] border-t-[2px] border-[#3F8CF3] flex items-center z-[9999] select-none shadow-none m-0 p-0", style: { background: 'linear-gradient(to bottom, #245DDA 0%, #3F8CF3 9%, #245DDA 18%, #245DDA 100%)' }, children: [(0, jsx_runtime_1.jsxs)("div", { ref: startButtonRef, onClick: () => setIsStartMenuOpen(!isStartMenuOpen), className: (0, utils_1.cn)("h-full flex items-center px-2 mr-2 cursor-pointer hover:brightness-110 active:brightness-90 relative transition-all", isStartMenuOpen && "brightness-90 shadow-[inset_1px_1px_2px_rgba(0,0,0,0.5)]"), style: {
                                background: 'linear-gradient(to bottom, #3C8018 0%, #46941B 100%)',
                                borderRadius: '0 10px 10px 0',
                                border: '1px solid #2B5F11',
                                boxShadow: isStartMenuOpen ? 'inset 1px 1px 2px rgba(0,0,0,0.5)' : 'inset 0 1px 0 rgba(255,255,255,0.3)'
                            }, children: [(0, jsx_runtime_1.jsx)("img", { src: "/devussy_logo_minimal.png", alt: "Logo", className: "h-5 w-5 invert brightness-0 drop-shadow-md" }), (0, jsx_runtime_1.jsx)("span", { className: "ml-1 font-bold italic text-white text-[14px] drop-shadow-md", style: { textShadow: '1px 1px 1px rgba(0,0,0,0.5)' }, children: "Start" })] }), (0, jsx_runtime_1.jsx)("div", { className: "h-[20px] w-[2px] bg-black/20 border-r border-white/10 mx-1" }), (0, jsx_runtime_1.jsx)("div", { className: "flex-1 flex items-center gap-1 overflow-x-auto px-1", children: windows.map((window) => {
                                const isActive = activeWindowId === window.id;
                                const isMinimized = minimizedWindowIds.includes(window.id);
                                return ((0, jsx_runtime_1.jsxs)("button", { onClick: () => onWindowClick(window.id), className: (0, utils_1.cn)("flex items-center gap-2 px-2 h-[24px] min-w-[140px] max-w-[200px] rounded-[2px] text-xs text-white truncate transition-all", isActive && !isMinimized
                                        ? "bg-[#1F4EBF] shadow-[inset_1px_1px_2px_rgba(0,0,0,0.5)]"
                                        : "bg-[#3C81F0] hover:bg-[#5291F3] shadow-[0_1px_2px_rgba(0,0,0,0.2)]"), children: [(0, jsx_runtime_1.jsx)("div", { className: "w-3 h-3 bg-white/20 rounded-sm" }), (0, jsx_runtime_1.jsx)("span", { className: "truncate", children: window.title })] }, window.id));
                            }) }), (0, jsx_runtime_1.jsx)("div", { className: "h-full bg-[#0B96D6] border-l border-[#155394] px-3 flex items-center shadow-[inset_1px_1px_2px_rgba(0,0,0,0.3)]", children: (0, jsx_runtime_1.jsx)("span", { className: "text-white text-xs font-medium", children: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }) })] })] }));
    }
    // Default / Terminal Theme Taskbar (Floating Glass)
    return ((0, jsx_runtime_1.jsxs)("div", { className: "fixed bottom-4 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-2 p-2 rounded-xl bg-black/60 backdrop-blur-md border border-white/10 shadow-2xl transition-all hover:bg-black/70", children: [(0, jsx_runtime_1.jsx)("div", { className: "px-2 border-r border-white/10 mr-1 flex items-center", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Layout, { className: "h-5 w-5 text-primary" }) }), (0, jsx_runtime_1.jsxs)("button", { onClick: () => {
                    if (onOpenApp) {
                        onOpenApp('init');
                    }
                    else {
                        onNewProject === null || onNewProject === void 0 ? void 0 : onNewProject();
                    }
                }, className: "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all text-muted-foreground hover:bg-white/5 hover:text-white", title: "New Project", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Plus, { className: "h-4 w-4" }), (0, jsx_runtime_1.jsx)("span", { children: "New" })] }), (0, jsx_runtime_1.jsxs)("button", { onClick: () => {
                    if (onOpenApp) {
                        onOpenApp('help');
                    }
                    else {
                        onHelp === null || onHelp === void 0 ? void 0 : onHelp();
                    }
                }, className: "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all text-muted-foreground hover:bg-white/5 hover:text-white", title: "Help", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.HelpCircle, { className: "h-4 w-4" }), (0, jsx_runtime_1.jsx)("span", { children: "Help" })] }), (0, jsx_runtime_1.jsxs)("button", { onClick: () => {
                    if (onOpenApp) {
                        onOpenApp('irc');
                    }
                    else {
                        onOpenIrc === null || onOpenIrc === void 0 ? void 0 : onOpenIrc();
                    }
                }, className: "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all text-muted-foreground hover:bg-white/5 hover:text-white", title: "IRC Chat", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.MessageSquare, { className: "h-4 w-4" }), (0, jsx_runtime_1.jsx)("span", { children: "Chat" })] }), windows.length > 0 && ((0, jsx_runtime_1.jsx)("div", { className: "h-6 w-px bg-white/10 mx-1" })), (0, jsx_runtime_1.jsx)("div", { className: "flex-1 flex items-center gap-1 overflow-x-auto", children: windows.map((window) => {
                    const isActive = activeWindowId === window.id;
                    const isMinimized = minimizedWindowIds.includes(window.id);
                    return ((0, jsx_runtime_1.jsxs)("button", { onClick: () => onWindowClick(window.id), className: (0, utils_1.cn)("relative group flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all min-w-[120px] max-w-[200px]", "text-muted-foreground hover:bg-white/5 hover:text-white", isActive && !isMinimized && "bg-white/10 text-white shadow-inner", isMinimized && "opacity-50 hover:opacity-100"), children: [(0, jsx_runtime_1.jsx)("div", { className: (0, utils_1.cn)("h-2 w-2 rounded-full transition-colors", isActive && !isMinimized ? "bg-green-500" : "bg-white/20 group-hover:bg-white/50") }), (0, jsx_runtime_1.jsx)("span", { className: "truncate flex-1 text-left", children: window.title }), isMinimized && ((0, jsx_runtime_1.jsx)("div", { className: "absolute -top-1 -right-1", children: (0, jsx_runtime_1.jsx)("div", { className: "h-2 w-2 bg-blue-500 rounded-full animate-pulse" }) }))] }, window.id));
                }) })] }));
};
exports.Taskbar = Taskbar;
