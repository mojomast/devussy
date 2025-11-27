"use client";

import React, { useState, useRef } from 'react';
import { motion, useDragControls } from 'framer-motion';
import { Minus, X } from 'lucide-react';
import { cn } from '@/utils';
import { useTheme } from '@/components/theme/ThemeProvider';
import { useWindowSize } from '@/hooks/useWindowSize';

interface WindowFrameProps {
    id?: string;
    title: string;
    children: React.ReactNode;
    isActive?: boolean;
    isMinimized?: boolean;
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
    const { theme } = useTheme();
    const dragControls = useDragControls();
    const [isMaximized, setIsMaximized] = useState(false);

    const { width: screenWidth } = useWindowSize();
    const isMobile = screenWidth < 768; // md breakpoint

    const [size, setSize] = useState(initialSize);
    const [position, setPosition] = useState(initialPosition);

    const variants = {
        hidden: { opacity: 0, scale: 0.8 },
        visible: { opacity: 1, scale: 1 },
        minimized: { opacity: 0, scale: 0.5, y: 500 },
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
                // Only move position by the actual width change, not the full delta
                const actualWidthChange = startWidth - newWidth;
                newX = startPosX + actualWidthChange;
            }
            if (direction.includes('n')) {
                newHeight = Math.max(200, startHeight - deltaY);
                // Only move position by the actual height change, not the full delta
                const actualHeightChange = startHeight - newHeight;
                newY = startPosY + actualHeightChange;
            }

