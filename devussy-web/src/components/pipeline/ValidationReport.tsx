"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
    Shield, 
    CheckCircle2, 
    XCircle, 
    AlertTriangle,
    FileCheck,
    Scale,
    Search,
    Lightbulb,
    Target,
    Wrench,
    Download
} from "lucide-react";
import { DownloadButton, formatValidationAsMarkdown } from "@/components/ui/DownloadButton";

/**
 * Validation issue structure matching backend ValidationReport
 */
export interface ValidationIssue {
    check_name: string;
    severity: 'error' | 'warning' | 'info';
    message: string;
    location?: string;
    suggestion?: string;
    auto_correctable: boolean;
}

/**
 * Full validation report from backend
 */
export interface ValidationReportData {
    is_valid: boolean;
    issues: ValidationIssue[];
    checks_passed: string[];
    checks_failed: string[];
    auto_correctable_count: number;
    manual_review_required: boolean;
    timestamp?: string;
}

/**
 * LLM sanity review result
 */
export interface SanityReviewResult {
    is_sane: boolean;
    confidence: number;
    issues_found: string[];
    suggestions: string[];
    overall_assessment: string;
}

interface ValidationReportProps {
    report: ValidationReportData;
    sanityReview?: SanityReviewResult | null;
    isLoading?: boolean;
    onRequestCorrection?: () => void;
    onFixIssue?: (issue: ValidationIssue, index: number) => void;
    onIgnoreIssue?: (issue: ValidationIssue, index: number) => void;
    ignoredIssues?: Set<number>;
    showDetails?: boolean;
}

/**
 * Get icon for check type
 */
function getCheckIcon(checkName: string) {
    switch (checkName.toLowerCase()) {
        case 'consistency': return FileCheck;
        case 'completeness': return Target;
        case 'scope_alignment': return Scale;
        case 'hallucination_detection': return Search;
        case 'over_engineering_detection': return Lightbulb;
        default: return Shield;
    }
}

/**
 * Get severity styling
 */
function getSeverityConfig(severity: 'error' | 'warning' | 'info') {
    switch (severity) {
        case 'error':
            return {
                icon: XCircle,
                color: 'text-red-500',
                bgColor: 'bg-red-500/10',
                borderColor: 'border-red-500/30',
                label: 'Error'
            };
        case 'warning':
            return {
                icon: AlertTriangle,
                color: 'text-yellow-500',
                bgColor: 'bg-yellow-500/10',
                borderColor: 'border-yellow-500/30',
                label: 'Warning'
            };
        case 'info':
            return {
                icon: Lightbulb,
                color: 'text-blue-500',
                bgColor: 'bg-blue-500/10',
                borderColor: 'border-blue-500/30',
                label: 'Info'
            };
    }
}

/**
 * Format check name for display
 */
