"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
    Gauge, 
    Layers, 
    Microscope, 
    ShieldCheck, 
    AlertTriangle,
    CheckCircle2,
    Clock,
    Users,
    Boxes,
    RefreshCw,
    ChevronDown
} from "lucide-react";

/**
 * Complexity profile data structure matching backend ComplexityProfile
 */
export interface ComplexityProfile {
    project_type_bucket?: string;
    technical_complexity_bucket?: string;
    integration_bucket?: string;
    team_size_bucket?: string;
    score?: number;
    complexity_score?: number; // Alternative field name from backend
    estimated_phase_count: number;
    depth_level: 'minimal' | 'standard' | 'detailed';
    confidence: number;
    // Additional fields from LLM-powered analysis
    rationale?: string;
    complexity_factors?: string[];
    follow_up_questions?: string[];
    hidden_risks?: string[];
    needs_clarification?: boolean;
}

interface ComplexityAssessmentProps {
    profile: ComplexityProfile;
    isLoading?: boolean;
    showDetails?: boolean;
    onRefresh?: () => void;
    onDepthOverride?: (depth: 'minimal' | 'standard' | 'detailed') => void;
    allowDepthOverride?: boolean;
}

/**
 * Visual mapping for depth levels
 */
const DEPTH_CONFIG = {
    minimal: {
        label: 'Minimal',
        color: 'text-green-500',
        bgColor: 'bg-green-500/10',
        borderColor: 'border-green-500/30',
        description: '3-5 phases, concise output'
    },
    standard: {
        label: 'Standard',
        color: 'text-blue-500',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/30',
        description: '5-7 phases, balanced detail'
    },
    detailed: {
        label: 'Detailed',
        color: 'text-purple-500',
        bgColor: 'bg-purple-500/10',
        borderColor: 'border-purple-500/30',
        description: '7-11 phases, comprehensive'
    }
};

/**
 * Format bucket names for display
 */
function formatBucket(bucket: string | undefined | null): string {
    if (!bucket) return 'N/A';
    return bucket
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Safely extract score from profile (handles both score and complexity_score fields)
 */
function getScore(profile: ComplexityProfile): number {
    return profile.score ?? profile.complexity_score ?? 5.0;
}

/**
 * Get color class based on score (0-20 scale)
 */
function getScoreColor(score: number): string {
    if (score <= 3) return 'text-green-500';
    if (score <= 7) return 'text-blue-500';
    if (score <= 12) return 'text-yellow-500';
    if (score <= 16) return 'text-orange-500';
    return 'text-red-500';
}

/**
 * Get confidence indicator
 */
function getConfidenceIndicator(confidence: number): { icon: typeof CheckCircle2; color: string; label: string } {
    if (confidence >= 0.8) {
        return { icon: CheckCircle2, color: 'text-green-500', label: 'High' };
    }
    if (confidence >= 0.6) {
        return { icon: ShieldCheck, color: 'text-yellow-500', label: 'Medium' };
    }
    return { icon: AlertTriangle, color: 'text-orange-500', label: 'Low' };
}

/**
 * Complexity score gauge component
 */
function ScoreGauge({ score, maxScore = 20 }: { score: number; maxScore?: number }) {
    const percentage = (score / maxScore) * 100;
    const circumference = 2 * Math.PI * 40; // radius of 40
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
        <div className="relative w-28 h-28">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                {/* Background circle */}
                <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="8"
                    className="text-muted/20"
                />
                {/* Progress circle */}
                <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    className={getScoreColor(score)}
                    style={{ transition: 'stroke-dashoffset 0.5s ease-in-out' }}
                />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
                    {score.toFixed(1)}
                </span>
                <span className="text-xs text-muted-foreground">/ {maxScore}</span>
            </div>
        </div>
    );
}

/**
 * Metric card for individual complexity factors
 */
function MetricCard({ 
    icon: Icon, 
    label, 
    value, 
    subtext 
}: { 
    icon: typeof Boxes; 
    label: string; 
    value: string; 
    subtext?: string 
}) {
    return (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
            <div className="p-2 rounded-md bg-primary/10">
                <Icon className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="text-sm font-medium truncate">{value}</p>
                {subtext && <p className="text-xs text-muted-foreground">{subtext}</p>}
            </div>
        </div>
    );
}

/**
 * ComplexityAssessment Component
 * 
 * Displays a visual representation of the project complexity profile
 * including score gauge, depth level, phase count, and individual factors.
 */
