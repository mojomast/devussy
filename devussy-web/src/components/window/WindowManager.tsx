"use client";

import React, { useState } from 'react';
import { WindowFrame } from './WindowFrame';
import { AnimatePresence } from 'framer-motion';

export interface WindowData {
    id: string;
    title: string;
    content: React.ReactNode;
    isMinimized: boolean;
    position?: { x: number; y: number };
}

interface WindowManagerProps {
    windows: WindowData[];
    setWindows: React.Dispatch<React.SetStateAction<WindowData[]>>;
}

export function WindowManager({ windows, setWindows }: WindowManagerProps) {
    const [activeWindowId, setActiveWindowId] = useState<string | null>(null);

    const handleFocus = (id: string) => {
        setActiveWindowId(id);
    };

    const handleClose = (id: string) => {
        setWindows((prev) => prev.filter((w) => w.id !== id));
    };

    const handleMinimize = (id: string) => {
        setWindows((prev) =>
            prev.map((w) => (w.id === id ? { ...w, isMinimized: !w.isMinimized } : w))
        );
    };

    return (
        <div className="relative h-full w-full overflow-hidden">
            <AnimatePresence>
                {windows.map((window) => (
                    !window.isMinimized && (
                        <WindowFrame
                            key={window.id}
                            id={window.id}
                            title={window.title}
                            isActive={activeWindowId === window.id}
                            isMinimized={window.isMinimized}
                            onFocus={() => handleFocus(window.id)}
                            onClose={() => handleClose(window.id)}
                            onMinimize={() => handleMinimize(window.id)}
                            initialPosition={window.position}
                        >
                            {window.content}
                        </WindowFrame>
                    )
                ))}
            </AnimatePresence>

            {/* Taskbar / Minimized Windows Area (Optional, for now just hidden) */}
            <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 gap-2">
                {windows.filter(w => w.isMinimized).map(w => (
                    <button
                        key={w.id}
                        onClick={() => handleMinimize(w.id)}
                        className="rounded-full bg-primary px-4 py-2 text-xs font-bold text-primary-foreground shadow-lg transition-transform hover:scale-105"
                    >
                        {w.title}
                    </button>
                ))}
            </div>
        </div>
    );
}