            setSize({ width: newWidth, height: newHeight });
            setPosition({ x: newX, y: newY });
        };

        const handlePointerUp = () => {
            document.removeEventListener('pointermove', handlePointerMove);
            document.removeEventListener('pointerup', handlePointerUp);
        };

        document.addEventListener('pointermove', handlePointerMove);
        document.addEventListener('pointerup', handlePointerUp);
    };

    // Bliss (XP) Theme
    if (theme === 'bliss') {
        return (
            <motion.div
                drag={!isMaximized && !isMobile}
                dragControls={dragControls}
                dragMomentum={false}
                initial="hidden"
                animate={isMinimized ? "minimized" : isMaximized ? "maximized" : "visible"}
                variants={variants}
                onPointerDown={onFocus}
                style={isMobile ? {
                    position: 'fixed',
                    left: 0,
                    top: 0,
                    width: '100%',
                    height: '100%',
                    zIndex: style?.zIndex || (isActive ? 50 : 10),
                    ...style,
                } : {
                    position: isMaximized ? 'fixed' : 'absolute',
                    left: isMaximized ? 0 : position.x,
                    top: isMaximized ? 0 : position.y,
                    width: isMaximized ? '100%' : size.width,
                    height: isMaximized ? '100%' : size.height,
                    zIndex: style?.zIndex || (isActive ? 50 : 10),
                    ...style,
                }}
                className="window-frame flex flex-col overflow-hidden"
            >
                {/* XP Window Header */}
                <div
                    onPointerDown={(e) => dragControls.start(e)}
                    className="flex items-center justify-between h-[30px] px-2 cursor-grab active:cursor-grabbing select-none window-header"
                >
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-white/20 rounded-sm" />
                        <span className="text-white text-sm font-bold drop-shadow-sm">{title}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        {onMinimize && (
                            <button
                                onClick={onMinimize}
                                className="w-[21px] h-[21px] rounded-sm flex items-center justify-center transition-colors group"
                                style={{
                                    background: 'linear-gradient(to bottom, #ECE9D8 0%, #E0DED0 50%, #D5CCBA 100%)',
                                    border: '1px solid #003c74',
                                    boxShadow: 'inset 1px 1px 0 rgba(255,255,255,0.8), inset -1px -1px 0 rgba(0,0,0,0.2)'
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.background = 'linear-gradient(to bottom, #F2F0E8 0%, #E8E5D8 50%, #DDD9CA 100%)'}
                                onMouseLeave={(e) => e.currentTarget.style.background = 'linear-gradient(to bottom, #ECE9D8 0%, #E0DED0 50%, #D5CCBA 100%)'}
                            >
                                <Minus className="w-3 h-3 text-black" strokeWidth={2} />
                            </button>
                        )}
                        {onClose && (
                            <button
                                onClick={onClose}
                                className="w-[21px] h-[21px] rounded-sm flex items-center justify-center transition-colors group"
                                style={{
                                    background: 'linear-gradient(to bottom, #ECE9D8 0%, #E0DED0 50%, #D5CCBA 100%)',
                                    border: '1px solid #003c74',
                                    boxShadow: 'inset 1px 1px 0 rgba(255,255,255,0.8), inset -1px -1px 0 rgba(0,0,0,0.2)'
                                }}
                                onMouseEnter={(e) => e.currentTarget.style.background = 'linear-gradient(to bottom, #FF6B68 0%, #FF4842 50%, #E63946 100%)'}
                                onMouseLeave={(e) => e.currentTarget.style.background = 'linear-gradient(to bottom, #ECE9D8 0%, #E0DED0 50%, #D5CCBA 100%)'}
                            >
                                <X className="w-3 h-3 text-black group-hover:text-white" strokeWidth={2} />
                            </button>
                        )}
                    </div>
                </div>

                {/* XP Window Content */}
                <div className="flex-1 overflow-auto bg-[#ece9d8] p-3">
                    {children}
                </div>

                {/* Resize Handles */}
                {!isMaximized && !isMobile && (
                    <>
                        <div onPointerDown={(e) => handleResizeStart(e, 'se')} className="absolute bottom-0 right-0 h-4 w-4 cursor-se-resize z-50" />
                        <div onPointerDown={(e) => handleResizeStart(e, 'sw')} className="absolute bottom-0 left-0 h-4 w-4 cursor-sw-resize z-50" />
                        <div onPointerDown={(e) => handleResizeStart(e, 'ne')} className="absolute top-0 right-0 h-4 w-4 cursor-ne-resize z-50" />
                        <div onPointerDown={(e) => handleResizeStart(e, 'nw')} className="absolute top-0 left-0 h-4 w-4 cursor-nw-resize z-50" />

                        <div onPointerDown={(e) => handleResizeStart(e, 'e')} className="absolute top-2 bottom-2 right-0 w-1 cursor-e-resize z-40" />
                        <div onPointerDown={(e) => handleResizeStart(e, 'w')} className="absolute top-2 bottom-2 left-0 w-1 cursor-w-resize z-40" />
                        <div onPointerDown={(e) => handleResizeStart(e, 's')} className="absolute bottom-0 left-2 right-2 h-1 cursor-s-resize z-40" />
                        <div onPointerDown={(e) => handleResizeStart(e, 'n')} className="absolute top-0 left-2 right-2 h-1 cursor-n-resize z-40" />
                    </>
                )}
            </motion.div>
        );
    }

    // Default / Terminal Theme
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
            <div
                onPointerDown={(e) => dragControls.start(e)}
                className={cn("flex h-10 shrink-0 items-center justify-between border-b border-white/10 bg-white/5 px-4 select-none", { "cursor-grab active:cursor-grabbing": !isMobile })}
            >
                <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-red-500/20" />
                    <span className="text-xs font-medium text-muted-foreground">{title}</span>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={onMinimize} className="rounded-sm p-1 hover:bg-white/10">
                        <Minus className="h-3 w-3" />
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
                {children}
            </div>

            {!isMaximized && !isMobile && (
                <>
                    <div onPointerDown={(e) => handleResizeStart(e, 'se')} className="absolute bottom-0 right-0 h-4 w-4 cursor-se-resize z-50" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'sw')} className="absolute bottom-0 left-0 h-4 w-4 cursor-sw-resize z-50" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'ne')} className="absolute top-0 right-0 h-4 w-4 cursor-ne-resize z-50" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'nw')} className="absolute top-0 left-0 h-4 w-4 cursor-nw-resize z-50" />

                    <div onPointerDown={(e) => handleResizeStart(e, 'e')} className="absolute top-2 bottom-2 right-0 w-1 cursor-e-resize z-40 hover:bg-white/10 transition-colors" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'w')} className="absolute top-2 bottom-2 left-0 w-1 cursor-w-resize z-40 hover:bg-white/10 transition-colors" />
                    <div onPointerDown={(e) => handleResizeStart(e, 's')} className="absolute bottom-0 left-2 right-2 h-1 cursor-s-resize z-40 hover:bg-white/10 transition-colors" />
                    <div onPointerDown={(e) => handleResizeStart(e, 'n')} className="absolute top-0 left-2 right-2 h-1 cursor-n-resize z-40 hover:bg-white/10 transition-colors" />
                </>
            )}
        </motion.div>
    );
}
