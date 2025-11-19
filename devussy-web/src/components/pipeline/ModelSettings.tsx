import React, { useState, useEffect } from 'react';
import { Settings, ChevronDown, Check, Loader2, Globe, Layers, GitBranch, Code2, ArrowRight, MessageSquare } from 'lucide-react';
import { cn } from '@/utils';
import { motion, AnimatePresence } from 'framer-motion';

export interface ModelConfig {
    model: string;
    temperature: number;
    reasoning_effort: 'low' | 'medium' | 'high' | null;
}

export type PipelineStage = 'global' | 'interview' | 'design' | 'plan' | 'execute' | 'handoff';

export type ModelConfigs = Record<PipelineStage, ModelConfig | null> & { global: ModelConfig };

interface Model {
    id: string;
    name: string;
    description: string;
    context_window: number;
}

interface ModelSettingsProps {
    configs: ModelConfigs;
    onConfigsChange: (configs: ModelConfigs) => void;
    activeStage?: PipelineStage; // Optional: highlight the currently active stage in the UI
}

const STAGE_ICONS: Record<PipelineStage, React.ElementType> = {
    global: Globe,
    interview: MessageSquare,
    design: Layers,
    plan: GitBranch,
    execute: Code2,
    handoff: ArrowRight,
};

const STAGE_LABELS: Record<PipelineStage, string> = {
    global: 'Global Default',
    interview: 'Interview',
    design: 'Design',
    plan: 'Plan',
    execute: 'Execute',
    handoff: 'Handoff',
};

