"use strict";
"use client";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HiveMindView = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const scroll_area_1 = require("@/components/ui/scroll-area");
const card_1 = require("@/components/ui/card");
const button_1 = require("@/components/ui/button");
const lucide_react_1 = require("lucide-react");
const utils_1 = require("@/utils");
const HiveMindView = ({ phase, plan, projectName, modelConfig, type = 'phase', requirements, languages }) => {
    const [drone1, setDrone1] = (0, react_1.useState)({ content: "", isActive: false, isComplete: false });
    const [drone2, setDrone2] = (0, react_1.useState)({ content: "", isActive: false, isComplete: false });
    const [drone3, setDrone3] = (0, react_1.useState)({ content: "", isActive: false, isComplete: false });
    const [arbiter, setArbiter] = (0, react_1.useState)({ content: "", isActive: false, isComplete: false });
    const [isFinished, setIsFinished] = (0, react_1.useState)(false);
    const [error, setError] = (0, react_1.useState)(null);
    const drone1Ref = (0, react_1.useRef)(null);
    const drone2Ref = (0, react_1.useRef)(null);
    const drone3Ref = (0, react_1.useRef)(null);
    const arbiterRef = (0, react_1.useRef)(null);
    const hasStartedRef = (0, react_1.useRef)(false);
    (0, react_1.useEffect)(() => {
        // Prevent duplicate execution in React StrictMode
        if (hasStartedRef.current)
            return;
        hasStartedRef.current = true;
        const executeHiveMind = async () => {
            var _a;
            try {
                const endpoint = type === 'design' ? '/api/design/hivemind' : '/api/plan/hivemind';
                const body = type === 'design'
                    ? { projectName, requirements, languages, modelConfig }
                    : { plan, phaseNumber: phase === null || phase === void 0 ? void 0 : phase.number, projectName, modelConfig };
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                if (!response.ok)
                    throw new Error('Failed to start HiveMind execution');
                const reader = (_a = response.body) === null || _a === void 0 ? void 0 : _a.getReader();
                if (!reader)
                    return;
                const decoder = new TextDecoder();
                while (true) {
                    const { done, value } = await reader.read();
                    if (done)
                        break;
                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.slice(6);
                            if (!dataStr.trim())
                                continue;
                            try {
                                const data = JSON.parse(dataStr);
                                if (data.type === 'drone1') {
                                    setDrone1(prev => (Object.assign(Object.assign({}, prev), { content: prev.content + data.content, isActive: true })));
                                }
                                else if (data.type === 'drone2') {
                                    setDrone2(prev => (Object.assign(Object.assign({}, prev), { content: prev.content + data.content, isActive: true })));
                                }
                                else if (data.type === 'drone3') {
                                    setDrone3(prev => (Object.assign(Object.assign({}, prev), { content: prev.content + data.content, isActive: true })));
                                }
                                else if (data.type === 'arbiter') {
                                    setArbiter(prev => (Object.assign(Object.assign({}, prev), { content: prev.content + data.content, isActive: true })));
                                }
                                else if (data.type === 'drone1_complete') {
                                    setDrone1(prev => (Object.assign(Object.assign({}, prev), { isComplete: true, isActive: false })));
                                }
                                else if (data.type === 'drone2_complete') {
                                    setDrone2(prev => (Object.assign(Object.assign({}, prev), { isComplete: true, isActive: false })));
                                }
                                else if (data.type === 'drone3_complete') {
                                    setDrone3(prev => (Object.assign(Object.assign({}, prev), { isComplete: true, isActive: false })));
                                }
                                else if (data.type === 'arbiter_complete') {
                                    setArbiter(prev => (Object.assign(Object.assign({}, prev), { isComplete: true, isActive: false })));
                                }
                                else if (data.done) {
                                    setIsFinished(true);
                                }
                                else if (data.error) {
                                    throw new Error(data.error);
                                }
                            }
                            catch (e) {
                                console.warn("Failed to parse SSE data:", e);
                            }
                        }
                    }
                }
            }
            catch (err) {
                console.error("HiveMind execution error:", err);
                setError(err.message || "An error occurred during HiveMind execution");
            }
        };
        executeHiveMind();
    }, [phase, plan, projectName, modelConfig]);
    // Auto-scroll each pane
    (0, react_1.useEffect)(() => {
        var _a;
        (_a = drone1Ref.current) === null || _a === void 0 ? void 0 : _a.scrollIntoView({ behavior: "smooth" });
    }, [drone1.content]);
    (0, react_1.useEffect)(() => {
        var _a;
        (_a = drone2Ref.current) === null || _a === void 0 ? void 0 : _a.scrollIntoView({ behavior: "smooth" });
    }, [drone2.content]);
    (0, react_1.useEffect)(() => {
        var _a;
        (_a = drone3Ref.current) === null || _a === void 0 ? void 0 : _a.scrollIntoView({ behavior: "smooth" });
    }, [drone3.content]);
    (0, react_1.useEffect)(() => {
        var _a;
        (_a = arbiterRef.current) === null || _a === void 0 ? void 0 : _a.scrollIntoView({ behavior: "smooth" });
    }, [arbiter.content]);
    const DronePane = ({ title, state, scrollRef, color }) => ((0, jsx_runtime_1.jsxs)(card_1.Card, { className: (0, utils_1.cn)("flex flex-col border-2 h-full", `border-${color}-500/30`), children: [(0, jsx_runtime_1.jsxs)("div", { className: (0, utils_1.cn)("px-3 py-2 border-b flex items-center justify-between", `bg-${color}-950/40`), children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Zap, { className: (0, utils_1.cn)("h-4 w-4", `text-${color}-400`) }), (0, jsx_runtime_1.jsx)("span", { className: (0, utils_1.cn)("font-semibold text-sm", `text-${color}-300`), children: title })] }), state.isActive && (0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: (0, utils_1.cn)("h-3 w-3 animate-spin", `text-${color}-400`) }), state.isComplete && (0, jsx_runtime_1.jsx)(lucide_react_1.Check, { className: (0, utils_1.cn)("h-3 w-3", `text-${color}-500`) })] }), (0, jsx_runtime_1.jsxs)(scroll_area_1.ScrollArea, { className: "flex-1 p-3 bg-black/80 font-mono text-xs overflow-auto", children: [(0, jsx_runtime_1.jsxs)("div", { className: (0, utils_1.cn)("whitespace-pre-wrap", `text-${color}-300`), children: [state.content || "Waiting...", state.isActive && (0, jsx_runtime_1.jsx)("span", { className: "animate-pulse", children: "_" })] }), (0, jsx_runtime_1.jsx)("div", { ref: scrollRef })] })] }));
    return ((0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col h-full p-4 gap-4", children: [(0, jsx_runtime_1.jsxs)("div", { className: "text-center", children: [(0, jsx_runtime_1.jsxs)("h2", { className: "text-xl font-bold flex items-center justify-center gap-2", children: ["\uD83D\uDC1D HiveMind: ", type === 'design' ? 'Design Phase' : `Phase ${phase === null || phase === void 0 ? void 0 : phase.number}`] }), (0, jsx_runtime_1.jsx)("p", { className: "text-sm text-muted-foreground", children: type === 'design' ? projectName : phase === null || phase === void 0 ? void 0 : phase.title })] }), error && ((0, jsx_runtime_1.jsx)("div", { className: "p-3 border border-red-500/50 bg-red-900/20 text-red-400 rounded text-sm", children: error })), (0, jsx_runtime_1.jsxs)("div", { className: "grid grid-cols-2 gap-4 flex-1", style: { gridAutoRows: '1fr' }, children: [(0, jsx_runtime_1.jsx)(DronePane, { title: "Drone 1", state: drone1, scrollRef: drone1Ref, color: "cyan" }), (0, jsx_runtime_1.jsx)(DronePane, { title: "Drone 2", state: drone2, scrollRef: drone2Ref, color: "purple" }), (0, jsx_runtime_1.jsx)(DronePane, { title: "Drone 3", state: drone3, scrollRef: drone3Ref, color: "orange" }), (0, jsx_runtime_1.jsxs)(card_1.Card, { className: "flex flex-col border-2 border-green-500/50 h-full", children: [(0, jsx_runtime_1.jsxs)("div", { className: "px-3 py-2 border-b flex items-center justify-between bg-green-950/40", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Zap, { className: "h-4 w-4 text-green-400" }), (0, jsx_runtime_1.jsx)("span", { className: "font-semibold text-sm text-green-300", children: "Arbiter (Synthesis)" }), isFinished && ((0, jsx_runtime_1.jsx)(button_1.Button, { size: "sm", variant: "ghost", className: "h-6 w-6 p-0 hover:bg-green-500/20 text-green-400", onClick: () => navigator.clipboard.writeText(arbiter.content), title: "Copy Result", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Copy, { className: "h-3 w-3" }) }))] }), arbiter.isActive && (0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "h-3 w-3 animate-spin text-green-400" }), arbiter.isComplete && (0, jsx_runtime_1.jsx)(lucide_react_1.Check, { className: "h-3 w-3 text-green-500" })] }), (0, jsx_runtime_1.jsxs)(scroll_area_1.ScrollArea, { className: "flex-1 p-3 bg-black/80 font-mono text-xs overflow-auto", children: [(0, jsx_runtime_1.jsxs)("div", { className: "whitespace-pre-wrap text-green-300", children: [arbiter.content || "Waiting for drones to complete...", arbiter.isActive && (0, jsx_runtime_1.jsx)("span", { className: "animate-pulse", children: "_" })] }), (0, jsx_runtime_1.jsx)("div", { ref: arbiterRef })] })] })] })] }));
};
exports.HiveMindView = HiveMindView;
