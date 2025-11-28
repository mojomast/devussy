"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, Send, Loader2, X, ArrowRight, List } from "lucide-react";
import { cn } from '@/utils';

interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

interface PlanRefinementViewProps {
    plan: any;
    design: any;
    projectName: string;
    onRefinementComplete: (updatedPlan: any) => void;
    onCancel?: () => void;
}

export const PlanRefinementView: React.FC<PlanRefinementViewProps> = ({
    plan,
    design,
    projectName,
    onRefinementComplete,
    onCancel
}) => {
    const phaseCount = plan?.phases?.length || 0;
    const phaseList = plan?.phases?.map((p: any, i: number) => 
        `Phase ${p.number || i+1}: ${p.title}`
    ).join('\n') || 'No phases defined';

    const [history, setHistory] = useState<Message[]>([
        {
            role: 'system',
            content: `Reviewing development plan for "${projectName}" with ${phaseCount} phases.`
        },
        {
            role: 'assistant',
            content: `I'm here to help you refine your development plan before execution. Current phases:

${phaseList}

You can:
• Ask me to add, remove, or reorder phases
• Discuss whether phases are properly scoped
• Verify phases cover all design requirements  
• Request phase title or description changes

Type "/analyze" for an automated plan review.

When you're satisfied with the plan, type "/done" and I'll apply any agreed-upon changes before continuing to execution.`
        }
    ]);
    const [input, setInput] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingMessage, setStreamingMessage] = useState("");
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [history, streamingMessage]);

    // Apply refinements by calling the backend to extract changes from conversation
    const applyRefinements = async () => {
        setStreamingMessage("Regenerating development plan with your feedback...");
        
        // Add a message to show we're regenerating
        setHistory(prev => [...prev, { 
            role: 'assistant', 
            content: '🔄 Regenerating development plan with your feedback. This may take a moment...' 
        }]);
        
        try {
            const response = await fetch('/api/plan/apply-refinements', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    plan,
                    design,
                    projectName,
                    chatHistory: history
                })
            });

            if (!response.ok) throw new Error('Failed to apply refinements');

            const reader = response.body?.getReader();
            if (!reader) throw new Error('No response body');

            const decoder = new TextDecoder();
            let buffer = "";
            let fullResponse = "";
            let tokenCount = 0;

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

                            if (data.content) {
                                fullResponse += data.content;
                                tokenCount++;
                                // Show progress with token count
                                if (tokenCount % 10 === 0) {
                                    setStreamingMessage(`Generating new plan... (${tokenCount} tokens)`);
                                }
                            }

                            if (data.done) {
                                const changes = data.changesApplied || [];
                                const wasRegenerated = data.regenerated === true;
                                
                                let summaryMessage = '';
                                if (wasRegenerated) {
                                    summaryMessage = `✓ Plan regenerated successfully!\n\n`;
                                    if (changes.length > 0) {
                                        summaryMessage += `Incorporated feedback:\n${changes.map((c: string) => `• ${c}`).join('\n')}\n\n`;
                                    }
                                    // Show new phase count
                                    const newPhaseCount = data.updatedPlan?.phases?.length || 0;
                                    summaryMessage += `New plan has ${newPhaseCount} phases.\n\n`;
                                } else {
                                    summaryMessage = changes.length > 0 
                                        ? `✓ Applied ${changes.length} change(s):\n${changes.map((c: string) => `• ${c}`).join('\n')}\n\n`
                                        : '✓ No changes needed - plan is ready as-is.\n\n';
                                }
                                summaryMessage += 'Continuing to execution...';
                                
                                setHistory(prev => [...prev, { 
                                    role: 'assistant', 
                                    content: summaryMessage
                                }]);
                                setStreamingMessage("");
                                
                                // Use updated plan if provided, otherwise use original
                                const finalPlan = data.updatedPlan || plan;
                                console.log('[PlanRefinement] Final plan has', finalPlan?.phases?.length, 'phases');
                                
                                // Small delay so user can see the summary
                                setTimeout(() => {
                                    onRefinementComplete(finalPlan);
                                }, 2000);
                                return;
                            }

                            if (data.error) {
                                throw new Error(data.error);
                            }
                        } catch (e) {
                            console.error("Failed to parse SSE:", e);
                        }
                    }
                }
            }
        } catch (err: any) {
            console.error("Apply refinements error:", err);
            setHistory(prev => [...prev, {
                role: 'assistant',
                content: `Failed to regenerate plan: ${err.message}\n\nContinuing with original plan...`
            }]);
            setStreamingMessage("");
            // Fall back to original plan
            setTimeout(() => {
                onRefinementComplete(plan);
            }, 1500);
        } finally {
            setIsStreaming(false);
        }
    };

    const sendMessage = async (message: string) => {
        if (!message.trim() || isStreaming) return;

        const userMessage = { role: 'user' as const, content: message.trim() };
        setHistory(prev => [...prev, userMessage]);
        setInput("");
        setIsStreaming(true);
        setStreamingMessage("");

        // Handle special commands
        if (message.trim() === '/analyze') {
            await runAutomatedReview();
            return;
        }

        // /done and /apply both finalize - call the apply-refinements endpoint
        if (message.trim() === '/apply' || message.trim() === '/done') {
            await applyRefinements();
            return;
        }

        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            const response = await fetch('/api/plan/refine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    plan,
                    design,
                    projectName,
                    chatHistory: history,
                    userMessage: message
                }),
                signal: controller.signal
            });

            if (!response.ok) throw new Error('Failed to get refinement response');

            const reader = response.body?.getReader();
            if (!reader) throw new Error('No response body');

            const decoder = new TextDecoder();
            let buffer = "";
            let fullResponse = "";
            let gotDoneSignal = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    // Stream ended - finalize if we have content and didn't get explicit done
                    if (fullResponse && !gotDoneSignal) {
                        console.log('[PlanRefinement] Stream ended without done signal, finalizing');
                        setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                        setStreamingMessage("");
                    }
                    break;
                }

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;

                const parts = buffer.split('\n\n');
                buffer = parts.pop() || "";

                for (const part of parts) {
                    const line = part.trim();
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.content) {
                                fullResponse += data.content;
                                setStreamingMessage(fullResponse);
                            }

                            if (data.done) {
                                gotDoneSignal = true;
                                setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                                setStreamingMessage("");
                                if (data.updatedPlan) {
                                    console.log('[PlanRefinement] Received updated plan');
                                }
                                return;
                            }

                            if (data.error) {
                                throw new Error(data.error);
                            }
                        } catch (e) {
                            console.error("Failed to parse SSE:", e);
                        }
                    }
                }
            }

            if (fullResponse && !gotDoneSignal) {
                setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                setStreamingMessage("");
            }

        } catch (err: any) {
            if (err.name === 'AbortError') {
                console.log('Refinement request aborted');
                return;
            }
            console.error("Plan refinement error:", err);
            setHistory(prev => [...prev, {
                role: 'assistant',
                content: `Sorry, I encountered an error: ${err.message}`
            }]);
        } finally {
            setIsStreaming(false);
            abortControllerRef.current = null;
        }
    };

    const runAutomatedReview = async () => {
        setIsStreaming(true);
        setStreamingMessage("");

        try {
            const response = await fetch('/api/plan/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ plan, design, projectName })
            });

            if (!response.ok) throw new Error('Failed to run automated review');

            const reader = response.body?.getReader();
            if (!reader) throw new Error('No response body');

            const decoder = new TextDecoder();
            let buffer = "";
            let fullResponse = "";
            let gotDoneSignal = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    // Stream ended - finalize if we have content and didn't get explicit done
                    if (fullResponse && !gotDoneSignal) {
                        console.log('[PlanRefinement] Review stream ended without done signal, finalizing');
                        setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                        setStreamingMessage("");
                    }
                    break;
                }

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;

                const parts = buffer.split('\n\n');
                buffer = parts.pop() || "";

                for (const part of parts) {
                    const line = part.trim();
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.content) {
                                fullResponse += data.content;
                                setStreamingMessage(fullResponse);
                            }
                            if (data.done) {
                                gotDoneSignal = true;
                                setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                                setStreamingMessage("");
                                return;
                            }
                        } catch (e) {
                            console.error("Failed to parse SSE:", e);
                        }
                    }
                }
            }

            if (fullResponse && !gotDoneSignal) {
                setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                setStreamingMessage("");
            }

        } catch (err: any) {
            console.error("Automated review error:", err);
            setHistory(prev => [...prev, {
                role: 'assistant',
                content: `Sorry, automated review failed: ${err.message}`
            }]);
        } finally {
            setIsStreaming(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    };

    const handleApplyRefinements = () => {
        onRefinementComplete(plan);
    };

    return (
        <div className="flex flex-col h-full bg-background">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <div>
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                        <List className="h-5 w-5" />
                        Plan Refinement Session
                    </h2>
                    <div className="text-xs text-muted-foreground">
                        Review and improve phases before execution
                    </div>
                </div>
                <div className="flex gap-2">
                    {onCancel && (
                        <Button variant="outline" size="sm" onClick={onCancel}>
                            <X className="h-4 w-4 mr-2" />
                            Cancel
                        </Button>
                    )}
                    <Button size="sm" onClick={handleApplyRefinements}>
                        <ArrowRight className="h-4 w-4 mr-2" />
                        Continue to Execution
                    </Button>
                </div>
            </div>

            <ScrollArea className="flex-1 p-4">
                <div className="space-y-4 pb-4">
                    {history.map((msg, idx) => (
                        msg.role !== 'system' && (
                            <div
                                key={idx}
                                className={cn(
                                    "flex w-full",
                                    msg.role === 'user' ? "justify-end" : "justify-start"
                                )}
                            >
                                <div
                                    className={cn(
                                        "max-w-[80%] rounded-lg px-4 py-2 text-sm",
                                        msg.role === 'user'
                                            ? "bg-primary text-primary-foreground"
                                            : "bg-muted text-foreground"
                                    )}
                                >
                                    <div className="whitespace-pre-wrap">{msg.content}</div>
                                </div>
                            </div>
                        )
                    ))}

                    {streamingMessage && (
                        <div className="flex w-full justify-start">
                            <div className="max-w-[80%] rounded-lg px-4 py-2 text-sm bg-muted text-foreground">
                                <div className="whitespace-pre-wrap">{streamingMessage}</div>
                                <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1"></span>
                            </div>
                        </div>
                    )}

                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            <div className="p-4 border-t border-border bg-muted/10">
                <div className="flex gap-2">
                    <Input
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask about the phases or type /analyze for automated review..."
                        disabled={isStreaming}
                        className="flex-1"
                    />
                    <Button
                        onClick={() => sendMessage(input)}
                        disabled={!input.trim() || isStreaming}
                        size="sm"
                    >
                        {isStreaming ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Send className="h-4 w-4" />
                        )}
                    </Button>
                </div>
                <div className="mt-2 text-xs text-muted-foreground">
                    Commands: <strong>/analyze</strong> - Run automated review • <strong>/done</strong> or <strong>/apply</strong> - Continue to execution
                </div>
            </div>
        </div>
    );
};
