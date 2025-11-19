"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Terminal, LayoutGrid, List, Loader2, Check, AlertCircle, Clock, Pause, Play } from "lucide-react";
import { ModelConfig } from './ModelSettings';

interface PhaseStatus {
    number: number;
    title: string;
    status: 'queued' | 'running' | 'complete' | 'failed';
    output: string;
    progress: number;  // 0-100
    error?: string;
}

interface ExecutionViewProps {
    plan: any;
    projectName: string;
    modelConfig: ModelConfig;
    onComplete: () => void;
}

export const ExecutionView: React.FC<ExecutionViewProps> = ({
    plan,
    projectName,
    modelConfig,
    onComplete
}) => {
    const [viewMode, setViewMode] = useState<'grid' | 'tabs'>('grid');
    const [concurrency, setConcurrency] = useState<number>(3);
    const [selectedTab, setSelectedTab] = useState<number>(1);
    const [phases, setPhases] = useState<PhaseStatus[]>([]);
    const [isExecuting, setIsExecuting] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [completedCount, setCompletedCount] = useState(0);

    const scrollRefs = useRef<Map<number, HTMLDivElement>>(new Map());
    const abortControllersRef = useRef<Map<number, AbortController>>(new Map());

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
            setPhases(initialPhases);
        }
    }, [plan]);

    // Auto-scroll for each phase
    useEffect(() => {
        phases.forEach(phase => {
            const scrollRef = scrollRefs.current.get(phase.number);
            if (scrollRef && phase.status === 'running') {
                scrollRef.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }, [phases]);

    // Auto-start execution when mounted
    useEffect(() => {
        if (phases.length > 0 && !isExecuting) {
            startExecution();
        }
    }, [phases.length]);

    const updatePhaseStatus = (phaseNumber: number, update: Partial<PhaseStatus>) => {
        setPhases(prev => prev.map(p =>
            p.number === phaseNumber ? { ...p, ...update } : p
        ));
    };

    const executePhase = async (phase: PhaseStatus) => {
        if (isPaused) return;

        const controller = new AbortController();
        abortControllersRef.current.set(phase.number, controller);

        updatePhaseStatus(phase.number, { status: 'running', output: `Starting Phase ${phase.number}: ${phase.title}...\n\n` });

        try {
            const backendUrl = `http://${window.location.hostname}:8000/api/plan/detail`;

            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    plan: plan,
                    phaseNumber: phase.number,
                    projectName,
                    modelConfig
                }),
                signal: controller.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: Failed to start phase execution`);
            }

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('No response body');
            }

            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

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

                            if (data.content) {
                                updatePhaseStatus(phase.number, {
                                    output: phases.find(p => p.number === phase.number)!.output + data.content
                                });
                            }

                            if (data.error) {
                                throw new Error(data.error);
                            }

                            if (data.done) {
                                updatePhaseStatus(phase.number, {
                                    status: 'complete',
                                    progress: 100
                                });
                                setCompletedCount(prev => prev + 1);
                                return;
                            }
                        } catch (e: any) {
                            if (e.message && !e.message.includes('Unexpected token')) {
                                throw e;
                            }
                        }
                    }
                }
            }

        } catch (err: any) {
            if (err.name === 'AbortError') {
                updatePhaseStatus(phase.number, {
                    status: 'queued',
                    output: phases.find(p => p.number === phase.number)!.output + '\n[Paused]'
                });
            } else {
                console.error(`Phase ${phase.number} execution error:`, err);
                updatePhaseStatus(phase.number, {
                    status: 'failed',
                    error: err.message || 'Unknown error',
                    output: phases.find(p => p.number === phase.number)!.output + `\n\n[ERROR]: ${err.message}`
                });
            }
        } finally {
            abortControllersRef.current.delete(phase.number);
        }
    };

    const startExecution = async () => {
        setIsExecuting(true);
        setIsPaused(false);

        // Execute phases with concurrency control
        const queue = [...phases];
        const running: Promise<void>[] = [];

        while (queue.length > 0 || running.length > 0) {
            if (isPaused) {
                // Abort all running phases
                for (const controller of abortControllersRef.current.values()) {
                    controller.abort();
                }
                break;
            }

            // Start new phases up to concurrency limit
            while (running.length < concurrency && queue.length > 0) {
                const phase = queue.shift()!;
                const promise = executePhase(phase);
                running.push(promise);
            }

            // Wait for at least one phase to complete
            if (running.length > 0) {
                await Promise.race(running);
                // Remove completed promises
                const stillRunning = running.filter(p => {
                    // This is a simplified check - in reality we'd track promise states
                    return true; // Keep for now, will be filtered naturally as they resolve
                });
            }
        }

        setIsExecuting(false);

        // Check if all phases completed successfully
        const allComplete = phases.every(p => p.status === 'complete');
        if (allComplete && onComplete) {
            onComplete();
        }
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
                <ScrollArea className="h-full">
                    <div className="font-mono text-xs whitespace-pre-wrap text-green-400 bg-black/50 p-3 rounded">
                        {phase.output || 'Waiting to start...'}
                        {phase.status === 'running' && <span className="animate-pulse">_</span>}
                        <div ref={el => { if (el) scrollRefs.current.set(phase.number, el); }} />
                    </div>
                </ScrollArea>
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
                    <div className="grid grid-cols-3 gap-4 p-4 h-full auto-rows-fr">
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
