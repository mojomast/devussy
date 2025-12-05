import React, { useState, useEffect } from 'react';
import { Settings, ChevronDown, Check, Loader2, Globe, Layers, GitBranch, Code2, ArrowRight, MessageSquare, User, Gauge, Shield, History } from 'lucide-react';
import { cn } from '@/utils';
import { motion, AnimatePresence } from 'framer-motion';

export interface ModelConfig {
    model: string;
    temperature: number;
    reasoning_effort: 'low' | 'medium' | 'high' | null;
    concurrency?: number; // Number of concurrent phase executions (1-10)
}

// Extended to include adaptive pipeline stages
export type PipelineStage = 'global' | 'interview' | 'complexity' | 'design' | 'validation' | 'correction' | 'plan' | 'execute' | 'handoff';

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
    isWindowMode?: boolean; // Optional: render content directly for window mode
}

const STAGE_ICONS: Record<PipelineStage, React.ElementType> = {
    global: Globe,
    interview: MessageSquare,
    complexity: Gauge,
    design: Layers,
    validation: Shield,
    correction: History,
    plan: GitBranch,
    execute: Code2,
    handoff: ArrowRight,
};

const STAGE_LABELS: Record<PipelineStage, string> = {
    global: 'Global Default',
    interview: 'Interview',
    complexity: 'Complexity Analysis',
    design: 'Design',
    validation: 'Validation',
    correction: 'Correction',
    plan: 'Plan',
    execute: 'Execute',
    handoff: 'Handoff',
};

