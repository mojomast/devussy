"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, Send, Loader2, CheckCircle, AlertCircle, X, ArrowRight } from "lucide-react";
import { cn } from '@/utils';

interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

interface DesignRefinementViewProps {
    design: any;
    projectName: string;
    requirements: string;
    languages: string[];
    onRefinementComplete: (updatedDesign: any) => void;
    onCancel?: () => void;
}

export const DesignRefinementView: React.FC<DesignRefinementViewProps> = ({
    design,
    projectName,
    requirements,
    languages,
    onRefinementComplete,
    onCancel
}) => {
    const [history, setHistory] = useState<Message[]>([
        {
            role: 'system',
            content: `I'm reviewing your project design for "${projectName}". Let's discuss potential issues, improvements, or clarifications before generating the development phases.`
        },
        {
            role: 'assistant',
            content: `I've analyzed your project design and I'm ready to help refine it. You can:

• Ask me to identify potential issues or gaps
• Request clarification on technical approaches
• Discuss alternative architectures or technologies
• Verify that the design aligns with your requirements

What would you like to focus on? Or type "/analyze" for an automated design review.`
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

        if (message.trim() === '/apply') {
            // Apply current refinements and complete
            onRefinementComplete(design);
            return;
        }

        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            const response = await fetch('/api/design/refine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design,
                    projectName,
                    requirements,
                    languages,
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
                        console.log('[DesignRefinement] Stream ended without done signal, finalizing');
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
                                if (data.updatedDesign) {
                                    // Backend provided an updated design structure
                                    console.log('[DesignRefinement] Received updated design');
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

            // Finalize if no explicit done signal
            if (fullResponse) {
                setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                setStreamingMessage("");
            }

        } catch (err: any) {
            if (err.name === 'AbortError') {
                console.log('Refinement request aborted');
                return;
            }
            console.error("Refinement error:", err);
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
            const response = await fetch('/api/design/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ design, projectName })
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
                        console.log('[DesignRefinement] Review stream ended without done signal, finalizing');
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
        // User is satisfied with refinements, pass back the design
        onRefinementComplete(design);
    };

    return (
        <div className="flex flex-col h-full bg-background">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <div>
                    <h2 className="text-lg font-semibold flex items-center gap-2">
                        <MessageSquare className="h-5 w-5" />
                        Design Refinement Session
                    </h2>
                    <div className="text-xs text-muted-foreground">
                        Discuss improvements before generating phases
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
                        Continue to Plan
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
                        placeholder="Ask about the design or type /analyze for automated review..."
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
                    Commands: <strong>/analyze</strong> - Run automated review • <strong>/apply</strong> - Continue to plan generation
                </div>
            </div>
        </div>
    );
};
