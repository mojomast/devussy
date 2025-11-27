"use client";

import React, { useState, useEffect, useRef } from 'react';
import { cn } from "@/utils";
import { Layout, HelpCircle, Plus, Power, Settings, MessageSquare } from "lucide-react";
import { useTheme } from "@/components/theme/ThemeProvider";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { CheckpointManager } from "@/components/pipeline/CheckpointManager";
import { ModelSettings, ModelConfigs, PipelineStage } from "@/components/pipeline/ModelSettings";

interface TaskbarProps {
    windows: Array<{ id: string; title: string; type: string }>;
    activeWindowId: string | null;
    minimizedWindowIds: string[];
    onWindowClick: (id: string) => void;
    onNewProject?: () => void;
    onHelp?: () => void;
    onOpenModelSettings?: () => void;
    onOpenIrc?: () => void;
    // Props for Start Menu options
    currentState?: any;
    onLoadCheckpoint?: (data: any) => void;
    modelConfigs?: ModelConfigs;
    onModelConfigsChange?: (configs: ModelConfigs) => void;
    activeStage?: PipelineStage;
    ircNick?: string;
}

export const Taskbar: React.FC<TaskbarProps> = ({
    windows,
    activeWindowId,
    minimizedWindowIds,
    onWindowClick,
    onNewProject,
    onHelp,
    onOpenModelSettings,
    onOpenIrc,
    currentState,
    onLoadCheckpoint,
    modelConfigs,
    onModelConfigsChange,
    activeStage,
    ircNick = 'Guest'
}) => {
    const { theme } = useTheme();
    const [isStartMenuOpen, setIsStartMenuOpen] = useState(false);
    const startMenuRef = useRef<HTMLDivElement>(null);
    const startButtonRef = useRef<HTMLDivElement>(null);

    // Close start menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                isStartMenuOpen &&
                startMenuRef.current &&
                !startMenuRef.current.contains(event.target as Node) &&
                startButtonRef.current &&
                !startButtonRef.current.contains(event.target as Node)
            ) {
                setIsStartMenuOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isStartMenuOpen]);

    // Bliss Theme (Windows XP) Taskbar
    if (theme === 'bliss') {
        return (
            <>
                {/* Start Menu */}
                {isStartMenuOpen && (
                    <div
                        ref={startMenuRef}
                        className="fixed bottom-[32px] left-0 z-[10000] flex flex-col rounded-tr-lg overflow-hidden shadow-xl animate-in slide-in-from-bottom-2 fade-in duration-200"
                        style={{
                            width: '380px',
                            height: '480px',
                            background: '#fff',
                            border: '1px solid #0054e3',
                            borderBottom: 'none',
                            boxShadow: '2px -2px 10px rgba(0,0,0,0.3)'
                        }}
                    >
                        {/* Header */}
                        <div className="h-16 flex items-center px-4 gap-3"
                            style={{
                                background: 'linear-gradient(to bottom, #1565DE 0%, #1C6CE1 100%)',
                                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)'
                            }}>
                            <div className="h-10 w-10 rounded-full bg-white border-2 border-white/40 overflow-hidden flex items-center justify-center">
                                <img src="/devussy_logo_minimal.png" alt="User" className="h-8 w-8 object-contain" />
                            </div>
                            <span className="text-white font-bold text-lg drop-shadow-md">{ircNick}</span>
                        </div>

                        {/* Body */}
                        <div className="flex-1 flex bg-white">
                            {/* Left Column (White) - Programs */}
                            <div className="flex-1 p-2 flex flex-col gap-1 bg-white">
                                <div className="text-xs text-gray-500 font-bold px-2 mb-1 uppercase tracking-wider">Most Used</div>

                                <button onClick={() => { onNewProject?.(); setIsStartMenuOpen(false); }} className="flex items-center gap-2 p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors text-left">
                                    <Plus className="h-8 w-8 text-gray-600 group-hover:text-white" />
                                    <div className="flex flex-col">
                                        <span className="font-bold text-sm">New Project</span>
                                        <span className="text-[10px] text-gray-500 group-hover:text-white/80">Start a new creation</span>
                                    </div>
                                </button>

                                <button onClick={() => { onHelp?.(); setIsStartMenuOpen(false); }} className="flex items-center gap-2 p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors text-left">
                                    <HelpCircle className="h-8 w-8 text-blue-600 group-hover:text-white" />
                                    <div className="flex flex-col">
                                        <span className="font-bold text-sm">Help & Support</span>
                                        <span className="text-[10px] text-gray-500 group-hover:text-white/80">Get assistance</span>
                                    </div>
                                </button>

                                <button onClick={() => { onOpenIrc?.(); setIsStartMenuOpen(false); }} className="flex items-center gap-2 p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors text-left">
                                    <MessageSquare className="h-8 w-8 text-green-600 group-hover:text-white" />
                                    <div className="flex flex-col">
                                        <span className="font-bold text-sm">IRC Chat</span>
                                        <span className="text-[10px] text-gray-500 group-hover:text-white/80">Chat with #devussy</span>
                                    </div>
                                </button>

                                <div className="mt-auto border-t border-gray-200 pt-2">
                                    <div className="text-xs text-gray-500 font-bold px-2 mb-1 uppercase tracking-wider">All Programs</div>
                                    <div className="flex items-center justify-center p-2 bg-blue-50 rounded border border-blue-100 text-blue-800 text-xs font-bold cursor-pointer hover:bg-blue-100">
                                        All Programs <span className="ml-1">▶</span>
                                    </div>
                                </div>
                            </div>

                            {/* Right Column (Blue) - Places & Options */}
                            <div className="w-[160px] bg-[#D3E5FA] border-l border-[#95BDE7] p-2 flex flex-col gap-1">
                                <div className="text-xs text-[#1A3E78] font-bold px-2 mb-1">Settings</div>

                                {/* Theme Toggle Wrapper */}
                                <div className="p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors cursor-pointer flex items-center gap-2">
                                    <div className="scale-75 origin-left">
                                        <ThemeToggle />
                                    </div>
                                    <span className="text-xs font-medium text-[#1A3E78] group-hover:text-white">Theme</span>
                                </div>

                                {/* Checkpoint Manager Wrapper */}
                                {currentState && onLoadCheckpoint && (
                                    <div className="p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors cursor-pointer flex items-center gap-2">
                                        <div className="scale-75 origin-left">
                                            <CheckpointManager
                                                currentState={currentState}
                                                onLoad={onLoadCheckpoint}
                                            />
                                        </div>
                                        <span className="text-xs font-medium text-[#1A3E78] group-hover:text-white">Save/Load</span>
                                    </div>
                                )}

                                {/* Model Settings Button */}
                                <button onClick={() => { onOpenModelSettings?.(); setIsStartMenuOpen(false); }} className="flex items-center gap-2 p-2 hover:bg-[#316AC5] hover:text-white rounded group transition-colors cursor-pointer text-left">
                                    <Settings className="h-8 w-8 text-gray-600 group-hover:text-white" />
                                    <div className="flex flex-col">
                                        <span className="font-bold text-sm">AI Models</span>
                                        <span className="text-[10px] text-gray-500 group-hover:text-white/80">Configure models</span>
                                    </div>
                                </button>
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="h-10 bg-[#1C6CE1] flex items-center justify-end px-3 gap-2"
                            style={{
                                background: 'linear-gradient(to bottom, #1C6CE1 0%, #1565DE 100%)',
                                boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)'
                            }}>
                            <button className="flex items-center gap-1 px-2 py-1 hover:bg-[#1565DE] rounded text-white text-xs">
                                <Power className="h-4 w-4" />
                                <span>Turn Off Computer</span>
                            </button>
                        </div>
                    </div>
                )}

                <div className="fixed bottom-0 left-0 right-0 w-full h-[32px] bg-[#245DDA] border-t-[2px] border-[#3F8CF3] flex items-center z-[9999] select-none shadow-none m-0 p-0"
                    style={{ background: 'linear-gradient(to bottom, #245DDA 0%, #3F8CF3 9%, #245DDA 18%, #245DDA 100%)' }}>

                    {/* Start Button */}
                    <div
                        ref={startButtonRef}
                        onClick={() => setIsStartMenuOpen(!isStartMenuOpen)}
                        className={cn(
                            "h-full flex items-center px-2 mr-2 cursor-pointer hover:brightness-110 active:brightness-90 relative transition-all",
                            isStartMenuOpen && "brightness-90 shadow-[inset_1px_1px_2px_rgba(0,0,0,0.5)]"
                        )}
                        style={{
                            background: 'linear-gradient(to bottom, #3C8018 0%, #46941B 100%)',
                            borderRadius: '0 10px 10px 0',
                            border: '1px solid #2B5F11',
                            boxShadow: isStartMenuOpen ? 'inset 1px 1px 2px rgba(0,0,0,0.5)' : 'inset 0 1px 0 rgba(255,255,255,0.3)'
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
            </>
        );
    }

    // Default / Terminal Theme Taskbar (Floating Glass on Desktop, Fixed Bar on Mobile)
    return (
        <div className="fixed bottom-0 left-0 right-0 z-[100] flex items-center gap-2 p-2 bg-black/80 backdrop-blur-md border-t border-white/10 md:bottom-4 md:left-1/2 md:-translate-x-1/2 md:right-auto md:border md:rounded-xl md:bg-black/60 md:w-auto">
            <div className="hidden md:flex px-2 border-r border-white/10 mr-1 items-center">
                <Layout className="h-5 w-5 text-primary" />
            </div>

            {/* Main actions - flex-shrink-0 to prevent them from shrinking on mobile */}
            <div className="flex items-center gap-1 flex-shrink-0">
                <button
                    onClick={onNewProject}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all text-muted-foreground hover:bg-white/5 hover:text-white"
                    title="New Project"
                >
                    <Plus className="h-4 w-4" />
                    <span className="hidden md:inline">New</span>
                </button>
                <button
                    onClick={onHelp}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all text-muted-foreground hover:bg-white/5 hover:text-white"
                    title="Help"
                >
                    <HelpCircle className="h-4 w-4" />
                    <span className="hidden md:inline">Help</span>
                </button>
                <button
                    onClick={onOpenIrc}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all text-muted-foreground hover:bg-white/5 hover:text-white"
                    title="IRC Chat"
                >
                    <MessageSquare className="h-4 w-4" />
                    <span className="hidden md:inline">Chat</span>
                </button>
            </div>

            {windows.length > 0 && (
                <div className="h-6 w-px bg-white/10 mx-1" />
            )}

            {/* Scrollable window list */}
            <div className="flex-1 flex items-center gap-1 overflow-x-auto min-w-0">
                {windows.map((window) => {
                    const isActive = activeWindowId === window.id;
                    const isMinimized = minimizedWindowIds.includes(window.id);

                    return (
                        <button
                            key={window.id}
                            onClick={() => onWindowClick(window.id)}
                            className={cn(
                                "relative group flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all w-full md:w-auto md:min-w-[120px] md:max-w-[200px]",
                                "text-muted-foreground hover:bg-white/5 hover:text-white",
                                isActive && !isMinimized && "bg-white/10 text-white shadow-inner",
                                isMinimized && "opacity-50 hover:opacity-100"
                            )}
                        >
                            <div className={cn(
                                "h-2 w-2 rounded-full transition-colors flex-shrink-0",
                                isActive && !isMinimized ? "bg-green-500" : "bg-white/20 group-hover:bg-white/50"
                            )} />
                            <span className="truncate flex-1 text-left">{window.title}</span>
                            {isMinimized && (
                                <div className="absolute top-1 right-1 h-2 w-2 bg-blue-500 rounded-full" />
                            )}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
