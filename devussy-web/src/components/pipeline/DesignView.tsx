"use client";

import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Check, ArrowRight, FileCode, LayoutGrid, Edit2, Gauge, AlertCircle } from "lucide-react";
import { ModelConfig } from './ModelSettings';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ComplexityAssessment, ComplexityProfile, ComplexityBadge } from './ComplexityAssessment';

interface DesignViewProps {
    projectName: string;
    requirements: string;
    languages: string[];
    modelConfig: ModelConfig;
    onDesignComplete: (design: any) => void;
    autoRun?: boolean;
    enableAdaptive?: boolean;  // Enable adaptive complexity analysis
}

export const DesignView = ({
    projectName,
    requirements,
    languages,
    modelConfig,
    onDesignComplete,
    autoRun = false,
    enableAdaptive = true
}: DesignViewProps) => {
    const [designContent, setDesignContent] = useState("");
    const [designData, setDesignData] = useState<any>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [viewMode, setViewMode] = useState<'preview' | 'raw'>('preview');
    const [isEditing, setIsEditing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Adaptive complexity state
    const [complexityProfile, setComplexityProfile] = useState<ComplexityProfile | null>(null);
    const [isAnalyzingComplexity, setIsAnalyzingComplexity] = useState(false);
    const [showComplexity, setShowComplexity] = useState(true);

    // Ref to track the current abort controller
    const abortControllerRef = React.useRef<AbortController | null>(null);
    const isGeneratingRef = React.useRef(false);

    // Analyze complexity before design generation
    const analyzeComplexity = async () => {
        if (!enableAdaptive) return null;
        
        setIsAnalyzingComplexity(true);
        try {
            // Build interview data from form inputs
            const interviewData = {
                project_name: projectName,
                project_type: inferProjectType(requirements),
                requirements: requirements,
                languages: languages.join(', '),
                team_size: '1', // Default for now
                integrations: inferIntegrations(requirements),
            };

            const response = await fetch('/api/adaptive/complexity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interview_data: interviewData }),
            });

            if (!response.ok) {
                console.warn('Complexity analysis failed, proceeding without adaptive scaling');
                return null;
            }

            // Parse SSE stream for complexity profile
            const reader = response.body?.getReader();
            if (!reader) return null;

            const decoder = new TextDecoder();
            let buffer = "";
            let profile: ComplexityProfile | null = null;

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
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.profile) {
                                profile = data.profile;
                                setComplexityProfile(profile);
                            }
                            if (data.done && data.profile) {
                                profile = data.profile;
                                setComplexityProfile(profile);
                            }
                        } catch (e) {
                            // Ignore parse errors
                        }
                    }
                }
            }

            return profile;
        } catch (err) {
            console.warn('Complexity analysis error:', err);
            return null;
        } finally {
            setIsAnalyzingComplexity(false);
        }
    };

    // Helper to infer project type from requirements
    const inferProjectType = (reqs: string): string => {
        const lower = reqs.toLowerCase();
        if (lower.includes('cli') || lower.includes('command line') || lower.includes('script')) return 'cli_tool';
        if (lower.includes('library') || lower.includes('package') || lower.includes('sdk')) return 'library';
        if (lower.includes('saas') || lower.includes('subscription') || lower.includes('multi-tenant')) return 'saas';
        if (lower.includes('api') || lower.includes('rest') || lower.includes('graphql')) return 'api';
        if (lower.includes('web') || lower.includes('website') || lower.includes('app')) return 'web_app';
        return 'web_app'; // Default
    };

    // Helper to infer integrations from requirements
    const inferIntegrations = (reqs: string): string => {
        const lower = reqs.toLowerCase();
        const integrations: string[] = [];
        if (lower.includes('stripe') || lower.includes('payment')) integrations.push('stripe');
        if (lower.includes('auth') || lower.includes('login') || lower.includes('oauth')) integrations.push('auth');
        if (lower.includes('database') || lower.includes('sql') || lower.includes('postgres')) integrations.push('database');
        if (lower.includes('email') || lower.includes('mail') || lower.includes('smtp')) integrations.push('email');
        if (lower.includes('s3') || lower.includes('storage') || lower.includes('upload')) integrations.push('storage');
        return integrations.join(', ') || 'none';
    };

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
                    modelConfig,
                    complexityProfile  // Pass complexity profile to design endpoint
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

    // Start pipeline: analyze complexity first (if adaptive), then generate design
    const startPipeline = async () => {
        if (enableAdaptive) {
            await analyzeComplexity();
        }
        await generateDesign();
    };

    // Auto-generate on mount
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            startPipeline();
        }, 50);

        return () => {
            clearTimeout(timeoutId);
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [projectName, requirements, JSON.stringify(languages), modelConfig]);

    const hasAutoAdvanced = React.useRef(false);

    // Auto-advance when complete - include complexity profile in design data
    useEffect(() => {
        if (autoRun && !isGenerating && !isAnalyzingComplexity && designContent && !hasAutoAdvanced.current) {
            const timer = setTimeout(() => {
                hasAutoAdvanced.current = true;
                // Pass the design data with complexity profile
                const designWithComplexity = {
                    ...(designData || { raw_llm_response: designContent, project_name: projectName }),
                    complexity_profile: complexityProfile
                };
                onDesignComplete(designWithComplexity);
            }, 1500);
            return () => clearTimeout(timer);
        }
    }, [autoRun, isGenerating, isAnalyzingComplexity, designContent, designData, complexityProfile, onDesignComplete, projectName]);

    const handleApprove = () => {
        const designWithComplexity = {
            ...(designData || { raw_llm_response: designContent, project_name: projectName }),
            complexity_profile: complexityProfile
        };
        onDesignComplete(designWithComplexity);
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <div className="flex items-center gap-4">
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                        <LayoutGrid className="h-5 w-5" />
                        System Design
                    </h2>
                    {/* Show complexity badge in header when collapsed */}
                    {complexityProfile && !showComplexity && (
                        <button 
                            onClick={() => setShowComplexity(true)}
                            className="hover:opacity-80 transition-opacity"
                        >
                            <ComplexityBadge profile={complexityProfile} />
                        </button>
                    )}
                </div>
                <div className="flex gap-2">
                    {complexityProfile && showComplexity && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowComplexity(false)}
                        >
                            <Gauge className="h-4 w-4 mr-2" />
                            Hide Complexity
                        </Button>
                    )}
                    
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
                        onClick={() => startPipeline()}
                        disabled={isGenerating || isAnalyzingComplexity}
                    >
                        Regenerate
                    </Button>

                    <Button
                        size="sm"
                        onClick={handleApprove}
                        disabled={isGenerating || isAnalyzingComplexity || !designContent}
                    >
                        <Check className="h-4 w-4 mr-2" />
                        Approve Design
                    </Button>
                </div>
            </div>

            <ScrollArea className="flex-1 p-6">
                {/* Complexity Assessment Panel */}
                {enableAdaptive && showComplexity && (isAnalyzingComplexity || complexityProfile) && (
                    <div className="mb-6">
                        {isAnalyzingComplexity ? (
                            <Card className="animate-pulse">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-base">
                                        <Gauge className="h-5 w-5 text-primary animate-spin" />
                                        Analyzing Project Complexity...
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="h-24 bg-muted rounded" />
                                </CardContent>
                            </Card>
                        ) : complexityProfile ? (
                            <ComplexityAssessment 
                                profile={complexityProfile}
                                showDetails={true}
                                onRefresh={() => analyzeComplexity()}
                            />
                        ) : null}
                    </div>
                )}

                {isGenerating && !designContent ? (
                    <div className="flex flex-col items-center justify-center h-64 space-y-4 text-muted-foreground">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <p>Architecting system solution{complexityProfile ? ` (${complexityProfile.depth_level} mode)` : ''}...</p>
                    </div>
                ) : error ? (
                    <div className="text-destructive p-4 border border-destructive/20 rounded-lg bg-destructive/10 flex items-center gap-2">
                        <AlertCircle className="h-5 w-5" />
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
