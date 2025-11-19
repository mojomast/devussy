"use client";

import React, { useState, useEffect, useRef } from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Loader2, Check, Zap } from "lucide-react";
import { cn } from '@/utils';

interface HiveMindViewProps {
    phase?: { number: number; title: string };
    plan?: any;
    projectName: string;
    modelConfig: any;
    type?: 'phase' | 'design';
    requirements?: string;
    languages?: string[];
}

interface StreamState {
    content: string;
    isActive: boolean;
    isComplete: boolean;
}

export const HiveMindView: React.FC<HiveMindViewProps> = ({
    phase,
    plan,
    projectName,
    modelConfig,
    type = 'phase',
    requirements,
    languages
}) => {
    const [drone1, setDrone1] = useState<StreamState>({ content: "", isActive: false, isComplete: false });
    const [drone2, setDrone2] = useState<StreamState>({ content: "", isActive: false, isComplete: false });
    const [drone3, setDrone3] = useState<StreamState>({ content: "", isActive: false, isComplete: false });
    const [arbiter, setArbiter] = useState<StreamState>({ content: "", isActive: false, isComplete: false });
    const [error, setError] = useState<string | null>(null);

    const drone1Ref = useRef<HTMLDivElement>(null);
    const drone2Ref = useRef<HTMLDivElement>(null);
    const drone3Ref = useRef<HTMLDivElement>(null);
    const arbiterRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const executeHiveMind = async () => {
            try {
                const endpoint = type === 'design' ? '/api/design/hivemind' : '/api/plan/hivemind';
                const body = type === 'design'
                    ? { projectName, requirements, languages, modelConfig }
                    : { plan, phaseNumber: phase?.number, projectName, modelConfig };

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });

                if (!response.ok) throw new Error('Failed to start HiveMind execution');

                const reader = response.body?.getReader();
                if (!reader) return;

                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.slice(6);
                            if (!dataStr.trim()) continue;

                            try {
                                const data = JSON.parse(dataStr);

                                if (data.type === 'drone1') {
                                    setDrone1(prev => ({ ...prev, content: prev.content + data.content, isActive: true }));
                                } else if (data.type === 'drone2') {
                                    setDrone2(prev => ({ ...prev, content: prev.content + data.content, isActive: true }));
                                } else if (data.type === 'drone3') {
                                    setDrone3(prev => ({ ...prev, content: prev.content + data.content, isActive: true }));
                                } else if (data.type === 'arbiter') {
                                    setArbiter(prev => ({ ...prev, content: prev.content + data.content, isActive: true }));
                                } else if (data.type === 'drone1_complete') {
                                    setDrone1(prev => ({ ...prev, isComplete: true, isActive: false }));
                                } else if (data.type === 'drone2_complete') {
                                    setDrone2(prev => ({ ...prev, isComplete: true, isActive: false }));
                                } else if (data.type === 'drone3_complete') {
                                    setDrone3(prev => ({ ...prev, isComplete: true, isActive: false }));
                                } else if (data.type === 'arbiter_complete') {
                                    setArbiter(prev => ({ ...prev, isComplete: true, isActive: false }));
                                } else if (data.error) {
                                    throw new Error(data.error);
                                }
                            } catch (e) {
                                console.warn("Failed to parse SSE data:", e);
                            }
                        }
                    }
                }
            } catch (err: any) {
                console.error("HiveMind execution error:", err);
                setError(err.message || "An error occurred during HiveMind execution");
            }
        };

        executeHiveMind();
    }, [phase, plan, projectName, modelConfig]);

    // Auto-scroll each pane
    useEffect(() => {
        drone1Ref.current?.scrollIntoView({ behavior: "smooth" });
    }, [drone1.content]);
    useEffect(() => {
        drone2Ref.current?.scrollIntoView({ behavior: "smooth" });
    }, [drone2.content]);
    useEffect(() => {
        drone3Ref.current?.scrollIntoView({ behavior: "smooth" });
    }, [drone3.content]);
    useEffect(() => {
        arbiterRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [arbiter.content]);

    const DronePane = ({ title, state, scrollRef, color }: { title: string; state: StreamState; scrollRef: React.RefObject<HTMLDivElement | null>; color: string }) => (
        <Card className={cn("flex flex-col border-2", `border-${color}-500/30`)}>
            <div className={cn("px-3 py-2 border-b flex items-center justify-between", `bg-${color}-950/40`)}>
                <div className="flex items-center gap-2">
                    <Zap className={cn("h-4 w-4", `text-${color}-400`)} />
                    <span className={cn("font-semibold text-sm", `text-${color}-300`)}>{title}</span>
                </div>
                {state.isActive && <Loader2 className={cn("h-3 w-3 animate-spin", `text-${color}-400`)} />}
                {state.isComplete && <Check className={cn("h-3 w-3", `text-${color}-500`)} />}
            </div>
            <ScrollArea className="flex-1 p-3 bg-black/80 font-mono text-xs min-h-[200px] max-h-[250px]">
                <div className={cn("whitespace-pre-wrap", `text-${color}-300`)}>
                    {state.content || "Waiting..."}
                    {state.isActive && <span className="animate-pulse">_</span>}
                </div>
                <div ref={scrollRef} />
            </ScrollArea>
        </Card>
    );

    return (
        <div className="flex flex-col h-full p-4 gap-4">
            <div className="text-center">
                <h2 className="text-xl font-bold flex items-center justify-center gap-2">
                    🐝 HiveMind: {type === 'design' ? 'Design Phase' : `Phase ${phase?.number}`}
                </h2>
                <p className="text-sm text-muted-foreground">{type === 'design' ? projectName : phase?.title}</p>
            </div>

            {error && (
                <div className="p-3 border border-red-500/50 bg-red-900/20 text-red-400 rounded text-sm">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-2 gap-4 flex-1 overflow-hidden">
                <DronePane title="Drone 1" state={drone1} scrollRef={drone1Ref} color="cyan" />
                <DronePane title="Drone 2" state={drone2} scrollRef={drone2Ref} color="purple" />
                <DronePane title="Drone 3" state={drone3} scrollRef={drone3Ref} color="orange" />

                <Card className="flex flex-col border-2 border-green-500/50">
                    <div className="px-3 py-2 border-b flex items-center justify-between bg-green-950/40">
                        <div className="flex items-center gap-2">
                            <Zap className="h-4 w-4 text-green-400" />
                            <span className="font-semibold text-sm text-green-300">Arbiter (Synthesis)</span>
                        </div>
                        {arbiter.isActive && <Loader2 className="h-3 w-3 animate-spin text-green-400" />}
                        {arbiter.isComplete && <Check className="h-3 w-3 text-green-500" />}
                    </div>
                    <ScrollArea className="flex-1 p-3 bg-black/80 font-mono text-xs min-h-[200px] max-h-[250px]">
                        <div className="whitespace-pre-wrap text-green-300">
                            {arbiter.content || "Waiting for drones to complete..."}
                            {arbiter.isActive && <span className="animate-pulse">_</span>}
                        </div>
                        <div ref={arbiterRef} />
                    </ScrollArea>
                </Card>
            </div>
        </div>
    );
};
