"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
    History, 
    CheckCircle2, 
    XCircle, 
    AlertTriangle,
    ArrowRight,
    RefreshCw,
    Clock,
    Wrench,
    Target,
    Loader2,
    Square,
    RotateCcw,
    Download
} from "lucide-react";
import { DownloadButton, formatCorrectionAsMarkdown } from "@/components/ui/DownloadButton";

/**
 * Single correction iteration data
 */
export interface CorrectionIteration {
    iteration_number: number;
    timestamp?: string;
    issues_addressed: string[];
    corrections_applied: string[];
    validation_result: {
        is_valid: boolean;
        remaining_issues: number;
    };
    llm_review_confidence?: number;
    duration_ms?: number;
}

/**
 * Full correction history from backend
 */
export interface CorrectionHistory {
    total_iterations: number;
    max_iterations: number;
    final_status: 'success' | 'max_iterations_reached' | 'manual_review_required' | 'in_progress';
    iterations: CorrectionIteration[];
    started_at?: string;
    completed_at?: string;
}

interface CorrectionTimelineProps {
    history: CorrectionHistory;
    isRunning?: boolean;
    currentIteration?: number;
    showDetails?: boolean;
    onStopAndAccept?: () => void;
    onRetryIteration?: (iterationNumber: number) => void;
}

/**
 * Get status configuration
 */
function getStatusConfig(status: CorrectionHistory['final_status']) {
    switch (status) {
        case 'success':
            return {
                icon: CheckCircle2,
                color: 'text-green-500',
                bgColor: 'bg-green-500/10',
                borderColor: 'border-green-500/30',
                label: 'Completed Successfully'
            };
        case 'max_iterations_reached':
            return {
                icon: AlertTriangle,
                color: 'text-yellow-500',
                bgColor: 'bg-yellow-500/10',
                borderColor: 'border-yellow-500/30',
                label: 'Max Iterations Reached'
            };
        case 'manual_review_required':
            return {
                icon: XCircle,
                color: 'text-orange-500',
                bgColor: 'bg-orange-500/10',
                borderColor: 'border-orange-500/30',
                label: 'Manual Review Required'
            };
        case 'in_progress':
            return {
                icon: RefreshCw,
                color: 'text-blue-500',
                bgColor: 'bg-blue-500/10',
                borderColor: 'border-blue-500/30',
                label: 'In Progress'
            };
    }
}

/**
 * Timeline node for an iteration
 */
