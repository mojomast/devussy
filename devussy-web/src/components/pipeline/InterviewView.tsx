"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Send, Loader2, MessageSquare } from "lucide-react";
import { ModelConfig } from './ModelSettings';
import { cn } from "@/utils";

interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

interface InterviewViewProps {
    modelConfig: ModelConfig;
    onInterviewComplete: (data: any) => void;
}

export const InterviewView: React.FC<InterviewViewProps> = ({
    modelConfig,
    onInterviewComplete
}) => {
    const [history, setHistory] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const hasInitialized = useRef(false);

    // Initial greeting
    useEffect(() => {
        if (!hasInitialized.current && history.length === 0) {
            hasInitialized.current = true;
            handleSend("Hello! I'd like to start a new project.");
        }
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [history, isLoading]);

    const handleSend = async (text: string) => {
        if (!text.trim()) return;

        const newHistory = [...history, { role: 'user' as const, content: text }];
        setHistory(newHistory);
        setInput("");
        setIsLoading(true);

        try {
            const response = await fetch('/api/interview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    userInput: text,
                    history: history.filter(m => m.role !== 'system'), // Only send user/assistant messages
                    modelConfig
                }),
            });

            if (!response.ok) throw new Error('Failed to send message');

            const data = await response.json();

            setHistory(prev => [...prev, { role: 'assistant', content: data.response }]);

            if (data.isComplete && data.extractedData) {
                // Add a small delay so the user can read the final message
                setTimeout(() => {
                    onInterviewComplete(data.extractedData);
                }, 2000);
            }

        } catch (error) {
            console.error("Interview error:", error);
            setHistory(prev => [...prev, { role: 'assistant', content: "I'm sorry, I encountered an error. Please try again." }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend(input);
        }
    };

    return (
        <div className="flex flex-col h-full max-w-3xl mx-auto">
            <div className="flex items-center justify-between p-4 border-b border-border bg-muted/20">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Project Interview
                </h2>
                <div className="text-xs text-muted-foreground">
                    Chat with AI to define your project requirements
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
                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-muted rounded-lg px-4 py-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                            </div>
                        </div>
                    )}
                    <div ref={scrollRef} />
                </div>
            </ScrollArea>

            <div className="p-4 border-t border-border bg-background">
                <div className="flex gap-2">
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your answer..."
                        disabled={isLoading}
                        className="flex-1"
                        autoFocus
                    />
                    <Button
                        onClick={() => handleSend(input)}
                        disabled={isLoading || !input.trim()}
                        size="icon"
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </div>
                <div className="mt-2 text-xs text-center text-muted-foreground">
                    Type <strong>/done</strong> when you are ready to generate the design.
                </div>
            </div>
        </div>
    );
}
