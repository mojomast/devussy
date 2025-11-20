import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Save, Download, Clock, FileJson, Loader2 } from "lucide-react";

interface Checkpoint {
    id: string;
    name: string;
    timestamp: number;
    projectName: string;
    stage: string;
}

interface CheckpointManagerProps {
    currentState: any; // The full state object to save
    onLoad: (state: any) => void;
}

export const CheckpointManager: React.FC<CheckpointManagerProps> = ({ currentState, onLoad }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
    const [newCheckpointName, setNewCheckpointName] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    const fetchCheckpoints = async () => {
        setIsLoading(true);
        try {
            const res = await fetch(`/api/checkpoints`);
            const data = await res.json();
            if (data.checkpoints) {
                setCheckpoints(data.checkpoints);
            }
        } catch (e) {
            console.error("Failed to fetch checkpoints", e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen) {
            fetchCheckpoints();
        }
    }, [isOpen]);

    const handleSave = async () => {
        if (!newCheckpointName) return;
        setIsSaving(true);
        try {
            const payload = {
                ...currentState,
                name: newCheckpointName,
                timestamp: Date.now() / 1000
            };

            await fetch(`/api/checkpoints`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            setNewCheckpointName("");
            fetchCheckpoints();
        } catch (e) {
            console.error("Failed to save checkpoint", e);
        } finally {
            setIsSaving(false);
        }
    };

    const handleLoad = async (id: string) => {
        setIsLoading(true);
        try {
            const res = await fetch(`/api/checkpoints?id=${id}`);
            const data = await res.json();
            onLoad(data);
            setIsOpen(false);
        } catch (e) {
            console.error("Failed to load checkpoint", e);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2">
                    <Save className="h-4 w-4" />
                    Checkpoints
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <FileJson className="h-5 w-5" />
                        Project Checkpoints
                    </DialogTitle>
                </DialogHeader>

                <div className="flex gap-2 py-4">
                    <Input
                        placeholder="Checkpoint Name..."
                        value={newCheckpointName}
                        onChange={(e) => setNewCheckpointName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                    />
                    <Button onClick={handleSave} disabled={!newCheckpointName || isSaving}>
                        {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Current"}
                    </Button>
                </div>

                <div className="text-sm font-medium mb-2">Saved Checkpoints</div>
                <ScrollArea className="h-[300px] border rounded-md p-2">
                    {isLoading && checkpoints.length === 0 ? (
                        <div className="flex justify-center items-center h-full">
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        </div>
                    ) : checkpoints.length === 0 ? (
                        <div className="text-center text-muted-foreground py-8">No checkpoints found</div>
                    ) : (
                        <div className="space-y-2">
                            {checkpoints.map((cp) => (
                                <div key={cp.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors group">
                                    <div className="flex flex-col gap-1 overflow-hidden">
                                        <div className="font-medium truncate">{cp.name}</div>
                                        <div className="text-xs text-muted-foreground flex items-center gap-2">
                                            <Clock className="h-3 w-3" />
                                            {new Date(cp.timestamp * 1000).toLocaleString()}
                                        </div>
                                        <div className="text-xs text-muted-foreground truncate">
                                            {cp.projectName} • {cp.stage}
                                        </div>
                                    </div>
                                    <Button
                                        size="sm"
                                        variant="secondary"
                                        onClick={() => handleLoad(cp.id)}
                                        disabled={isLoading}
                                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        <Download className="h-4 w-4 mr-2" /> Load
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </ScrollArea>
            </DialogContent>
        </Dialog>
    );
};
