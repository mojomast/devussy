"use strict";
"use client";
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
exports.PlanView = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importStar(require("react"));
const button_1 = require("@/components/ui/button");
const scroll_area_1 = require("@/components/ui/scroll-area");
const lucide_react_1 = require("lucide-react");
const PhaseCard_1 = require("./PhaseCard");
const shareLinks_1 = require("@/shareLinks");
const eventBus_1 = require("@/apps/eventBus");
const PlanView = ({ design, modelConfig, onPlanApproved, autoRun = false }) => {
    const bus = (0, eventBus_1.useEventBus)();
    const [plan, setPlan] = (0, react_1.useState)(null);
    const [planContent, setPlanContent] = (0, react_1.useState)(""); // Track streaming content
    const [phases, setPhases] = (0, react_1.useState)([]); // Parsed phases
    const [expandedPhases, setExpandedPhases] = (0, react_1.useState)(new Set()); // Track expanded phases
    const [isLoading, setIsLoading] = (0, react_1.useState)(false);
    const [isEditing, setIsEditing] = (0, react_1.useState)(false); // For raw text editing
    const [viewMode, setViewMode] = (0, react_1.useState)('cards'); // Toggle between card/raw view
    const [error, setError] = (0, react_1.useState)(null);
    // Parse phases from raw text content
    const parsePhasesFromText = (text) => {
        const phases = [];
        const lines = text.split('\n');
        let currentPhase = null;
        let collectingContent = false;
        let contentLines = [];
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();
            // Match phase headers like "1. **Phase 1: Title**"
            const phaseMatch = trimmed.match(/^(\d+)\.\s*\*\*\s*Phase\s+\d+:\s*(.+?)\s*\*\*\s*$/i);
            if (phaseMatch) {
                // Save previous phase with collected content
                if (currentPhase && contentLines.length > 0) {
                    currentPhase.description = contentLines.join('\n').trim();
                    phases.push(currentPhase);
                }
                // Start new phase
                const phaseNum = parseInt(phaseMatch[1]);
                const title = phaseMatch[2].trim();
                currentPhase = {
                    number: phaseNum,
                    title: title,
                    description: ''
                };
                contentLines = [];
                collectingContent = true;
            }
            // Collect all content lines until next phase
            else if (collectingContent && currentPhase) {
                // Check if this is a "Brief:" line (not indented)
                if (trimmed.startsWith('Brief:')) {
                    const brief = trimmed.substring(6).trim();
                    if (brief)
                        contentLines.push(brief);
                    contentLines.push(''); // Add blank line after brief
                }
                // Bullet points (components)
                else if (trimmed.startsWith('- ')) {
                    contentLines.push(trimmed);
                }
                // Indented content (sub-bullets or continuation)
                else if (trimmed && (line.startsWith('   ') || line.startsWith('\t'))) {
                    contentLines.push('  ' + trimmed); // Preserve some indentation
                }
                // Empty lines between sections
                else if (!trimmed && contentLines.length > 0) {
                    // Don't add multiple consecutive blank lines
                    if (contentLines[contentLines.length - 1] !== '') {
                        contentLines.push('');
                    }
                }
            }
        }
        // Don't forget the last phase
        if (currentPhase && contentLines.length > 0) {
            currentPhase.description = contentLines.join('\n').trim();
            phases.push(currentPhase);
        }
        console.log('[PlanView] Parsed', phases.length, 'phases from text');
        phases.forEach((p) => { var _a; return console.log(`  Phase ${p.number}: ${p.title} (${((_a = p.description) === null || _a === void 0 ? void 0 : _a.length) || 0} chars)`); });
        return phases;
    };
    // Parse phases from plan data (fallback)
    const parsePhasesFromPlan = (planData) => {
        if (!planData || !planData.phases)
            return [];
        return planData.phases.map((phase, index) => ({
            number: phase.number || index + 1,
            title: phase.title || phase.name || `Phase ${index + 1}`,
            description: phase.description || ""
        }));
    };
    // Ref to track the current abort controller
    const abortControllerRef = react_1.default.useRef(null);
    const isGeneratingRef = react_1.default.useRef(false);
    const generatePlan = async () => {
        var _a;
        if (isGeneratingRef.current)
            return;
        setIsLoading(true);
        setError(null);
        setPlanContent(""); // Reset content
        isGeneratingRef.current = true;
        // Create new abort controller
        const controller = new AbortController();
        abortControllerRef.current = controller;
        try {
            // Bypass Next.js proxy and hit backend directly to avoid buffering
            const backendUrl = `/api/plan/basic`;
            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design: design,
                    modelConfig
                }),
                signal: controller.signal
            });
            if (!response.ok)
                throw new Error('Failed to generate plan');
            const reader = (_a = response.body) === null || _a === void 0 ? void 0 : _a.getReader();
            if (!reader)
                throw new Error('No response body');
            const decoder = new TextDecoder();
            let buffer = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || "";
                for (const part of parts) {
                    const line = part.trim();
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);
                        try {
                            const data = JSON.parse(dataStr);
                            // Display streaming content as it arrives
                            if (data.content) {
                                setPlanContent((prev) => prev + data.content);
                            }
                            if (data.done && data.plan) {
                                setPlan(data.plan);
                                console.log('[PlanView] Plan received, parsing phases from text...');
                                console.log('[PlanView] Plan content length:', planContent.length);
                                // Parse phases from the raw text content (more complete)
                                const parsedPhases = parsePhasesFromText(planContent);
                                // Fallback to plan data if text parsing fails
                                const finalPhases = parsedPhases.length > 0 ? parsedPhases : parsePhasesFromPlan(data.plan);
                                console.log('[PlanView] Using', finalPhases.length, 'phases');
                                setPhases(finalPhases);
                                // Expand all phases by default
                                setExpandedPhases(new Set(finalPhases.map((p) => p.number)));
                                return; // Stop reading
                            }
                            if (data.error) {
                                throw new Error(data.error);
                            }
                        }
                        catch (e) {
                            console.error("Failed to parse SSE JSON:", e);
                        }
                    }
                }
            }
        }
        catch (err) {
            if (err.name === 'AbortError') {
                console.log('Plan generation aborted');
                return;
            }
            console.error("Plan generation error:", err);
            setError(err.message || "An error occurred");
        }
        finally {
            if (abortControllerRef.current === controller) {
                setIsLoading(false);
                isGeneratingRef.current = false;
                abortControllerRef.current = null;
            }
        }
    };
    // Auto-generate on mount if not present
    react_1.default.useEffect(() => {
        if (plan || isLoading || error)
            return;
        const timeoutId = setTimeout(() => {
            generatePlan();
        }, 50); // Debounce to handle StrictMode double-mount
        return () => {
            clearTimeout(timeoutId);
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);
    // Phase management functions
    const handleUpdatePhase = (index, updatedPhase) => {
        const newPhases = [...phases];
        newPhases[index] = updatedPhase;
        setPhases(newPhases);
    };
    const handleDeletePhase = (index) => {
        const newPhases = phases.filter((_, i) => i !== index);
        // Renumber phases
        const renumbered = newPhases.map((p, i) => (Object.assign(Object.assign({}, p), { number: i + 1 })));
        setPhases(renumbered);
    };
    const handleMovePhase = (index, direction) => {
        const newPhases = [...phases];
        const targetIndex = direction === 'up' ? index - 1 : index + 1;
        if (targetIndex < 0 || targetIndex >= newPhases.length)
            return;
        // Swap
        [newPhases[index], newPhases[targetIndex]] = [newPhases[targetIndex], newPhases[index]];
        // Renumber
        const renumbered = newPhases.map((p, i) => (Object.assign(Object.assign({}, p), { number: i + 1 })));
        setPhases(renumbered);
    };
    const handleAddPhase = () => {
        const newPhase = {
            number: phases.length + 1,
            title: "New Phase",
            description: ""
        };
        setPhases([...phases, newPhase]);
        setExpandedPhases(new Set([...expandedPhases, newPhase.number]));
    };
    const togglePhaseExpanded = (phaseNumber) => {
        const newExpanded = new Set(expandedPhases);
        if (newExpanded.has(phaseNumber)) {
            newExpanded.delete(phaseNumber);
        }
        else {
            newExpanded.add(phaseNumber);
        }
        setExpandedPhases(newExpanded);
    };
    const handleApprove = () => {
        // Reconstruct plan with updated phases
        const updatedPlan = Object.assign(Object.assign({}, plan), { phases: phases.map((p) => ({
                number: p.number,
                title: p.title,
                description: p.description,
                steps: [] // Steps will be generated in execution phase
            })) });
        console.log('[PlanView] Approving plan with', updatedPlan.phases.length, 'phases');
        updatedPlan.phases.forEach((p) => {
            var _a;
            console.log(`  Phase ${p.number}: ${p.title} (desc: ${(_a = p.description) === null || _a === void 0 ? void 0 : _a.substring(0, 50)}...)`);
        });
        onPlanApproved(updatedPlan);
    };
    const hasAutoApproved = react_1.default.useRef(false);
    // Auto-approve effect
    (0, react_1.useEffect)(() => {
        if (autoRun && plan && !isLoading && phases.length > 0 && !hasAutoApproved.current) {
            const timer = setTimeout(() => {
                hasAutoApproved.current = true;
                handleApprove();
            }, 1500);
            return () => clearTimeout(timer);
        }
    }, [autoRun, plan, isLoading, phases]);
    const handleShare = async () => {
        var _a;
        if (!design || (!plan && !planContent))
            return;
        try {
            const shareData = {
                design,
                plan: plan || { raw_llm_response: planContent },
            };
            if (design === null || design === void 0 ? void 0 : design.project_name) {
                shareData.projectName = design.project_name;
            }
            const url = (0, shareLinks_1.generateShareLink)('plan', shareData);
            try {
                bus.emit('shareLinkGenerated', {
                    stage: 'plan',
                    data: shareData,
                    url,
                });
            }
            catch (err) {
                console.error('[PlanView] Failed to emit shareLinkGenerated event', err);
            }
            let copied = false;
            if (typeof navigator !== 'undefined' && ((_a = navigator.clipboard) === null || _a === void 0 ? void 0 : _a.writeText)) {
                try {
                    await navigator.clipboard.writeText(url);
                    copied = true;
                }
                catch (_b) {
                    copied = false;
                }
            }
            if (typeof window !== 'undefined') {
                window.prompt(copied
                    ? 'Share link copied to clipboard. You can also copy it from here:'
                    : 'Copy this Devussy share link:', url);
            }
        }
        catch (err) {
            console.error('[PlanView] Failed to generate share link', err);
        }
    };
    return ((0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col h-full", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between p-4 border-b border-border bg-muted/20", children: [(0, jsx_runtime_1.jsxs)("h2", { className: "text-lg font-semibold flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.FileText, { className: "h-5 w-5" }), "Development Plan"] }), (0, jsx_runtime_1.jsxs)("div", { className: "flex gap-2", children: [plan && !isLoading && ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(button_1.Button, { variant: "outline", size: "sm", onClick: () => setViewMode(viewMode === 'cards' ? 'raw' : 'cards'), children: viewMode === 'cards' ? ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(lucide_react_1.FileCode, { className: "h-4 w-4 mr-2" }), " Raw Text"] })) : ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(lucide_react_1.LayoutGrid, { className: "h-4 w-4 mr-2" }), " Cards"] })) }), viewMode === 'raw' && ((0, jsx_runtime_1.jsxs)(button_1.Button, { variant: "outline", size: "sm", onClick: () => setIsEditing(!isEditing), children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Edit2, { className: "h-4 w-4 mr-2" }), isEditing ? "Preview" : "Edit"] }))] })), (0, jsx_runtime_1.jsx)(button_1.Button, { variant: "outline", size: "sm", onClick: generatePlan, disabled: isLoading, children: "Regenerate" }), (0, jsx_runtime_1.jsxs)(button_1.Button, { variant: "outline", size: "sm", onClick: handleShare, disabled: !plan && !planContent, children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Share2, { className: "h-4 w-4 mr-2" }), "Share"] }), (0, jsx_runtime_1.jsxs)(button_1.Button, { size: "sm", onClick: handleApprove, disabled: !plan || isLoading || phases.length === 0, children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Play, { className: "h-4 w-4 mr-2" }), "Approve & Start Execution"] })] })] }), (0, jsx_runtime_1.jsx)(scroll_area_1.ScrollArea, { className: "flex-1 p-6", children: isLoading ? ((0, jsx_runtime_1.jsxs)("div", { className: "space-y-4", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center gap-2 text-muted-foreground", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "h-4 w-4 animate-spin text-primary" }), (0, jsx_runtime_1.jsx)("p", { children: "Generating development plan..." })] }), planContent && ((0, jsx_runtime_1.jsx)("div", { className: "prose prose-invert max-w-none font-mono text-sm", children: (0, jsx_runtime_1.jsx)("pre", { className: "whitespace-pre-wrap bg-transparent p-0", children: planContent }) }))] })) : error ? ((0, jsx_runtime_1.jsxs)("div", { className: "text-destructive p-4 border border-destructive/20 rounded-lg bg-destructive/10", children: ["Error: ", error] })) : plan ? (viewMode === 'cards' ? (
                // Card view - show editable phase cards
                (0, jsx_runtime_1.jsxs)("div", { className: "space-y-4", children: [(0, jsx_runtime_1.jsx)("div", { className: "prose prose-invert max-w-none", children: (0, jsx_runtime_1.jsx)("h3", { children: plan.summary }) }), (0, jsx_runtime_1.jsx)("div", { className: "space-y-3", children: phases.map((phase, index) => ((0, jsx_runtime_1.jsx)(PhaseCard_1.PhaseCard, { phase: phase, isExpanded: expandedPhases.has(phase.number), canMoveUp: index > 0, canMoveDown: index < phases.length - 1, onUpdate: (updated) => handleUpdatePhase(index, updated), onDelete: () => handleDeletePhase(index), onMoveUp: () => handleMovePhase(index, 'up'), onMoveDown: () => handleMovePhase(index, 'down'), onToggle: () => togglePhaseExpanded(phase.number) }, phase.number))) }), (0, jsx_runtime_1.jsxs)(button_1.Button, { variant: "outline", className: "w-full border-dashed", onClick: handleAddPhase, children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Plus, { className: "h-4 w-4 mr-2" }), "Add Phase"] })] })) : (
                // Raw text view - show full devplan text
                (0, jsx_runtime_1.jsxs)("div", { className: "space-y-4", children: [(0, jsx_runtime_1.jsx)("div", { className: "prose prose-invert max-w-none", children: (0, jsx_runtime_1.jsx)("h3", { children: plan.summary }) }), isEditing ? ((0, jsx_runtime_1.jsx)("textarea", { className: "w-full h-full min-h-[400px] bg-transparent border border-border rounded-lg p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary", value: planContent, onChange: (e) => setPlanContent(e.target.value) })) : ((0, jsx_runtime_1.jsx)("div", { className: "prose prose-invert max-w-none font-mono text-sm", children: (0, jsx_runtime_1.jsx)("pre", { className: "whitespace-pre-wrap bg-transparent p-0", children: planContent }) }))] }))) : null })] }));
};
exports.PlanView = PlanView;
