"use client";

import React from 'react';
import { cn } from "@/utils";
import { Layout, HelpCircle, Plus } from "lucide-react";

interface TaskbarProps {
    windows: Array<{ id: string; title: string; type: string }>;
    activeWindowId: string | null;
    minimizedWindowIds: string[];
    onWindowClick: (id: string) => void;
    onNewProject?: () => void;
    onHelp?: () => void;
}

export const Taskbar: React.FC<TaskbarProps> = ({
    windows,
    activeWindowId,
    minimizedWindowIds,
    onWindowClick,
    onNewProject,
    onHelp
}) => {
    return (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-2 p-2 rounded-xl bg-black/60 backdrop-blur-md border border-white/10 shadow-2xl transition-all hover:bg-black/70">
            <div className="px-2 border-r border-white/10 mr-1">
                <Layout className="h-5 w-5 text-primary" />
            </div>

            {/* New Project Button */}
            <button
                onClick={onNewProject}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all text-muted-foreground hover:bg-white/5 hover:text-white"
                title="New Project"
            >
                <Plus className="h-4 w-4" />
                <span>New</span>
            </button>

            {/* Help Button */}
            <button
                onClick={onHelp}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all text-muted-foreground hover:bg-white/5 hover:text-white"
                title="Help"
            >
                <HelpCircle className="h-4 w-4" />
                <span>Help</span>
            </button>

            {windows.length > 0 && (
                <div className="h-6 w-px bg-white/10 mx-1" />
            )}

            {windows.map((window) => {
                const isActive = activeWindowId === window.id;
                const isMinimized = minimizedWindowIds.includes(window.id);

                return (
                    <button
                        key={window.id}
                        onClick={() => onWindowClick(window.id)}
                        className={cn(
                            "relative group flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                            isActive && !isMinimized
                                ? "bg-white/10 text-white shadow-inner"
                                : "text-muted-foreground hover:bg-white/5 hover:text-white",
                            isMinimized && "opacity-50 hover:opacity-100"
                        )}
                    >
                        <div className={cn(
                            "h-2 w-2 rounded-full transition-colors",
                            isActive && !isMinimized ? "bg-green-500" : "bg-white/20 group-hover:bg-white/50"
                        )} />
                        <span className="max-w-[100px] truncate">{window.title}</span>

                        {/* Tooltip-ish indicator for minimized */}
                        {isMinimized && (
                            <div className="absolute -top-1 -right-1">
                                <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
                            </div>
                        )}
                    </button>
                );
            })}
        </div>
    );
}
