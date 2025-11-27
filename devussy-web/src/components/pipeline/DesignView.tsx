"use client";

import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Check, ArrowRight, FileCode, LayoutGrid, Edit2, Gauge, AlertCircle, Shield, History, ArrowLeft, MessageSquare } from "lucide-react";
import { ModelConfig } from './ModelSettings';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ComplexityAssessment, ComplexityProfile, ComplexityBadge } from './ComplexityAssessment';
import { ValidationReport, ValidationReportData, SanityReviewResult, ValidationBadge, ValidationIssue } from './ValidationReport';
import { CorrectionTimeline, CorrectionHistory, CorrectionBadge } from './CorrectionTimeline';
import { YoloModeToggle, YoloModeBadge } from './YoloMode';

interface DesignViewProps {
    projectName: string;
    requirements: string;
    languages: string[];
    modelConfig: ModelConfig;
    onDesignComplete: (design: any) => void;
    onGoBack?: () => void;
    onRequestRefinement?: () => void;  // Callback to open refinement window
    autoRun?: boolean;
    enableAdaptive?: boolean;  // Enable adaptive complexity analysis
    yoloMode?: boolean;
    onYoloModeChange?: (enabled: boolean) => void;
}

export const DesignView = ({
    projectName,
    requirements,
    languages,
    modelConfig,
    onDesignComplete,
    onGoBack,
    onRequestRefinement,
    autoRun = false,
    enableAdaptive = true,
    yoloMode = false,
    onYoloModeChange
}: DesignViewProps) => {
    const [designContent, setDesignContent] = useState("");
    const [designData, setDesignData] = useState<any>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [viewMode, setViewMode] = useState<'preview' | 'raw'>('preview');
    const [isEditing, setIsEditing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Ignored issues state for ValidationReport
    const [ignoredIssues, setIgnoredIssues] = useState<Set<number>>(new Set());
    
    // Adaptive complexity state
    const [complexityProfile, setComplexityProfile] = useState<ComplexityProfile | null>(null);
    const [isAnalyzingComplexity, setIsAnalyzingComplexity] = useState(false);
    const [showComplexity, setShowComplexity] = useState(true);
    
    // Validation state
    const [validationReport, setValidationReport] = useState<ValidationReportData | null>(null);
    const [sanityReview, setSanityReview] = useState<SanityReviewResult | null>(null);
    const [isValidating, setIsValidating] = useState(false);
    const [showValidation, setShowValidation] = useState(true);
    
    // Correction loop state
    const [correctionHistory, setCorrectionHistory] = useState<CorrectionHistory | null>(null);
    const [isCorrecting, setIsCorrecting] = useState(false);
    const [currentCorrectionIteration, setCurrentCorrectionIteration] = useState(0);
    const [showCorrection, setShowCorrection] = useState(true);
    
    // Refinement prompt state (when not in YOLO mode)
    const [showRefinementPrompt, setShowRefinementPrompt] = useState(false);

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

    // Validate design after generation
    const validateDesign = async (design: string) => {
        if (!enableAdaptive || !design) return null;
        
        setIsValidating(true);
        setValidationReport(null);
        setSanityReview(null);
        
        try {
            const response = await fetch('/api/adaptive/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    design_text: design,
                    complexity_profile: complexityProfile 
                }),
            });

            if (!response.ok) {
                console.warn('Validation failed, proceeding without validation');
                return null;
            }

            // Parse SSE stream for validation results
            const reader = response.body?.getReader();
            if (!reader) return null;

            const decoder = new TextDecoder();
            let buffer = "";
            let report: ValidationReportData | null = null;
            let review: SanityReviewResult | null = null;

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
                            if (data.validation_report) {
                                report = data.validation_report;
                                setValidationReport(report);
                            }
                            if (data.sanity_review) {
                                review = data.sanity_review;
                                setSanityReview(review);
                            }
                            if (data.done) {
                                if (data.validation_report) setValidationReport(data.validation_report);
                                if (data.sanity_review) setSanityReview(data.sanity_review);
                            }
                        } catch (e) {
                            // Ignore parse errors
                        }
                    }
                }
            }

            return { report, review };
        } catch (err) {
            console.warn('Validation error:', err);
            return null;
        } finally {
            setIsValidating(false);
        }
    };

    // Run correction loop to auto-fix issues
    const runCorrectionLoop = async () => {
        if (!designContent || isCorrecting) return;
        
        setIsCorrecting(true);
        setCurrentCorrectionIteration(0);
        setCorrectionHistory({
            total_iterations: 0,
            max_iterations: 3,
            final_status: 'in_progress',
            iterations: []
        });
        
        try {
            const response = await fetch('/api/adaptive/correct', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    design_text: designContent,
                    validation_report: validationReport,
                    complexity_profile: complexityProfile 
                }),
            });

            if (!response.ok) {
                console.warn('Correction loop failed');
                return;
            }

            // Parse SSE stream for correction updates
            const reader = response.body?.getReader();
            if (!reader) return;

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
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.iteration) {
                                setCurrentCorrectionIteration(data.iteration.iteration_number);
                                setCorrectionHistory(prev => prev ? {
                                    ...prev,
                                    total_iterations: data.iteration.iteration_number,
                                    iterations: [...prev.iterations, data.iteration]
                                } : prev);
                            }
                            
                            if (data.corrected_design) {
                                setDesignContent(data.corrected_design);
                            }
                            
                            if (data.done && data.history) {
                                setCorrectionHistory(data.history);
                                // Re-validate after corrections
                                if (data.corrected_design) {
                                    await validateDesign(data.corrected_design);
                                }
                            }
                        } catch (e) {
                            // Ignore parse errors
                        }
                    }
                }
            }
        } catch (err) {
            console.warn('Correction loop error:', err);
        } finally {
            setIsCorrecting(false);
        }
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
                                console.log('[DesignView] Received structured design:', data.design);
                                console.log('[DesignView] Design fields:', Object.keys(data.design));
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

    // Start pipeline: analyze complexity first (if adaptive), then generate design, then validate
    const startPipeline = async () => {
        // Reset validation/correction state
        setValidationReport(null);
        setSanityReview(null);
        setCorrectionHistory(null);
        
        if (enableAdaptive) {
            await analyzeComplexity();
        }
        await generateDesign();
    };
    
    // Trigger validation when design generation completes
    useEffect(() => {
        if (enableAdaptive && designContent && !isGenerating && !isValidating && !validationReport) {
            // Small delay to let the UI settle
            const timer = setTimeout(() => {
                validateDesign(designContent);
            }, 500);
            return () => clearTimeout(timer);
        }
    }, [designContent, isGenerating, enableAdaptive]);

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

    // Auto-advance when complete - only in YOLO mode
    // Otherwise show refinement prompt for user decision
    useEffect(() => {
        const isFullyComplete = !isGenerating && 
            !isAnalyzingComplexity && 
            !isValidating &&
            !isCorrecting &&
            designContent && 
            !hasAutoAdvanced.current;
            
        if (!isFullyComplete) return;
        
        // In YOLO mode: auto-advance immediately (skip validation checks)
        if (yoloMode && autoRun) {
            const timer = setTimeout(() => {
                hasAutoAdvanced.current = true;
                handleApprove();
            }, 1500);
            return () => clearTimeout(timer);
        }
        
        // Not in YOLO mode: show refinement prompt instead of auto-advancing
        if (!yoloMode && !showRefinementPrompt) {
            setShowRefinementPrompt(true);
        }
    }, [yoloMode, autoRun, isGenerating, isAnalyzingComplexity, isValidating, isCorrecting, designContent, showRefinementPrompt]);

    const handleApprove = () => {
        const designWithMetadata = {
            ...(designData || { raw_llm_response: designContent, project_name: projectName }),
            complexity_profile: complexityProfile,
            validation_report: validationReport,
            sanity_review: sanityReview,
            correction_history: correctionHistory
        };
        console.log('[DesignView] Passing design to next stage:', designWithMetadata);
        console.log('[DesignView] Design has fields:', Object.keys(designWithMetadata));
        onDesignComplete(designWithMetadata);
    };
    
    // Check if approval should be blocked
    const isApprovalBlocked = isGenerating || isAnalyzingComplexity || isValidating || isCorrecting || !designContent;
    const hasValidationIssues = validationReport && !validationReport.is_valid;
    
    // Handler for fixing individual issues
    const handleFixIssue = async (issue: ValidationIssue, index: number) => {
        // TODO: Implement single-issue fix via backend
        console.log('Fix issue:', issue, 'at index:', index);
    };
    
    // Handler for ignoring/unignoring issues
    const handleIgnoreIssue = (issue: ValidationIssue, index: number) => {
        setIgnoredIssues(prev => {
            const next = new Set(prev);
            if (next.has(index)) {
                next.delete(index);
            } else {
                next.add(index);
            }
            return next;
        });
    };
    
    // Handler for stopping correction loop and accepting current state
    const handleStopAndAccept = () => {
        // TODO: Signal backend to stop correction loop
        setIsCorrecting(false);
    };
    
    // Handler for depth level override
    const handleDepthOverride = (depth: 'minimal' | 'standard' | 'detailed') => {
        if (complexityProfile) {
            setComplexityProfile({ ...complexityProfile, depth_level: depth });
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <div className="flex items-center gap-4">
                    {/* Go Back button */}
                    {onGoBack && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onGoBack}
                            className="gap-1"
                        >
                            <ArrowLeft className="h-4 w-4" />
                            Back
                        </Button>
                    )}
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                        <LayoutGrid className="h-5 w-5" />
                        System Design
                    </h2>
                    {/* YOLO mode badge */}
                    <YoloModeBadge enabled={yoloMode} />
                    {/* Show badges in header when panels collapsed */}
                    <div className="flex items-center gap-2">
                        {complexityProfile && !showComplexity && (
                            <button 
                                onClick={() => setShowComplexity(true)}
                                className="hover:opacity-80 transition-opacity"
                            >
                                <ComplexityBadge profile={complexityProfile} />
                            </button>
                        )}
                        {validationReport && !showValidation && (
                            <button 
                                onClick={() => setShowValidation(true)}
                                className="hover:opacity-80 transition-opacity"
                            >
                                <ValidationBadge report={validationReport} />
                            </button>
                        )}
                        {correctionHistory && correctionHistory.total_iterations > 0 && !showCorrection && (
                            <button 
                                onClick={() => setShowCorrection(true)}
                                className="hover:opacity-80 transition-opacity"
                            >
                                <CorrectionBadge history={correctionHistory} isRunning={isCorrecting} />
                            </button>
                        )}
                    </div>
                </div>
                <div className="flex gap-2">
                    {/* Toggle buttons for panels */}
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
                    {validationReport && showValidation && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowValidation(false)}
                        >
                            <Shield className="h-4 w-4 mr-2" />
                            Hide Validation
                        </Button>
                    )}
                    {correctionHistory && correctionHistory.total_iterations > 0 && showCorrection && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowCorrection(false)}
                        >
                            <History className="h-4 w-4 mr-2" />
                            Hide Corrections
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
                        disabled={isGenerating || isAnalyzingComplexity || isValidating || isCorrecting}
                    >
                        Regenerate
                    </Button>
                    
                    {/* Refinement Button */}
                    {designContent && !isGenerating && onRequestRefinement && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={onRequestRefinement}
                            className="gap-2"
                        >
                            <MessageSquare className="h-4 w-4" />
                            Refine Design
                        </Button>
                    )}
                    
                    {/* YOLO Mode Toggle */}
                    {onYoloModeChange && (
                        <YoloModeToggle
                            enabled={yoloMode}
                            onToggle={onYoloModeChange}
                            disabled={isGenerating || isAnalyzingComplexity}
                        />
                    )}

                    <Button
                        size="sm"
                        onClick={handleApprove}
                        disabled={isApprovalBlocked}
                        variant={hasValidationIssues ? "outline" : "default"}
                    >
                        <Check className="h-4 w-4 mr-2" />
                        {hasValidationIssues ? "Approve Anyway" : "Approve Design"}
                    </Button>
                </div>
            </div>

            <ScrollArea className="flex-1 p-6">
                {/* Adaptive Pipeline Stage Indicator */}
                {enableAdaptive && (
                    <div className="mb-4 p-3 bg-muted/20 border border-border/30 rounded-lg">
                        <div className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2">
                                <span className="font-mono text-muted-foreground">ADAPTIVE PIPELINE:</span>
                                <div className="flex items-center gap-2">
                                    <span className={`px-2 py-0.5 rounded ${complexityProfile ? 'bg-green-500/20 text-green-400' : isAnalyzingComplexity ? 'bg-blue-500/20 text-blue-400' : 'bg-muted/30 text-muted-foreground'}`}>
                                        1. Complexity
                                    </span>
                                    <span className={`px-2 py-0.5 rounded ${validationReport ? 'bg-green-500/20 text-green-400' : isValidating ? 'bg-blue-500/20 text-blue-400' : 'bg-muted/30 text-muted-foreground'}`}>
                                        2. Validation
                                    </span>
                                    <span className={`px-2 py-0.5 rounded ${correctionHistory && correctionHistory.total_iterations > 0 ? 'bg-green-500/20 text-green-400' : isCorrecting ? 'bg-blue-500/20 text-blue-400' : 'bg-muted/30 text-muted-foreground'}`}>
                                        3. Correction
                                    </span>
                                </div>
                            </div>
                            <span className="text-muted-foreground">
                                {complexityProfile?.depth_level ? `Depth: ${complexityProfile.depth_level}` : 'Analyzing...'}
                            </span>
                        </div>
                    </div>
                )}
                
                {/* Refinement Prompt (when not in YOLO mode) */}
                {showRefinementPrompt && !yoloMode && designContent && (
                    <Card className="mb-6 border-primary/50 bg-primary/5">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base">
                                <MessageSquare className="h-5 w-5 text-primary" />
                                Ready to Continue
                            </CardTitle>
                            <CardDescription>
                                Design generation is complete. Would you like to refine the design before generating phases?
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="flex gap-3">
                            <Button
                                variant="outline"
                                className="flex-1"
                                onClick={() => {
                                    if (onRequestRefinement) {
                                        onRequestRefinement();
                                    }
                                }}
                                disabled={!onRequestRefinement}
                            >
                                <MessageSquare className="h-4 w-4 mr-2" />
                                Yes, Refine Design
                            </Button>
                            <Button
                                className="flex-1"
                                onClick={() => {
                                    setShowRefinementPrompt(false);
                                    hasAutoAdvanced.current = true;
                                    handleApprove();
                                }}
                            >
                                <ArrowRight className="h-4 w-4 mr-2" />
                                No, Continue to Plan
                            </Button>
                        </CardContent>
                    </Card>
                )}
                
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
                                onDepthOverride={handleDepthOverride}
                                allowDepthOverride={true}
                            />
                        ) : null}
                    </div>
                )}

                {/* Validation Report Panel */}
                {enableAdaptive && showValidation && (isValidating || validationReport) && (
                    <div className="mb-6">
                        {isValidating ? (
                            <Card className="animate-pulse">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-base">
                                        <Shield className="h-5 w-5 text-primary animate-spin" />
                                        Validating Design...
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="h-24 bg-muted rounded" />
                                </CardContent>
                            </Card>
                        ) : validationReport ? (
                            <ValidationReport 
                                report={validationReport}
                                sanityReview={sanityReview}
                                onRequestCorrection={validationReport.auto_correctable_count > 0 ? runCorrectionLoop : undefined}
                                onFixIssue={handleFixIssue}
                                onIgnoreIssue={handleIgnoreIssue}
                                ignoredIssues={ignoredIssues}
                                showDetails={true}
                            />
                        ) : null}
                    </div>
                )}

                {/* Correction Timeline Panel */}
                {enableAdaptive && showCorrection && (isCorrecting || (correctionHistory && correctionHistory.total_iterations > 0)) && (
                    <div className="mb-6">
                        {correctionHistory && (
                            <CorrectionTimeline 
                                history={correctionHistory}
                                isRunning={isCorrecting}
                                currentIteration={currentCorrectionIteration}
                                showDetails={true}
                                onStopAndAccept={handleStopAndAccept}
                            />
                        )}
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