export const ModelSettings: React.FC<ModelSettingsProps> = ({ configs, onConfigsChange, activeStage, isWindowMode = false }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedTab, setSelectedTab] = useState<PipelineStage>('global');
    const [models, setModels] = useState<Model[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [search, setSearch] = useState('');
    const [ircNick, setIrcNick] = useState('');

    // Sync selected tab with active stage if provided and open
    useEffect(() => {
        if ((isWindowMode || isOpen) && activeStage) {
            setSelectedTab(activeStage);
        }
    }, [isOpen, isWindowMode, activeStage]);

    // Load IRC Nick from localStorage
    useEffect(() => {
        const stored = localStorage.getItem('devussy_irc_nick');
        if (stored) setIrcNick(stored);
    }, []);

    const handleIrcNickChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;
        setIrcNick(val);
        localStorage.setItem('devussy_irc_nick', val);
    };

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

        // In window mode, load immediately. In dropdown mode, load when opened.
        if ((isWindowMode || isOpen) && models.length === 0) {
            fetchModels();
        }
    }, [isOpen, isWindowMode, models.length]);

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

    const renderContent = () => (
        <div className="space-y-4">
             {/* Header */}
             <div className="flex items-center justify-between pb-2 border-b border-gray-300">
                <h2 className="text-base font-bold text-gray-800 flex items-center gap-2">
                    {React.createElement(STAGE_ICONS[selectedTab], { className: "w-5 h-5 text-blue-600" })}
                    {STAGE_LABELS[selectedTab]} Configuration
                </h2>
                {selectedTab !== 'global' && (
                    isOverride ? (
                        <button
                            onClick={handleClearOverride}
                            className="text-xs text-red-600 hover:text-red-800 underline font-semibold"
                        >
                            Reset to Global
                        </button>
                    ) : (
                        <button
                            onClick={handleCreateOverride}
                            className="text-xs text-blue-600 hover:text-blue-800 underline font-semibold"
                        >
                            Customize
                        </button>
                    )
                )}
            </div>

            {/* Global Settings: IRC Identity */}
            {selectedTab === 'global' && (
                <div className="space-y-2 pt-2 border-b border-gray-300 pb-4">
                    <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                        <User className="w-4 h-4" />
                        IRC Identity
                    </h3>
                    <div className="bg-white border border-gray-400 rounded p-3 space-y-2">
                        <label className="text-xs text-gray-600 block">Persistent Nickname</label>
                        <input 
                            type="text"
                            value={ircNick}
                            onChange={handleIrcNickChange}
                            placeholder="Enter IRC Nickname"
                            className="w-full border border-gray-400 rounded px-2 py-1 text-sm focus:outline-none focus:border-blue-500"
                        />
                        <p className="text-[10px] text-gray-500">This nickname will be used across sessions.</p>
                    </div>
                </div>
            )}

            {(!isOverride && selectedTab !== 'global') ? (
                <div className="p-6 rounded bg-blue-50 border border-blue-200 text-center space-y-3">
                    <p className="text-sm text-gray-700 font-semibold">Using Global Configuration</p>
                    <div className="text-xs font-mono text-gray-600 bg-white p-2 rounded border border-gray-300">
                        {configs.global.model}  Temperature: {configs.global.temperature}
                    </div>
                    <button
                        onClick={handleCreateOverride}
                        className="mt-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-xs font-bold"
                    >
                        Customize for {STAGE_LABELS[selectedTab]}
                    </button>
                </div>
            ) : (
                <>
                    {/* Model Selection */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-bold text-gray-800">AI Model</h3>
                        <div className="bg-white border border-gray-400 rounded p-3 space-y-2">
                            <input
                                type="text"
                                placeholder="Search models..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="w-full border border-gray-400 rounded px-2 py-1 text-sm focus:outline-none focus:border-blue-500"
                            />
                            <div className="max-h-40 overflow-y-auto space-y-1">
                                {loading ? (
                                    <div className="flex items-center justify-center py-4 text-gray-500">
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    </div>
                                ) : error ? (
                                    <div className="text-red-600 text-xs py-2">{error}</div>
                                ) : (
                                    filteredModels.map(model => (
                                        <button
                                            key={model.id}
                                            onClick={() => handleConfigUpdate({ ...currentConfig, model: model.id })}
                                            className={cn(
                                                "w-full text-left px-2 py-1.5 rounded text-xs flex items-center justify-between hover:bg-blue-100",
                                                currentConfig.model === model.id ? "bg-blue-500 text-white font-bold" : "text-gray-800"
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
                        <h3 className="text-sm font-bold text-gray-800">Temperature</h3>
                        <div className="bg-white border border-gray-400 rounded p-3 space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-xs text-gray-600">Current Value:</span>
                                <span className="text-sm font-bold text-blue-600">{currentConfig.temperature}</span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="2"
                                step="0.1"
                                value={currentConfig.temperature}
                                onChange={(e) => handleConfigUpdate({ ...currentConfig, temperature: parseFloat(e.target.value) })}
                                className="w-full"
                            />
                            <div className="flex justify-between text-xs text-gray-600">
                                <span>Precise</span>
                                <span>Creative</span>
                            </div>
                        </div>
                    </div>

                    {/* Reasoning Effort */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-bold text-gray-800">Reasoning Effort</h3>
                        <div className="bg-white border border-gray-400 rounded p-3">
                            <div className="grid grid-cols-4 gap-2">
                                {[null, 'low', 'medium', 'high'].map((effort) => (
                                    <button
                                        key={String(effort)}
                                        onClick={() => handleConfigUpdate({ ...currentConfig, reasoning_effort: effort as any })}
                                        className={cn(
                                            "px-2 py-1.5 rounded text-xs font-bold border transition-colors uppercase",
                                            currentConfig.reasoning_effort === effort
                                                ? "bg-blue-500 border-blue-700 text-white"
                                                : "bg-gray-100 border-gray-400 text-gray-700 hover:bg-gray-200"
                                        )}
                                    >
                                        {effort || 'None'}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );

    // Window Mode Render
    if (isWindowMode) {
        return (
            <div className="h-full flex flex-col bg-transparent">
                {/* XP Category View Tabs */}
                <div className="flex border-b border-gray-400 bg-gradient-to-b from-white to-gray-100">
                    {(Object.keys(STAGE_LABELS) as PipelineStage[]).map((stage) => {
                        const Icon = STAGE_ICONS[stage];
                        const hasOverride = stage !== 'global' && configs[stage] !== null;
                        return (
                            <button
                                key={stage}
                                onClick={() => setSelectedTab(stage)}
                                className={cn(
                                    "flex-1 flex items-center justify-center py-2 text-xs font-bold transition-colors relative border-r border-gray-300",
                                    selectedTab === stage
                                        ? "bg-white text-blue-700"
                                        : "text-gray-700 hover:bg-gray-50"
                                )}
                                title={STAGE_LABELS[stage]}
                            >
                                <Icon className="w-4 h-4 mr-1" />
                                {STAGE_LABELS[stage]}
                                {hasOverride && (
                                    <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-green-600" />
                                )}
                            </button>
                        );
                    })}
                </div>
                {/* XP Content Area */}
                <div className="flex-1 overflow-auto p-4">
                    {renderContent()}
                </div>
            </div>
        );
    }

    return (
        <div className="relative">
             <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50 transition-colors"
            >
                <Settings className="w-4 h-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-700">
                    {configs.global.model.split('/').pop()}
                </span>
                <ChevronDown className={cn("w-3 h-3 text-gray-500 transition-transform", isOpen && "rotate-180")} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
                        <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            className="absolute right-0 mt-2 w-[400px] bg-white border border-gray-300 rounded-lg shadow-xl z-50 overflow-hidden flex flex-col max-h-[80vh]"
                        >
                             {/* Tabs */}
                             <div className="flex border-b border-gray-200 bg-gray-50 overflow-x-auto">
                                {(Object.keys(STAGE_LABELS) as PipelineStage[]).map((stage) => (
                                    <button
                                        key={stage}
                                        onClick={() => setSelectedTab(stage)}
                                        className={cn(
                                            "px-3 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors",
                                            selectedTab === stage
                                                ? "border-blue-500 text-blue-600 bg-white"
                                                : "border-transparent text-gray-600 hover:bg-gray-100"
                                        )}
                                    >
                                        {STAGE_LABELS[stage]}
                                    </button>
                                ))}
                            </div>
                            <div className="p-4 overflow-y-auto">
                                {renderContent()}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};
