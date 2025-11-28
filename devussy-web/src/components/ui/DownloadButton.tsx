"use client";

import React from 'react';
import { Button } from "@/components/ui/button";
import { Download, Loader2 } from "lucide-react";
import { cn } from "@/utils";

interface DownloadButtonProps {
    content: string;
    filename: string;
    label?: string;
    className?: string;
    variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
    size?: "default" | "sm" | "lg" | "icon";
    disabled?: boolean;
    isLoading?: boolean;
}

/**
 * Reusable download button component for exporting content as markdown files.
 * Used across pipeline stages to allow users to download individual artifacts.
 */
export const DownloadButton: React.FC<DownloadButtonProps> = ({
    content,
    filename,
    label = "Download",
    className,
    variant = "outline",
    size = "sm",
    disabled = false,
    isLoading = false,
}) => {
    const handleDownload = () => {
        if (!content || isLoading) return;

        // Ensure filename ends with .md
        const finalFilename = filename.endsWith('.md') ? filename : `${filename}.md`;

        // Create blob and trigger download
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = finalFilename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    };

    return (
        <Button
            variant={variant}
            size={size}
            onClick={handleDownload}
            disabled={disabled || !content || isLoading}
            className={cn("gap-2", className)}
        >
            {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
                <Download className="h-4 w-4" />
            )}
            {label}
        </Button>
    );
};

/**
 * Helper function to format interview data as markdown
 */
export function formatInterviewAsMarkdown(history: Array<{ role: string; content: string }>): string {
    let md = "# Project Interview Transcript\n\n";
    md += `_Generated: ${new Date().toISOString()}_\n\n`;
    md += "---\n\n";

    history.forEach((msg, idx) => {
        if (msg.role === 'user') {
            md += `### User:\n${msg.content}\n\n`;
        } else if (msg.role === 'assistant') {
            md += `### Assistant:\n${msg.content}\n\n`;
        }
    });

    return md;
}

/**
 * Helper function to format complexity profile as markdown
 */
export function formatComplexityAsMarkdown(profile: any): string {
    if (!profile) return "";

    let md = "# Complexity Analysis Report\n\n";
    md += `_Generated: ${new Date().toISOString()}_\n\n`;
    md += "---\n\n";

    md += "## Overview\n\n";
    md += `| Metric | Value |\n`;
    md += `|--------|-------|\n`;
    md += `| **Complexity Score** | ${profile.score ?? profile.complexity_score ?? 'N/A'}/20 |\n`;
    md += `| **Depth Level** | ${profile.depth_level || 'N/A'} |\n`;
    md += `| **Estimated Phases** | ${profile.estimated_phase_count || 'N/A'} |\n`;
    md += `| **Confidence** | ${profile.confidence ? `${(profile.confidence * 100).toFixed(0)}%` : 'N/A'} |\n`;
    md += "\n";

    if (profile.rationale) {
        md += "## Rationale\n\n";
        md += `${profile.rationale}\n\n`;
    }

    if (profile.complexity_factors && profile.complexity_factors.length > 0) {
        md += "## Complexity Factors\n\n";
        profile.complexity_factors.forEach((factor: string) => {
            md += `- ${factor}\n`;
        });
        md += "\n";
    }

    if (profile.hidden_risks && profile.hidden_risks.length > 0) {
        md += "## Hidden Risks\n\n";
        profile.hidden_risks.forEach((risk: string) => {
            md += `- ${risk}\n`;
        });
        md += "\n";
    }

    if (profile.follow_up_questions && profile.follow_up_questions.length > 0) {
        md += "## Follow-up Questions\n\n";
        profile.follow_up_questions.forEach((q: string) => {
            md += `- ${q}\n`;
        });
        md += "\n";
    }

    return md;
}

/**
 * Helper function to format validation report as markdown
 */