export const ModelSettings: React.FC<ModelSettingsProps> = ({ configs, onConfigsChange, activeStage }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedTab, setSelectedTab] = useState<PipelineStage>('global');
    const [models, setModels] = useState<Model[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [search, setSearch] = useState('');

    // Sync selected tab with active stage if provided and open
    useEffect(() => {
        if (isOpen && activeStage) {
            setSelectedTab(activeStage);
        }
    }, [isOpen, activeStage]);

    useEffect(() => {
        const fetchModels = async () => {
            setLoading(true);
            try {
                const res = await fetch('/api/models');
                if (!res.ok) throw new Error('Failed to fetch models');
                const data = await res.json();
                setModels(data.models || []);
            } catch (err) {
                console.error(err);
                setError('Failed to load models');
            } finally {
                setLoading(false);
            }
        };

        if (isOpen && models.length === 0) {
            fetchModels();
        }
    }, [isOpen, models.length]);

    const filteredModels = models.filter(m =>
        m.id.toLowerCase().includes(search.toLowerCase()) ||
        m.name.toLowerCase().includes(search.toLowerCase())
    );

    const currentConfig = configs[selectedTab] || configs.global;
    const isOverride = selectedTab !== 'global' && configs[selectedTab] !== null;

    const handleConfigUpdate = (newConfig: ModelConfig) => {
        if (selectedTab === 'global') {
            onConfigsChange({ ...configs, global: newConfig });
        } else {
            onConfigsChange({ ...configs, [selectedTab]: newConfig });
        }
    };

    const handleClearOverride = () => {
        if (selectedTab !== 'global') {
            onConfigsChange({ ...configs, [selectedTab]: null });
        }
    };

    const handleCreateOverride = () => {
        if (selectedTab !== 'global') {
            onConfigsChange({ ...configs, [selectedTab]: { ...configs.global } });
        }
    };

    // Helper to get display string for the button
    const getButtonLabel = () => {
        const activeConfig = activeStage ? (configs[activeStage] || configs.global) : configs.global;
        return activeConfig.model.split('/').pop();
    };

    return (
        <div className="relative z-50">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={cn(
                    "flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-mono transition-colors border",
                    isOpen
                        ? "bg-green-500/20 border-green-500/50 text-green-400"
                        : "bg-black/40 border-white/10 text-white/60 hover:text-white hover:border-white/30"
                )}
            >
                <Settings className="w-3.5 h-3.5" />
                <span>{getButtonLabel()}</span>
                {activeStage && activeStage !== 'global' && configs[activeStage] && (
                    <span className="flex h-1.5 w-1.5 rounded-full bg-green-500" />
                )}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        <div
                            className="fixed inset-0 z-40"
                            onClick={() => setIsOpen(false)}
                        />
                        <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            transition={{ duration: 0.1 }}
                            className="absolute right-0 top-full mt-2 w-[400px] bg-[#0a0a0a] border border-white/10 rounded-lg shadow-2xl z-50 overflow-hidden backdrop-blur-xl flex flex-col"
                        >
                            {/* Tabs */}
                            <div className="flex border-b border-white/10 bg-white/5">
                                {(Object.keys(STAGE_LABELS) as PipelineStage[]).map((stage) => {
                                    const Icon = STAGE_ICONS[stage];
                                    const hasOverride = stage !== 'global' && configs[stage] !== null;
                                    return (
                                        <button
                                            key={stage}
                                            onClick={() => setSelectedTab(stage)}
                                            className={cn(
                                                "flex-1 flex items-center justify-center py-2.5 text-[10px] uppercase tracking-wider font-medium transition-colors relative",
                                                selectedTab === stage
                                                    ? "text-white bg-white/5"
                                                    : "text-white/40 hover:text-white/70 hover:bg-white/5"
                                            )}
                                            title={STAGE_LABELS[stage]}
                                        >
                                            <Icon className="w-3.5 h-3.5" />
                                            {hasOverride && (
                                                <span className="absolute top-1.5 right-1.5 w-1 h-1 rounded-full bg-green-500" />
                                            )}
                                            {selectedTab === stage && (
                                                <motion.div
                                                    layoutId="activeTab"
                                                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-green-500"
                                                />
                                            )}
                                        </button>
                                    );
                                })}
                            </div>

                            <div className="p-4 space-y-4">
                                <div className="flex items-center justify-between mb-2">
                                    <h3 className="text-sm font-medium text-white flex items-center gap-2">
                                        {React.createElement(STAGE_ICONS[selectedTab], { className: "w-4 h-4 text-green-500" })}
                                        {STAGE_LABELS[selectedTab]} Settings
                                    </h3>

                                    {selectedTab !== 'global' && (
                                        isOverride ? (
                                            <button
                                                onClick={handleClearOverride}
                                                className="text-[10px] text-red-400 hover:text-red-300 underline"
                                            >
                                                Reset to Global
                                            </button>
                                        ) : (
                                            <button
                                                onClick={handleCreateOverride}
                                                className="text-[10px] text-green-400 hover:text-green-300 underline"
                                            >
                                                Override Global
                                            </button>
                                        )
                                    )}
                                </div>

                                {(!isOverride && selectedTab !== 'global') ? (
                                    <div className="p-4 rounded-lg border border-white/10 bg-white/5 text-center space-y-2">
                                        <p className="text-xs text-white/60">Using Global Configuration</p>
                                        <div className="text-xs font-mono text-white/40">
                                            {configs.global.model} • T={configs.global.temperature}
                                        </div>
                                        <button
                                            onClick={handleCreateOverride}
                                            className="mt-2 px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded text-xs text-white transition-colors"
                                        >
                                            Customize for {STAGE_LABELS[selectedTab]}
                                        </button>
                                    </div>
                                ) : (
                                    <>
                                        {/* Model Selection */}
                                        <div className="space-y-2">
                                            <label className="text-xs font-mono text-white/50 uppercase tracking-wider">Model</label>
                                            <div className="relative">
                                                <input
                                                    type="text"
                                                    placeholder="Search models..."
                                                    value={search}
                                                    onChange={(e) => setSearch(e.target.value)}
                                                    className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-green-500/50 mb-2"
                                                />
                                                <div className="max-h-40 overflow-y-auto space-y-1 custom-scrollbar">
                                                    {loading ? (
                                                        <div className="flex items-center justify-center py-4 text-white/30">
                                                            <Loader2 className="w-4 h-4 animate-spin" />
                                                        </div>
                                                    ) : error ? (
                                                        <div className="text-red-400 text-xs py-2">{error}</div>
                                                    ) : (
                                                        filteredModels.map(model => (
                                                            <button
                                                                key={model.id}
                                                                onClick={() => handleConfigUpdate({ ...currentConfig, model: model.id })}
                                                                className={cn(
                                                                    "w-full text-left px-2 py-1.5 rounded text-xs flex items-center justify-between group hover:bg-white/5",
                                                                    currentConfig.model === model.id ? "text-green-400 bg-green-500/10" : "text-white/70"
                                                                )}
                                                            >
                                                                <span className="truncate pr-2">{model.id}</span>
                                                                {currentConfig.model === model.id && <Check className="w-3 h-3 flex-shrink-0" />}
                                                            </button>
                                                        ))
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Temperature */}
                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between">
                                                <label className="text-xs font-mono text-white/50 uppercase tracking-wider">Temperature</label>
                                                <span className="text-xs font-mono text-green-400">{currentConfig.temperature}</span>
                                            </div>
                                            <input
                                                type="range"
                                                min="0"
                                                max="2"
                                                step="0.1"
                                                value={currentConfig.temperature}
                                                onChange={(e) => handleConfigUpdate({ ...currentConfig, temperature: parseFloat(e.target.value) })}
                                                className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-green-500"
                                            />
                                            <div className="flex justify-between text-[10px] text-white/30 font-mono">
                                                <span>Precise</span>
                                                <span>Creative</span>
                                            </div>
                                        </div>

                                        {/* Reasoning Effort */}
                                        <div className="space-y-2">
                                            <label className="text-xs font-mono text-white/50 uppercase tracking-wider">Reasoning Effort (Thinking)</label>
                                            <div className="grid grid-cols-4 gap-2">
                                                {[null, 'low', 'medium', 'high'].map((effort) => (
                                                    <button
                                                        key={String(effort)}
                                                        onClick={() => handleConfigUpdate({ ...currentConfig, reasoning_effort: effort as any })}
                                                        className={cn(
                                                            "px-2 py-1.5 rounded text-[10px] font-mono border transition-colors uppercase",
                                                            currentConfig.reasoning_effort === effort
                                                                ? "bg-green-500/20 border-green-500/50 text-green-400"
                                                                : "bg-black/40 border-white/10 text-white/50 hover:border-white/30"
                                                        )}
                                                    >
                                                        {effort || 'Off'}
                                                    </button>
                                                ))}
                                            </div>
                                            <p className="text-[10px] text-white/30">
                                                Only supported on reasoning models (e.g. o1, gpt-5-preview).
                                            </p>
                                        </div>
                                    </>
                                )}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};