export function ComplexityAssessment({ 
    profile, 
    isLoading = false, 
    showDetails = true,
    onRefresh,
    onDepthOverride,
    allowDepthOverride = true
}: ComplexityAssessmentProps) {
    const [showDepthDropdown, setShowDepthDropdown] = React.useState(false);
    const depthConfig = DEPTH_CONFIG[profile.depth_level];
    const confidenceInfo = getConfidenceIndicator(profile.confidence);
    const ConfidenceIcon = confidenceInfo.icon;

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

    return (
        <Card className="overflow-hidden">
            <CardHeader className="border-b border-border/50">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <Gauge className="h-5 w-5 text-primary" />
                            Complexity Assessment
                        </CardTitle>
                        <CardDescription>
                            Adaptive pipeline configuration based on project analysis
                        </CardDescription>
                    </div>
                    {onRefresh && (
                        <button 
                            onClick={onRefresh}
                            className="text-sm text-primary hover:underline"
                        >
                            Refresh
                        </button>
                    )}
                </div>
            </CardHeader>

            <CardContent className="pt-6">
                {/* Main metrics row */}
                <div className="flex items-start gap-8 mb-6">
                    {/* Score gauge */}
                    <div className="flex flex-col items-center">
                        <ScoreGauge score={getScore(profile)} />
                        <p className="text-sm text-muted-foreground mt-2">Complexity Score</p>
                    </div>

                    {/* Key metrics */}
                    <div className="flex-1 grid grid-cols-2 gap-4">
                        {/* Depth Level - with override dropdown */}
                        <div className={`relative p-4 rounded-lg border ${depthConfig.borderColor} ${depthConfig.bgColor}`}>
                            <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center gap-2">
                                    <Microscope className={`h-4 w-4 ${depthConfig.color}`} />
                                    <span className="text-sm font-medium">Depth Level</span>
                                </div>
                                {allowDepthOverride && onDepthOverride && (
                                    <button
                                        onClick={() => setShowDepthDropdown(!showDepthDropdown)}
                                        className="p-1 hover:bg-muted/50 rounded transition-colors"
                                        title="Override depth level"
                                    >
                                        <ChevronDown className={`h-4 w-4 transition-transform ${showDepthDropdown ? 'rotate-180' : ''}`} />
                                    </button>
                                )}
                            </div>
                            <p className={`text-lg font-bold ${depthConfig.color}`}>
                                {depthConfig.label}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                {depthConfig.description}
                            </p>
                            
                            {/* Depth override dropdown */}
                            {showDepthDropdown && onDepthOverride && (
                                <div className="absolute top-full left-0 right-0 mt-1 z-10 bg-card border border-border rounded-lg shadow-lg overflow-hidden">
                                    {(Object.keys(DEPTH_CONFIG) as Array<'minimal' | 'standard' | 'detailed'>).map((level) => {
                                        const config = DEPTH_CONFIG[level];
                                        const isActive = level === profile.depth_level;
                                        return (
                                            <button
                                                key={level}
                                                onClick={() => {
                                                    onDepthOverride(level);
                                                    setShowDepthDropdown(false);
                                                }}
                                                className={`w-full px-3 py-2 text-left text-sm hover:bg-muted/50 transition-colors flex items-center justify-between ${
                                                    isActive ? 'bg-muted/30' : ''
                                                }`}
                                            >
                                                <div>
                                                    <span className={`font-medium ${config.color}`}>{config.label}</span>
                                                    <p className="text-xs text-muted-foreground">{config.description}</p>
                                                </div>
                                                {isActive && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}
                        </div>

                        {/* Phase Count */}
                        <div className="p-4 rounded-lg border border-border/50 bg-muted/20">
                            <div className="flex items-center gap-2 mb-1">
                                <Layers className="h-4 w-4 text-primary" />
                                <span className="text-sm font-medium">Estimated Phases</span>
                            </div>
                            <p className="text-lg font-bold text-primary">
                                {profile.estimated_phase_count}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                Development phases
                            </p>
                        </div>

                        {/* Confidence */}
                        <div className="p-4 rounded-lg border border-border/50 bg-muted/20">
                            <div className="flex items-center gap-2 mb-1">
                                <ConfidenceIcon className={`h-4 w-4 ${confidenceInfo.color}`} />
                                <span className="text-sm font-medium">Confidence</span>
                            </div>
                            <p className={`text-lg font-bold ${confidenceInfo.color}`}>
                                {(profile.confidence * 100).toFixed(0)}%
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                {confidenceInfo.label} confidence
                            </p>
                        </div>

                        {/* Timeline indicator */}
                        <div className="p-4 rounded-lg border border-border/50 bg-muted/20">
                            <div className="flex items-center gap-2 mb-1">
                                <Clock className="h-4 w-4 text-muted-foreground" />
                                <span className="text-sm font-medium">Scale</span>
                            </div>
                            <p className="text-lg font-bold">
                                {getScore(profile) <= 3 ? 'Simple' : 
                                 getScore(profile) <= 7 ? 'Moderate' :
                                 getScore(profile) <= 12 ? 'Complex' : 'Enterprise'}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                                Project scale
                            </p>
                        </div>
                    </div>
                </div>

                {/* Detailed breakdown */}
                {showDetails && (
                    <div className="border-t border-border/50 pt-4">
                        <h4 className="text-sm font-medium mb-3 text-muted-foreground">
                            Complexity Factors
                        </h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <MetricCard
                                icon={Boxes}
                                label="Project Type"
                                value={formatBucket(profile.project_type_bucket)}
                            />
                            <MetricCard
                                icon={Layers}
                                label="Technical Complexity"
                                value={formatBucket(profile.technical_complexity_bucket)}
                            />
                            <MetricCard
                                icon={Boxes}
                                label="Integrations"
                                value={formatBucket(profile.integration_bucket)}
                            />
                            <MetricCard
                                icon={Users}
                                label="Team Size"
                                value={formatBucket(profile.team_size_bucket)}
                            />
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

/**
 * Compact version for embedding in other views
 */
export function ComplexityBadge({ profile }: { profile: ComplexityProfile }) {
    const depthConfig = DEPTH_CONFIG[profile.depth_level];

    return (
        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${depthConfig.bgColor} ${depthConfig.borderColor} border`}>
            <Gauge className={`h-4 w-4 ${depthConfig.color}`} />
            <span className={`font-medium ${depthConfig.color}`}>
                {getScore(profile).toFixed(1)}
            </span>
            <span className="text-muted-foreground">|</span>
            <span className="text-muted-foreground">
                {profile.estimated_phase_count} phases
            </span>
            <span className="text-muted-foreground">|</span>
            <span className={depthConfig.color}>
                {depthConfig.label}
            </span>
        </div>
    );
}

export default ComplexityAssessment;
