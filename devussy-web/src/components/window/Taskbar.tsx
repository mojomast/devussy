"use client";

import React from 'react';
import { cn } from "@/utils";
import { Layout, HelpCircle, Plus } from "lucide-react";
import { useTheme } from "@/components/theme/ThemeProvider";

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
    const { theme } = useTheme();

    // Bliss Theme (Windows XP) Taskbar
    if (theme === 'bliss') {
        return (
            <div className="fixed bottom-0 left-0 right-0 w-full h-[32px] bg-[#245DDA] border-t-[2px] border-[#3F8CF3] flex items-center z-[9999] select-none shadow-none m-0 p-0"
                style={{ background: 'linear-gradient(to bottom, #245DDA 0%, #3F8CF3 9%, #245DDA 18%, #245DDA 100%)' }}>

                {/* Start Button */}
                <div className="h-full flex items-center px-2 mr-2 cursor-pointer hover:brightness-110 active:brightness-90 relative"
                    style={{
                        background: 'linear-gradient(to bottom, #3C8018 0%, #46941B 100%)',
                        borderRadius: '0 10px 10px 0',
                        border: '1px solid #2B5F11',
                        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.3)'
                    }}>
                    <img src="/devussy_logo_minimal.png" alt="Logo" className="h-5 w-5 invert brightness-0 drop-shadow-md" />
                    <span className="ml-1 font-bold italic text-white text-[14px] drop-shadow-md" style={{ textShadow: '1px 1px 1px rgba(0,0,0,0.5)' }}>Start</span>
                </div>

                {/* Divider */}
                <div className="h-[20px] w-[2px] bg-black/20 border-r border-white/10 mx-1" />

                {/* Window Buttons */}
                <div className="flex-1 flex items-center gap-1 overflow-x-auto px-1">
                    {windows.map((window) => {
                        const isActive = activeWindowId === window.id;
                        const isMinimized = minimizedWindowIds.includes(window.id);

                        return (
                            <button
                                key={window.id}
                                onClick={() => onWindowClick(window.id)}
                                className={cn(
                                    "flex items-center gap-2 px-2 h-[24px] min-w-[140px] max-w-[200px] rounded-[2px] text-xs text-white truncate transition-all",
                                    isActive && !isMinimized
                                        ? "bg-[#1F4EBF] shadow-[inset_1px_1px_2px_rgba(0,0,0,0.5)]"
                                        : "bg-[#3C81F0] hover:bg-[#5291F3] shadow-[0_1px_2px_rgba(0,0,0,0.2)]"
                                )}
                            >
                                <div className="w-3 h-3 bg-white/20 rounded-sm" />
                                <span className="truncate">{window.title}</span>
                            </button>
                        );
                    })}
                </div>

                {/* Tray Area (Clock, etc - Placeholder) */}
                <div className="h-full bg-[#0B96D6] border-l border-[#155394] px-3 flex items-center shadow-[inset_1px_1px_2px_rgba(0,0,0,0.3)]">
                    <span className="text-white text-xs font-medium">
                        {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                </div>
            </div>
        );
    }

    // Default / Terminal Theme Taskbar (Floating Glass)
    return (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-2 p-2 rounded-xl bg-black/60 backdrop-blur-md border border-white/10 shadow-2xl transition-all hover:bg-black/70">
            <div className="px-2 border-r border-white/10 mr-1 flex items-center">
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

            <div className="flex-1 flex items-center gap-1 overflow-x-auto">
                {windows.map((window) => {
                    const isActive = activeWindowId === window.id;
                    const isMinimized = minimizedWindowIds.includes(window.id);

                    return (
                        <button
                            key={window.id}
                            onClick={() => onWindowClick(window.id)}
                            className={cn(
                                "relative group flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all min-w-[120px] max-w-[200px]",
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
                            <span className="truncate flex-1 text-left">{window.title}</span>

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
        </div>
    );
}