function IterationNode({ 
    iteration, 
    isLast, 
    isCurrent,
    showDetails,
    onRetry
}: { 
    iteration: CorrectionIteration; 
    isLast: boolean;
    isCurrent: boolean;
    showDetails: boolean;
    onRetry?: (iterationNumber: number) => void;
}) {
    const isSuccess = iteration.validation_result.is_valid;
    
    return (
        <div className="relative">
            {/* Connector line */}
            {!isLast && (
                <div className="absolute left-4 top-10 w-0.5 h-full bg-border/50" />
            )}
            
            <div className="flex items-start gap-4">
                {/* Node indicator */}
                <div className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                    isCurrent 
                        ? 'border-blue-500 bg-blue-500/20'
                        : isSuccess 
                            ? 'border-green-500 bg-green-500/20'
                            : 'border-yellow-500 bg-yellow-500/20'
                }`}>
                    {isCurrent ? (
                        <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
                    ) : isSuccess ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                        <RefreshCw className="h-4 w-4 text-yellow-500" />
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 pb-8">
                    <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-medium">
                            Iteration {iteration.iteration_number}
                        </h4>
                        {iteration.duration_ms && (
                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {(iteration.duration_ms / 1000).toFixed(1)}s
                            </span>
                        )}
                        {iteration.llm_review_confidence !== undefined && (
                            <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full">
                                {Math.round(iteration.llm_review_confidence * 100)}% confidence
                            </span>
                        )}
                        {/* Retry button for failed iterations */}
                        {!isSuccess && !isCurrent && onRetry && (
                            <button
                                onClick={() => onRetry(iteration.iteration_number)}
                                className="flex items-center gap-1 px-2 py-0.5 text-xs bg-muted hover:bg-muted/80 rounded-md transition-colors"
                            >
                                <RotateCcw className="h-3 w-3" />
                                Retry
                            </button>
                        )}
                    </div>

                    {showDetails && (
                        <div className="space-y-3">
                            {/* Issues addressed */}
                            {iteration.issues_addressed.length > 0 && (
                                <div>
                                    <p className="text-xs font-medium text-muted-foreground mb-1">
                                        Issues Addressed:
                                    </p>
                                    <div className="flex flex-wrap gap-1">
                                        {iteration.issues_addressed.map((issue, i) => (
                                            <span 
                                                key={i}
                                                className="text-xs px-2 py-0.5 bg-muted rounded-full"
                                            >
                                                {issue}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Corrections applied */}
                            {iteration.corrections_applied.length > 0 && (
                                <div>
                                    <p className="text-xs font-medium text-muted-foreground mb-1">
                                        Corrections Applied:
                                    </p>
                                    <ul className="text-sm space-y-1">
                                        {iteration.corrections_applied.map((correction, i) => (
                                            <li key={i} className="flex items-start gap-2">
                                                <Wrench className="h-3 w-3 mt-1 text-primary" />
                                                <span className="text-muted-foreground">{correction}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Result */}
                            <div className={`inline-flex items-center gap-2 px-2 py-1 rounded-md text-xs ${
                                isSuccess 
                                    ? 'bg-green-500/10 text-green-500'
                                    : 'bg-yellow-500/10 text-yellow-500'
                            }`}>
                                {isSuccess ? (
                                    <>
                                        <CheckCircle2 className="h-3 w-3" />
                                        All checks passed
                                    </>
                                ) : (
                                    <>
                                        <AlertTriangle className="h-3 w-3" />
                                        {iteration.validation_result.remaining_issues} issue(s) remaining
                                    </>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

/**
 * CorrectionTimeline Component
 * 
 * Displays the history of correction loop iterations with visual timeline.
 */
export function CorrectionTimeline({ 
    history, 
    isRunning = false,
    currentIteration,
    showDetails = true,
    onStopAndAccept,
    onRetryIteration
}: CorrectionTimelineProps) {
    const statusConfig = getStatusConfig(isRunning ? 'in_progress' : history.final_status);
    const StatusIcon = statusConfig.icon;

    return (
        <Card className="overflow-hidden">
            <CardHeader className="border-b border-border/50">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <History className="h-5 w-5 text-primary" />
                            Correction Timeline
                        </CardTitle>
                        <CardDescription>
                            {history.total_iterations} of {history.max_iterations} iterations
                        </CardDescription>
                    </div>
                    
                    <div className="flex items-center gap-2">
                        <DownloadButton
                            content={formatCorrectionAsMarkdown(history)}
                            filename="correction_history.md"
                            label="Download"
                            size="sm"
                        />
                        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${statusConfig.bgColor} border ${statusConfig.borderColor}`}>
                            <StatusIcon className={`h-4 w-4 ${statusConfig.color} ${isRunning ? 'animate-spin' : ''}`} />
                            <span className={`text-sm font-medium ${statusConfig.color}`}>
                                {statusConfig.label}
                            </span>
                        </div>
                        
                        {/* Stop & Accept button - only show when running */}
                        {isRunning && onStopAndAccept && (
                            <button
                                onClick={onStopAndAccept}
                                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-orange-500/10 hover:bg-orange-500/20 text-orange-400 border border-orange-500/30 rounded-lg transition-colors"
                            >
                                <Square className="h-3.5 w-3.5" />
                                Stop & Accept
                            </button>
                        )}
                    </div>
                </div>
            </CardHeader>

            <CardContent className="pt-6">
                {/* Progress bar */}
                <div className="mb-6">
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
                        <span>Progress</span>
                        <span>{history.total_iterations} / {history.max_iterations}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <div 
                            className={`h-full rounded-full transition-all duration-500 ${
                                history.final_status === 'success' 
                                    ? 'bg-green-500'
                                    : isRunning 
                                        ? 'bg-blue-500'
                                        : 'bg-yellow-500'
                            }`}
                            style={{ width: `${(history.total_iterations / history.max_iterations) * 100}%` }}
                        />
                    </div>
                </div>

                {/* Timeline */}
                {history.iterations.length > 0 ? (
                    <div className="relative">
                        {history.iterations.map((iteration, index) => (
                            <IterationNode
                                key={iteration.iteration_number}
                                iteration={iteration}
                                isLast={index === history.iterations.length - 1}
                                isCurrent={isRunning && currentIteration === iteration.iteration_number}
                                showDetails={showDetails}
                                onRetry={onRetryIteration}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-muted-foreground">
                        <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No corrections needed</p>
                        <p className="text-xs">Design passed all validation checks</p>
                    </div>
                )}

                {/* Summary */}
                {history.total_iterations > 0 && (
                    <div className="mt-6 pt-4 border-t border-border/50">
                        <div className="grid grid-cols-3 gap-4 text-center">
                            <div>
                                <p className="text-2xl font-bold text-primary">
                                    {history.total_iterations}
                                </p>
                                <p className="text-xs text-muted-foreground">Iterations</p>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-primary">
                                    {history.iterations.reduce(
                                        (sum, it) => sum + it.corrections_applied.length, 
                                        0
                                    )}
                                </p>
                                <p className="text-xs text-muted-foreground">Corrections</p>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-primary">
                                    {history.iterations.length > 0 
                                        ? Math.round(
                                            (history.iterations[history.iterations.length - 1]
                                                .llm_review_confidence ?? 0) * 100
                                        )
                                        : 0
                                    }%
                                </p>
                                <p className="text-xs text-muted-foreground">Final Confidence</p>
                            </div>
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

/**
 * Compact correction status badge
 */
export function CorrectionBadge({ history, isRunning }: { history: CorrectionHistory; isRunning?: boolean }) {
    const status = isRunning ? 'in_progress' : history.final_status;
    const config = getStatusConfig(status);
    const Icon = config.icon;

    return (
        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${config.bgColor} border ${config.borderColor}`}>
            <Icon className={`h-4 w-4 ${config.color} ${isRunning ? 'animate-spin' : ''}`} />
            <span className={config.color}>
                {history.total_iterations}/{history.max_iterations}
            </span>
            <span className="text-muted-foreground">|</span>
            <span className={config.color}>
                {config.label.split(' ')[0]}
            </span>
        </div>
    );
}

export default CorrectionTimeline;
