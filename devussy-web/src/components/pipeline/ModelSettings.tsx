import React, { useState, useEffect } from 'react';
import { Settings, ChevronDown, Check, Loader2, Globe, Layers, GitBranch, Code2, ArrowRight, MessageSquare, User, Gauge, Shield, History } from 'lucide-react';
import { cn } from '@/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/components/theme/ThemeProvider';

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
    const { theme } = useTheme();
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

    // Theme-aware color classes
    const themeClasses = {
        bg: theme === 'bliss' ? 'bg-white' : theme === 'terminal' ? 'bg-gray-900' : 'bg-background',
        bgAlt: theme === 'bliss' ? 'bg-gray-50' : theme === 'terminal' ? 'bg-gray-800' : 'bg-muted',
        border: theme === 'bliss' ? 'border-gray-400' : theme === 'terminal' ? 'border-green-500/30' : 'border-border',
        borderSoft: theme === 'bliss' ? 'border-gray-300' : theme === 'terminal' ? 'border-green-500/20' : 'border-border/50',
        text: theme === 'bliss' ? 'text-gray-800' : theme === 'terminal' ? 'text-green-400' : 'text-foreground',
        textMuted: theme === 'bliss' ? 'text-gray-600' : theme === 'terminal' ? 'text-green-500/70' : 'text-muted-foreground',
        textDim: theme === 'bliss' ? 'text-gray-500' : theme === 'terminal' ? 'text-green-500/50' : 'text-muted-foreground/70',
        hover: theme === 'bliss' ? 'hover:bg-gray-50' : theme === 'terminal' ? 'hover:bg-gray-800' : 'hover:bg-muted/50',
        hoverAlt: theme === 'bliss' ? 'hover:bg-blue-100' : theme === 'terminal' ? 'hover:bg-green-500/10' : 'hover:bg-primary/10',
        active: theme === 'bliss' ? 'bg-blue-500 text-white' : theme === 'terminal' ? 'bg-green-500 text-black' : 'bg-primary text-primary-foreground',
        accent: theme === 'bliss' ? 'text-blue-600' : theme === 'terminal' ? 'text-green-400' : 'text-primary',
        accentBg: theme === 'bliss' ? 'bg-blue-50 border-blue-200' : theme === 'terminal' ? 'bg-green-500/10 border-green-500/20' : 'bg-primary/10 border-primary/20',
        input: theme === 'bliss' ? 'border-gray-400 focus:border-blue-500' : theme === 'terminal' ? 'border-green-500/30 focus:border-green-500 bg-gray-900' : 'border-input focus:border-primary',
        button: theme === 'bliss' ? 'bg-blue-500 hover:bg-blue-600 text-white' : theme === 'terminal' ? 'bg-green-500 hover:bg-green-600 text-black' : 'bg-primary hover:bg-primary/90 text-primary-foreground',
        buttonAlt: theme === 'bliss' ? 'bg-gray-100 border-gray-400 text-gray-700 hover:bg-gray-200' : theme === 'terminal' ? 'bg-gray-800 border-green-500/30 text-green-400 hover:bg-gray-700' : 'bg-secondary border-border text-secondary-foreground hover:bg-secondary/80',
    };

    const renderContent = () => (
        <div className="space-y-4">
             {/* Header */}
             <div className={cn("flex items-center justify-between pb-2 border-b", themeClasses.borderSoft)}>
                <h2 className={cn("text-base font-bold flex items-center gap-2", themeClasses.text)}>
                    {React.createElement(STAGE_ICONS[selectedTab], { className: cn("w-5 h-5", themeClasses.accent) })}
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
                            className={cn("text-xs underline font-semibold", themeClasses.accent, theme === 'bliss' ? 'hover:text-blue-800' : theme === 'terminal' ? 'hover:text-green-300' : 'hover:text-primary/80')}
                        >
                            Customize
                        </button>
                    )
                )}
            </div>

            {/* Global Settings: IRC Identity */}
            {selectedTab === 'global' && (
                <div className={cn("space-y-2 pt-2 border-b pb-4", themeClasses.borderSoft)}>
                    <h3 className={cn("text-sm font-bold flex items-center gap-2", themeClasses.text)}>
                        <User className="w-4 h-4" />
                        IRC Identity
                    </h3>
                    <div className={cn("border rounded p-3 space-y-2", themeClasses.bg, themeClasses.border)}>
                        <label className={cn("text-xs block", themeClasses.textMuted)}>Persistent Nickname</label>
                        <input 
                            type="text"
                            value={ircNick}
                            onChange={handleIrcNickChange}
                            placeholder="Enter IRC Nickname"
                            className={cn("w-full border rounded px-2 py-1 text-sm focus:outline-none", themeClasses.input, themeClasses.text)}
                        />
                        <p className={cn("text-[10px]", themeClasses.textDim)}>This nickname will be used across sessions.</p>
                    </div>
                </div>
            )}

            {(!isOverride && selectedTab !== 'global') ? (
                <div className={cn("p-6 rounded border text-center space-y-3", themeClasses.accentBg)}>
                    <p className={cn("text-sm font-semibold", themeClasses.text)}>Using Global Configuration</p>
                    <div className={cn("text-xs font-mono p-2 rounded border", themeClasses.textMuted, themeClasses.bg, themeClasses.borderSoft)}>
                        {configs.global.model}  Temperature: {configs.global.temperature}
                    </div>
                    <button
                        onClick={handleCreateOverride}
                        className={cn("mt-2 px-4 py-2 rounded text-xs font-bold", themeClasses.button)}
                    >
                        Customize for {STAGE_LABELS[selectedTab]}
                    </button>
                </div>
            ) : (
                <>
                    {/* Model Selection */}
                    <div className="space-y-2">
                        <h3 className={cn("text-sm font-bold", themeClasses.text)}>AI Model</h3>
                        <div className={cn("border rounded p-3 space-y-2", themeClasses.bg, themeClasses.border)}>
                            <input
                                type="text"
                                placeholder="Search models..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className={cn("w-full border rounded px-2 py-1 text-sm focus:outline-none", themeClasses.input, themeClasses.text)}
                            />
                            <div className="max-h-40 overflow-y-auto space-y-1">
                                {loading ? (
                                    <div className={cn("flex items-center justify-center py-4", themeClasses.textDim)}>
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
                                                "w-full text-left px-2 py-1.5 rounded text-xs flex items-center justify-between",
                                                currentConfig.model === model.id ? themeClasses.active : cn(themeClasses.text, themeClasses.hoverAlt)
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
                        <h3 className={cn("text-sm font-bold", themeClasses.text)}>Temperature</h3>
                        <div className={cn("border rounded p-3 space-y-2", themeClasses.bg, themeClasses.border)}>
                            <div className="flex items-center justify-between">
                                <span className={cn("text-xs", themeClasses.textMuted)}>Current Value:</span>
                                <span className={cn("text-sm font-bold", themeClasses.accent)}>{currentConfig.temperature}</span>
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
                            <div className={cn("flex justify-between text-xs", themeClasses.textMuted)}>
                                <span>Precise</span>
                                <span>Creative</span>
                            </div>
                        </div>
                    </div>

                    {/* Reasoning Effort */}
                    <div className="space-y-2">
                        <h3 className={cn("text-sm font-bold", themeClasses.text)}>Reasoning Effort</h3>
                        <div className={cn("border rounded p-3", themeClasses.bg, themeClasses.border)}>
                            <div className="grid grid-cols-4 gap-2">
                                {[null, 'low', 'medium', 'high'].map((effort) => (
                                    <button
                                        key={String(effort)}
                                        onClick={() => handleConfigUpdate({ ...currentConfig, reasoning_effort: effort as any })}
                                        className={cn(
                                            "px-2 py-1.5 rounded text-xs font-bold border transition-colors uppercase",
                                            currentConfig.reasoning_effort === effort
                                                ? themeClasses.active
                                                : themeClasses.buttonAlt
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
                <div className={cn("flex border-b bg-gradient-to-b", 
                    theme === 'bliss' ? 'border-gray-400 from-white to-gray-100' : 
                    theme === 'terminal' ? 'border-green-500/30 from-gray-900 to-gray-800' : 
                    'border-border from-background to-muted')}>
                    {(Object.keys(STAGE_LABELS) as PipelineStage[]).map((stage) => {
                        const Icon = STAGE_ICONS[stage];
                        const hasOverride = stage !== 'global' && configs[stage] !== null;
                        return (
                            <button
                                key={stage}
                                onClick={() => setSelectedTab(stage)}
                                className={cn(
                                    "flex-1 flex items-center justify-center py-2 text-xs font-bold transition-colors relative border-r",
                                    theme === 'bliss' ? 'border-gray-300' : theme === 'terminal' ? 'border-green-500/20' : 'border-border/50',
                                    selectedTab === stage
                                        ? theme === 'bliss' ? "bg-white text-blue-700" : theme === 'terminal' ? "bg-gray-900 text-green-400" : "bg-background text-primary"
                                        : theme === 'bliss' ? "text-gray-700 hover:bg-gray-50" : theme === 'terminal' ? "text-green-500/70 hover:bg-gray-800" : "text-muted-foreground hover:bg-muted/50"
                                )}
                                title={STAGE_LABELS[stage]}
                            >
                                <Icon className="w-4 h-4 mr-1" />
                                {STAGE_LABELS[stage]}
                                {hasOverride && (
                                    <span className={cn("absolute top-1 right-1 w-2 h-2 rounded-full", 
                                        theme === 'terminal' ? 'bg-green-500' : 'bg-green-600')} />
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
                className={cn(
                    "flex items-center gap-2 px-3 py-1.5 border rounded shadow-sm transition-colors",
                    theme === 'bliss' ? "bg-white border-gray-300 hover:bg-gray-50" :
                    theme === 'terminal' ? "bg-gray-900 border-green-500/30 hover:bg-gray-800" :
                    "bg-background border-border hover:bg-muted/50"
                )}
            >
                <Settings className={cn("w-4 h-4", themeClasses.textMuted)} />
                <span className={cn("text-sm font-medium", themeClasses.text)}>
                    {configs.global.model.split('/').pop()}
                </span>
                <ChevronDown className={cn("w-3 h-3 transition-transform", themeClasses.textDim, isOpen && "rotate-180")} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
                        <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            className={cn(
                                "absolute right-0 mt-2 w-[400px] border rounded-lg shadow-xl z-50 overflow-hidden flex flex-col max-h-[80vh]",
                                theme === 'bliss' ? "bg-white border-gray-300" :
                                theme === 'terminal' ? "bg-gray-900 border-green-500/30" :
                                "bg-background border-border"
                            )}
                        >
                             {/* Tabs */}
                             <div className={cn(
                                 "flex border-b overflow-x-auto",
                                 theme === 'bliss' ? "border-gray-200 bg-gray-50" :
                                 theme === 'terminal' ? "border-green-500/20 bg-gray-800" :
                                 "border-border bg-muted/30"
                             )}>
                                {(Object.keys(STAGE_LABELS) as PipelineStage[]).map((stage) => (
                                    <button
                                        key={stage}
                                        onClick={() => setSelectedTab(stage)}
                                        className={cn(
                                            "px-3 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors",
                                            selectedTab === stage
                                                ? theme === 'bliss' ? "border-blue-500 text-blue-600 bg-white" :
                                                  theme === 'terminal' ? "border-green-500 text-green-400 bg-gray-900" :
                                                  "border-primary text-primary bg-background"
                                                : theme === 'bliss' ? "border-transparent text-gray-600 hover:bg-gray-100" :
                                                  theme === 'terminal' ? "border-transparent text-green-500/70 hover:bg-gray-800" :
                                                  "border-transparent text-muted-foreground hover:bg-muted"
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
