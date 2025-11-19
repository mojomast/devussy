"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Terminal, LayoutGrid, List, Loader2, Check, AlertCircle, Clock, Pause, Play, Sparkles, ArrowRight } from "lucide-react";
import { ModelConfig } from './ModelSettings';

interface PhaseStatus {
    number: number;
    title: string;
    status: 'queued' | 'running' | 'complete' | 'failed';
    output: string;
    progress: number;  // 0-100
    error?: string;
    detailedPhase?: any;  // The detailed phase data with steps from backend
}

interface ExecutionViewProps {
    plan: any;
    projectName: string;
    modelConfig: ModelConfig;
    onComplete: (detailedPlan?: any) => void;
    onSpawnHiveMindWindow?: (phase: PhaseStatus, plan: any, projectName: string) => void;
}

export const ExecutionView: React.FC<ExecutionViewProps> = ({
    plan,
    projectName,
    modelConfig,
    onComplete,
    onSpawnHiveMindWindow
}) => {
    const [viewMode, setViewMode] = useState<'grid' | 'tabs'>('grid');
    const [concurrency, setConcurrency] = useState<number>(modelConfig.concurrency || 3);
    const [selectedTab, setSelectedTab] = useState<number>(1);
    const [phases, setPhases] = useState<PhaseStatus[]>([]);
    const [isExecuting, setIsExecuting] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [completedCount, setCompletedCount] = useState(0);

    const buildDetailedPlan = () => {
        if (!plan || !plan.phases) return plan;

        return {
            ...plan,
            phases: plan.phases.map((originalPhase: any) => {
                const executedPhase = phases.find(p => p.number === originalPhase.number);
                if (executedPhase && executedPhase.detailedPhase) {
                    return executedPhase.detailedPhase;
                }
                return originalPhase;
            })
        };
    };

    const handleManualComplete = () => {
        const detailedPlan = buildDetailedPlan();
        onComplete(detailedPlan);
    };

    // Update concurrency when modelConfig changes
    useEffect(() => {
        if (modelConfig.concurrency && !isExecuting) {
            setConcurrency(modelConfig.concurrency);
        }
    }, [modelConfig.concurrency, isExecuting]);

    const scrollRefs = useRef<Map<number, HTMLDivElement>>(new Map());
    const scrollContainerRefs = useRef<Map<number, HTMLDivElement>>(new Map());
    const abortControllersRef = useRef<Map<number, AbortController>>(new Map());
    const phaseOutputBuffers = useRef<Map<number, string>>(new Map());
    const updateTimers = useRef<Map<number, NodeJS.Timeout>>(new Map());

    // Initialize phases from plan
    useEffect(() => {
        if (plan && plan.phases) {
            const initialPhases: PhaseStatus[] = plan.phases.map((p: any) => ({
                number: p.number,
                title: p.title || p.name || `Phase ${p.number}`,
                status: 'queued',
                output: '',
                progress: 0
            }));
            console.log('[ExecutionView] Initialized phases:', initialPhases.map(p => ({ number: p.number, title: p.title })));
            setPhases(initialPhases);
        }
    }, [plan]);

    // Auto-scroll for each phase - scroll to bottom when content updates
    useEffect(() => {
        phases.forEach(phase => {
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
    useEffect(() => {
        if (phases.length > 0 && !isExecuting) {
            startExecution();
        }
    }, [phases.length]);



    const executePhase = async (phase: PhaseStatus) => {
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

        setPhases(prev => {
            const updated = prev.map(p =>
                p.number === phase.number
                    ? { ...p, status: 'running' as const, output: initialOutput }
                    : p
            );
            console.log('[executePhase] Updated phases:', updated.map(p => ({ number: p.number, status: p.status })));
            return updated;
        });

        try {
            const backendUrl = `http://${window.location.hostname}:8000/api/plan/detail`;
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
                planPhasesCount: plan?.phases?.length,
                firstPhase: plan?.phases?.[0]
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

            const reader = response.body?.getReader();
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
                                        setPhases(prev => prev.map(p =>
                                            p.number === phase.number
                                                ? { ...p, output: bufferedContent }
                                                : p
                                        ));

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
                                    setPhases(prev => prev.map(p =>
                                        p.number === phase.number
                                            ? {
                                                ...p,
                                                status: 'complete',
                                                progress: 100,
                                                output: finalOutput,
                                                detailedPhase: data.phase // Store the detailed phase with steps
                                            }
                                            : p
                                    ));
                                    setCompletedCount(prev => prev + 1);

                                    // Clean up buffer
                                    phaseOutputBuffers.current.delete(phase.number);

                                    // Close reader to release connection
                                    reader.cancel();
                                    console.log('[executePhase] Phase', phase.number, 'reader closed');
                                    return;
                                }
                            } catch (e: any) {
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
                    setPhases(prev => prev.map(p =>
                        p.number === phase.number
                            ? { ...p, status: 'complete', progress: 100, output: finalOutput }
                            : p
                    ));
                    setCompletedCount(prev => prev + 1);

                    // Clean up buffer
                    phaseOutputBuffers.current.delete(phase.number);
                }
            } finally {
                // Always close the reader to release the connection
                try {
                    reader.cancel();
                    console.log('[executePhase] Phase', phase.number, 'reader closed in finally block');
                } catch (e) {
                    console.log('[executePhase] Phase', phase.number, 'reader already closed');
                }
            }

        } catch (err: any) {
            // Clean up timers and buffers
            const existingTimer = updateTimers.current.get(phase.number);
            if (existingTimer) {
                clearTimeout(existingTimer);
                updateTimers.current.delete(phase.number);
            }

            const currentOutput = phaseOutputBuffers.current.get(phase.number) || '';
            phaseOutputBuffers.current.delete(phase.number);

            if (err.name === 'AbortError') {
                setPhases(prev => prev.map(p =>
                    p.number === phase.number
                        ? { ...p, status: 'queued' as const, output: currentOutput + '\n[Paused]' }
                        : p
                ));
            } else {
                console.error(`Phase ${phase.number} execution error:`, err);
                setPhases(prev => prev.map(p =>
                    p.number === phase.number
                        ? { ...p, status: 'failed' as const, error: err.message || 'Unknown error', output: currentOutput + `\n\n[ERROR]: ${err.message}` }
                        : p
                ));
            }
        } finally {
            abortControllersRef.current.delete(phase.number);
        }
    };

    const startExecution = async () => {
        console.log('[ExecutionView] Starting execution with', phases.length, 'phases - STARTING ALL AT ONCE');
        setIsExecuting(true);
        setIsPaused(false);

        // Start ALL phases immediately
        const promises = phases.map(phase => {
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
        const allComplete = phases.every(p => p.status === 'complete');
        console.log('[ExecutionView] All complete?', allComplete);

        // We disable auto-advance to allow user to review output and manually proceed
        // if (allComplete && onComplete) {
        //     const detailedPlan = buildDetailedPlan();
        //     setTimeout(() => onComplete(detailedPlan), 0);
        // }
    };

    const togglePause = () => {
        setIsPaused(!isPaused);
        if (isPaused) {
            // Resume
            startExecution();
        } else {
            // Pause - abort controllers will be handled in the execution loop
        }
    };

    const getStatusIcon = (status: PhaseStatus['status']) => {
        switch (status) {
            case 'complete':
                return <Check className="h-4 w-4 text-green-500" />;
            case 'running':
                return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
            case 'failed':
                return <AlertCircle className="h-4 w-4 text-red-500" />;
            case 'queued':
            default:
                return <Clock className="h-4 w-4 text-gray-500" />;
        }
    };

    const getStatusColor = (status: PhaseStatus['status']) => {
        switch (status) {
            case 'complete': return 'border-green-500/50 bg-green-900/10';
            case 'running': return 'border-blue-500/50 bg-blue-900/10';
            case 'failed': return 'border-red-500/50 bg-red-900/10';
            case 'queued': default: return 'border-border/50';
        }
    };

    const renderPhaseColumn = (phase: PhaseStatus) => (
        <Card key={phase.number} className={`flex flex-col h-full ${getStatusColor(phase.status)}`}>
            <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                    {getStatusIcon(phase.status)}
                    <span>Phase {phase.number}</span>
                </CardTitle>
                <div className="text-xs text-muted-foreground truncate">{phase.title}</div>

                {/* Hive Mode button - available for all phases */}
                {onSpawnHiveMindWindow && (
                    <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onSpawnHiveMindWindow(phase, plan, projectName)}
                        className="mt-2 border-yellow-500/50 text-yellow-400 hover:bg-yellow-500/10"
                    >
                        <Sparkles className="h-4 w-4 mr-2" />
                        🐝 Hive Mode
                    </Button>
                )}

                {phase.status === 'running' && (
                    <div className="mt-2 h-1 bg-border rounded-full overflow-hidden">
                        <div
                            className="h-full bg-primary transition-all duration-300"
                            style={{ width: `${phase.progress}%` }}
                        />
                    </div>
                )}
            </CardHeader>
            <CardContent className="flex-1 pt-0 overflow-hidden">
                <div
                    ref={el => { if (el) scrollContainerRefs.current.set(phase.number, el); }}
                    className="h-full overflow-y-auto custom-scrollbar"
                >
                    <div className="font-mono text-xs whitespace-pre-wrap text-green-400 bg-black/50 p-3 rounded min-h-full">
                        {phase.output || 'Waiting to start...'}
                        {phase.status === 'running' && <span className="animate-pulse">_</span>}
                    </div>
                </div>
            </CardContent>
        </Card>
    );

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Terminal className="h-5 w-5" />
                    Execution Phase
                    <span className="text-sm text-muted-foreground font-normal">
                        ({completedCount}/{phases.length} complete)
                    </span>
                </h2>

                <div className="flex items-center gap-3">
                    {/* Proceed to Handoff */}
                    <Button
                        size="sm"
                        onClick={handleManualComplete}
                        disabled={isExecuting}
                        className={completedCount === phases.length ? "bg-green-600 hover:bg-green-700 text-white" : ""}
                    >
                        Proceed to Handoff <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>

                    {/* Concurrency Control */}
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">Concurrency:</span>
                        <Select
                            value={concurrency.toString()}
                            onValueChange={(v: string) => setConcurrency(parseInt(v))}
                            disabled={isExecuting}
                        >
                            <SelectTrigger className="w-20 h-8">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="1">1</SelectItem>
                                <SelectItem value="2">2</SelectItem>
                                <SelectItem value="3">3</SelectItem>
                                <SelectItem value="5">5</SelectItem>
                                <SelectItem value={phases.length.toString()}>All</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* View Mode Toggle */}
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setViewMode(viewMode === 'grid' ? 'tabs' : 'grid')}
                    >
                        {viewMode === 'grid' ? (
                            <><List className="h-4 w-4 mr-2" /> Tabs</>
                        ) : (
                            <><LayoutGrid className="h-4 w-4 mr-2" /> Grid</>
                        )}
                    </Button>

                    {/* Pause/Resume */}
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={togglePause}
                        disabled={!isExecuting && !isPaused}
                    >
                        {isPaused ? (
                            <><Play className="h-4 w-4 mr-2" /> Resume</>
                        ) : (
                            <><Pause className="h-4 w-4 mr-2" /> Pause</>
                        )}
                    </Button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden">
                {viewMode === 'grid' ? (
                    <div className={`grid gap-4 p-4 h-full auto-rows-fr ${phases.length <= 3 ? 'grid-cols-3' :
                        phases.length <= 6 ? 'grid-cols-3' :
                            'grid-cols-4'
                        }`}>
                        {phases.map(phase => renderPhaseColumn(phase))}
                    </div>
                ) : (
                    <div className="h-full flex flex-col">
                        {/* Tab Headers */}
                        <div className="flex gap-2 p-4 border-b border-border overflow-x-auto">
                            {phases.map(phase => (
                                <Button
                                    key={phase.number}
                                    variant={selectedTab === phase.number ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => setSelectedTab(phase.number)}
                                    className="flex items-center gap-2 shrink-0"
                                >
                                    {getStatusIcon(phase.status)}
                                    Phase {phase.number}
                                </Button>
                            ))}
                        </div>

                        {/* Tab Content */}
                        <div className="flex-1 p-4">
                            {phases.filter(p => p.number === selectedTab).map(phase => renderPhaseColumn(phase))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
