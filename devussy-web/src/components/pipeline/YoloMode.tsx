"use client";

import React from 'react';
import { Zap } from "lucide-react";

/**
 * Tiny kangaroo SVG icon for YOLO mode
 */
function KangarooIcon({ className = "h-4 w-4" }: { className?: string }) {
    return (
        <svg 
            viewBox="0 0 24 24" 
            fill="currentColor" 
            className={className}
            aria-label="Kangaroo"
        >
            {/* Stylized hopping kangaroo silhouette */}
            <path d="M19.5 12c0-1.5-.5-2.5-1.5-3.5-.5-.5-1-1-1-2 0-.5.2-1 .5-1.5.3-.5.5-1 .5-1.5 0-1-.8-1.5-1.5-1.5-.5 0-1 .3-1.3.7-.2.3-.5.5-.7.8-.5.5-1 1-1.5 1.5-.3.3-.7.5-1 .5H10c-.5 0-1-.2-1.3-.5L7.5 3.3c-.2-.2-.5-.3-.8-.3-.5 0-1 .3-1.2.8-.1.3-.1.5 0 .8l.8 2c.1.3.2.5.2.8 0 .5-.3.8-.7 1L4.5 9c-.3.1-.5.4-.5.7v.8c0 .3.2.6.5.7l1.5.8v2l-2 3c-.3.5-.3 1 0 1.5s.8.7 1.3.5l2.2-1c.3-.1.5-.3.7-.5l.8-1 2 1.5c.3.2.7.3 1 .3h1c.5 0 1-.2 1.3-.5l1-1c.2-.2.3-.5.3-.8v-1.5c0-.3.1-.5.3-.7l.8-.8c.5-.5.8-1.2.8-2v-1z"/>
            {/* Ear */}
            <ellipse cx="16" cy="3.5" rx="1" ry="1.5" />
            {/* Joey in pouch (small bump) */}
            <circle cx="11" cy="14" r="1.2" className="opacity-60" />
        </svg>
    );
}

interface YoloModeToggleProps {
    enabled: boolean;
    onToggle: (enabled: boolean) => void;
    disabled?: boolean;
}

/**
 * YOLO Mode Toggle
 * 
 * When enabled, auto-approves all pipeline stages without waiting for user input.
 * Features a tiny kangaroo icon because... why not hop through everything quickly?
 */
export function YoloModeToggle({ 
    enabled, 
    onToggle, 
    disabled = false 
}: YoloModeToggleProps) {
    return (
        <button
            onClick={() => onToggle(!enabled)}
            disabled={disabled}
            className={`
                flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium
                transition-all duration-200 border
                ${enabled 
                    ? 'bg-orange-500/20 border-orange-500/50 text-orange-400 hover:bg-orange-500/30' 
                    : 'bg-muted/30 border-border/50 text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
            title={enabled ? 'YOLO Mode: Auto-approve everything!' : 'Enable YOLO Mode to auto-approve all stages'}
        >
            <KangarooIcon className={`h-4 w-4 ${enabled ? 'animate-bounce' : ''}`} />
            <span>YOLO</span>
            {enabled && (
                <Zap className="h-3 w-3 text-yellow-400" />
            )}
        </button>
    );
}

/**
 * YOLO Mode Badge - compact indicator
 */
export function YoloModeBadge({ enabled }: { enabled: boolean }) {
    if (!enabled) return null;
    
    return (
        <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs bg-orange-500/20 border border-orange-500/30 text-orange-400">
            <KangarooIcon className="h-3 w-3 animate-bounce" />
            <span>YOLO</span>
        </div>
    );
}

export { KangarooIcon };
export default YoloModeToggle;
