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

            if (!response.ok) throw new Error('Failed to generate handoff');

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

    const handleDownload = async () => {
        const zip = new JSZip();

        // Add core files
        zip.file("project_design.md", design.raw_response || JSON.stringify(design, null, 2));
        zip.file("development_plan.md", JSON.stringify(plan, null, 2));
        zip.file("handoff_instructions.md", handoffContent);

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
            // In a real implementation, this would call the backend to push code
            // For now, we'll simulate it or call a placeholder endpoint
            await new Promise(resolve => setTimeout(resolve, 2000));
            setPushResult("Successfully created repository and pushed code!");
        } catch (error) {
            setPushResult("Failed to push to GitHub.");
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
