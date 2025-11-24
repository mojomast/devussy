"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.ModelSettings = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importStar(require("react"));
const lucide_react_1 = require("lucide-react");
const utils_1 = require("@/utils");
const framer_motion_1 = require("framer-motion");
const STAGE_ICONS = {
    global: lucide_react_1.Globe,
    interview: lucide_react_1.MessageSquare,
    design: lucide_react_1.Layers,
    plan: lucide_react_1.GitBranch,
    execute: lucide_react_1.Code2,
    handoff: lucide_react_1.ArrowRight,
};
const STAGE_LABELS = {
    global: 'Global Default',
    interview: 'Interview',
    design: 'Design',
    plan: 'Plan',
    execute: 'Execute',
    handoff: 'Handoff',
};
const ModelSettings = ({ configs, onConfigsChange, activeStage, isWindowMode = false }) => {
    const [isOpen, setIsOpen] = (0, react_1.useState)(false);
    const [selectedTab, setSelectedTab] = (0, react_1.useState)('global');
    const [models, setModels] = (0, react_1.useState)([]);
    const [loading, setLoading] = (0, react_1.useState)(false);
    const [error, setError] = (0, react_1.useState)(null);
    const [search, setSearch] = (0, react_1.useState)('');
    const [ircNick, setIrcNick] = (0, react_1.useState)('');
    // Sync selected tab with active stage if provided and open
    (0, react_1.useEffect)(() => {
        if ((isWindowMode || isOpen) && activeStage) {
            setSelectedTab(activeStage);
        }
    }, [isOpen, isWindowMode, activeStage]);
    // Load IRC Nick from localStorage
    (0, react_1.useEffect)(() => {
        const stored = localStorage.getItem('devussy_irc_nick');
        if (stored)
            setIrcNick(stored);
    }, []);
    const handleIrcNickChange = (e) => {
        const val = e.target.value;
        setIrcNick(val);
        localStorage.setItem('devussy_irc_nick', val);
    };
    (0, react_1.useEffect)(() => {
        const fetchModels = async () => {
            setLoading(true);
            try {
                const res = await fetch('/api/models');
                if (!res.ok)
                    throw new Error('Failed to fetch models');
                const data = await res.json();
                setModels(data.models || []);
            }
            catch (err) {
                console.error(err);
                setError('Failed to load models');
            }
            finally {
                setLoading(false);
            }
        };
        // In window mode, load immediately. In dropdown mode, load when opened.
        if ((isWindowMode || isOpen) && models.length === 0) {
            fetchModels();
        }
    }, [isOpen, isWindowMode, models.length]);
    const filteredModels = models.filter(m => m.id.toLowerCase().includes(search.toLowerCase()) ||
        m.name.toLowerCase().includes(search.toLowerCase()));
    const currentConfig = configs[selectedTab] || configs.global;
    const isOverride = selectedTab !== 'global' && configs[selectedTab] !== null;
    const handleConfigUpdate = (newConfig) => {
        if (selectedTab === 'global') {
            onConfigsChange(Object.assign(Object.assign({}, configs), { global: newConfig }));
        }
        else {
            onConfigsChange(Object.assign(Object.assign({}, configs), { [selectedTab]: newConfig }));
        }
    };
    const handleClearOverride = () => {
        if (selectedTab !== 'global') {
            onConfigsChange(Object.assign(Object.assign({}, configs), { [selectedTab]: null }));
        }
    };
    const handleCreateOverride = () => {
        if (selectedTab !== 'global') {
            onConfigsChange(Object.assign(Object.assign({}, configs), { [selectedTab]: Object.assign({}, configs.global) }));
        }
    };
    const renderContent = () => ((0, jsx_runtime_1.jsxs)("div", { className: "space-y-4", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between pb-2 border-b border-gray-300", children: [(0, jsx_runtime_1.jsxs)("h2", { className: "text-base font-bold text-gray-800 flex items-center gap-2", children: [react_1.default.createElement(STAGE_ICONS[selectedTab], { className: "w-5 h-5 text-blue-600" }), STAGE_LABELS[selectedTab], " Configuration"] }), selectedTab !== 'global' && (isOverride ? ((0, jsx_runtime_1.jsx)("button", { onClick: handleClearOverride, className: "text-xs text-red-600 hover:text-red-800 underline font-semibold", children: "Reset to Global" })) : ((0, jsx_runtime_1.jsx)("button", { onClick: handleCreateOverride, className: "text-xs text-blue-600 hover:text-blue-800 underline font-semibold", children: "Customize" })))] }), selectedTab === 'global' && ((0, jsx_runtime_1.jsxs)("div", { className: "space-y-2 pt-2 border-b border-gray-300 pb-4", children: [(0, jsx_runtime_1.jsxs)("h3", { className: "text-sm font-bold text-gray-800 flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.User, { className: "w-4 h-4" }), "IRC Identity"] }), (0, jsx_runtime_1.jsxs)("div", { className: "bg-white border border-gray-400 rounded p-3 space-y-2", children: [(0, jsx_runtime_1.jsx)("label", { className: "text-xs text-gray-600 block", children: "Persistent Nickname" }), (0, jsx_runtime_1.jsx)("input", { type: "text", value: ircNick, onChange: handleIrcNickChange, placeholder: "Enter IRC Nickname", className: "w-full border border-gray-400 rounded px-2 py-1 text-sm focus:outline-none focus:border-blue-500" }), (0, jsx_runtime_1.jsx)("p", { className: "text-[10px] text-gray-500", children: "This nickname will be used across sessions." })] })] })), (!isOverride && selectedTab !== 'global') ? ((0, jsx_runtime_1.jsxs)("div", { className: "p-6 rounded bg-blue-50 border border-blue-200 text-center space-y-3", children: [(0, jsx_runtime_1.jsx)("p", { className: "text-sm text-gray-700 font-semibold", children: "Using Global Configuration" }), (0, jsx_runtime_1.jsxs)("div", { className: "text-xs font-mono text-gray-600 bg-white p-2 rounded border border-gray-300", children: [configs.global.model, "  Temperature: ", configs.global.temperature] }), (0, jsx_runtime_1.jsxs)("button", { onClick: handleCreateOverride, className: "mt-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-xs font-bold", children: ["Customize for ", STAGE_LABELS[selectedTab]] })] })) : ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsxs)("div", { className: "space-y-2", children: [(0, jsx_runtime_1.jsx)("h3", { className: "text-sm font-bold text-gray-800", children: "AI Model" }), (0, jsx_runtime_1.jsxs)("div", { className: "bg-white border border-gray-400 rounded p-3 space-y-2", children: [(0, jsx_runtime_1.jsx)("input", { type: "text", placeholder: "Search models...", value: search, onChange: (e) => setSearch(e.target.value), className: "w-full border border-gray-400 rounded px-2 py-1 text-sm focus:outline-none focus:border-blue-500" }), (0, jsx_runtime_1.jsx)("div", { className: "max-h-40 overflow-y-auto space-y-1", children: loading ? ((0, jsx_runtime_1.jsx)("div", { className: "flex items-center justify-center py-4 text-gray-500", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "w-4 h-4 animate-spin" }) })) : error ? ((0, jsx_runtime_1.jsx)("div", { className: "text-red-600 text-xs py-2", children: error })) : (filteredModels.map(model => ((0, jsx_runtime_1.jsxs)("button", { onClick: () => handleConfigUpdate(Object.assign(Object.assign({}, currentConfig), { model: model.id })), className: (0, utils_1.cn)("w-full text-left px-2 py-1.5 rounded text-xs flex items-center justify-between hover:bg-blue-100", currentConfig.model === model.id ? "bg-blue-500 text-white font-bold" : "text-gray-800"), children: [(0, jsx_runtime_1.jsx)("span", { className: "truncate pr-2", children: model.id }), currentConfig.model === model.id && (0, jsx_runtime_1.jsx)(lucide_react_1.Check, { className: "w-3 h-3 flex-shrink-0" })] }, model.id)))) })] })] }), (0, jsx_runtime_1.jsxs)("div", { className: "space-y-2", children: [(0, jsx_runtime_1.jsx)("h3", { className: "text-sm font-bold text-gray-800", children: "Temperature" }), (0, jsx_runtime_1.jsxs)("div", { className: "bg-white border border-gray-400 rounded p-3 space-y-2", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between", children: [(0, jsx_runtime_1.jsx)("span", { className: "text-xs text-gray-600", children: "Current Value:" }), (0, jsx_runtime_1.jsx)("span", { className: "text-sm font-bold text-blue-600", children: currentConfig.temperature })] }), (0, jsx_runtime_1.jsx)("input", { type: "range", min: "0", max: "2", step: "0.1", value: currentConfig.temperature, onChange: (e) => handleConfigUpdate(Object.assign(Object.assign({}, currentConfig), { temperature: parseFloat(e.target.value) })), className: "w-full" }), (0, jsx_runtime_1.jsxs)("div", { className: "flex justify-between text-xs text-gray-600", children: [(0, jsx_runtime_1.jsx)("span", { children: "Precise" }), (0, jsx_runtime_1.jsx)("span", { children: "Creative" })] })] })] }), (0, jsx_runtime_1.jsxs)("div", { className: "space-y-2", children: [(0, jsx_runtime_1.jsx)("h3", { className: "text-sm font-bold text-gray-800", children: "Reasoning Effort" }), (0, jsx_runtime_1.jsx)("div", { className: "bg-white border border-gray-400 rounded p-3", children: (0, jsx_runtime_1.jsx)("div", { className: "grid grid-cols-4 gap-2", children: [null, 'low', 'medium', 'high'].map((effort) => ((0, jsx_runtime_1.jsx)("button", { onClick: () => handleConfigUpdate(Object.assign(Object.assign({}, currentConfig), { reasoning_effort: effort })), className: (0, utils_1.cn)("px-2 py-1.5 rounded text-xs font-bold border transition-colors uppercase", currentConfig.reasoning_effort === effort
                                            ? "bg-blue-500 border-blue-700 text-white"
                                            : "bg-gray-100 border-gray-400 text-gray-700 hover:bg-gray-200"), children: effort || 'None' }, String(effort)))) }) })] })] }))] }));
    // Window Mode Render
    if (isWindowMode) {
        return ((0, jsx_runtime_1.jsxs)("div", { className: "h-full flex flex-col bg-transparent", children: [(0, jsx_runtime_1.jsx)("div", { className: "flex border-b border-gray-400 bg-gradient-to-b from-white to-gray-100", children: Object.keys(STAGE_LABELS).map((stage) => {
                        const Icon = STAGE_ICONS[stage];
                        const hasOverride = stage !== 'global' && configs[stage] !== null;
                        return ((0, jsx_runtime_1.jsxs)("button", { onClick: () => setSelectedTab(stage), className: (0, utils_1.cn)("flex-1 flex items-center justify-center py-2 text-xs font-bold transition-colors relative border-r border-gray-300", selectedTab === stage
                                ? "bg-white text-blue-700"
                                : "text-gray-700 hover:bg-gray-50"), title: STAGE_LABELS[stage], children: [(0, jsx_runtime_1.jsx)(Icon, { className: "w-4 h-4 mr-1" }), STAGE_LABELS[stage], hasOverride && ((0, jsx_runtime_1.jsx)("span", { className: "absolute top-1 right-1 w-2 h-2 rounded-full bg-green-600" }))] }, stage));
                    }) }), (0, jsx_runtime_1.jsx)("div", { className: "flex-1 overflow-auto p-4", children: renderContent() })] }));
    }
    return ((0, jsx_runtime_1.jsxs)("div", { className: "relative", children: [(0, jsx_runtime_1.jsxs)("button", { onClick: () => setIsOpen(!isOpen), className: "flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Settings, { className: "w-4 h-4 text-gray-600" }), (0, jsx_runtime_1.jsx)("span", { className: "text-sm font-medium text-gray-700", children: configs.global.model.split('/').pop() }), (0, jsx_runtime_1.jsx)(lucide_react_1.ChevronDown, { className: (0, utils_1.cn)("w-3 h-3 text-gray-500 transition-transform", isOpen && "rotate-180") })] }), (0, jsx_runtime_1.jsx)(framer_motion_1.AnimatePresence, { children: isOpen && ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)("div", { className: "fixed inset-0 z-40", onClick: () => setIsOpen(false) }), (0, jsx_runtime_1.jsxs)(framer_motion_1.motion.div, { initial: { opacity: 0, y: 10, scale: 0.95 }, animate: { opacity: 1, y: 0, scale: 1 }, exit: { opacity: 0, y: 10, scale: 0.95 }, className: "absolute right-0 mt-2 w-[400px] bg-white border border-gray-300 rounded-lg shadow-xl z-50 overflow-hidden flex flex-col max-h-[80vh]", children: [(0, jsx_runtime_1.jsx)("div", { className: "flex border-b border-gray-200 bg-gray-50 overflow-x-auto", children: Object.keys(STAGE_LABELS).map((stage) => ((0, jsx_runtime_1.jsx)("button", { onClick: () => setSelectedTab(stage), className: (0, utils_1.cn)("px-3 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors", selectedTab === stage
                                            ? "border-blue-500 text-blue-600 bg-white"
                                            : "border-transparent text-gray-600 hover:bg-gray-100"), children: STAGE_LABELS[stage] }, stage))) }), (0, jsx_runtime_1.jsx)("div", { className: "p-4 overflow-y-auto", children: renderContent() })] })] })) })] }));
};
exports.ModelSettings = ModelSettings;
