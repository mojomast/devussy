"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Check, Edit2, RefreshCw, Sparkles } from "lucide-react";
import { ModelConfig } from './ModelSettings';

interface DesignViewProps {
    projectName: string;
    requirements: string;
    languages: string[];
    modelConfig: ModelConfig;
    onDesignComplete: (design: any) => void;
}

export const DesignView: React.FC<DesignViewProps> = ({
    projectName,
    requirements,
    languages,
    modelConfig,
    onDesignComplete
}) => {
    const [designContent, setDesignContent] = useState("");
    const [isGenerating, setIsGenerating] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [designData, setDesignData] = useState<any>(null);

    // We use a ref to track the abort controller so we can abort on unmount
    const abortControllerRef = useRef<AbortController | null>(null);

    useEffect(() => {
        // If we already have data or are editing, don't regenerate
        if (designData || isEditing) return;

        console.log("DesignView mounted, scheduling generation...");
        const controller = new AbortController();
        abortControllerRef.current = controller;

        const timeoutId = setTimeout(() => {
            const generateDesign = async () => {
                console.log("Starting design generation request...");
                try {
                    // Bypass Next.js proxy and hit backend directly to avoid buffering
                    const backendUrl = `/api/design`;
                    console.log("Fetching from:", backendUrl);

                    const response = await fetch(backendUrl, {
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
                    if (!reader) return;

                    const decoder = new TextDecoder();
                    let buffer = "";

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const chunk = decoder.decode(value, { stream: true });
                        buffer += chunk;

                        // Split by double newline to get SSE messages
                        const parts = buffer.split('\n\n');
                        buffer = parts.pop() || ""; // Keep the last partial part in buffer

                        for (const part of parts) {
                            const line = part.trim();
                            if (line.startsWith('data: ')) {
                                const dataStr = line.slice(6);
                                try {
                                    const data = JSON.parse(dataStr);

                                    if (data.content) {
                                        setDesignContent(prev => prev + data.content);
                                    }

                                    if (data.done && data.design) {
                                        setDesignData(data.design);
                                        // Stop reading stream once we have the final result
                                        return;
                                    }

                                    if (data.error) {
                                        console.error("Backend reported error:", data.error);
                                        setDesignContent(prev => prev + `\n\nError: ${data.error}`);
                                    }
                                } catch (e) {
                                    console.error("Failed to parse SSE JSON:", e, dataStr);
                                }
                            }
                        }
                    }

                } catch (error: any) {
                    if (error.name === 'AbortError') {
                        console.log('Design generation aborted by user/cleanup');
                        return;
                    }
                    console.error("Design generation failed:", error);
                    setDesignContent("Error generating design. Please try again.");
                } finally {
                    setIsGenerating(false);
                }
            };

            generateDesign();
        }, 50); // Debounce to handle StrictMode double-mount

        return () => {
            console.log("DesignView unmounting, clearing timeout/aborting...");
            clearTimeout(timeoutId);
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [projectName, requirements, JSON.stringify(languages), modelConfig]);

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    {isGenerating && <RefreshCw className="h-4 w-4 animate-spin" />}
                    System Architecture Design
                </h2>
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsEditing(!isEditing)}
                        disabled={isGenerating}
                    >
                        <Edit2 className="h-4 w-4 mr-2" />
                        {isEditing ? "Preview" : "Edit"}
                    </Button>
                    <Button
                        size="sm"
                        onClick={() => onDesignComplete(designData || { raw_llm_response: designContent, project_name: projectName })}
                        disabled={isGenerating}
                    >
                        <Check className="h-4 w-4 mr-2" />
                        Approve & Plan
                    </Button>
                </div>
            </div>

            <ScrollArea className="flex-1 p-6">
                {isEditing ? (
                    <textarea
                        className="w-full h-full min-h-[400px] bg-transparent font-mono text-sm resize-none focus:outline-none"
                        value={designContent}
                        onChange={(e) => setDesignContent(e.target.value)}
                    />
                ) : (
                    <div className="prose prose-invert max-w-none font-mono text-sm">
                        <pre className="whitespace-pre-wrap bg-transparent p-0">
                            {designContent}
                        </pre>
                    </div>
                )}
            </ScrollArea>
        </div >
    );
}
