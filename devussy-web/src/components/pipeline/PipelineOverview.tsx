"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
    MessageSquare, 
    Gauge, 
    Lightbulb, 
    ShieldCheck, 
    FileText, 
    Play, 
    Download,
    CheckCircle2,
    Circle,
    Loader2
} from "lucide-react";

export interface PipelineStage {
    id: number;
    name: string;
    title: string;
    description: string;
    outputs: string[];
    features: string[];
    status: 'pending' | 'active' | 'completed';
}

interface PipelineOverviewProps {
    currentStage?: number; // 1-7
    onStageClick?: (stageId: number) => void;
    compact?: boolean;
}

const PIPELINE_STAGES: PipelineStage[] = [
    {
        id: 1,
        name: "INPUT",
        title: "Interview & Requirements",
        description: "Guided Q&A captures goals, constraints, target stack, and vibe. Output is structured as interview.json to feed the rest of the pipeline.",
        outputs: ["interview.json"],
        features: ["User intent → structured data", "No LLM orchestration yet"],
        status: 'pending'
    },
    {
        id: 2,
        name: "ANALYSIS",
        title: "Complexity Analyzer",
        description: "Pure-Python scoring rubrics rate difficulty, estimate phase count, and select template depth (minimal / standard / detailed) with no LLM calls.",
        outputs: ["complexity_profile.json"],
        features: ["Deterministic scoring", "Drives all downstream branching"],
        status: 'pending'
    },
    {
        id: 3,
        name: "DESIGN",
        title: "Adaptive Design Generator",
        description: "The LLM combines interview.json + complexity_profile.json to propose an initial architecture. Small projects stay tiny; big systems get richer multi-module designs.",
        outputs: ["design_draft.md"],
        features: ["Complexity-aware branching", "Mocked in tests for stability"],
        status: 'pending'
    },
    {
        id: 4,
        name: "VALIDATION & FEEDBACK",
        title: "Design Validation & Correction Loop",
        description: "Rule-based checks + an LLM sanity reviewer catch inconsistencies, hallucinated services, scope creep, and missing tests. An iterative correction loop stabilizes the design before any devplan is generated.",
        outputs: ["validated_design.md"],
        features: ["Guardrails against nonsense", "All pieces mockable in CI"],
        status: 'pending'
    },
    {
        id: 5,
        name: "PLANNING",
        title: "Adaptive Devplan Generator",
        description: "Using the validated design and complexity profile, the system generates a dynamic set of phases, with explicit tests and acceptance criteria for each milestone.",
        outputs: ["devplan.md + phases.json"],
        features: ["Tiny plans for tiny projects", "Full roadmaps for complex builds"],
        status: 'pending'
    },
    {
        id: 6,
        name: "EXECUTION",
        title: "Pipeline Execution & Checkpoints",
        description: "Phases run with streaming output, checkpointing, and schema-validated artifacts. In dev-mode everything can be swapped for mocks to keep tests fast and deterministic.",
        outputs: ["artifacts + devplan.zip"],
        features: ["Recoverable at every checkpoint", "Ready for multiple LLM providers"],
        status: 'pending'
    },
    {
        id: 7,
        name: "UI & HANDOFF",
        title: "Frontend, Downloads & Circular Handoff",
        description: "The frontend visualizes complexity, phases, and validation results, and exposes controls to refine or approve. A final handoff.md bundle instructs the next agent how to continue the work.",
        outputs: ["devplan.zip + handoff.md"],
        features: ["One-click export for agents", "Circular development baked in"],
        status: 'pending'
    }
];

const StageIcon = ({ stageId, status }: { stageId: number; status: string }) => {
    const icons = [
        MessageSquare,
        Gauge,
        Lightbulb,
        ShieldCheck,
        FileText,
        Play,
        Download
    ];
    
    const Icon = icons[stageId - 1] || Circle;
    
    if (status === 'completed') {
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    } else if (status === 'active') {
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
    }
    
    return <Icon className="h-5 w-5 text-muted-foreground" />;
};

export const PipelineOverview: React.FC<PipelineOverviewProps> = ({ 
    currentStage = 0, 
    onStageClick,
    compact = false 
}) => {
    const stages = PIPELINE_STAGES.map(stage => ({
        ...stage,
        status: stage.id < currentStage ? 'completed' : stage.id === currentStage ? 'active' : 'pending'
    })) as PipelineStage[];

    if (compact) {
        return (
            <div className="flex items-center gap-2 overflow-x-auto py-2">
                {stages.map((stage, idx) => (
                    <React.Fragment key={stage.id}>
                        <button
                            onClick={() => onStageClick?.(stage.id)}
                            disabled={!onStageClick}
                            className={`
                                flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium
                                transition-all duration-200 border whitespace-nowrap
                                ${stage.status === 'completed' ? 'bg-green-500/10 border-green-500/30 text-green-400' :
                                  stage.status === 'active' ? 'bg-blue-500/20 border-blue-500/50 text-blue-400' :
                                  'bg-muted/20 border-border/30 text-muted-foreground'}
                                ${onStageClick ? 'hover:bg-muted/40 cursor-pointer' : 'cursor-default'}
                            `}
                            title={stage.description}
                        >
                            <StageIcon stageId={stage.id} status={stage.status} />
                            <span className="text-xs font-mono">{stage.name}</span>
                        </button>
                        {idx < stages.length - 1 && (
                            <div className={`h-px w-4 ${stage.status === 'completed' ? 'bg-green-500/30' : 'bg-border/30'}`} />
                        )}
                    </React.Fragment>
                ))}
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {stages.map((stage) => (
                <Card 
                    key={stage.id}
                    className={`
                        transition-all duration-300 border
                        ${stage.status === 'completed' ? 'border-green-500/30 bg-green-500/5' :
                          stage.status === 'active' ? 'border-blue-500/50 bg-blue-500/10 shadow-lg' :
                          'border-border/30 bg-muted/5'}
                        ${onStageClick ? 'cursor-pointer hover:border-primary/50' : ''}
                    `}
                    onClick={() => onStageClick?.(stage.id)}
                >
                    <CardHeader className="pb-3">
                        <div className="flex items-start gap-3">
                            <div className={`
                                mt-1 p-2 rounded-lg
                                ${stage.status === 'completed' ? 'bg-green-500/20' :
                                  stage.status === 'active' ? 'bg-blue-500/20' :
                                  'bg-muted/30'}
                            `}>
                                <StageIcon stageId={stage.id} status={stage.status} />
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs font-mono text-muted-foreground">
                                        STAGE {stage.id} · {stage.name}
                                    </span>
                                    {stage.outputs.map(output => (
                                        <code key={output} className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary">
                                            {output}
                                        </code>
                                    ))}
                                </div>
                                <CardTitle className="text-base">{stage.title}</CardTitle>
                                <CardDescription className="text-xs mt-1">
                                    {stage.description}
                                </CardDescription>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                        <div className="flex flex-wrap gap-2 text-xs">
                            {stage.features.map((feature, idx) => (
                                <div 
                                    key={idx}
                                    className="flex items-center gap-1 text-muted-foreground"
                                >
                                    <span>•</span>
                                    <span>{feature}</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
};

export default PipelineOverview;