function formatCheckName(name: string): string {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Individual issue card with controls
 */
function IssueCard({ 
    issue, 
    index,
    isIgnored = false,
    onFix,
    onIgnore 
}: { 
    issue: ValidationIssue; 
    index: number;
    isIgnored?: boolean;
    onFix?: (issue: ValidationIssue, index: number) => void;
    onIgnore?: (issue: ValidationIssue, index: number) => void;
}) {
    const config = getSeverityConfig(issue.severity);
    const SeverityIcon = config.icon;
    const CheckIcon = getCheckIcon(issue.check_name);

    return (
        <div className={`p-4 rounded-lg border ${config.borderColor} ${config.bgColor} ${isIgnored ? 'opacity-50' : ''} transition-opacity`}>
            <div className="flex items-start gap-3">
                <SeverityIcon className={`h-5 w-5 mt-0.5 ${config.color}`} />
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <CheckIcon className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">
                            {formatCheckName(issue.check_name)}
                        </span>
                        {issue.auto_correctable && (
                            <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded-full flex items-center gap-1">
                                <Wrench className="h-3 w-3" />
                                Auto-fix
                            </span>
                        )}
                        {isIgnored && (
                            <span className="text-xs px-2 py-0.5 bg-gray-500/20 text-gray-400 rounded-full">
                                Ignored
                            </span>
                        )}
                    </div>
                    <p className="text-sm">{issue.message}</p>
                    {issue.location && (
                        <p className="text-xs text-muted-foreground mt-1">
                            Location: {issue.location}
                        </p>
                    )}
                    {issue.suggestion && (
                        <p className="text-xs text-muted-foreground mt-2 italic">
                            💡 {issue.suggestion}
                        </p>
                    )}
                    
                    {/* Issue action buttons */}
                    {(onFix || onIgnore) && (
                        <div className="flex items-center gap-2 mt-3 pt-2 border-t border-border/30">
                            {onFix && issue.auto_correctable && !isIgnored && (
                                <button
                                    onClick={() => onFix(issue, index)}
                                    className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-primary/10 hover:bg-primary/20 text-primary rounded-md transition-colors"
                                >
                                    <Wrench className="h-3 w-3" />
                                    Fix This
                                </button>
                            )}
                            {onIgnore && (
                                <button
                                    onClick={() => onIgnore(issue, index)}
                                    className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-md transition-colors ${
                                        isIgnored 
                                            ? 'bg-green-500/10 hover:bg-green-500/20 text-green-400'
                                            : 'bg-muted/50 hover:bg-muted text-muted-foreground'
                                    }`}
                                >
                                    {isIgnored ? (
                                        <>
                                            <CheckCircle2 className="h-3 w-3" />
                                            Unignore
                                        </>
                                    ) : (
                                        <>
                                            <XCircle className="h-3 w-3" />
                                            Ignore
                                        </>
                                    )}
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

/**
 * Check result badge
 */
function CheckBadge({ name, passed }: { name: string; passed: boolean }) {
    return (
        <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${
            passed 
                ? 'bg-green-500/10 text-green-500 border border-green-500/30'
                : 'bg-red-500/10 text-red-500 border border-red-500/30'
        }`}>
            {passed ? (
                <CheckCircle2 className="h-3 w-3" />
            ) : (
                <XCircle className="h-3 w-3" />
            )}
            {formatCheckName(name)}
        </div>
    );
}

/**
 * Sanity Review Section
 */
function SanityReviewSection({ review }: { review: SanityReviewResult }) {
    const confidencePercent = Math.round(review.confidence * 100);
    const confidenceColor = review.confidence >= 0.8 
        ? 'text-green-500' 
        : review.confidence >= 0.6 
            ? 'text-yellow-500' 
            : 'text-red-500';

    return (
        <div className="mt-4 pt-4 border-t border-border/50">
            <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Search className="h-4 w-4 text-primary" />
                LLM Sanity Review
            </h4>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
                    <p className="text-xs text-muted-foreground mb-1">Status</p>
                    <div className="flex items-center gap-2">
                        {review.is_sane ? (
                            <>
                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                                <span className="font-medium text-green-500">Sane</span>
                            </>
                        ) : (
                            <>
                                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                                <span className="font-medium text-yellow-500">Needs Review</span>
                            </>
                        )}
                    </div>
                </div>
                
                <div className="p-3 rounded-lg bg-muted/30 border border-border/50">
                    <p className="text-xs text-muted-foreground mb-1">Confidence</p>
                    <p className={`font-bold ${confidenceColor}`}>
                        {confidencePercent}%
                    </p>
                </div>
            </div>

            {review.overall_assessment && (
                <p className="text-sm text-muted-foreground mb-3">
                    {review.overall_assessment}
                </p>
            )}

            {review.issues_found.length > 0 && (
                <div className="mb-3">
                    <p className="text-xs font-medium text-muted-foreground mb-2">Issues Found:</p>
                    <ul className="text-sm space-y-1">
                        {review.issues_found.map((issue, i) => (
                            <li key={i} className="flex items-start gap-2">
                                <AlertTriangle className="h-3 w-3 mt-1 text-yellow-500" />
                                <span>{issue}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {review.suggestions.length > 0 && (
                <div>
                    <p className="text-xs font-medium text-muted-foreground mb-2">Suggestions:</p>
                    <ul className="text-sm space-y-1">
                        {review.suggestions.map((suggestion, i) => (
                            <li key={i} className="flex items-start gap-2">
                                <Lightbulb className="h-3 w-3 mt-1 text-blue-500" />
                                <span>{suggestion}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

/**
 * ValidationReport Component
 * 
 * Displays validation results including rule-based checks and LLM sanity review.
 */
export function ValidationReport({ 
    report, 
    sanityReview,
    isLoading = false,
    onRequestCorrection,
    onFixIssue,
    onIgnoreIssue,
    ignoredIssues,
    showDetails = true
}: ValidationReportProps) {
    if (isLoading) {
        return (
            <Card className="animate-pulse">
                <CardHeader>
                    <div className="h-6 bg-muted rounded w-48" />
                    <div className="h-4 bg-muted rounded w-64 mt-2" />
                </CardHeader>
                <CardContent>
                    <div className="h-32 bg-muted rounded" />
                </CardContent>
            </Card>
        );
    }

    const errorCount = report.issues.filter(i => i.severity === 'error').length;
    const warningCount = report.issues.filter(i => i.severity === 'warning').length;
    const infoCount = report.issues.filter(i => i.severity === 'info').length;

    return (
        <Card className="overflow-hidden">
            <CardHeader className="border-b border-border/50">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <Shield className={`h-5 w-5 ${report.is_valid ? 'text-green-500' : 'text-yellow-500'}`} />
                            Design Validation
                        </CardTitle>
                        <CardDescription>
                            {report.is_valid 
                                ? 'All validation checks passed'
                                : `${report.checks_failed.length} check(s) need attention`
                            }
                        </CardDescription>
                    </div>
                    
                    <div className="flex items-center gap-2">
                        <DownloadButton
                            content={formatValidationAsMarkdown(report, sanityReview)}
                            filename="validation_report.md"
                            label="Download"
                            size="sm"
                        />
                        {!report.is_valid && report.auto_correctable_count > 0 && onRequestCorrection && (
                            <button 
                                onClick={onRequestCorrection}
                                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary/10 hover:bg-primary/20 text-primary rounded-lg transition-colors"
                            >
                                <Wrench className="h-4 w-4" />
                                Auto-correct ({report.auto_correctable_count})
                            </button>
                        )}
                    </div>
                </div>
            </CardHeader>

            <CardContent className="pt-6">
                {/* Summary row */}
                <div className="flex items-center gap-4 mb-6">
                    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                        report.is_valid 
                            ? 'bg-green-500/10 border border-green-500/30' 
                            : 'bg-yellow-500/10 border border-yellow-500/30'
                    }`}>
                        {report.is_valid ? (
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                        ) : (
                            <AlertTriangle className="h-5 w-5 text-yellow-500" />
                        )}
                        <span className={`font-medium ${report.is_valid ? 'text-green-500' : 'text-yellow-500'}`}>
                            {report.is_valid ? 'Valid' : 'Needs Review'}
                        </span>
                    </div>

                    <div className="flex items-center gap-3 text-sm">
                        {errorCount > 0 && (
                            <span className="flex items-center gap-1 text-red-500">
                                <XCircle className="h-4 w-4" />
                                {errorCount} error{errorCount !== 1 ? 's' : ''}
                            </span>
                        )}
                        {warningCount > 0 && (
                            <span className="flex items-center gap-1 text-yellow-500">
                                <AlertTriangle className="h-4 w-4" />
                                {warningCount} warning{warningCount !== 1 ? 's' : ''}
                            </span>
                        )}
                        {infoCount > 0 && (
                            <span className="flex items-center gap-1 text-blue-500">
                                <Lightbulb className="h-4 w-4" />
                                {infoCount} info
                            </span>
                        )}
                    </div>

                    {report.manual_review_required && (
                        <span className="ml-auto text-xs px-2 py-1 bg-orange-500/20 text-orange-400 rounded-full">
                            Manual review required
                        </span>
                    )}
                </div>

                {/* Checks overview */}
                <div className="mb-6">
                    <h4 className="text-sm font-medium mb-3 text-muted-foreground">
                        Validation Checks
                    </h4>
                    <div className="flex flex-wrap gap-2">
                        {report.checks_passed.map(check => (
                            <CheckBadge key={check} name={check} passed={true} />
                        ))}
                        {report.checks_failed.map(check => (
                            <CheckBadge key={check} name={check} passed={false} />
                        ))}
                    </div>
                </div>

                {/* Issues list */}
                {showDetails && report.issues.length > 0 && (
                    <div className="space-y-3">
                        <h4 className="text-sm font-medium text-muted-foreground">
                            Issues ({report.issues.length})
                        </h4>
                        {report.issues.map((issue, index) => (
                            <IssueCard 
                                key={index} 
                                issue={issue} 
                                index={index}
                                isIgnored={ignoredIssues?.has(index)}
                                onFix={onFixIssue}
                                onIgnore={onIgnoreIssue}
                            />
                        ))}
                    </div>
                )}

                {/* LLM Sanity Review */}
                {sanityReview && (
                    <SanityReviewSection review={sanityReview} />
                )}
            </CardContent>
        </Card>
    );
}

/**
 * Compact validation status badge
 */
export function ValidationBadge({ report }: { report: ValidationReportData }) {
    const errorCount = report.issues.filter(i => i.severity === 'error').length;
    const warningCount = report.issues.filter(i => i.severity === 'warning').length;

    return (
        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
            report.is_valid 
                ? 'bg-green-500/10 border border-green-500/30'
                : 'bg-yellow-500/10 border border-yellow-500/30'
        }`}>
            {report.is_valid ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
            ) : (
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
            )}
            <span className={report.is_valid ? 'text-green-500' : 'text-yellow-500'}>
                {report.is_valid ? 'Valid' : 'Issues'}
            </span>
            {!report.is_valid && (
                <>
                    <span className="text-muted-foreground">|</span>
                    {errorCount > 0 && <span className="text-red-500">{errorCount}E</span>}
                    {warningCount > 0 && <span className="text-yellow-500">{warningCount}W</span>}
                </>
            )}
        </div>
    );
}

export default ValidationReport;