export function formatValidationAsMarkdown(report: any, sanityReview?: any): string {
    if (!report) return "";

    let md = "# Validation Report\n\n";
    md += `_Generated: ${new Date().toISOString()}_\n\n`;
    md += "---\n\n";

    md += "## Summary\n\n";
    md += `| Status | Value |\n`;
    md += `|--------|-------|\n`;
    md += `| **Valid** | ${report.is_valid ? '✅ Yes' : '❌ No'} |\n`;
    md += `| **Checks Passed** | ${report.checks_passed?.length || 0} |\n`;
    md += `| **Checks Failed** | ${report.checks_failed?.length || 0} |\n`;
    md += `| **Auto-correctable Issues** | ${report.auto_correctable_count || 0} |\n`;
    md += `| **Manual Review Required** | ${report.manual_review_required ? 'Yes' : 'No'} |\n`;
    md += "\n";

    if (report.checks_passed && report.checks_passed.length > 0) {
        md += "## Checks Passed\n\n";
        report.checks_passed.forEach((check: string) => {
            md += `- ✅ ${check}\n`;
        });
        md += "\n";
    }

    if (report.issues && report.issues.length > 0) {
        md += "## Issues Found\n\n";
        report.issues.forEach((issue: any, idx: number) => {
            const severity = issue.severity === 'error' ? '🔴' : issue.severity === 'warning' ? '🟡' : 'ℹ️';
            md += `### ${idx + 1}. ${severity} ${issue.check_name}\n\n`;
            md += `**Severity:** ${issue.severity}\n\n`;
            md += `**Message:** ${issue.message}\n\n`;
            if (issue.location) {
                md += `**Location:** ${issue.location}\n\n`;
            }
            if (issue.suggestion) {
                md += `**Suggestion:** ${issue.suggestion}\n\n`;
            }
            md += `**Auto-correctable:** ${issue.auto_correctable ? 'Yes' : 'No'}\n\n`;
        });
    }

    if (sanityReview) {
        md += "## LLM Sanity Review\n\n";
        md += `| Metric | Value |\n`;
        md += `|--------|-------|\n`;
        md += `| **Is Sane** | ${sanityReview.is_sane ? '✅ Yes' : '❌ No'} |\n`;
        md += `| **Confidence** | ${sanityReview.confidence ? `${(sanityReview.confidence * 100).toFixed(0)}%` : 'N/A'} |\n`;
        md += "\n";

        if (sanityReview.overall_assessment) {
            md += `**Overall Assessment:** ${sanityReview.overall_assessment}\n\n`;
        }

        if (sanityReview.issues_found && sanityReview.issues_found.length > 0) {
            md += "### Issues Found by LLM\n\n";
            sanityReview.issues_found.forEach((issue: string) => {
                md += `- ${issue}\n`;
            });
            md += "\n";
        }

        if (sanityReview.suggestions && sanityReview.suggestions.length > 0) {
            md += "### Suggestions\n\n";
            sanityReview.suggestions.forEach((suggestion: string) => {
                md += `- ${suggestion}\n`;
            });
            md += "\n";
        }
    }

    return md;
}

/**
 * Helper function to format correction history as markdown
 */
export function formatCorrectionAsMarkdown(history: any): string {
    if (!history) return "";

    let md = "# Correction History\n\n";
    md += `_Generated: ${new Date().toISOString()}_\n\n`;
    md += "---\n\n";

    md += "## Summary\n\n";
    md += `| Metric | Value |\n`;
    md += `|--------|-------|\n`;
    md += `| **Total Iterations** | ${history.total_iterations}/${history.max_iterations} |\n`;
    md += `| **Final Status** | ${history.final_status} |\n`;
    if (history.started_at) {
        md += `| **Started** | ${history.started_at} |\n`;
    }
    if (history.completed_at) {
        md += `| **Completed** | ${history.completed_at} |\n`;
    }
    md += "\n";

    if (history.iterations && history.iterations.length > 0) {
        md += "## Iteration Details\n\n";
        history.iterations.forEach((iter: any) => {
            md += `### Iteration ${iter.iteration_number}\n\n`;
            
            if (iter.timestamp) {
                md += `_Timestamp: ${iter.timestamp}_\n\n`;
            }

            if (iter.issues_addressed && iter.issues_addressed.length > 0) {
                md += "**Issues Addressed:**\n";
                iter.issues_addressed.forEach((issue: string) => {
                    md += `- ${issue}\n`;
                });
                md += "\n";
            }

            if (iter.corrections_applied && iter.corrections_applied.length > 0) {
                md += "**Corrections Applied:**\n";
                iter.corrections_applied.forEach((correction: string) => {
                    md += `- ${correction}\n`;
                });
                md += "\n";
            }

            md += `**Validation Result:** ${iter.validation_result?.is_valid ? '✅ Valid' : '❌ Invalid'} `;
            md += `(${iter.validation_result?.remaining_issues || 0} remaining issues)\n\n`;

            if (iter.llm_review_confidence) {
                md += `**LLM Confidence:** ${(iter.llm_review_confidence * 100).toFixed(0)}%\n\n`;
            }

            if (iter.duration_ms) {
                md += `**Duration:** ${iter.duration_ms}ms\n\n`;
            }
        });
    }

    return md;
}

export default DownloadButton;
