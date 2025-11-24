"use strict";
"use client";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PhaseDetailView = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const button_1 = require("@/components/ui/button");
const scroll_area_1 = require("@/components/ui/scroll-area");
const lucide_react_1 = require("lucide-react");
const PhaseDetailView = ({ phase, plan, projectName, modelConfig, onComplete, status, output: controlledOutput, error: controlledError, onStart }) => {
    const [internalOutput, setInternalOutput] = (0, react_1.useState)("");
    const [internalIsExecuting, setInternalIsExecuting] = (0, react_1.useState)(false);
    const [internalIsComplete, setInternalIsComplete] = (0, react_1.useState)(false);
    const [internalError, setInternalError] = (0, react_1.useState)(null);
    // Derived state (controlled vs uncontrolled)
    const isControlled = typeof status !== 'undefined';
    const output = isControlled ? controlledOutput || "" : internalOutput;
    const isExecuting = isControlled ? status === 'running' : internalIsExecuting;
    const isComplete = isControlled ? status === 'complete' : internalIsComplete;
    const error = isControlled ? controlledError || null : internalError;
    const scrollRef = (0, react_1.useRef)(null);
    const hasStarted = (0, react_1.useRef)(false);
    // Update hasStarted ref based on status
    (0, react_1.useEffect)(() => {
        if (isExecuting || isComplete || output) {
            hasStarted.current = true;
        }
    }, [isExecuting, isComplete, output]);
    // Auto-scroll to bottom
    (0, react_1.useEffect)(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [output]);
    const executePhase = async () => {
        var _a;
        if (onStart) {
            onStart();
            return;
        }
        if (isExecuting || isComplete)
            return;
        setInternalIsExecuting(true);
        setInternalError(null);
        hasStarted.current = true;
        setInternalOutput("");
        try {
            const response = await fetch('/api/plan/detail', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    basicPlan: plan,
                    phaseNumber: phase.number,
                    projectName,
                    modelConfig
                })
            });
            if (!response.ok)
                throw new Error('Failed to start phase execution');
            const reader = (_a = response.body) === null || _a === void 0 ? void 0 : _a.getReader();
            if (!reader)
                return;
            const decoder = new TextDecoder();
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                const chunk = decoder.decode(value, { stream: true });
                // Parse SSE data
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);
                        if (!dataStr.trim())
                            continue;
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.content) {
                                setInternalOutput(prev => prev + data.content);
                            }
                            else if (data.error) {
                                throw new Error(data.error);
                            }
                            else if (data.done) {
                                setInternalIsComplete(true);
                            }
                        }
                        catch (e) {
                            // If it's not JSON, just append it (fallback)
                            console.warn("Failed to parse SSE data:", e);
                        }
                    }
                }
            }
        }
        catch (err) {
            console.error("Phase execution error:", err);
            setInternalError(err.message || "An error occurred during execution");
            setInternalOutput(prev => prev + `\n\n[ERROR]: ${err.message}`);
        }
        finally {
            setInternalIsExecuting(false);
        }
    };
    return ((0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col h-full", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between p-4 border-b border-border bg-muted/20", children: [(0, jsx_runtime_1.jsxs)("h2", { className: "text-lg font-semibold flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Terminal, { className: "h-5 w-5" }), "Phase ", phase.number, " Execution"] }), (0, jsx_runtime_1.jsxs)("div", { className: "flex gap-2", children: [!hasStarted.current && ((0, jsx_runtime_1.jsxs)(button_1.Button, { size: "sm", onClick: executePhase, disabled: isExecuting, children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Play, { className: "h-4 w-4 mr-2" }), "Start Phase"] })), isComplete && onComplete && ((0, jsx_runtime_1.jsxs)(button_1.Button, { size: "sm", onClick: onComplete, variant: "default", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Check, { className: "h-4 w-4 mr-2" }), "Next Phase"] }))] })] }), (0, jsx_runtime_1.jsxs)(scroll_area_1.ScrollArea, { className: "flex-1 p-4 bg-black/90 font-mono text-sm text-green-400 overflow-auto", children: [(0, jsx_runtime_1.jsxs)("div", { className: "whitespace-pre-wrap", children: [output, isExecuting && (0, jsx_runtime_1.jsx)("span", { className: "animate-pulse", children: "_" })] }), (0, jsx_runtime_1.jsx)("div", { ref: scrollRef }), !hasStarted.current && !error && ((0, jsx_runtime_1.jsx)("div", { className: "text-muted-foreground text-center mt-10", children: "Click \"Start Phase\" to begin execution." })), error && ((0, jsx_runtime_1.jsxs)("div", { className: "mt-4 p-4 border border-red-500/50 bg-red-900/20 text-red-400 rounded", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center gap-2 font-bold mb-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.AlertCircle, { className: "h-4 w-4" }), "Execution Failed"] }), error, (0, jsx_runtime_1.jsx)(button_1.Button, { variant: "outline", size: "sm", className: "mt-4 border-red-500/50 hover:bg-red-900/40 text-red-400", onClick: executePhase, children: "Retry" })] }))] })] }));
};
exports.PhaseDetailView = PhaseDetailView;
