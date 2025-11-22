"use client";

import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Check, ArrowRight, FileCode, LayoutGrid, Edit2 } from "lucide-react";
import { ModelConfig } from './ModelSettings';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface DesignViewProps {
    projectName: string;
    requirements: string;
    languages: string[];
    modelConfig: ModelConfig;
    onDesignComplete: (design: any) => void;
    autoRun?: boolean;
}

export const DesignView = ({
    projectName,
    requirements,
    languages,
    modelConfig,
    onDesignComplete,
    autoRun = false
}: DesignViewProps) => {
    const [designContent, setDesignContent] = useState("");
    const [designData, setDesignData] = useState<any>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [viewMode, setViewMode] = useState<'preview' | 'raw'>('preview');
    const [isEditing, setIsEditing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Ref to track the current abort controller
    const abortControllerRef = React.useRef<AbortController | null>(null);
    const isGeneratingRef = React.useRef(false);

    const generateDesign = async () => {
        if (isGeneratingRef.current) return;

        setIsGenerating(true);
        setError(null);
        setDesignContent("");
        isGeneratingRef.current = true;

        // Create new abort controller
        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            const response = await fetch('/api/design', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    projectName,
                    requirements,
                    languages,
                    modelConfig
                }),
                signal: controller.signal
            });

            if (!response.ok) throw new Error('Failed to generate design');

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

                            if (data.content) {
                                setDesignContent((prev: string) => prev + data.content);
                            }

                            if (data.done && data.design) {
                                setDesignData(data.design);
                                return;
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
            if (err.name === 'AbortError') {
                console.log('Design generation aborted');
                return;
            }
            console.error("Design generation error:", err);
            setError(err.message || "An error occurred");
        } finally {
            if (abortControllerRef.current === controller) {
                setIsGenerating(false);
                isGeneratingRef.current = false;
                abortControllerRef.current = null;
            }
        }
    };

    // Auto-generate on mount
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            generateDesign();
        }, 50);

        return () => {
            clearTimeout(timeoutId);
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [projectName, requirements, JSON.stringify(languages), modelConfig]);

    const hasAutoAdvanced = React.useRef(false);

    // Auto-advance when complete
    useEffect(() => {
        if (autoRun && !isGenerating && designContent && !hasAutoAdvanced.current) {
            const timer = setTimeout(() => {
                hasAutoAdvanced.current = true;
                // Pass the design data or construct it from content if structured data is missing
                onDesignComplete(designData || { raw_llm_response: designContent, project_name: projectName });
            }, 1500);
            return () => clearTimeout(timer);
        }
    }, [autoRun, isGenerating, designContent, designData, onDesignComplete, projectName]);

    const handleApprove = () => {
        onDesignComplete(designData || { raw_llm_response: designContent, project_name: projectName });
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <LayoutGrid className="h-5 w-5" />
                    System Design
                </h2>
                <div className="flex gap-2">
                    {designContent && !isGenerating && (
                        <>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setViewMode(viewMode === 'preview' ? 'raw' : 'preview')}
                            >
                                {viewMode === 'preview' ? (
                                    <><FileCode className="h-4 w-4 mr-2" /> Raw Text</>
                                ) : (
                                    <><LayoutGrid className="h-4 w-4 mr-2" /> Preview</>
                                )}
                            </Button>

                            {viewMode === 'raw' && (
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setIsEditing(!isEditing)}
                                >
                                    <Edit2 className="h-4 w-4 mr-2" />
                                    {isEditing ? "Preview" : "Edit"}
                                </Button>
                            )}
                        </>
                    )}

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={generateDesign}
                        disabled={isGenerating}
                    >
                        Regenerate
                    </Button>

                    <Button
                        size="sm"
                        onClick={handleApprove}
                        disabled={isGenerating || !designContent}
                    >
                        <Check className="h-4 w-4 mr-2" />
                        Approve Design
                    </Button>
                </div>
            </div>

            <ScrollArea className="flex-1 p-6">
                {isGenerating && !designContent ? (
                    <div className="flex flex-col items-center justify-center h-full space-y-4 text-muted-foreground">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <p>Architecting system solution...</p>
                    </div>
                ) : error ? (
                    <div className="text-destructive p-4 border border-destructive/20 rounded-lg bg-destructive/10">
                        Error: {error}
                    </div>
                ) : (
                    viewMode === 'preview' ? (
                        <div className="prose prose-invert max-w-none">
                            {/* Render markdown content */}
                            <div className="whitespace-pre-wrap font-mono text-sm">
                                {designContent}
                            </div>
                        </div>
                    ) : (
                        <div className="h-full">
                            {isEditing ? (
                                <textarea
                                    className="w-full h-full min-h-[400px] bg-transparent border border-border rounded-lg p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                                    value={designContent}
                                    onChange={(e) => setDesignContent(e.target.value)}
                                />
                            ) : (
                                <pre className="whitespace-pre-wrap font-mono text-sm bg-transparent p-0">
                                    {designContent}
                                </pre>
                            )}
                        </div>
                    )
                )}
            </ScrollArea>
        </div>
    );
}
