"use strict";
"use client";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ExecutionView = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const button_1 = require("@/components/ui/button");
const select_1 = require("@/components/ui/select");
const lucide_react_1 = require("lucide-react");
const PhaseDetailView_1 = require("./PhaseDetailView");
const shareLinks_1 = require("@/shareLinks");
const eventBus_1 = require("@/apps/eventBus");
const ExecutionView = ({ plan, projectName, modelConfig, onComplete, onExecutionStateChange, initialPhases, autoRun = false }) => {
    const bus = (0, eventBus_1.useEventBus)();
    const [viewMode, setViewMode] = (0, react_1.useState)('grid');
    const [concurrency, setConcurrency] = (0, react_1.useState)(modelConfig.concurrency || 3);
    const [selectedTab, setSelectedTab] = (0, react_1.useState)(1);
    const [phases, setPhases] = (0, react_1.useState)([]);
    const [isExecuting, setIsExecuting] = (0, react_1.useState)(false);
    const [isPaused, setIsPaused] = (0, react_1.useState)(false);
    const [completedCount, setCompletedCount] = (0, react_1.useState)(0);
    const buildDetailedPlan = () => {
        if (!plan || !plan.phases)
            return plan;
        return Object.assign(Object.assign({}, plan), { phases: plan.phases.map((originalPhase) => {
                const executedPhase = phases.find((p) => p.number === originalPhase.number);
                if (executedPhase && executedPhase.detailedPhase) {
                    return executedPhase.detailedPhase;
                }
                return originalPhase;
            }) });
    };
    const handleManualComplete = () => {
        var _a;
        const detailedPlan = buildDetailedPlan();
        try {
            const finalPlan = detailedPlan || plan;
            bus.emit('executionCompleted', {
                projectName,
                plan: finalPlan,
                totalPhases: ((_a = finalPlan === null || finalPlan === void 0 ? void 0 : finalPlan.phases) === null || _a === void 0 ? void 0 : _a.length) || 0,
            });
        }
        catch (err) {
            console.error('[ExecutionView] Failed to emit executionCompleted event', err);
        }
        onComplete(detailedPlan);
    };
    const handleShare = async () => {
        var _a;
        if (!plan)
            return;
        try {
            const shareData = {
                projectName,
                plan,
            };
            const url = (0, shareLinks_1.generateShareLink)('execute', shareData);
            try {
                bus.emit('shareLinkGenerated', {
                    stage: 'execute',
                    data: shareData,
                    url,
                });
            }
            catch (err) {
                console.error('[ExecutionView] Failed to emit shareLinkGenerated event', err);
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
            console.error('[ExecutionView] Failed to generate share link', err);
        }
    };
    // Update concurrency when modelConfig changes
    (0, react_1.useEffect)(() => {
        if (modelConfig.concurrency && !isExecuting) {
            setConcurrency(modelConfig.concurrency);
        }
    }, [modelConfig.concurrency, isExecuting]);
    const scrollRefs = (0, react_1.useRef)(new Map());
    const scrollContainerRefs = (0, react_1.useRef)(new Map());
    const abortControllersRef = (0, react_1.useRef)(new Map());
    const phaseOutputBuffers = (0, react_1.useRef)(new Map());
    const updateTimers = (0, react_1.useRef)(new Map());
    // Initialize phases from plan or restore from checkpoint
    (0, react_1.useEffect)(() => {
        if (initialPhases && initialPhases.length > 0) {
            console.log('[ExecutionView] Restoring phases from checkpoint:', initialPhases.length);
            setPhases(initialPhases);
        }
        else if (plan && plan.phases) {
            // Only initialize if we don't have phases OR if the plan has changed significantly
            // AND we haven't started execution yet.
            // This prevents resetting state when "Proceed to Handoff" updates the plan prop.
            setPhases((prev) => {
                if (prev.length > 0 && prev.some((p) => p.status !== 'queued' || p.output)) {
                    console.log('[ExecutionView] Preserving existing execution state');
                    return prev;
                }
                const initialPhases = plan.phases.map((p) => ({
                    number: p.number,
                    title: p.title || p.name || `Phase ${p.number}`,
                    status: 'queued',
                    output: '',
                    progress: 0
                }));
                console.log('[ExecutionView] Initialized phases:', initialPhases.map((p) => ({ number: p.number, title: p.title })));
                return initialPhases;
            });
        }
    }, [plan, initialPhases]);
    // Emit phase state changes for checkpoints
    (0, react_1.useEffect)(() => {
        if (onExecutionStateChange && phases.length > 0) {
            onExecutionStateChange(phases);
        }
    }, [phases, onExecutionStateChange]);
    // Auto-scroll for each phase - scroll to bottom when content updates
    (0, react_1.useEffect)(() => {
        phases.forEach((phase) => {
            if (phase.status === 'running') {
                const scrollContainer = scrollContainerRefs.current.get(phase.number);
                if (scrollContainer) {
                    // Scroll to bottom smoothly
                    scrollContainer.scrollTop = scrollContainer.scrollHeight;
                }
            }
        });
    }, [phases]);
    // Auto-start execution when mounted
    (0, react_1.useEffect)(() => {
        if (phases.length > 0 && !isExecuting) {
            startExecution();
        }
    }, [phases.length]);
    const executePhase = async (phase) => {
        var _a, _b, _c;
        console.log('[executePhase] ========== Starting phase', phase.number, phase.title, '==========');
        if (isPaused) {
            console.log('[executePhase] Skipping phase', phase.number, '- execution is paused');
            return;
        }
        const controller = new AbortController();
        abortControllersRef.current.set(phase.number, controller);
        console.log('[executePhase] Setting phase', phase.number, 'to running state');
        // Initialize output buffer for this phase
        const initialOutput = `Starting Phase ${phase.number}: ${phase.title}...\n\n`;
        phaseOutputBuffers.current.set(phase.number, initialOutput);
        setPhases((prev) => {
            const updated = prev.map((p) => p.number === phase.number
                ? Object.assign(Object.assign({}, p), { status: 'running', output: initialOutput }) : p);
            console.log('[executePhase] Updated phases:', updated.map((p) => ({ number: p.number, status: p.status })));
            return updated;
        });
        try {
            const backendUrl = `/api/plan/detail`;
            console.log('[executePhase] Fetching from', backendUrl, 'for phase', phase.number);
            const requestBody = {
                plan: plan,
                phaseNumber: phase.number,
                projectName,
                modelConfig
            };
            console.log('[executePhase] Request body:', {
                phaseNumber: phase.number,
                projectName,
                planPhasesCount: (_a = plan === null || plan === void 0 ? void 0 : plan.phases) === null || _a === void 0 ? void 0 : _a.length,
                firstPhase: (_b = plan === null || plan === void 0 ? void 0 : plan.phases) === null || _b === void 0 ? void 0 : _b[0]
            });
            // Add timeout to detect hanging requests
            const fetchTimeout = setTimeout(() => {
                console.warn('[executePhase] Fetch taking longer than 10s for phase', phase.number);
            }, 10000);
            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody),
                signal: controller.signal
            });
            clearTimeout(fetchTimeout);
            console.log('[executePhase] Response status:', response.status);
            console.log('[executePhase] Response headers:', {
                contentType: response.headers.get('content-type'),
                cacheControl: response.headers.get('cache-control')
            });
            if (!response.ok) {
                const errorText = await response.text();
                console.error('[executePhase] Error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText || 'Failed to start phase execution'}`);
            }
            const reader = (_c = response.body) === null || _c === void 0 ? void 0 : _c.getReader();
            if (!reader) {
                console.error('[executePhase] No response body!');
                throw new Error('No response body');
            }
            console.log('[executePhase] Got reader, starting to read stream for phase', phase.number);
            const decoder = new TextDecoder();
            let buffer = "";
            let chunkCount = 0;
            let contentCount = 0;
            console.log('[executePhase] Starting to read stream for phase', phase.number);
            let phaseCompleted = false;
            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        console.log('[executePhase] Stream done for phase', phase.number);
                        break;
                    }
                    chunkCount++;
                    const chunk = decoder.decode(value, { stream: true });
                    buffer += chunk;
                    if (chunkCount % 10 === 0) {
                        console.log(`[executePhase] Phase ${phase.number}: Received ${chunkCount} chunks, ${contentCount} content messages`);
                    }
                    const parts = buffer.split('\n\n');
                    buffer = parts.pop() || "";
                    for (const part of parts) {
                        const line = part.trim();
                        if (line.startsWith('data: ')) {
                            const dataStr = line.slice(6);
                            try {
                                const data = JSON.parse(dataStr);
                                if (data.content) {
                                    contentCount++;
                                    if (contentCount <= 5 || contentCount % 50 === 0) {
                                        console.log(`[executePhase] Phase ${phase.number}: Content #${contentCount}:`, data.content.substring(0, 50));
                                    }
                                    // Accumulate content in buffer
                                    const currentBuffer = phaseOutputBuffers.current.get(phase.number) || '';
                                    phaseOutputBuffers.current.set(phase.number, currentBuffer + data.content);
                                    // Debounce state updates to avoid overwhelming React
                                    const existingTimer = updateTimers.current.get(phase.number);
                                    if (existingTimer) {
                                        clearTimeout(existingTimer);
                                    }
                                    const timer = setTimeout(() => {
                                        const bufferedContent = phaseOutputBuffers.current.get(phase.number) || '';
                                        setPhases((prev) => prev.map((p) => p.number === phase.number
                                            ? Object.assign(Object.assign({}, p), { output: bufferedContent }) : p));
                                        // Auto-scroll to bottom after update
                                        requestAnimationFrame(() => {
                                            const scrollContainer = scrollContainerRefs.current.get(phase.number);
                                            if (scrollContainer) {
                                                scrollContainer.scrollTop = scrollContainer.scrollHeight;
                                            }
                                        });
                                        updateTimers.current.delete(phase.number);
                                    }, 50); // Update every 50ms max
                                    updateTimers.current.set(phase.number, timer);
                                }
                                if (data.error) {
                                    console.error('[executePhase] Phase', phase.number, 'error:', data.error);
                                    throw new Error(data.error);
                                }
                                if (data.done) {
                                    console.log('[executePhase] Phase', phase.number, 'done signal received');
                                    phaseCompleted = true;
                                    // Flush any pending updates
                                    const existingTimer = updateTimers.current.get(phase.number);
                                    if (existingTimer) {
                                        clearTimeout(existingTimer);
                                        updateTimers.current.delete(phase.number);
                                    }
                                    // Final state update with buffered content AND detailed phase data
                                    const finalOutput = phaseOutputBuffers.current.get(phase.number) || '';
                                    setPhases((prev) => prev.map((p) => p.number === phase.number
                                        ? Object.assign(Object.assign({}, p), { status: 'complete', progress: 100, output: finalOutput, detailedPhase: data.phase // Store the detailed phase with steps
                                         }) : p));
                                    setCompletedCount(prev => prev + 1);
                                    // Clean up buffer
                                    phaseOutputBuffers.current.delete(phase.number);
                                    // Close reader to release connection
                                    reader.cancel();
                                    console.log('[executePhase] Phase', phase.number, 'reader closed');
                                    return;
                                }
                            }
                            catch (e) {
                                if (e.message && !e.message.includes('Unexpected token')) {
                                    console.error('[executePhase] Parse error:', e);
                                    throw e;
                                }
                            }
                        }
                    }
                }
                // If stream ended without explicit done signal, mark as complete anyway
                if (!phaseCompleted) {
                    console.log('[executePhase] Stream ended without done signal for phase', phase.number, '- marking complete');
                    // Flush any pending updates
                    const existingTimer = updateTimers.current.get(phase.number);
                    if (existingTimer) {
                        clearTimeout(existingTimer);
                        updateTimers.current.delete(phase.number);
                    }
                    // Final state update with buffered content
                    const finalOutput = phaseOutputBuffers.current.get(phase.number) || '';
                    setPhases((prev) => prev.map((p) => p.number === phase.number
                        ? Object.assign(Object.assign({}, p), { status: 'complete', progress: 100, output: finalOutput }) : p));
                    setCompletedCount(prev => prev + 1);
                    // Clean up buffer
                    phaseOutputBuffers.current.delete(phase.number);
                }
            }
            finally {
                // Always close the reader to release the connection
                try {
                    reader.cancel();
                    console.log('[executePhase] Phase', phase.number, 'reader closed in finally block');
                }
                catch (e) {
                    console.log('[executePhase] Phase', phase.number, 'reader already closed');
                }
            }
        }
        catch (err) {
            // Clean up timers and buffers
            const existingTimer = updateTimers.current.get(phase.number);
            if (existingTimer) {
                clearTimeout(existingTimer);
                updateTimers.current.delete(phase.number);
            }
            const currentOutput = phaseOutputBuffers.current.get(phase.number) || '';
            phaseOutputBuffers.current.delete(phase.number);
            if (err.name === 'AbortError') {
                setPhases((prev) => prev.map((p) => p.number === phase.number
                    ? Object.assign(Object.assign({}, p), { status: 'queued', output: currentOutput + '\n[Paused]' }) : p));
            }
            else {
                console.error(`Phase ${phase.number} execution error:`, err);
                setPhases((prev) => prev.map((p) => p.number === phase.number
                    ? Object.assign(Object.assign({}, p), { status: 'failed', error: err.message || 'Unknown error', output: currentOutput + `\n\n[ERROR]: ${err.message}` }) : p));
            }
        }
        finally {
            abortControllersRef.current.delete(phase.number);
        }
    };
    const hasAutoCompleted = (0, react_1.useRef)(false);
    const startExecution = async () => {
        var _a;
        console.log('[ExecutionView] Starting execution with', phases.length, 'phases - STARTING ALL AT ONCE');
        setIsExecuting(true);
        setIsPaused(false);
        // Start ALL phases immediately
        const promises = phases.map((phase) => {
            console.log('[ExecutionView] Starting phase', phase.number);
            return executePhase(phase).catch(err => {
                console.error('[ExecutionView] Phase', phase.number, 'failed:', err);
            });
        });
        // Wait for all to complete
        console.log('[ExecutionView] Waiting for all', promises.length, 'phases to complete...');
        await Promise.all(promises);
        console.log('[ExecutionView] All phases completed');
        setIsExecuting(false);
        // Check if all phases completed successfully - use effect to avoid setState during render
        const allComplete = phases.every((p) => p.status === 'complete');
        console.log('[ExecutionView] All complete?', allComplete);
        // Auto-advance if enabled
        if (autoRun && allComplete && onComplete && !hasAutoCompleted.current) {
            console.log('[ExecutionView] Auto-advancing to handoff...');
            hasAutoCompleted.current = true;
            const detailedPlan = buildDetailedPlan();
            try {
                const finalPlan = detailedPlan || plan;
                bus.emit('executionCompleted', {
                    projectName,
                    plan: finalPlan,
                    totalPhases: ((_a = finalPlan === null || finalPlan === void 0 ? void 0 : finalPlan.phases) === null || _a === void 0 ? void 0 : _a.length) || 0,
                });
            }
            catch (err) {
                console.error('[ExecutionView] Failed to emit executionCompleted event (autoRun)', err);
            }
            setTimeout(() => onComplete(detailedPlan), 2000); // 2s delay for visual confirmation
        }
    };
    const togglePause = () => {
        setIsPaused(!isPaused);
        if (isPaused) {
            // Resume
            startExecution();
        }
        else {
            // Pause - abort controllers will be handled in the execution loop
        }
    };
    const getStatusIcon = (status) => {
        switch (status) {
            case 'complete':
                return (0, jsx_runtime_1.jsx)(lucide_react_1.Check, { className: "h-4 w-4 text-green-500" });
            case 'running':
                return (0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "h-4 w-4 text-blue-500 animate-spin" });
            case 'failed':
                return (0, jsx_runtime_1.jsx)(lucide_react_1.AlertCircle, { className: "h-4 w-4 text-red-500" });
            case 'queued':
            default:
                return (0, jsx_runtime_1.jsx)(lucide_react_1.Clock, { className: "h-4 w-4 text-gray-500" });
        }
    };
    const getStatusColor = (status) => {
        switch (status) {
            case 'complete': return 'border-green-500/50 bg-green-900/10';
            case 'running': return 'border-blue-500/50 bg-blue-900/10';
            case 'failed': return 'border-red-500/50 bg-red-900/10';
            case 'queued':
            default: return 'border-border/50';
        }
    };
    const renderPhaseColumn = (phase) => ((0, jsx_runtime_1.jsx)("div", { className: `${getStatusColor(phase.status)} rounded-lg overflow-hidden border flex flex-col h-full`, children: (0, jsx_runtime_1.jsx)(PhaseDetailView_1.PhaseDetailView, { phase: { number: phase.number }, plan: plan, projectName: projectName, modelConfig: modelConfig, status: phase.status, output: phase.output, error: phase.error, onStart: () => executePhase(phase) }) }, phase.number));
    return ((0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col h-full", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between p-4 border-b border-border bg-muted/20", children: [(0, jsx_runtime_1.jsxs)("h2", { className: "text-lg font-semibold flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Terminal, { className: "h-5 w-5" }), "Execution Phase", (0, jsx_runtime_1.jsxs)("span", { className: "text-sm text-muted-foreground font-normal", children: ["(", completedCount, "/", phases.length, " complete)"] })] }), (0, jsx_runtime_1.jsxs)("div", { className: "flex items-center gap-3", children: [(0, jsx_runtime_1.jsxs)(button_1.Button, { size: "sm", onClick: handleManualComplete, disabled: isExecuting, className: completedCount === phases.length ? "bg-green-600 hover:bg-green-700 text-white" : "", children: ["Proceed to Handoff ", (0, jsx_runtime_1.jsx)(lucide_react_1.ArrowRight, { className: "ml-2 h-4 w-4" })] }), (0, jsx_runtime_1.jsxs)(button_1.Button, { variant: "outline", size: "sm", onClick: handleShare, disabled: !plan, children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Share2, { className: "h-4 w-4 mr-2" }), "Share"] }), (0, jsx_runtime_1.jsxs)("div", { className: "flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)("span", { className: "text-sm text-muted-foreground", children: "Concurrency:" }), (0, jsx_runtime_1.jsxs)(select_1.Select, { value: concurrency.toString(), onValueChange: (v) => setConcurrency(parseInt(v)), disabled: isExecuting, children: [(0, jsx_runtime_1.jsx)(select_1.SelectTrigger, { className: "w-20 h-8", children: (0, jsx_runtime_1.jsx)(select_1.SelectValue, {}) }), (0, jsx_runtime_1.jsxs)(select_1.SelectContent, { children: [(0, jsx_runtime_1.jsx)(select_1.SelectItem, { value: "1", children: "1" }), (0, jsx_runtime_1.jsx)(select_1.SelectItem, { value: "2", children: "2" }), (0, jsx_runtime_1.jsx)(select_1.SelectItem, { value: "3", children: "3" }), (0, jsx_runtime_1.jsx)(select_1.SelectItem, { value: "5", children: "5" }), (0, jsx_runtime_1.jsx)(select_1.SelectItem, { value: phases.length.toString(), children: "All" })] })] })] }), (0, jsx_runtime_1.jsx)(button_1.Button, { variant: "outline", size: "sm", onClick: () => setViewMode(viewMode === 'grid' ? 'tabs' : 'grid'), children: viewMode === 'grid' ? ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(lucide_react_1.List, { className: "h-4 w-4 mr-2" }), " Tabs"] })) : ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(lucide_react_1.LayoutGrid, { className: "h-4 w-4 mr-2" }), " Grid"] })) }), (0, jsx_runtime_1.jsx)(button_1.Button, { variant: "outline", size: "sm", onClick: togglePause, disabled: !isExecuting && !isPaused, children: isPaused ? ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Play, { className: "h-4 w-4 mr-2" }), " Resume"] })) : ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Pause, { className: "h-4 w-4 mr-2" }), " Pause"] })) })] })] }), (0, jsx_runtime_1.jsx)("div", { className: "flex-1 overflow-hidden", children: viewMode === 'grid' ? ((0, jsx_runtime_1.jsx)("div", { className: `grid gap-4 p-4 h-full ${phases.length <= 3 ? 'grid-cols-3' :
                        phases.length <= 6 ? 'grid-cols-3' :
                            'grid-cols-4'}`, style: { gridAutoRows: '1fr' }, children: phases.map((phase) => renderPhaseColumn(phase)) })) : ((0, jsx_runtime_1.jsxs)("div", { className: "h-full flex flex-col", children: [(0, jsx_runtime_1.jsx)("div", { className: "flex gap-2 p-4 border-b border-border overflow-x-auto", children: phases.map((phase) => ((0, jsx_runtime_1.jsxs)(button_1.Button, { variant: selectedTab === phase.number ? 'default' : 'outline', size: "sm", onClick: () => setSelectedTab(phase.number), className: "flex items-center gap-2 shrink-0", children: [getStatusIcon(phase.status), "Phase ", phase.number] }, phase.number))) }), (0, jsx_runtime_1.jsx)("div", { className: "flex-1 overflow-hidden p-4", children: phases.filter((p) => p.number === selectedTab).map((phase) => renderPhaseColumn(phase)) })] })) })] }));
};
exports.ExecutionView = ExecutionView;
