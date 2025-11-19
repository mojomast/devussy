"use client";

import React, { useState, useRef } from 'react';
import { motion, useDragControls } from 'framer-motion';
import { X, Minus, Square, Maximize2 } from 'lucide-react';
import { cn } from '@/utils';

interface WindowFrameProps {
    id?: string; // Made optional as it wasn't strictly used
    title: string;
    children: React.ReactNode;
    isActive?: boolean; // Made optional with default
    isMinimized?: boolean; // Made optional with default
    onClose?: () => void;
    onMinimize?: () => void;
    onFocus?: () => void;
    initialPosition?: { x: number; y: number };
    initialSize?: { width: number; height: number };
    className?: string;
    style?: React.CSSProperties;
}

export function WindowFrame({
    id,
    title,
    children,
    isActive = true,
    isMinimized = false,
    onClose,
    onMinimize,
    onFocus,
    initialPosition = { x: 100, y: 100 },
    initialSize = { width: 600, height: 400 },
    className,
    style,
}: WindowFrameProps) {
    const dragControls = useDragControls();
    const [isMaximized, setIsMaximized] = useState(false);
    const [size, setSize] = useState(initialSize);
    const [position, setPosition] = useState(initialPosition); // Track position locally for resizing from top/left

    // Variants for window animation
    const variants = {
        hidden: { opacity: 0, scale: 0.8 },
        visible: { opacity: 1, scale: 1 },
        minimized: { opacity: 0, scale: 0.5, y: 500 }, // Animate out to bottom
        maximized: { x: 0, y: 0, width: '100%', height: '100%' },
    };

    const handleResizeStart = (e: React.PointerEvent, direction: string) => {
        e.preventDefault();
        e.stopPropagation();

        const startX = e.clientX;
        const startY = e.clientY;
        const startWidth = size.width;
        const startHeight = size.height;
        const startPosX = position.x;
        const startPosY = position.y;

        const handlePointerMove = (moveEvent: PointerEvent) => {
            const deltaX = moveEvent.clientX - startX;
            const deltaY = moveEvent.clientY - startY;

            let newWidth = startWidth;
            let newHeight = startHeight;
            let newX = startPosX;
            let newY = startPosY;

            if (direction.includes('e')) {
                newWidth = Math.max(300, startWidth + deltaX);
            }
            if (direction.includes('s')) {
                newHeight = Math.max(200, startHeight + deltaY);
            }
            if (direction.includes('w')) {
                newWidth = Math.max(300, startWidth - deltaX);
                newX = startPosX + (startWidth - newWidth);
            }
            if (direction.includes('n')) {
                newHeight = Math.max(200, startHeight - deltaY);
                newY = startPosY + (startHeight - newHeight);
            }

            setSize({ width: newWidth, height: newHeight });
            if (direction.includes('w') || direction.includes('n')) {
                setPosition({ x: newX, y: newY });
            }
        };

        const handlePointerUp = () => {
            document.removeEventListener('pointermove', handlePointerMove);
            document.removeEventListener('pointerup', handlePointerUp);
        };

        document.addEventListener('pointermove', handlePointerMove);
        document.addEventListener('pointerup', handlePointerUp);
    };

    return (
        <motion.div
            drag={!isMaximized}
            dragControls={dragControls}
            dragMomentum={false}
            initial="hidden"
            animate={isMinimized ? "minimized" : isMaximized ? "maximized" : "visible"}
            variants={variants}
            onPointerDown={onFocus}
            style={{
                position: isMaximized ? 'fixed' : 'absolute',
                left: isMaximized ? 0 : position.x,
                top: isMaximized ? 0 : position.y,
                width: isMaximized ? '100%' : size.width,
                height: isMaximized ? '100%' : size.height,
                zIndex: style?.zIndex || (isActive ? 50 : 10),
                ...style,
            }}
            className={cn(
                "flex flex-col overflow-hidden rounded-lg border border-white/10 shadow-2xl backdrop-blur-md bg-black/40",
                isActive ? "ring-1 ring-primary/50" : "grayscale-[0.5]",
                className
            )}
        >
            {/* Window Header */}
            <div
                onPointerDown={(e) => dragControls.start(e)}
                className="flex h-10 shrink-0 cursor-grab items-center justify-between border-b border-white/10 bg-white/5 px-4 active:cursor-grabbing select-none"
            >
                <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-red-500/20" />
                    <span className="text-xs font-medium text-muted-foreground">{title}</span>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={onMinimize} className="rounded-sm p-1 hover:bg-white/10">
                        <Minus className="h-3 w-3" />
                    </button>
                    <button onClick={() => setIsMaximized(!isMaximized)} className="rounded-sm p-1 hover:bg-white/10">
                        {isMaximized ? <Square className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
                    </button>
                    <button onClick={onClose} className="rounded-sm p-1 hover:bg-destructive/20 hover:text-destructive">
                        <X className="h-3 w-3" />
                    </button>
                </div>
            </div>

            {/* Window Content */}
            <div className="flex-1 overflow-auto p-4">
                {children}
            </div>

            {/* Resize Handles */}
            {!isMaximized && (
                <>
                    {/* Corners */}
                    <div onPointerDown={(e) => handleResizeStart(e, 'se')} className="absolute bottom-0 right-0 h-4 w-4 cursor-se-resize z-50" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'sw')} className="absolute bottom-0 left-0 h-4 w-4 cursor-sw-resize z-50" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'ne')} className="absolute top-0 right-0 h-4 w-4 cursor-ne-resize z-50" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'nw')} className="absolute top-0 left-0 h-4 w-4 cursor-nw-resize z-50" />

                    {/* Sides */}
                    <div onPointerDown={(e) => handleResizeStart(e, 'e')} className="absolute top-2 bottom-2 right-0 w-1 cursor-e-resize z-40 hover:bg-white/10 transition-colors" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'w')} className="absolute top-2 bottom-2 left-0 w-1 cursor-w-resize z-40 hover:bg-white/10 transition-colors" />
                    <div onPointerDown={(e) => handleResizeStart(e, 's')} className="absolute bottom-0 left-2 right-2 h-1 cursor-s-resize z-40 hover:bg-white/10 transition-colors" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'n')} className="absolute top-0 left-2 right-2 h-1 cursor-n-resize z-40 hover:bg-white/10 transition-colors" />
                </>
            )}
        </motion.div>
    );
}
