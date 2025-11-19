"use client";

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Check, Play, FileText, Loader2 } from "lucide-react";
import { ModelConfig } from './ModelSettings';

interface PlanViewProps {
    design: any;
    modelConfig: ModelConfig;
    onPlanApproved: (plan: any) => void;
}

export const PlanView: React.FC<PlanViewProps> = ({
    design,
    modelConfig,
    onPlanApproved
}) => {
    const [plan, setPlan] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const generatePlan = async () => {
        setIsLoading(true);
        setError(null);
        try {
            // Bypass Next.js proxy and hit backend directly to avoid buffering
            const backendUrl = `http://${window.location.hostname}:8000/api/plan/basic`;

            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design: design,
                    modelConfig
                })
            });

            if (!response.ok) throw new Error('Failed to generate plan');

            const reader = response.body?.getReader();
            if (!reader) throw new Error('No response body');

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

                            if (data.done && data.plan) {
                                setPlan(data.plan);
                                return; // Stop reading
                            }

                            if (data.error) {
                                throw new Error(data.error);
                            }
                        } catch (e) {
                            console.error("Failed to parse SSE JSON:", e);
                        }
                    }
                }
            }
        } catch (err: any) {
            console.error("Plan generation error:", err);
            setError(err.message || "An error occurred");
        } finally {
            setIsLoading(false);
        }
    };

    // Auto-generate on mount if not present
    React.useEffect(() => {
        if (!plan && !isLoading && !error) {
            generatePlan();
        }
    }, []);

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Development Plan
                </h2>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={generatePlan}
                        disabled={isLoading}
                    >
                        Regenerate
                    </Button>
                    <Button
                        size="sm"
                        onClick={() => onPlanApproved(plan)}
                        disabled={!plan || isLoading}
                    >
                        <Play className="h-4 w-4 mr-2" />
                        Start Execution
                    </Button>
                </div>
            </div>

            <ScrollArea className="flex-1 p-6">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center h-64 space-y-4">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <p className="text-muted-foreground">Generating development plan...</p>
                    </div>
                ) : error ? (
                    <div className="text-destructive p-4 border border-destructive/20 rounded-lg bg-destructive/10">
                        Error: {error}
                    </div>
                ) : plan ? (
                    <div className="space-y-6">
                        <div className="prose prose-invert max-w-none">
                            <h3>{plan.summary}</h3>
                        </div>

                        <div className="grid gap-4">
                            {plan.phases?.map((phase: any, idx: number) => (
                                <Card key={idx} className="bg-card/50">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-base font-medium flex justify-between">
                                            <span>Phase {phase.number}: {phase.name}</span>
                                        </CardTitle>
                                        <CardDescription>{phase.description}</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <ul className="list-disc list-inside text-sm text-muted-foreground">
                                            {phase.steps?.map((step: string, sIdx: number) => (
                                                <li key={sIdx}>{step}</li>
                                            ))}
                                        </ul>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                ) : null}
            </ScrollArea>
        </div>
    );
}
