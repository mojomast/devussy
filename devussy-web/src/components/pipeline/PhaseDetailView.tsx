"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Check, Terminal, Play, Loader2, AlertCircle } from "lucide-react";
import { ModelConfig } from './ModelSettings';

interface PhaseDetailViewProps {
    phase: { number: number };
    plan: any;
    projectName: string;
    modelConfig: ModelConfig;
    onComplete?: () => void;
    // Controlled props
    status?: 'queued' | 'running' | 'complete' | 'failed';
    output?: string;
    error?: string;
    onStart?: () => void;
}

export const PhaseDetailView: React.FC<PhaseDetailViewProps> = ({
    phase,
    plan,
    projectName,
    modelConfig,
    onComplete,
    status,
    output: controlledOutput,
    error: controlledError,
    onStart
}) => {
    const [internalOutput, setInternalOutput] = useState<string>("");
    const [internalIsExecuting, setInternalIsExecuting] = useState(false);
    const [internalIsComplete, setInternalIsComplete] = useState(false);
    const [internalError, setInternalError] = useState<string | null>(null);

    // Derived state (controlled vs uncontrolled)
    const isControlled = typeof status !== 'undefined';
    const output = isControlled ? controlledOutput || "" : internalOutput;
    const isExecuting = isControlled ? status === 'running' : internalIsExecuting;
    const isComplete = isControlled ? status === 'complete' : internalIsComplete;
    const error = isControlled ? controlledError || null : internalError;

    const scrollRef = useRef<HTMLDivElement>(null);
    const hasStarted = useRef(false);

    // Update hasStarted ref based on status
    useEffect(() => {
        if (isExecuting || isComplete || output) {
            hasStarted.current = true;
        }
    }, [isExecuting, isComplete, output]);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [output]);

    const executePhase = async () => {
        if (onStart) {
            onStart();
            return;
        }

        if (isExecuting || isComplete) return;

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

            if (!response.ok) throw new Error('Failed to start phase execution');

            const reader = response.body?.getReader();
            if (!reader) return;

            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });

                // Parse SSE data
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);
                        if (!dataStr.trim()) continue;

                        try {
                            const data = JSON.parse(dataStr);
                            if (data.content) {
                                setInternalOutput(prev => prev + data.content);
                            } else if (data.error) {
                                throw new Error(data.error);
                            } else if (data.done) {
                                setInternalIsComplete(true);
                            }
                        } catch (e) {
                            // If it's not JSON, just append it (fallback)
                            console.warn("Failed to parse SSE data:", e);
                        }
                    }
                }
            }

        } catch (err: any) {
            console.error("Phase execution error:", err);
            setInternalError(err.message || "An error occurred during execution");
            setInternalOutput(prev => prev + `\n\n[ERROR]: ${err.message}`);
        } finally {
            setInternalIsExecuting(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <Terminal className="h-5 w-5" />
                    Phase {phase.number} Execution
                </h2>
                <div className="flex gap-2">
                    {!hasStarted.current && (
                        <Button
                            size="sm"
                            onClick={executePhase}
                            disabled={isExecuting}
                        >
                            <Play className="h-4 w-4 mr-2" />
                            Start Phase
                        </Button>
                    )}
                    {isComplete && onComplete && (
                        <Button
                            size="sm"
                            onClick={onComplete}
                            variant="default"
                        >
                            <Check className="h-4 w-4 mr-2" />
                            Next Phase
                        </Button>
                    )}
                </div>
            </div>

            <ScrollArea className="flex-1 p-4 bg-black/90 font-mono text-sm text-green-400 overflow-auto">
                <div className="whitespace-pre-wrap">
                    {output}
                    {isExecuting && <span className="animate-pulse">_</span>}
                </div>
                <div ref={scrollRef} />

                {!hasStarted.current && !error && (
                    <div className="text-muted-foreground text-center mt-10">
                        Click "Start Phase" to begin execution.
                    </div>
                )}

                {error && (
                    <div className="mt-4 p-4 border border-red-500/50 bg-red-900/20 text-red-400 rounded">
                        <div className="flex items-center gap-2 font-bold mb-2">
                            <AlertCircle className="h-4 w-4" />
                            Execution Failed
                        </div>
                        {error}
                        <Button
                            variant="outline"
                            size="sm"
                            className="mt-4 border-red-500/50 hover:bg-red-900/40 text-red-400"
                            onClick={executePhase}
                        >
                            Retry
                        </Button>
                    </div>
                )}
            </ScrollArea>
        </div>
    );
}
