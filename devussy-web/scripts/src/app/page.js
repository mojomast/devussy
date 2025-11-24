"use strict";
"use client";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = Page;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const card_1 = require("@/components/ui/card");
const button_1 = require("@/components/ui/button");
const input_1 = require("@/components/ui/input");
const textarea_1 = require("@/components/ui/textarea");
const lucide_react_1 = require("lucide-react");
const WindowFrame_1 = require("@/components/window/WindowFrame");
const DesignView_1 = require("@/components/pipeline/DesignView");
const PlanView_1 = require("@/components/pipeline/PlanView");
const ExecutionView_1 = require("@/components/pipeline/ExecutionView");
const HandoffView_1 = require("@/components/pipeline/HandoffView");
const InterviewView_1 = require("@/components/pipeline/InterviewView");
const ModelSettings_1 = require("@/components/pipeline/ModelSettings");
const CheckpointManager_1 = require("@/components/pipeline/CheckpointManager");
const Taskbar_1 = require("@/components/window/Taskbar");
const ThemeToggle_1 = require("@/components/theme/ThemeToggle");
const ThemeProvider_1 = require("@/components/theme/ThemeProvider");
const AppRegistry_1 = require("@/apps/AppRegistry");
const eventBus_1 = require("@/apps/eventBus");
const shareLinks_1 = require("@/shareLinks");
function PageInner() {
    const { theme } = (0, ThemeProvider_1.useTheme)();
    const bus = (0, eventBus_1.useEventBus)();
    // Window State Management
    const [windows, setWindows] = (0, react_1.useState)([
        { id: 'help-1', type: 'help', title: 'Devussy Studio Help', position: { x: 50, y: 50 }, zIndex: 10, size: { width: 700, height: 600 } }
    ]);
    const [activeWindowId, setActiveWindowId] = (0, react_1.useState)('help-1');
    const [nextZIndex, setNextZIndex] = (0, react_1.useState)(20);
    // Project State (Shared across windows)
    const [projectName, setProjectName] = (0, react_1.useState)("");
    const [languages, setLanguages] = (0, react_1.useState)("");
    const [requirements, setRequirements] = (0, react_1.useState)("");
    // Auto-run State
    const [isAutoRun, setIsAutoRun] = (0, react_1.useState)(false);
    // Pipeline Data
    const [design, setDesign] = (0, react_1.useState)(null);
    const [plan, setPlan] = (0, react_1.useState)(null);
    const [currentPhaseIndex, setCurrentPhaseIndex] = (0, react_1.useState)(0);
    // Help preferences
    const [dontShowHelpAgain, setDontShowHelpAgain] = (0, react_1.useState)(() => {
        try {
            return localStorage.getItem('devussy_help_dismissed') === '1';
        }
        catch (e) {
            return false;
        }
    });
    const [analyticsOptOut, setAnalyticsOptOut] = (0, react_1.useState)(false);
    (0, react_1.useEffect)(() => {
        try {
            const cookies = document.cookie.split(';').map(c => c.trim());
            const cookie = cookies.find(c => c.startsWith('devussy_analytics_optout='));
            if (cookie) {
                const value = (cookie.split('=')[1] || '').toLowerCase();
                if (value === '1' || value === 'true' || value === 'yes') {
                    setAnalyticsOptOut(true);
                }
            }
        }
        catch (e) { }
    }, []);
    // IRC nickname (from localStorage)
    const [ircNick, setIrcNick] = (0, react_1.useState)(() => {
        try {
            return localStorage.getItem('devussy_irc_nick') || 'Guest';
        }
        catch (e) {
            return 'Guest';
        }
    });
    // Listen for IRC nick changes
    (0, react_1.useEffect)(() => {
        const handleStorage = () => {
            try {
                const nick = localStorage.getItem('devussy_irc_nick');
                if (nick)
                    setIrcNick(nick);
            }
            catch (e) { }
        };
        window.addEventListener('storage', handleStorage);
        // Also poll for changes since same-tab changes don't trigger storage event
        const interval = setInterval(handleStorage, 1000);
        return () => {
            window.removeEventListener('storage', handleStorage);
            clearInterval(interval);
        };
    }, []);
    // Model Configuration
    const [modelConfigs, setModelConfigs] = (0, react_1.useState)({
        global: {
            model: 'openai/gpt-5-mini',
            temperature: 0.7,
            reasoning_effort: 'medium',
            concurrency: 3
        },
        interview: null,
        design: null,
        plan: null,
        execute: null,
        handoff: null
    });
    // Helper to get effective config for current stage
    const getEffectiveConfig = (stage) => {
        return modelConfigs[stage] || modelConfigs.global;
    };
    // Determine active stage based on active window
    const getActiveStage = () => {
        const activeWindow = windows.find(w => w.id === activeWindowId);
        if (!activeWindow)
            return 'global';
        switch (activeWindow.type) {
            case 'interview': return 'interview';
            case 'design': return 'design';
            case 'plan': return 'plan';
            case 'execute': return 'execute';
            case 'handoff': return 'handoff';
            default: return 'global';
        }
    };
    // Checkpoint Handler
    const handleLoadCheckpoint = (data) => {
        console.log('[page.tsx] Loading checkpoint:', data.name);
        // Restore project state
        if (data.projectName)
            setProjectName(data.projectName);
        if (data.languages)
            setLanguages(data.languages);
        if (data.requirements)
            setRequirements(data.requirements);
        if (data.design)
            setDesign(data.design);
        if (data.plan)
            setPlan(data.plan);
        // Reset auto-run on manual load
        setIsAutoRun(false);
        // Restore windows based on stage
        // We'll clear existing windows and spawn the relevant one
        setWindows([]);
        setTimeout(() => {
            if (data.stage === 'handoff') {
                spawnAppWindow('handoff', 'Project Handoff');
            }
            else if (data.stage === 'execute' && data.plan) {
                spawnAppWindow('execute', 'Execution Phase');
            }
            else if (data.stage === 'plan' && data.design) {
                spawnAppWindow('plan', 'Development Plan');
            }
            else if (data.stage === 'design') {
                spawnAppWindow('design', 'System Design');
            }
            else if (data.stage === 'interview') {
                spawnAppWindow('interview', 'Requirements Interview');
            }
            else {
                // Default to init if unknown or incomplete
                spawnAppWindow('init', 'Devussy Studio');
            }
        }, 100);
    };
    (0, react_1.useEffect)(() => {
        const unsubscribe = bus.subscribe('openShareLink', (payload) => {
            try {
                const sharePayload = payload;
                if (!sharePayload)
                    return;
                const checkpointLike = Object.assign(Object.assign({}, (sharePayload.data || {})), { stage: sharePayload.stage ||
                        (sharePayload.data && sharePayload.data.stage) });
                handleLoadCheckpoint(checkpointLike);
            }
            catch (e) {
                console.error('[page.tsx] Error handling openShareLink event', e);
            }
        });
        return () => {
            unsubscribe();
        };
    }, [bus]);
    (0, react_1.useEffect)(() => {
        try {
            if (typeof window === 'undefined')
                return;
            const key = 'devussy_share_payload';
            const encoded = window.sessionStorage.getItem(key);
            if (!encoded)
                return;
            window.sessionStorage.removeItem(key);
            const decoded = (0, shareLinks_1.decodeSharePayload)(encoded);
            if (!decoded)
                return;
            const checkpointLike = Object.assign(Object.assign({}, (decoded.data || {})), { stage: decoded.stage || (decoded.data && decoded.data.stage) });
            handleLoadCheckpoint(checkpointLike);
        }
        catch (e) {
            console.error('[page.tsx] Failed to restore from share payload in sessionStorage', e);
        }
    }, []);
    // Window Management Functions
    const getWindowSize = (type) => {
        const appDef = AppRegistry_1.AppRegistry[type];
        if (appDef && appDef.defaultSize) {
            return appDef.defaultSize;
        }
        return { width: 600, height: 400 };
    };
    // Window Management Functions
    const spawnWindow = (type, title, props, options) => {
        const id = `${type}-${Date.now()}`;
        const offset = windows.length * 30;
        const size = getWindowSize(type);
        const newWindow = {
            id,
            type,
            title,
            position: { x: 100 + offset, y: 100 + offset },
            zIndex: nextZIndex,
            isMinimized: options === null || options === void 0 ? void 0 : options.isMinimized,
            props,
            size
        };
        setWindows(prev => [...prev, newWindow]);
        setNextZIndex(prev => prev + 1);
        if (!(options === null || options === void 0 ? void 0 : options.isMinimized)) {
            setActiveWindowId(id);
        }
    };
    const spawnAppWindow = (appId, title, props, options) => {
        spawnWindow(appId, title, props, options);
    };
    const closeWindow = (id) => {
        setWindows(prev => prev.filter(w => w.id !== id));
    };
    const focusWindow = (id) => {
        setWindows(prev => prev.map(w => w.id === id ? Object.assign(Object.assign({}, w), { zIndex: nextZIndex }) : w));
        setNextZIndex(prev => prev + 1);
        setActiveWindowId(id);
    };
    const toggleMinimize = (id) => {
        setWindows(prev => prev.map(w => {
            if (w.id === id) {
                const isNowMinimized = !w.isMinimized;
                // If restoring, bring to front
                if (!isNowMinimized) {
                    setActiveWindowId(id);
                    return Object.assign(Object.assign({}, w), { isMinimized: false, zIndex: nextZIndex + 1 }); // Increment zIndex locally effectively
                }
                return Object.assign(Object.assign({}, w), { isMinimized: true });
            }
            return w;
        }));
        // If restoring, we need to update global zIndex state too
        const window = windows.find(w => w.id === id);
        if (window && window.isMinimized) {
            setNextZIndex(prev => prev + 1);
        }
    };
    // Pipeline Handlers
    const handleStartInterview = () => {
        setIsAutoRun(false);
        spawnAppWindow('interview', 'Requirements Interview');
    };
    const handleSkipInterview = () => {
        if (projectName && requirements) {
            spawnAppWindow('design', 'System Design');
        }
    };
    const handleTryItNow = () => {
        // Set sample project data
        setProjectName("Todo SaaS with Stripe");
        setLanguages("Next.js, TypeScript, TailwindCSS, Supabase, Stripe");
        setRequirements("A modern Todo list SaaS application where users can sign up, create lists, add tasks with due dates, and upgrade to a premium plan via Stripe to unlock unlimited lists and collaboration features. It should have a clean, responsive UI.");
        // Enable auto-run mode
        setIsAutoRun(true);
        // Start the pipeline immediately
        setTimeout(() => {
            spawnAppWindow('design', 'System Design');
        }, 100);
    };
    const handleInterviewComplete = (data) => {
        setProjectName(data.project_name || "");
        setRequirements(data.requirements || "");
        setLanguages(data.primary_language || "");
        spawnAppWindow('design', 'System Design');
    };
    const handleDesignComplete = (designData) => {
        setDesign(designData);
        spawnAppWindow('plan', 'Development Plan');
    };
    const handlePlanApproved = (planData) => {
        var _a, _b;
        console.log('[page.tsx] Plan approved with', (_a = planData === null || planData === void 0 ? void 0 : planData.phases) === null || _a === void 0 ? void 0 : _a.length, 'phases');
        if (planData === null || planData === void 0 ? void 0 : planData.phases) {
            planData.phases.forEach((p, i) => {
                if (i < 5) { // Only log first 5
                    console.log(`  Phase ${p.number}: ${p.title}`);
                }
            });
        }
        setPlan(planData);
        try {
            bus.emit('planGenerated', {
                projectName,
                languages,
                requirements,
                plan: planData,
                phaseCount: ((_b = planData === null || planData === void 0 ? void 0 : planData.phases) === null || _b === void 0 ? void 0 : _b.length) || 0,
            });
        }
        catch (e) {
            console.error('[page.tsx] Error emitting planGenerated event', e);
        }
        spawnAppWindow('execute', 'Execution Phase');
    };
    const handlePhaseComplete = (detailedPlan) => {
        // Update plan with detailed phases if provided
        if (detailedPlan) {
            console.log('[page.tsx] Updating plan with detailed phases');
            setPlan(detailedPlan);
        }
        spawnAppWindow('handoff', 'Project Handoff');
    };
    const handleNewProject = () => {
        spawnAppWindow('init', 'New Project');
    };
    const handleHelp = () => {
        // Prevent duplicate help windows
        const existingHelp = windows.find(w => w.type === 'help');
        if (existingHelp) {
            focusWindow(existingHelp.id);
            if (existingHelp.isMinimized) {
                toggleMinimize(existingHelp.id);
            }
            return;
        }
        spawnAppWindow('help', 'Devussy Studio Help');
    };
    const handleOpenModelSettings = () => {
        // Prevent duplicate model settings windows
        const existing = windows.find(w => w.type === 'model-settings');
        if (existing) {
            focusWindow(existing.id);
            if (existing.isMinimized) {
                toggleMinimize(existing.id);
            }
            return;
        }
        spawnAppWindow('model-settings', 'AI Model Settings');
    };
    const handleOpenIrc = (options) => {
        const existing = windows.find(w => w.type === 'irc');
        if (existing) {
            if (!(options === null || options === void 0 ? void 0 : options.isMinimized)) {
                focusWindow(existing.id);
                if (existing.isMinimized) {
                    toggleMinimize(existing.id);
                }
            }
            return;
        }
        spawnAppWindow('irc', 'IRC Chat – #devussy-chat', undefined, options);
    };
    // Auto-launch IRC (always, minimized)
    (0, react_1.useEffect)(() => {
        try {
            // Check preference, default to true if not set, or just always do it per requirements
            const autoLaunch = localStorage.getItem('devussy_auto_launch_irc');
            if (autoLaunch !== 'false') {
                // Delay to let page load
                setTimeout(() => {
                    handleOpenIrc({ isMinimized: true });
                }, 500);
            }
        }
        catch (e) { }
    }, []);
    // Help window is now shown by default on startup (init state changed above)
    // This effect is no longer needed
    // Render Content based on Window Type
    const renderAppContent = (window) => {
        switch (window.type) {
            case 'init':
                return ((0, jsx_runtime_1.jsx)("div", { className: "h-full flex items-center justify-center p-8", children: (0, jsx_runtime_1.jsxs)(card_1.Card, { className: "w-full max-w-md border-primary/10 shadow-2xl", children: [(0, jsx_runtime_1.jsxs)(card_1.CardHeader, { children: [(0, jsx_runtime_1.jsxs)(card_1.CardTitle, { className: "text-2xl flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Sparkles, { className: "h-6 w-6 text-primary" }), "New Project"] }), (0, jsx_runtime_1.jsx)(card_1.CardDescription, { children: "Interview \u2192 Project design \u2192 DevPlan phases \u2192 Handoff Markdown artifacts" })] }), (0, jsx_runtime_1.jsxs)(card_1.CardContent, { className: "space-y-4", children: [(0, jsx_runtime_1.jsxs)(button_1.Button, { className: "w-full font-bold bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0", size: "lg", onClick: handleTryItNow, children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Play, { className: "mr-2 h-5 w-5 fill-current" }), "Try it now (One-click sample)"] }), (0, jsx_runtime_1.jsxs)("div", { className: "relative py-2", children: [(0, jsx_runtime_1.jsx)("div", { className: "absolute inset-0 flex items-center", children: (0, jsx_runtime_1.jsx)("span", { className: "w-full border-t" }) }), (0, jsx_runtime_1.jsx)("div", { className: "relative flex justify-center text-xs uppercase", children: (0, jsx_runtime_1.jsx)("span", { className: "bg-background px-2 text-muted-foreground", children: "Or Start Fresh" }) })] }), (0, jsx_runtime_1.jsxs)(button_1.Button, { className: "w-full font-bold", variant: "outline", size: "lg", onClick: handleStartInterview, children: [(0, jsx_runtime_1.jsx)(lucide_react_1.MessageSquare, { className: "mr-2 h-4 w-4" }), "Start Interactive Interview"] }), (0, jsx_runtime_1.jsxs)("div", { className: "relative py-2", children: [(0, jsx_runtime_1.jsx)("div", { className: "absolute inset-0 flex items-center", children: (0, jsx_runtime_1.jsx)("span", { className: "w-full border-t" }) }), (0, jsx_runtime_1.jsx)("div", { className: "relative flex justify-center text-xs uppercase", children: (0, jsx_runtime_1.jsx)("span", { className: "bg-background px-2 text-muted-foreground", children: "Or Manual Input" }) })] }), (0, jsx_runtime_1.jsxs)("div", { className: "space-y-2", children: [(0, jsx_runtime_1.jsx)("label", { htmlFor: "name", className: "text-sm font-medium", children: "Project Name" }), (0, jsx_runtime_1.jsx)(input_1.Input, { id: "name", placeholder: "e.g., E-commerce Platform", value: projectName, onChange: (e) => setProjectName(e.target.value) })] }), (0, jsx_runtime_1.jsxs)("div", { className: "space-y-2", children: [(0, jsx_runtime_1.jsx)("label", { htmlFor: "languages", className: "text-sm font-medium", children: "Languages & Stack" }), (0, jsx_runtime_1.jsx)(input_1.Input, { id: "languages", placeholder: "Python, Next.js, PostgreSQL...", value: languages, onChange: (e) => setLanguages(e.target.value) })] }), (0, jsx_runtime_1.jsxs)("div", { className: "space-y-2", children: [(0, jsx_runtime_1.jsx)("label", { htmlFor: "requirements", className: "text-sm font-medium", children: "Requirements" }), (0, jsx_runtime_1.jsx)(textarea_1.Textarea, { id: "requirements", placeholder: "I want a web app that...", className: "min-h-[100px]", value: requirements, onChange: (e) => setRequirements(e.target.value) })] })] }), (0, jsx_runtime_1.jsxs)(card_1.CardFooter, { className: "flex flex-col gap-2", children: [(0, jsx_runtime_1.jsxs)(button_1.Button, { className: "w-full", variant: "secondary", onClick: handleSkipInterview, disabled: !projectName || !requirements, children: ["Skip Interview & Initialize ", (0, jsx_runtime_1.jsx)(lucide_react_1.ArrowRight, { className: "ml-2 h-4 w-4" })] }), (0, jsx_runtime_1.jsx)("p", { className: "text-xs text-center text-muted-foreground mt-2", children: "Works with OpenAI / generic OpenAI-compatible / Requesty / Aether / AgentRouter" })] })] }) }));
            case 'interview':
                return ((0, jsx_runtime_1.jsx)(InterviewView_1.InterviewView, { modelConfig: getEffectiveConfig('interview'), onInterviewComplete: handleInterviewComplete }));
            case 'design':
                return ((0, jsx_runtime_1.jsx)(DesignView_1.DesignView, { projectName: projectName, requirements: requirements, languages: languages.split(',').map(l => l.trim()).filter(Boolean), modelConfig: getEffectiveConfig('design'), onDesignComplete: handleDesignComplete, autoRun: isAutoRun }));
            case 'plan':
                return ((0, jsx_runtime_1.jsx)(PlanView_1.PlanView, { design: design, onPlanApproved: handlePlanApproved, modelConfig: getEffectiveConfig('plan'), autoRun: isAutoRun }));
            case 'execute':
                return ((0, jsx_runtime_1.jsx)(ExecutionView_1.ExecutionView, { plan: plan, projectName: projectName, modelConfig: getEffectiveConfig('execute'), onComplete: handlePhaseComplete, autoRun: isAutoRun }));
            case 'handoff':
                return ((0, jsx_runtime_1.jsx)(HandoffView_1.HandoffView, { design: design, plan: plan, modelConfig: getEffectiveConfig('handoff') }));
            case 'model-settings': {
                const appDef = AppRegistry_1.AppRegistry[window.type];
                if (appDef && appDef.component) {
                    const Component = appDef.component;
                    return ((0, jsx_runtime_1.jsx)(Component, Object.assign({ configs: modelConfigs, onConfigsChange: setModelConfigs, activeStage: getActiveStage() }, (window.props || {}))));
                }
                return null;
            }
            case 'help': {
                const appDef = AppRegistry_1.AppRegistry[window.type];
                if (appDef && appDef.component) {
                    const Component = appDef.component;
                    return ((0, jsx_runtime_1.jsx)(Component, Object.assign({ dontShowHelpAgain: dontShowHelpAgain, setDontShowHelpAgain: setDontShowHelpAgain, analyticsOptOut: analyticsOptOut, setAnalyticsOptOut: setAnalyticsOptOut, onClose: () => closeWindow(window.id) }, (window.props || {}))));
                }
                return null;
            }
            case 'irc': {
                const appDef = AppRegistry_1.AppRegistry[window.type];
                if (appDef && appDef.component) {
                    const Component = appDef.component;
                    return (0, jsx_runtime_1.jsx)(Component, Object.assign({}, (window.props || {})));
                }
                return null;
            }
            default: {
                const appDef = AppRegistry_1.AppRegistry[window.type];
                if (appDef && appDef.component) {
                    const Component = appDef.component;
                    return (0, jsx_runtime_1.jsx)(Component, Object.assign({}, (window.props || {})));
                }
                return null;
            }
        }
    };
    return ((0, jsx_runtime_1.jsxs)("main", { className: "flex min-h-screen flex-col relative bg-transparent overflow-hidden", children: [theme === 'bliss' && ((0, jsx_runtime_1.jsxs)("div", { className: "absolute top-4 left-4 z-0 flex flex-col gap-6 p-4", children: [(0, jsx_runtime_1.jsxs)("button", { className: "group flex flex-col items-center w-[70px] gap-1 focus:outline-none", onDoubleClick: handleNewProject, children: [(0, jsx_runtime_1.jsx)("div", { className: "w-12 h-12 relative", children: (0, jsx_runtime_1.jsx)("img", { src: "/devussy_logo_minimal.png", className: "w-full h-full object-contain drop-shadow-md" }) }), (0, jsx_runtime_1.jsx)("span", { className: "text-white text-xs font-medium px-1 rounded group-hover:bg-[#0B61DE] group-focus:bg-[#0B61DE] group-focus:border group-focus:border-dotted drop-shadow-md text-center leading-tight", children: "My Computer" })] }), (0, jsx_runtime_1.jsxs)("button", { className: "group flex flex-col items-center w-[70px] gap-1 focus:outline-none", onDoubleClick: () => handleOpenIrc(), children: [(0, jsx_runtime_1.jsx)("div", { className: "w-12 h-12 relative bg-white/10 rounded-lg border border-white/20 flex items-center justify-center shadow-lg backdrop-blur-sm", children: (0, jsx_runtime_1.jsxs)("div", { className: "relative w-8 h-8", children: [(0, jsx_runtime_1.jsx)("div", { className: "absolute inset-0 bg-red-500 rounded-full transform -rotate-12 opacity-80" }), (0, jsx_runtime_1.jsx)("div", { className: "absolute inset-0 flex items-center justify-center", children: (0, jsx_runtime_1.jsx)(lucide_react_1.MessageSquare, { className: "text-white w-5 h-5 transform rotate-12", fill: "currentColor" }) }), (0, jsx_runtime_1.jsx)("div", { className: "absolute -bottom-1 -right-1 bg-green-500 w-3 h-3 rounded-full border-2 border-white" })] }) }), (0, jsx_runtime_1.jsx)("span", { className: "text-white text-xs font-medium px-1 rounded group-hover:bg-[#0B61DE] group-focus:bg-[#0B61DE] group-focus:border group-focus:border-dotted drop-shadow-md text-center leading-tight", children: "mIRC" })] })] })), theme !== 'bliss' && ((0, jsx_runtime_1.jsxs)("div", { className: "absolute top-4 right-4 z-50 flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(ThemeToggle_1.ThemeToggle, {}), (0, jsx_runtime_1.jsx)(CheckpointManager_1.CheckpointManager, { currentState: {
                            projectName,
                            languages,
                            requirements,
                            design,
                            plan,
                            stage: getActiveStage()
                        }, onLoad: handleLoadCheckpoint }), (0, jsx_runtime_1.jsx)(ModelSettings_1.ModelSettings, { configs: modelConfigs, onConfigsChange: setModelConfigs, activeStage: getActiveStage() })] })), windows.map((window) => ((0, jsx_runtime_1.jsx)(WindowFrame_1.WindowFrame, { title: window.title, initialPosition: window.position, initialSize: window.size, isActive: activeWindowId === window.id, isMinimized: window.isMinimized, onFocus: () => focusWindow(window.id), onClose: () => closeWindow(window.id), onMinimize: () => toggleMinimize(window.id), className: "absolute", style: { zIndex: window.zIndex }, children: renderAppContent(window) }, window.id))), (0, jsx_runtime_1.jsx)(Taskbar_1.Taskbar, { windows: windows.map(w => ({ id: w.id, title: w.title, type: w.type })), activeWindowId: activeWindowId, minimizedWindowIds: windows.filter(w => w.isMinimized).map(w => w.id), onWindowClick: (id) => {
                    const win = windows.find(w => w.id === id);
                    if (win === null || win === void 0 ? void 0 : win.isMinimized) {
                        toggleMinimize(id);
                    }
                    else {
                        focusWindow(id);
                    }
                }, onNewProject: handleNewProject, onHelp: handleHelp, onOpenModelSettings: handleOpenModelSettings, onOpenIrc: () => handleOpenIrc(), onOpenApp: (appId) => {
                    switch (appId) {
                        case 'init':
                            handleNewProject();
                            break;
                        case 'interview':
                            handleStartInterview();
                            break;
                        case 'design':
                            spawnAppWindow('design', 'System Design');
                            break;
                        case 'plan':
                            spawnAppWindow('plan', 'Development Plan');
                            break;
                        case 'execute':
                            spawnAppWindow('execute', 'Execution Phase');
                            break;
                        case 'handoff':
                            spawnAppWindow('handoff', 'Project Handoff');
                            break;
                        case 'help':
                            handleHelp();
                            break;
                        case 'model-settings':
                            handleOpenModelSettings();
                            break;
                        case 'irc':
                            handleOpenIrc();
                            break;
                        default: {
                            const appDef = AppRegistry_1.AppRegistry[appId];
                            const title = (appDef === null || appDef === void 0 ? void 0 : appDef.name) || 'Devussy App';
                            spawnAppWindow(appId, title);
                        }
                    }
                }, currentState: {
                    projectName,
                    languages,
                    requirements,
                    design,
                    plan,
                    stage: getActiveStage()
                }, onLoadCheckpoint: handleLoadCheckpoint, modelConfigs: modelConfigs, onModelConfigsChange: setModelConfigs, activeStage: getActiveStage(), ircNick: ircNick })] }));
}
function Page() {
    return ((0, jsx_runtime_1.jsx)(eventBus_1.EventBusProvider, { children: (0, jsx_runtime_1.jsx)(PageInner, {}) }));
}
