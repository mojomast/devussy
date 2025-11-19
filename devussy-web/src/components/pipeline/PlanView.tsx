"use client";

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Play, FileText, Loader2, Edit2, LayoutGrid, FileCode, Plus } from "lucide-react";
import { ModelConfig } from './ModelSettings';
import { PhaseCard, PhaseData } from './PhaseCard';

interface PlanViewProps {
    design: any;
    modelConfig: ModelConfig;
    onPlanApproved: (plan: any) => void;
}

export const PlanView: React.FC<PlanViewProps> = ({
    design,
    modelConfig,
    onPlanApproved
}) => {
    const [plan, setPlan] = useState<any>(null);
    const [planContent, setPlanContent] = useState("");  // Track streaming content
    const [phases, setPhases] = useState<PhaseData[]>([]);  // Parsed phases
    const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set());  // Track expanded phases
    const [isLoading, setIsLoading] = useState(false);
    const [isEditing, setIsEditing] = useState(false);  // For raw text editing
    const [viewMode, setViewMode] = useState<'cards' | 'raw'>('cards');  // Toggle between card/raw view
    const [error, setError] = useState<string | null>(null);

    // Parse phases from raw text content
    const parsePhasesFromText = (text: string): PhaseData[] => {
        const phases: PhaseData[] = [];
        const lines = text.split('\n');
        
        let currentPhase: PhaseData | null = null;
        let collectingContent = false;
        let contentLines: string[] = [];
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();
            
            // Match phase headers like "1. **Phase 1: Title**"
            const phaseMatch = trimmed.match(/^(\d+)\.\s*\*\*\s*Phase\s+\d+:\s*(.+?)\s*\*\*\s*$/i);
            
            if (phaseMatch) {
                // Save previous phase with collected content
                if (currentPhase && contentLines.length > 0) {
                    currentPhase.description = contentLines.join('\n').trim();
                    phases.push(currentPhase);
                }
                
                // Start new phase
                const phaseNum = parseInt(phaseMatch[1]);
                const title = phaseMatch[2].trim();
                currentPhase = {
                    number: phaseNum,
                    title: title,
                    description: ''
                };
                contentLines = [];
                collectingContent = true;
            }
            // Collect all content lines until next phase
            else if (collectingContent && currentPhase) {
                // Check if this is a "Brief:" line (not indented)
                if (trimmed.startsWith('Brief:')) {
                    const brief = trimmed.substring(6).trim();
                    if (brief) contentLines.push(brief);
                    contentLines.push(''); // Add blank line after brief
                }
                // Bullet points (components)
                else if (trimmed.startsWith('- ')) {
                    contentLines.push(trimmed);
                }
                // Indented content (sub-bullets or continuation)
                else if (trimmed && (line.startsWith('   ') || line.startsWith('\t'))) {
                    contentLines.push('  ' + trimmed); // Preserve some indentation
                }
                // Empty lines between sections
                else if (!trimmed && contentLines.length > 0) {
                    // Don't add multiple consecutive blank lines
                    if (contentLines[contentLines.length - 1] !== '') {
                        contentLines.push('');
                    }
                }
            }
        }
        
        // Don't forget the last phase
        if (currentPhase && contentLines.length > 0) {
            currentPhase.description = contentLines.join('\n').trim();
            phases.push(currentPhase);
        }
        
        console.log('[PlanView] Parsed', phases.length, 'phases from text');
        phases.forEach(p => console.log(`  Phase ${p.number}: ${p.title} (${p.description?.length || 0} chars)`));
        
        return phases;
    };

    // Parse phases from plan data (fallback)
    const parsePhasesFromPlan = (planData: any) => {
        if (!planData || !planData.phases) return [];

        return planData.phases.map((phase: any, index: number) => ({
            number: phase.number || index + 1,
            title: phase.title || phase.name || `Phase ${index + 1}`,
            description: phase.description || ""
        }));
    };

    const generatePlan = async () => {
        setIsLoading(true);
        setError(null);
        setPlanContent("");  // Reset content
        try {
            // Bypass Next.js proxy and hit backend directly to avoid buffering
            const backendUrl = `http://${window.location.hostname}:8000/api/plan/basic`;

            const response = await fetch(backendUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design: design,
                    modelConfig
                })
            });

            if (!response.ok) throw new Error('Failed to generate plan');

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

                            // Display streaming content as it arrives
                            if (data.content) {
                                setPlanContent(prev => prev + data.content);
                            }

                            if (data.done && data.plan) {
                                setPlan(data.plan);
                                console.log('[PlanView] Plan received, parsing phases from text...');
                                console.log('[PlanView] Plan content length:', planContent.length);
                                // Parse phases from the raw text content (more complete)
                                const parsedPhases = parsePhasesFromText(planContent);
                                // Fallback to plan data if text parsing fails
                                const finalPhases = parsedPhases.length > 0 ? parsedPhases : parsePhasesFromPlan(data.plan);
                                console.log('[PlanView] Using', finalPhases.length, 'phases');
                                setPhases(finalPhases);
                                // Expand all phases by default
                                setExpandedPhases(new Set(finalPhases.map(p => p.number)));
                                return; // Stop reading
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
            console.error("Plan generation error:", err);
            setError(err.message || "An error occurred");
        } finally {
            setIsLoading(false);
        }
    };

    // Auto-generate on mount if not present
    React.useEffect(() => {
        if (!plan && !isLoading && !error) {
            generatePlan();
        }
    }, []);

    // Phase management functions
    const handleUpdatePhase = (index: number, updatedPhase: PhaseData) => {
        const newPhases = [...phases];
        newPhases[index] = updatedPhase;
        setPhases(newPhases);
    };

    const handleDeletePhase = (index: number) => {
        const newPhases = phases.filter((_, i) => i !== index);
        // Renumber phases
        const renumbered = newPhases.map((p, i) => ({ ...p, number: i + 1 }));
        setPhases(renumbered);
    };

    const handleMovePhase = (index: number, direction: 'up' | 'down') => {
        const newPhases = [...phases];
        const targetIndex = direction === 'up' ? index - 1 : index + 1;

        if (targetIndex < 0 || targetIndex >= newPhases.length) return;

        // Swap
        [newPhases[index], newPhases[targetIndex]] = [newPhases[targetIndex], newPhases[index]];

        // Renumber
        const renumbered = newPhases.map((p, i) => ({ ...p, number: i + 1 }));
        setPhases(renumbered);
    };

    const handleAddPhase = () => {
        const newPhase: PhaseData = {
            number: phases.length + 1,
            title: "New Phase",
            description: ""
        };
        setPhases([...phases, newPhase]);
        setExpandedPhases(new Set([...expandedPhases, newPhase.number]));
    };

    const togglePhaseExpanded = (phaseNumber: number) => {
        const newExpanded = new Set(expandedPhases);
        if (newExpanded.has(phaseNumber)) {
            newExpanded.delete(phaseNumber);
        } else {
            newExpanded.add(phaseNumber);
        }
        setExpandedPhases(newExpanded);
    };

    const handleApprove = () => {
        // Reconstruct plan with updated phases
        const updatedPlan = {
            ...plan,
            phases: phases.map(p => ({
                number: p.number,
                title: p.title,
                description: p.description,
                steps: []  // Steps will be generated in execution phase
            }))
        };
        console.log('[PlanView] Approving plan with', updatedPlan.phases.length, 'phases');
        updatedPlan.phases.forEach((p: any) => {
            console.log(`  Phase ${p.number}: ${p.title} (desc: ${p.description?.substring(0, 50)}...)`);
        });
        onPlanApproved(updatedPlan);
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Development Plan
                </h2>
                <div className="flex gap-2">
                    {plan && !isLoading && (
                        <>
                            {/* View toggle */}
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setViewMode(viewMode === 'cards' ? 'raw' : 'cards')}
                            >
                                {viewMode === 'cards' ? (
                                    <><FileCode className="h-4 w-4 mr-2" /> Raw Text</>
                                ) : (
                                    <><LayoutGrid className="h-4 w-4 mr-2" /> Cards</>
                                )}
                            </Button>

                            {/* Edit toggle (only in raw mode) */}
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
                        onClick={generatePlan}
                        disabled={isLoading}
                    >
                        Regenerate
                    </Button>

                    <Button
                        size="sm"
                        onClick={handleApprove}
                        disabled={!plan || isLoading || phases.length === 0}
                    >
                        <Play className="h-4 w-4 mr-2" />
                        Approve & Start Execution
                    </Button>
                </div>
            </div>

            <ScrollArea className="flex-1 p-6">
                {isLoading ? (
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-muted-foreground">
                            <Loader2 className="h-4 w-4 animate-spin text-primary" />
                            <p>Generating development plan...</p>
                        </div>
                        {planContent && (
                            <div className="prose prose-invert max-w-none font-mono text-sm">
                                <pre className="whitespace-pre-wrap bg-transparent p-0">
                                    {planContent}
                                </pre>
                            </div>
                        )}
                    </div>
                ) : error ? (
                    <div className="text-destructive p-4 border border-destructive/20 rounded-lg bg-destructive/10">
                        Error: {error}
                    </div>
                ) : plan ? (
                    viewMode === 'cards' ? (
                        // Card view - show editable phase cards
                        <div className="space-y-4">
                            <div className="prose prose-invert max-w-none">
                                <h3>{plan.summary}</h3>
                            </div>

                            <div className="space-y-3">
                                {phases.map((phase, index) => (
                                    <PhaseCard
                                        key={phase.number}
                                        phase={phase}
                                        isExpanded={expandedPhases.has(phase.number)}
                                        canMoveUp={index > 0}
                                        canMoveDown={index < phases.length - 1}
                                        onUpdate={(updated) => handleUpdatePhase(index, updated)}
                                        onDelete={() => handleDeletePhase(index)}
                                        onMoveUp={() => handleMovePhase(index, 'up')}
                                        onMoveDown={() => handleMovePhase(index, 'down')}
                                        onToggle={() => togglePhaseExpanded(phase.number)}
                                    />
                                ))}
                            </div>

                            {/* Add Phase Button */}
                            <Button
                                variant="outline"
                                className="w-full border-dashed"
                                onClick={handleAddPhase}
                            >
                                <Plus className="h-4 w-4 mr-2" />
                                Add Phase
                            </Button>
                        </div>
                    ) : (
                        // Raw text view - show full devplan text
                        <div className="space-y-4">
                            <div className="prose prose-invert max-w-none">
                                <h3>{plan.summary}</h3>
                            </div>
                            {isEditing ? (
                                <textarea
                                    className="w-full h-full min-h-[400px] bg-transparent border border-border rounded-lg p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                                    value={planContent}
                                    onChange={(e) => setPlanContent(e.target.value)}
                                />
                            ) : (
                                <div className="prose prose-invert max-w-none font-mono text-sm">
                                    <pre className="whitespace-pre-wrap bg-transparent p-0">
                                        {planContent}
                                    </pre>
                                </div>
                            )}
                        </div>
                    )
                ) : null}
            </ScrollArea>
        </div>
    );
}
