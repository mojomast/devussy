"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
    MessageSquare, 
    Send, 
    Loader2, 
    X, 
    ArrowRight, 
    Sparkles,
    RefreshCw,
    CheckCircle2
} from "lucide-react";
import { cn } from '@/utils';

interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

interface InlineRefinementPanelProps {
    design: any;
    projectName: string;
    requirements: string;
    languages: string[];
    isOpen: boolean;
    onClose: () => void;
    onRefinementComplete: (updatedDesign: any) => void;
    onRequestReanalysis?: () => void;  // Trigger complexity/validation re-run
}

/**
 * InlineRefinementPanel - Embedded chat interface for design refinement
 * 
 * Appears directly below ComplexityAssessment instead of spawning a separate window.
 * Supports:
 * - Free-form conversation about the design
 * - /analyze command for automated review
 * - /apply command to finalize and trigger re-analysis
 */
export const InlineRefinementPanel: React.FC<InlineRefinementPanelProps> = ({
    design,
    projectName,
    requirements,
    languages,
    isOpen,
    onClose,
    onRefinementComplete,
    onRequestReanalysis
}) => {
    const [history, setHistory] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamingMessage, setStreamingMessage] = useState("");
    const [hasChanges, setHasChanges] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);
    const hasInitialized = useRef(false);

    // Initialize with welcome message when opened
    useEffect(() => {
        if (isOpen && !hasInitialized.current) {
            hasInitialized.current = true;
            setHistory([
                {
                    role: 'assistant',
                    content: `Let's refine your design for **${projectName}**. You can:

• Ask questions about the architecture
• Request specific improvements
• Identify potential issues or gaps
• Type **/analyze** for an automated review
• Type **/apply** when you're satisfied to continue

What would you like to focus on?`
                }
            ]);
        }
    }, [isOpen, projectName]);

    // Reset when closed
    useEffect(() => {
        if (!isOpen) {
            hasInitialized.current = false;
            setHistory([]);
            setInput("");
            setStreamingMessage("");
            setHasChanges(false);
        }
    }, [isOpen]);

    // Auto-scroll on new messages
    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [history, streamingMessage]);

    // Focus input when opened
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    const sendMessage = async (message: string) => {
        if (!message.trim() || isStreaming) return;

        const userMessage = { role: 'user' as const, content: message.trim() };
        setHistory(prev => [...prev, userMessage]);
        setInput("");
        setIsStreaming(true);
        setStreamingMessage("");

        // Handle special commands
        if (message.trim().toLowerCase() === '/analyze') {
            await runAutomatedReview();
            return;
        }

        if (message.trim().toLowerCase() === '/apply') {
            // Apply refinements and complete
            setIsStreaming(false);
            setHistory(prev => [...prev, {
                role: 'assistant',
                content: '✅ Refinements applied! Re-analyzing complexity and validating design...'
            }]);
            
            // Small delay for UX
            setTimeout(() => {
                onRefinementComplete(design);
                if (onRequestReanalysis) {
                    onRequestReanalysis();
                }
                onClose();
            }, 1000);
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
                        console.log('[InlineRefinement] Stream ended without done signal, finalizing');
                        setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                        setStreamingMessage("");
                        setHasChanges(true);
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
                                setHasChanges(true);
                                if (data.updatedDesign) {
                                    console.log('[InlineRefinement] Received updated design');
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

            // Finalize if no explicit done signal (backup - should rarely hit now)
            if (fullResponse && !gotDoneSignal) {
                setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                setStreamingMessage("");
                setHasChanges(true);
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
                        console.log('[InlineRefinement] Review stream ended without done signal, finalizing');
                        setHistory(prev => [...prev, { role: 'assistant', content: fullResponse }]);
                        setStreamingMessage("");
                        setHasChanges(true);
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
                                setHasChanges(true);
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
                setHasChanges(true);
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

    const handleApplyAndContinue = () => {
        onRefinementComplete(design);
        if (onRequestReanalysis) {
            onRequestReanalysis();
        }
        onClose();
    };

    if (!isOpen) return null;

    return (
        <Card className="mb-6 border-primary/30 bg-primary/5 overflow-hidden">
            <CardHeader className="border-b border-border/50 py-3">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2 text-base">
                            <MessageSquare className="h-5 w-5 text-primary" />
                            Design Refinement
                        </CardTitle>
                        <CardDescription className="text-xs mt-1">
                            Chat to improve your design before generating phases
                        </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                        {hasChanges && (
                            <span className="text-xs text-green-500 flex items-center gap-1">
                                <CheckCircle2 className="h-3 w-3" />
                                Changes discussed
                            </span>
                        )}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onClose}
                            className="h-8 w-8 p-0"
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="p-0">
                {/* Chat Messages */}
                <ScrollArea className="h-[280px] p-4">
                    <div className="space-y-3 pb-4">
                        {history.map((msg, idx) => (
                            <div
                                key={idx}
                                className={cn(
                                    "flex w-full",
                                    msg.role === 'user' ? "justify-end" : "justify-start"
                                )}
                            >
                                <div
                                    className={cn(
                                        "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                                        msg.role === 'user'
                                            ? "bg-primary text-primary-foreground"
                                            : "bg-muted/50 text-foreground border border-border/30"
                                    )}
                                >
                                    <div className="whitespace-pre-wrap">{msg.content}</div>
                                </div>
                            </div>
                        ))}

                        {streamingMessage && (
                            <div className="flex w-full justify-start">
                                <div className="max-w-[85%] rounded-lg px-3 py-2 text-sm bg-muted/50 text-foreground border border-border/30">
                                    <div className="whitespace-pre-wrap">{streamingMessage}</div>
                                    <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1"></span>
                                </div>
                            </div>
                        )}

                        <div ref={scrollRef} />
                    </div>
                </ScrollArea>

                {/* Input Area */}
                <div className="p-3 border-t border-border/50 bg-muted/10">
                    <div className="flex gap-2">
                        <Input
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask about the design or type /analyze..."
                            disabled={isStreaming}
                            className="flex-1 h-9 text-sm"
                        />
                        <Button
                            onClick={() => sendMessage(input)}
                            disabled={!input.trim() || isStreaming}
                            size="sm"
                            className="h-9 w-9 p-0"
                        >
                            {isStreaming ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <Send className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                    
                    {/* Quick Actions */}
                    <div className="flex items-center justify-between mt-2">
                        <div className="text-xs text-muted-foreground">
                            <span className="font-mono bg-muted/50 px-1 rounded">/analyze</span> review
                            <span className="mx-2">•</span>
                            <span className="font-mono bg-muted/50 px-1 rounded">/apply</span> continue
                        </div>
                        <Button
                            variant="default"
                            size="sm"
                            onClick={handleApplyAndContinue}
                            className="h-7 text-xs gap-1"
                        >
                            <ArrowRight className="h-3 w-3" />
                            Apply & Continue
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

export default InlineRefinementPanel;
