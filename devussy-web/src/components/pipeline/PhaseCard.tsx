"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ChevronUp, ChevronDown, Edit2, Save, X, Trash2 } from "lucide-react";

export interface PhaseData {
    number: number;
    title: string;
    description?: string;
}

interface PhaseCardProps {
    phase: PhaseData;
    isExpanded?: boolean;
    canMoveUp?: boolean;
    canMoveDown?: boolean;
    onUpdate?: (phase: PhaseData) => void;
    onDelete?: () => void;
    onMoveUp?: () => void;
    onMoveDown?: () => void;
    onToggle?: () => void;
}

export const PhaseCard: React.FC<PhaseCardProps> = ({
    phase,
    isExpanded = true,
    canMoveUp = false,
    canMoveDown = false,
    onUpdate,
    onDelete,
    onMoveUp,
    onMoveDown,
    onToggle
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editedTitle, setEditedTitle] = useState(phase.title);
    const [editedDescription, setEditedDescription] = useState(phase.description || "");

    const handleSave = () => {
        if (onUpdate) {
            onUpdate({
                ...phase,
                title: editedTitle,
                description: editedDescription
            });
        }
        setIsEditing(false);
    };

    const handleCancel = () => {
        setEditedTitle(phase.title);
        setEditedDescription(phase.description || "");
        setIsEditing(false);
    };

    return (
        <Card className="bg-card/50 border-border/50 hover:border-border transition-colors">
            <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2">
                    <div className="flex-1 min-w-0">
                        {isEditing ? (
                            <Input
                                value={editedTitle}
                                onChange={(e) => setEditedTitle(e.target.value)}
                                className="font-medium"
                                placeholder="Phase title"
                            />
                        ) : (
                            <CardTitle
                                className="text-base font-medium cursor-pointer hover:text-primary transition-colors"
                                onClick={onToggle}
                            >
                                Phase {phase.number}: {phase.title}
                            </CardTitle>
                        )}
                    </div>

                    <div className="flex items-center gap-1">
                        {/* Reorder buttons */}
                        {canMoveUp && (
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={onMoveUp}
                                title="Move up"
                            >
                                <ChevronUp className="h-4 w-4" />
                            </Button>
                        )}
                        {canMoveDown && (
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={onMoveDown}
                                title="Move down"
                            >
                                <ChevronDown className="h-4 w-4" />
                            </Button>
                        )}

                        {/* Edit/Save buttons */}
                        {isEditing ? (
                            <>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 w-7 p-0 text-green-500 hover:text-green-600"
                                    onClick={handleSave}
                                    title="Save"
                                >
                                    <Save className="h-4 w-4" />
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 w-7 p-0"
                                    onClick={handleCancel}
                                    title="Cancel"
                                >
                                    <X className="h-4 w-4" />
                                </Button>
                            </>
                        ) : (
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0"
                                onClick={() => setIsEditing(true)}
                                title="Edit"
                            >
                                <Edit2 className="h-4 w-4" />
                            </Button>
                        )}

                        {/* Delete button */}
                        {onDelete && (
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0 text-destructive hover:text-destructive/80"
                                onClick={onDelete}
                                title="Delete"
                            >
                                <Trash2 className="h-4 w-4" />
                            </Button>
                        )}
                    </div>
                </div>
            </CardHeader>

            {isExpanded && (
                <CardContent className="pt-0">
                    {isEditing ? (
                        <Textarea
                            value={editedDescription}
                            onChange={(e) => setEditedDescription(e.target.value)}
                            placeholder="Phase description..."
                            className="min-h-[80px] text-sm"
                        />
                    ) : (
                        <CardDescription className="text-sm whitespace-pre-wrap">
                            {phase.description || "No description"}
                        </CardDescription>
                    )}
                </CardContent>
            )}
        </Card>
    );
};
