"use client";

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Download, Github, CheckCircle, Loader2 } from "lucide-react";
import { ModelConfig } from './ModelSettings';
import JSZip from 'jszip';

interface HandoffViewProps {
    design: any;
    plan: any;
    modelConfig: ModelConfig;
}

export const HandoffView: React.FC<HandoffViewProps> = ({
    design,
    plan,
    modelConfig
}) => {
    const [handoffContent, setHandoffContent] = useState<string>("");
    const [isGenerating, setIsGenerating] = useState(false);
    const [githubToken, setGithubToken] = useState("");
    const [repoName, setRepoName] = useState("");
    const [isPushing, setIsPushing] = useState(false);
    const [pushResult, setPushResult] = useState<string | null>(null);

    const generateHandoff = async () => {
        setIsGenerating(true);
        try {
            const response = await fetch('/api/handoff', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design,
                    plan,
                    modelConfig
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = 'Failed to generate handoff';
                try {
                    const errorJson = JSON.parse(errorText);
                    if (errorJson.error) errorMessage = errorJson.error;
                } catch (e) {
                    errorMessage = errorText || errorMessage;
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            setHandoffContent(data.content);
        } catch (error) {
            console.error("Handoff generation failed:", error);
            setHandoffContent("Error generating handoff documentation.");
        } finally {
            setIsGenerating(false);
        }
    };

    // Auto-generate on mount
    React.useEffect(() => {
        generateHandoff();
    }, []);

    const formatDesignAsMarkdown = (design: any): string => {
        // If we have raw_llm_response (new standard) or raw_response (legacy), use it
        if (design.raw_llm_response) {
            return design.raw_llm_response;
        }
        if (design.raw_response) {
            return design.raw_response;
        }

        // Otherwise, format the design object as markdown
        let md = `# ${design.project_name || 'Project Design'}\n\n`;

        if (design.objectives && Array.isArray(design.objectives)) {
            md += `## Objectives\n\n`;
            design.objectives.forEach((obj: string) => {
                // Skip separator markers
                if (obj === '--' || obj === '---') return;
                md += `- ${obj}\n`;
            });
            md += `\n`;
        }

        if (design.architecture) {
            md += `## Architecture\n\n${design.architecture}\n\n`;
        }

        if (design.tech_stack && Array.isArray(design.tech_stack)) {
            md += `## Technology Stack\n\n`;
            design.tech_stack.forEach((tech: string) => {
                md += `- ${tech}\n`;
            });
            md += `\n`;
        }

        if (design.data_model) {
            md += `## Data Model\n\n${design.data_model}\n\n`;
        }

        if (design.api_design) {
            md += `## API Design\n\n${design.api_design}\n\n`;
        }

        if (design.security) {
            md += `## Security\n\n${design.security}\n\n`;
        }

        if (design.deployment) {
            md += `## Deployment\n\n${design.deployment}\n\n`;
        }

        return md;
    };

    const formatPlanAsMarkdown = (plan: any): string => {
        let md = `# Development Plan\n\n`;

        if (plan.project_name) {
            md += `**Project:** ${plan.project_name}\n\n`;
        }

        if (plan.phases && Array.isArray(plan.phases)) {
            md += `## Phases\n\n`;
            plan.phases.forEach((phase: any) => {
                const phaseNum = phase.number || phase.phase_number;
                const phaseTitle = phase.title || phase.name || `Phase ${phaseNum}`;

                md += `### Phase ${phaseNum}: ${phaseTitle}\n\n`;

                if (phase.description) {
                    md += `${phase.description}\n\n`;
                }

                if (phase.steps && Array.isArray(phase.steps) && phase.steps.length > 0) {
                    md += `**Steps:**\n\n`;
                    phase.steps.forEach((step: any, idx: number) => {
                        const stepTitle = step.title || step.name || `Step ${idx + 1}`;
                        md += `${idx + 1}. ${stepTitle}\n`;
                        if (step.description) {
                            md += `   ${step.description}\n`;
                        }
                    });
                    md += `\n`;
                }

                if (phase.deliverables && Array.isArray(phase.deliverables)) {
                    md += `**Deliverables:**\n`;
                    phase.deliverables.forEach((deliverable: string) => {
                        md += `- ${deliverable}\n`;
                    });
                    md += `\n`;
                }

                if (phase.acceptance_criteria && Array.isArray(phase.acceptance_criteria)) {
                    md += `**Acceptance Criteria:**\n`;
                    phase.acceptance_criteria.forEach((criteria: string) => {
                        md += `- ${criteria}\n`;
                    });
                    md += `\n`;
                }

                md += `---\n\n`;
            });
        }

        return md;
    };

    const handleDownload = async () => {
        const zip = new JSZip();

        // Add core files with proper markdown formatting
        zip.file("project_design.md", formatDesignAsMarkdown(design));
        zip.file("development_plan.md", formatPlanAsMarkdown(plan));
        zip.file("handoff_instructions.md", handoffContent);

        // Add individual phase documents
        if (plan && plan.phases) {
            const phasesFolder = zip.folder("phases");
            plan.phases.forEach((phase: any) => {
                const phaseNumber = phase.number || phase.phase_number;
                const phaseTitle = (phase.title || phase.name || `Phase ${phaseNumber}`).replace(/[^a-z0-9]/gi, '_').toLowerCase();
                const fileName = `phase_${phaseNumber}_${phaseTitle}.md`;

                // Build phase document content
                let content = `# Phase ${phaseNumber}: ${phase.title || phase.name}\n\n`;
                content += `## Description\n${phase.description || 'No description'}\n\n`;

                if (phase.steps && phase.steps.length > 0) {
                    content += `## Steps\n\n`;
                    phase.steps.forEach((step: any, idx: number) => {
                        content += `### ${idx + 1}. ${step.title || step.name || `Step ${idx + 1}`}\n\n`;
                        if (step.description) {
                            content += `${step.description}\n\n`;
                        }
                        if (step.details) {
                            content += `**Details:**\n${step.details}\n\n`;
                        }
                        if (step.acceptance_criteria && step.acceptance_criteria.length > 0) {
                            content += `**Acceptance Criteria:**\n`;
                            step.acceptance_criteria.forEach((criteria: string) => {
                                content += `- ${criteria}\n`;
                            });
                            content += `\n`;
                        }
                    });
                }

                phasesFolder?.file(fileName, content);
            });
        }

        // Generate blob and download
        const content = await zip.generateAsync({ type: "blob" });
        const url = window.URL.createObjectURL(content);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${design.project_name || "devussy-project"}.zip`;
        a.click();
        window.URL.revokeObjectURL(url);
    };

    const handleGithubPush = async () => {
        if (!githubToken || !repoName) return;

        setIsPushing(true);
        setPushResult(null);

        try {
            const response = await fetch('/api/github/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    repoName,
                    token: githubToken,
                    design,
                    plan,
                    handoffContent
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to create repository');
            }

            setPushResult(`Success! Repository created at: ${data.data.repoUrl}`);
            // Optionally open in new tab
            // window.open(data.data.repoUrl, '_blank');
        } catch (error: any) {
            console.error("GitHub push failed:", error);
            setPushResult(`Failed to push to GitHub: ${error.message}`);
        } finally {
            setIsPushing(false);
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    Project Handoff
                </h2>
                <Button
                    size="sm"
                    onClick={handleDownload}
                    disabled={!handoffContent}
                >
                    <Download className="h-4 w-4 mr-2" />
                    Download Artifacts
                </Button>
            </div>

            <ScrollArea className="flex-1 p-6">
                <div className="grid gap-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Handoff Instructions</CardTitle>
                            <CardDescription>
                                Final summary and next steps for your project.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {isGenerating ? (
                                <div className="flex items-center justify-center p-8">
                                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                                </div>
                            ) : (
                                <div className="prose prose-invert max-w-none text-sm">
                                    <pre className="whitespace-pre-wrap font-sans">
                                        {handoffContent}
                                    </pre>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Github className="h-5 w-5" />
                                Push to GitHub
                            </CardTitle>
                            <CardDescription>
                                Create a new repository and push your project code.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid gap-2">
                                <label className="text-sm font-medium">Repository Name</label>
                                <Input
                                    placeholder="my-awesome-project"
                                    value={repoName}
                                    onChange={(e) => setRepoName(e.target.value)}
                                />
                            </div>
                            <div className="grid gap-2">
                                <label className="text-sm font-medium">Personal Access Token</label>
                                <Input
                                    type="password"
                                    placeholder="ghp_..."
                                    value={githubToken}
                                    onChange={(e) => setGithubToken(e.target.value)}
                                />
                            </div>

                            {pushResult && (
                                <div className={`text-sm ${pushResult.includes("Success") ? "text-green-500" : "text-red-500"}`}>
                                    {pushResult}
                                </div>
                            )}

                            <Button
                                className="w-full"
                                onClick={handleGithubPush}
                                disabled={isPushing || !repoName || !githubToken}
                            >
                                {isPushing ? (
                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                ) : (
                                    <Github className="h-4 w-4 mr-2" />
                                )}
                                Create & Push
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </ScrollArea>
        </div>
    );
}
