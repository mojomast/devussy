"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ArrowRight, Sparkles, Layers, Code2, GitBranch, MessageSquare, Zap, Play, Settings } from "lucide-react";
import { WindowFrame } from "@/components/window/WindowFrame";
import { DesignView } from "@/components/pipeline/DesignView";
import { PlanView } from "@/components/pipeline/PlanView";
import { ExecutionView } from "@/components/pipeline/ExecutionView";
import { HandoffView } from "@/components/pipeline/HandoffView";
import { InterviewView } from "@/components/pipeline/InterviewView";
import { ModelSettings, ModelConfigs, PipelineStage } from "@/components/pipeline/ModelSettings";
import { CheckpointManager } from "@/components/pipeline/CheckpointManager";
import { Taskbar } from "@/components/window/Taskbar";
import { ThemeToggle } from "@/components/theme/ThemeToggle";
import { useTheme } from "@/components/theme/ThemeProvider";
import IrcClient from '@/components/addons/irc/IrcClient';
import { YoloModeToggle } from "@/components/pipeline/YoloMode";
import { PipelineOverview } from "@/components/pipeline/PipelineOverview";
import { DesignRefinementView } from "@/components/pipeline/DesignRefinementView";
import { PlanRefinementView } from "@/components/pipeline/PlanRefinementView";

type WindowType = 'init' | 'interview' | 'design' | 'plan' | 'execute' | 'handoff' | 'help' | 'model-settings' | 'irc' | 'pipeline-guide' | 'design-refinement' | 'plan-refinement';

interface WindowState {
  id: string;
  type: WindowType;
  title: string;
  position: { x: number; y: number };
  zIndex: number;
  isMinimized?: boolean;
  props?: Record<string, any>;
  size?: { width: number; height: number };
}

export default function Page() {
  const { theme } = useTheme();
  // Window State Management
  const [windows, setWindows] = useState<WindowState[]>([
    { id: 'help-1', type: 'help', title: 'Devussy Studio Help', position: { x: 50, y: 50 }, zIndex: 10, size: { width: 700, height: 600 } }
  ]);
  const [activeWindowId, setActiveWindowId] = useState<string>('help-1');
  const [nextZIndex, setNextZIndex] = useState(20);

  // Project State (Shared across windows)
  const [projectName, setProjectName] = useState("");
  const [languages, setLanguages] = useState("");
  const [requirements, setRequirements] = useState("");

  // Auto-run State
  const [isAutoRun, setIsAutoRun] = useState(false);
  
  // YOLO Mode State (auto-approve all stages)
  const [yoloMode, setYoloMode] = useState(false);

  // Pipeline Data
  const [design, setDesign] = useState<any>(null);
  const [plan, setPlan] = useState<any>(null);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);

  // Help preferences
  const [dontShowHelpAgain, setDontShowHelpAgain] = useState<boolean>(() => {
    try { return localStorage.getItem('devussy_help_dismissed') === '1'; } catch (e) { return false; }
  });

  const [analyticsOptOut, setAnalyticsOptOut] = useState<boolean>(false);

  useEffect(() => {
    try {
      const cookies = document.cookie.split(';').map(c => c.trim());
      const cookie = cookies.find(c => c.startsWith('devussy_analytics_optout='));
      if (cookie) {
        const value = (cookie.split('=')[1] || '').toLowerCase();
        if (value === '1' || value === 'true' || value === 'yes') {
          setAnalyticsOptOut(true);
        }
      }
    } catch (e) { }
  }, []);

  // IRC nickname (from localStorage)
  const [ircNick, setIrcNick] = useState<string>(() => {
    try { return localStorage.getItem('devussy_irc_nick') || 'Guest'; } catch (e) { return 'Guest'; }
  });

  // Listen for IRC nick changes
  useEffect(() => {
    const handleStorage = () => {
      try {
        const nick = localStorage.getItem('devussy_irc_nick');
        if (nick) setIrcNick(nick);
      } catch (e) { }
    };
    window.addEventListener('storage', handleStorage);
    // Also poll for changes since same-tab changes don't trigger storage event
    const interval = setInterval(handleStorage, 1000);
    return () => {
      window.removeEventListener('storage', handleStorage);
      clearInterval(interval);
    };
  }, []);

  // Model Configuration
  const [modelConfigs, setModelConfigs] = useState<ModelConfigs>({
    global: {
      model: 'openai/gpt-5-mini',
      temperature: 0.7,
      reasoning_effort: 'medium',
      concurrency: 3
    },
    interview: null,
    design: null,
    plan: null,
    execute: null,
    handoff: null,
    complexity: null,
    validation: null,
    correction: null
  });

  // Helper to get effective config for current stage
  const getEffectiveConfig = (stage: PipelineStage) => {
    return modelConfigs[stage] || modelConfigs.global;
  };

  // Determine active stage based on active window
  const getActiveStage = (): PipelineStage => {
    const activeWindow = windows.find(w => w.id === activeWindowId);
    if (!activeWindow) return 'global';

    switch (activeWindow.type) {
      case 'interview': return 'interview';
      case 'design': return 'design';
      case 'plan': return 'plan';
      case 'execute': return 'execute';
      case 'handoff': return 'handoff';
      default: return 'global';
    }
  };

  // Checkpoint Handler
  const handleLoadCheckpoint = (data: any) => {
    console.log('[page.tsx] Loading checkpoint:', data.name);

    // Restore project state
    if (data.projectName) setProjectName(data.projectName);
    if (data.languages) setLanguages(data.languages);
    if (data.requirements) setRequirements(data.requirements);
    if (data.design) setDesign(data.design);
    if (data.plan) setPlan(data.plan);

    // Reset auto-run on manual load
    setIsAutoRun(false);

    // Restore windows based on stage
    // We'll clear existing windows and spawn the relevant one
    setWindows([]);

    setTimeout(() => {
      if (data.stage === 'handoff') {
        spawnWindow('handoff', 'Project Handoff');
      } else if (data.stage === 'execute' && data.plan) {
        spawnWindow('execute', 'Execution Phase');
      } else if (data.stage === 'plan' && data.design) {
        spawnWindow('plan', 'Development Plan');
      } else if (data.stage === 'design') {
        spawnWindow('design', 'System Design');
      } else if (data.stage === 'interview') {
        spawnWindow('interview', 'Requirements Interview');
      } else {
        // Default to init if unknown or incomplete
        spawnWindow('init', 'Devussy Studio');
      }
    }, 100);
  };

  // Window Management Functions
  const getWindowSize = (type: WindowType): { width: number; height: number } => {
    switch (type) {
      case 'init':
        return { width: 550, height: 650 };  // Compact, scrollable design
      case 'interview':
        return { width: 700, height: 600 };
      case 'design':
        return { width: 800, height: 700 };
      case 'plan':
        return { width: 900, height: 750 };
      case 'execute':
        return { width: 1200, height: 800 };  // Wide for multi-column
      case 'handoff':
        return { width: 900, height: 800 };
      case 'help':
        return { width: 700, height: 600 };
      case 'model-settings':
        return { width: 500, height: 650 };
      case 'irc':
        return { width: 800, height: 600 };
      case 'pipeline-guide':
        return { width: 900, height: 700 };
      default:
        return { width: 600, height: 400 };
    }
  };

  // Window Management Functions
  const spawnWindow = (type: WindowType, title: string, props?: Record<string, any>, options?: { isMinimized?: boolean }) => {
    const id = `${type}-${Date.now()}`;
    const offset = windows.length * 30;
    const size = getWindowSize(type);
    const newWindow: WindowState = {
      id,
      type,
      title,
      position: { x: 100 + offset, y: 100 + offset },
      zIndex: nextZIndex,
      isMinimized: options?.isMinimized,
      props,
      size
    };

    setWindows(prev => [...prev, newWindow]);
    setNextZIndex(prev => prev + 1);
    if (!options?.isMinimized) {
      setActiveWindowId(id);
    }
  };

  const closeWindow = (id: string) => {
    setWindows(prev => prev.filter(w => w.id !== id));
  };

  const focusWindow = (id: string) => {
    setWindows(prev => prev.map(w =>
      w.id === id ? { ...w, zIndex: nextZIndex } : w
    ));
    setNextZIndex(prev => prev + 1);
    setActiveWindowId(id);
  };

  const toggleMinimize = (id: string) => {
    setWindows(prev => prev.map(w => {
      if (w.id === id) {
        const isNowMinimized = !w.isMinimized;
        // If restoring, bring to front
        if (!isNowMinimized) {
          setActiveWindowId(id);
          return { ...w, isMinimized: false, zIndex: nextZIndex + 1 }; // Increment zIndex locally effectively
        }
        return { ...w, isMinimized: true };
      }
      return w;
    }));

    // If restoring, we need to update global zIndex state too
    const window = windows.find(w => w.id === id);
    if (window && window.isMinimized) {
      setNextZIndex(prev => prev + 1);
    }
  };

  // Pipeline Handlers
  const handleStartInterview = () => {
    setIsAutoRun(false);
    spawnWindow('interview', 'Requirements Interview');
  };

  const handleSkipInterview = () => {
    if (projectName && requirements) {
      spawnWindow('design', 'System Design');
    }
  };

  const handleTryItNow = () => {
    // Set sample project data
    setProjectName("Todo SaaS with Stripe");
    setLanguages("Next.js, TypeScript, TailwindCSS, Supabase, Stripe");
    setRequirements("A modern Todo list SaaS application where users can sign up, create lists, add tasks with due dates, and upgrade to a premium plan via Stripe to unlock unlimited lists and collaboration features. It should have a clean, responsive UI.");

    // Enable auto-run mode
    setIsAutoRun(true);

    // Start the pipeline immediately
    setTimeout(() => {
      spawnWindow('design', 'System Design');
    }, 100);
  };

  const handleInterviewComplete = (data: any) => {
    setProjectName(data.project_name || "");
    setRequirements(data.requirements || "");
    setLanguages(data.primary_language || "");

    spawnWindow('design', 'System Design');
  };

  const handleDesignComplete = (designData: any) => {
    setDesign(designData);
    spawnWindow('plan', 'Development Plan');
  };

  const handlePlanApproved = (planData: any) => {
    console.log('[page.tsx] Plan approved with', planData?.phases?.length, 'phases');
    if (planData?.phases) {
      planData.phases.forEach((p: any, i: number) => {
        if (i < 5) { // Only log first 5
          console.log(`  Phase ${p.number}: ${p.title}`);
        }
      });
    }
    setPlan(planData);
    spawnWindow('execute', 'Execution Phase');
  };

  const handlePhaseComplete = (detailedPlan?: any) => {
    // Update plan with detailed phases if provided
    if (detailedPlan) {
      console.log('[page.tsx] Updating plan with detailed phases');
      setPlan(detailedPlan);
    }
    spawnWindow('handoff', 'Project Handoff');
  };

  const handleRequestDesignRefinement = () => {
    spawnWindow('design-refinement', 'Refine Design');
  };

  const handleRequestPlanRefinement = () => {
    spawnWindow('plan-refinement', 'Refine Plan');
  };

  const handleDesignRefinementComplete = (updatedDesign: any) => {
    console.log('[page.tsx] Design refinement complete, updating design');
    setDesign(updatedDesign);
    // Close refinement window
    setWindows(prev => prev.filter(w => w.type !== 'design-refinement'));
    // Can optionally regenerate plan here or let user do it manually
  };

  const handlePlanRefinementComplete = (updatedPlan: any) => {
    console.log('[page.tsx] Plan refinement complete, updating plan');
    setPlan(updatedPlan);
    // Close refinement window
    setWindows(prev => prev.filter(w => w.type !== 'plan-refinement'));
  };



  const handleNewProject = () => {
    spawnWindow('init', 'New Project');
  };

  const handleHelp = () => {
    // Prevent duplicate help windows
    const existingHelp = windows.find(w => w.type === 'help');
    if (existingHelp) {
      focusWindow(existingHelp.id);
      if (existingHelp.isMinimized) {
        toggleMinimize(existingHelp.id);
      }
      return;
    }
    spawnWindow('help', 'Devussy Studio Help');
  };

  const handleOpenModelSettings = () => {
    // Prevent duplicate model settings windows
    const existing = windows.find(w => w.type === 'model-settings');
    if (existing) {
      focusWindow(existing.id);
      if (existing.isMinimized) {
        toggleMinimize(existing.id);
      }
      return;
    }
    spawnWindow('model-settings', 'AI Model Settings');
  };

  const handleOpenIrc = (options?: { isMinimized?: boolean }) => {
    const existing = windows.find(w => w.type === 'irc');
    if (existing) {
      if (!options?.isMinimized) {
        focusWindow(existing.id);
        if (existing.isMinimized) {
          toggleMinimize(existing.id);
        }
      }
      return;
    }
    spawnWindow('irc', 'IRC Chat – #devussy-chat', undefined, options);
  };

  // Auto-launch IRC (always, minimized)
  useEffect(() => {
    try {
      // Check preference, default to true if not set, or just always do it per requirements
      const autoLaunch = localStorage.getItem('devussy_auto_launch_irc');
      if (autoLaunch !== 'false') {
        // Delay to let page load
        setTimeout(() => {
          handleOpenIrc({ isMinimized: true });
        }, 500);
      }
    } catch (e) { }
  }, []);

  // Help window is now shown by default on startup (init state changed above)
  // This effect is no longer needed

  // Render Content based on Window Type
  const renderWindowContent = (window: WindowState) => {
    switch (window.type) {
      case 'init':
        return (
          <div className="h-full flex flex-col bg-gradient-to-b from-white to-gray-50 overflow-hidden">
            {/* Header Section */}
            <div className="flex-shrink-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 border-b border-blue-700">
              <div className="flex items-center gap-3">
                <Sparkles className="h-7 w-7" />
                <div>
                  <h1 className="text-xl font-bold">New Project</h1>
                  <p className="text-xs text-blue-100">Interview → Design → DevPlan → Handoff Artifacts</p>
                </div>
              </div>
            </div>

            {/* Main Content Area - Scrollable */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {/* Quick Start Section */}
              <div className="bg-white border border-gray-400 rounded p-3 space-y-3 shadow-sm">
                <div className="flex items-center justify-between pb-2 border-b border-gray-300">
                  <h2 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-blue-600" />
                    Quick Start
                  </h2>
                  <button
                    onClick={() => spawnWindow('pipeline-guide', 'Adaptive Pipeline Guide')}
                    className="text-xs text-blue-600 hover:text-blue-800 underline font-semibold"
                  >
                    📖 Pipeline Guide
                  </button>
                </div>
                
                <button
                  onClick={handleTryItNow}
                  className="w-full px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded font-bold text-sm flex items-center justify-center gap-2 shadow-md transition-all hover:shadow-lg"
                >
                  <Play className="w-5 h-5 fill-current" />
                  Try it now (One-click sample)
                </button>
              </div>

              {/* Interactive Interview Section */}
              <div className="bg-white border border-gray-400 rounded p-3 space-y-3 shadow-sm">
                <div className="pb-2 border-b border-gray-300">
                  <h2 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-blue-600" />
                    Guided Setup
                  </h2>
                </div>
                
                <button
                  onClick={handleStartInterview}
                  className="w-full px-4 py-2.5 bg-white border-2 border-blue-500 text-blue-600 rounded font-bold text-sm flex items-center justify-center gap-2 hover:bg-blue-50 transition-colors"
                >
                  <MessageSquare className="w-4 h-4" />
                  Start Interactive Interview
                </button>
              </div>

              {/* Manual Input Section */}
              <div className="bg-white border border-gray-400 rounded p-3 space-y-3 shadow-sm">
                <div className="pb-2 border-b border-gray-300">
                  <h2 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                    <Code2 className="w-4 h-4 text-blue-600" />
                    Manual Configuration
                  </h2>
                </div>

                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label htmlFor="name" className="text-xs font-bold text-gray-700 block">
                      Project Name
                    </label>
                    <input
                      id="name"
                      type="text"
                      placeholder="e.g., E-commerce Platform"
                      value={projectName}
                      onChange={(e) => setProjectName(e.target.value)}
                      className="w-full border border-gray-400 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label htmlFor="languages" className="text-xs font-bold text-gray-700 block">
                      Languages & Stack
                    </label>
                    <input
                      id="languages"
                      type="text"
                      placeholder="Python, Next.js, PostgreSQL..."
                      value={languages}
                      onChange={(e) => setLanguages(e.target.value)}
                      className="w-full border border-gray-400 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label htmlFor="requirements" className="text-xs font-bold text-gray-700 block">
                      Requirements
                    </label>
                    <textarea
                      id="requirements"
                      placeholder="I want a web app that..."
                      value={requirements}
                      onChange={(e) => setRequirements(e.target.value)}
                      rows={4}
                      className="w-full border border-gray-400 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none"
                    />
                  </div>
                </div>
              </div>

              {/* Options Section */}
              <div className="bg-white border border-gray-400 rounded p-3 space-y-3 shadow-sm">
                <div className="pb-2 border-b border-gray-300">
                  <h2 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                    <Settings className="w-4 h-4 text-blue-600" />
                    Options
                  </h2>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded p-3 flex items-center justify-between">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-sm font-bold text-gray-800">YOLO Mode</span>
                    <span className="text-xs text-gray-600">Auto-approve all stages without manual review</span>
                  </div>
                  <YoloModeToggle
                    enabled={yoloMode}
                    onToggle={setYoloMode}
                  />
                </div>
              </div>
            </div>

            {/* Footer Actions */}
            <div className="flex-shrink-0 bg-gray-100 border-t border-gray-400 p-3 space-y-2">
              <button
                onClick={handleSkipInterview}
                disabled={!projectName || !requirements}
                className="w-full px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded font-bold text-sm flex items-center justify-center gap-2 shadow transition-colors"
              >
                Skip Interview & Initialize
                <ArrowRight className="w-4 h-4" />
              </button>
              <p className="text-xs text-center text-gray-600">
                Works with OpenAI / generic OpenAI-compatible / Requesty / Aether / AgentRouter
              </p>
            </div>
          </div>
        );
      case 'interview':
        return (
          <InterviewView
            modelConfig={getEffectiveConfig('interview')}
            onInterviewComplete={handleInterviewComplete}
          />
        );
      case 'design':
        return (
          <DesignView
            projectName={projectName}
            requirements={requirements}
            languages={languages.split(',').map(l => l.trim()).filter(Boolean)}
            modelConfig={getEffectiveConfig('design')}
            onDesignComplete={handleDesignComplete}
            onRequestRefinement={handleRequestDesignRefinement}
            autoRun={isAutoRun}
            enableAdaptive={true}
            yoloMode={yoloMode}
            onYoloModeChange={setYoloMode}
          />
        );
      case 'design-refinement':
        return (
          <DesignRefinementView
            design={design}
            projectName={projectName}
            requirements={requirements}
            languages={languages.split(',').map(l => l.trim()).filter(Boolean)}
            onRefinementComplete={handleDesignRefinementComplete}
            onCancel={() => setWindows(prev => prev.filter(w => w.type !== 'design-refinement'))}
          />
        );
      case 'plan':
        return (
          <PlanView
            design={design}
            onPlanApproved={handlePlanApproved}
            onRequestRefinement={handleRequestPlanRefinement}
            modelConfig={getEffectiveConfig('plan')}
            autoRun={isAutoRun}
            yoloMode={yoloMode}
          />
        );
      case 'plan-refinement':
        return (
          <PlanRefinementView
            plan={plan}
            design={design}
            projectName={projectName}
            onRefinementComplete={handlePlanRefinementComplete}
            onCancel={() => setWindows(prev => prev.filter(w => w.type !== 'plan-refinement'))}
          />
        );
      case 'execute':
        return (
          <ExecutionView
            plan={plan}
            projectName={projectName}
            modelConfig={getEffectiveConfig('execute')}
            onComplete={handlePhaseComplete}
            autoRun={isAutoRun}
          />
        );
      case 'handoff':
        return (
          <HandoffView
            design={design}
            plan={plan}
            modelConfig={getEffectiveConfig('handoff')}
          />
        );
      case 'model-settings':
        return (
          <ModelSettings
            configs={modelConfigs}
            onConfigsChange={setModelConfigs}
            activeStage={getActiveStage()}
            isWindowMode={true}
          />
        );
      case 'help':
        return (
          <div className="h-full overflow-auto p-6 prose prose-invert max-w-none" style={{ backgroundColor: '#1C2125' }}>
            {/* Devussy Logo with matching background */}
            <div className="flex justify-center mb-6 -mx-6 -mt-6 px-6 pt-6 pb-6" style={{ backgroundColor: '#1C2125' }}>
              <img 
                src="/devussy_logo_minimal.png" 
                alt="Devussy Logo" 
                className="w-full h-auto object-contain"
                style={{ maxWidth: '1344px' }}
              />
            </div>
            
            <h1 className="text-2xl font-bold mb-4">Devussy Studio Help</h1>
            <div className="rounded-md p-3 bg-background/80 text-sm text-muted-foreground mb-4">
              <strong className="text-primary">Public Demo:</strong> This is a limited time public demo for Devussy. It is in constant development and things may break at times, but we're working on it! Please avoid putting any sensitive secrets here. Thank you for trying Devussy Studio.
            </div>

            <div className="rounded-md p-4 bg-primary/10 border border-primary/20 mb-6">
              <h2 className="text-lg font-semibold mb-2 flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                GitHub Repository
              </h2>
              <p className="text-sm mb-3">
                For full documentation, installation instructions, and the complete codebase:
              </p>
              <a
                href="https://github.com/mojomast/devussy"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium text-sm no-underline"
              >
                <GitBranch className="h-4 w-4" />
                Visit GitHub Repository
              </a>
            </div>

            <h2 className="text-xl font-semibold mt-6 mb-3">🚀 Getting Started with Devussy</h2>
            <p className="mb-4">
              Devussy is both a <strong>software tool</strong> and a <strong>methodology</strong> for creating stateless, agent-agnostic development plans that work across humans and AI coding assistants.
            </p>

            <h2 className="text-xl font-semibold mt-6 mb-3">🎯 How to Use This Frontend</h2>
            <div className="rounded-md p-4 bg-blue-500/10 border border-blue-500/20 mb-4">
              <h3 className="text-lg font-semibold mb-3">Step-by-Step Pipeline Process:</h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center font-bold text-sm">1</div>
                  <div className="flex-1">
                    <strong className="block mb-1">Start a New Project</strong>
                    <p className="text-muted-foreground">
                      Click <strong>"+ NEW"</strong> from the taskbar at the bottom of the screen (or from the <strong>Start Menu</strong> if using Bliss theme). 
                      Then choose <strong>"Try it now"</strong> to run a sample project, or fill out the form with your project name, tech stack, and requirements. 
                      You can also click <strong>"Start Interactive Interview"</strong> for a guided Q&A session.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center font-bold text-sm">2</div>
                  <div className="flex-1">
                    <strong className="block mb-1">Design Generation</strong>
                    <p className="text-muted-foreground">
                      The system generates a system architecture using AI. Review the design and click <strong>"Approve Design"</strong> to continue, 
                      or click <strong>"Refine Design"</strong> to discuss improvements with the AI.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center font-bold text-sm">3</div>
                  <div className="flex-1">
                    <strong className="block mb-1">Development Plan Generation</strong>
                    <p className="text-muted-foreground">
                      Review the generated phases and click <strong>"Approve & Continue"</strong> to generate detailed phase documents. 
                      Enable <strong>YOLO Mode</strong> in settings to skip manual approval steps.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center font-bold text-sm">4</div>
                  <div className="flex-1">
                    <strong className="block mb-1">Phase Execution</strong>
                    <p className="text-muted-foreground">
                      Watch as detailed plans are generated for each phase in parallel. The system creates comprehensive phase documents 
                      with tasks, acceptance criteria, and implementation details.
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center font-bold text-sm">5</div>
                  <div className="flex-1">
                    <strong className="block mb-1">Download Artifacts</strong>
                    <p className="text-muted-foreground">
                      Click <strong>"Download Project Artifacts"</strong> to get a ZIP file containing all your project documentation. 
                      This is what you'll use for circular development!
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-3 bg-primary/10 rounded border border-primary/20">
                <p className="text-xs">
                  <strong>💡 Pro Tip:</strong> Use the <strong>Model Settings</strong> button (gear icon in taskbar) to configure different AI models 
                  for each stage. Adjust <strong>concurrency</strong> to control how many phases generate in parallel.
                </p>
              </div>
            </div>

            <div className="rounded-md p-4 bg-yellow-500/10 border border-yellow-500/20 mb-4">
              <h3 className="text-lg font-semibold mb-2">📦 What You Get (The Artifacts)</h3>
              <p className="mb-2">
                At the end of the pipeline, you'll download a ZIP file containing:
              </p>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li><code className="bg-gray-800 px-2 py-1 rounded">handoff.md</code> - The single source of truth for what to do next</li>
                <li><code className="bg-gray-800 px-2 py-1 rounded">devplan.md</code> - Complete project plan with anchored sections</li>
                <li><code className="bg-gray-800 px-2 py-1 rounded">phase*.md</code> - Per-phase detailed plans (e.g., phase1.md, phase2.md)</li>
                <li><code className="bg-gray-800 px-2 py-1 rounded">design.md</code> - System architecture and design document</li>
              </ul>
            </div>

            <h2 className="text-xl font-semibold mt-6 mb-3">🔄 Using Devussy: Circular Development</h2>
            <p className="mb-4">
              <strong>The key principle:</strong> Put the downloaded files in a folder and tell <strong>ANY</strong> AI coding assistant (ChatGPT, Claude, Gemini, Cursor, Roo Code, etc.):
            </p>
            <div className="rounded-md p-4 bg-green-500/10 border border-green-500/20 mb-4">
              <code className="text-sm block">"Read handoff.md and start working on the tasks it describes"</code>
            </div>

            <h3 className="text-lg font-semibold mt-4 mb-2">How Circular Development Works:</h3>
            <ol className="list-decimal list-inside space-y-3 mb-4">
              <li>
                <strong>Agent Reads handoff.md</strong> - Learns what part of which phase to focus on
              </li>
              <li>
                <strong>Agent Does the Work</strong> - Implements features, writes code, etc.
              </li>
              <li>
                <strong>Agent Updates Phase Doc</strong> - Records discoveries and blockers in phase*.md
              </li>
              <li>
                <strong>Agent Updates DevPlan</strong> - Updates anchored sections in devplan.md (constraints, risks, timeline)
              </li>
              <li>
                <strong>Agent Updates Handoff</strong> - Modifies handoff.md to point next agent to next slice of work
              </li>
              <li>
                <strong>Handoff to Next Agent</strong> - Pass the updated files to another agent (or new context window)
              </li>
            </ol>

            <div className="rounded-md p-4 bg-blue-500/10 border border-blue-500/20 mb-4">
              <h3 className="text-lg font-semibold mb-2">🎯 The Three Artifacts That Travel Together</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-600">
                    <th className="text-left py-2">Artifact</th>
                    <th className="text-left py-2">Purpose</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-700">
                    <td className="py-2"><code className="bg-gray-800 px-2 py-1 rounded">handoff.md</code></td>
                    <td className="py-2">Single source of truth for "what to do next"</td>
                  </tr>
                  <tr className="border-b border-gray-700">
                    <td className="py-2"><code className="bg-gray-800 px-2 py-1 rounded">devplan.md</code></td>
                    <td className="py-2">Full project context with anchored sections</td>
                  </tr>
                  <tr>
                    <td className="py-2"><code className="bg-gray-800 px-2 py-1 rounded">phase*.md</code></td>
                    <td className="py-2">Phase-specific progress and decisions</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h3 className="text-lg font-semibold mt-4 mb-2">💡 Real Example Flow:</h3>
            <div className="rounded-md p-4 bg-gray-800/50 mb-4 text-sm font-mono">
              <p className="mb-2">Agent A:</p>
              <ul className="list-none space-y-1 ml-4 text-xs">
                <li>└─ Reads: handoff.md ("Work on Phase 1, tasks 1-3")</li>
                <li>└─ Discovers: "We need 3× more compute than planned"</li>
                <li>└─ Updates: phase1.md (adds discovery notes)</li>
                <li>└─ Updates: devplan.md (updates progress log anchor)</li>
                <li>└─ Updates: handoff.md ("Next: Phase 2, task 1 with 3× compute")</li>
              </ul>
              <p className="mt-3 mb-2">Agent B receives:</p>
              <ul className="list-none space-y-1 ml-4 text-xs">
                <li>├─ handoff.md (knows to work on Phase 2 with compute constraint)</li>
                <li>├─ devplan.md (sees updated compute requirement)</li>
                <li>└─ phase1.md (sees Phase 1 discoveries)</li>
              </ul>
            </div>

            <h2 className="text-xl font-semibold mt-6 mb-3">🎨 Web UI Pipeline Stages</h2>
            <ol className="list-decimal list-inside space-y-2 mb-4">
              <li><strong>Interview</strong> - Interactive chat to gather requirements</li>
              <li><strong>Design</strong> - Generate system architecture (with validation)</li>
              <li><strong>Plan</strong> - Create detailed development plan with phases</li>
              <li><strong>Execute</strong> - Generate phase-specific detailed plans</li>
              <li><strong>Handoff</strong> - Download artifacts and start circular development</li>
            </ol>

            <h2 className="text-xl font-semibold mt-6 mb-3">✨ Key Benefits</h2>
            <ul className="list-disc list-inside space-y-2 mb-4">
              <li><strong>🔄 Reusable</strong> - One plan works across humans and LLMs</li>
              <li><strong>📦 Portable</strong> - Export as plain markdown, no runtime state</li>
              <li><strong>🤖 Agent-agnostic</strong> - Switch between any AI provider freely</li>
              <li><strong>🔗 No vendor lock-in</strong> - Works with ChatGPT, Claude, Gemini, Cursor, etc.</li>
              <li><strong>📊 Full context</strong> - Every handoff contains everything needed</li>
              <li><strong>⚡ Parallel work</strong> - Multiple agents can work on different phases</li>
            </ul>

            <h2 className="text-xl font-semibold mt-6 mb-3">💻 IRC Chat Addon</h2>
            <p className="mb-2">Devussy includes a built-in IRC client accessible via the taskbar or desktop icon.</p>
            <ul className="list-disc list-inside space-y-1 mb-4">
              <li>Join <code className="bg-gray-800 px-2 py-1 rounded">#devussy-chat</code> to chat with other users</li>
              <li>Click on usernames to start private messages</li>
              <li>Your IRC nickname is saved automatically</li>
            </ul>

            <h2 className="text-xl font-semibold mt-6 mb-3">🔧 Tips & Features</h2>
            <ul className="list-disc list-inside space-y-1 mb-4">
              <li>Use <strong>checkpoints</strong> to save your progress at any stage</li>
              <li>Enable <strong>YOLO Mode</strong> to auto-approve all stages without manual review</li>
              <li>Adjust <strong>concurrency</strong> in model settings to control parallel execution</li>
              <li>Windows can be minimized - find them in the taskbar</li>
              <li>Use the <strong>Start Menu</strong> (Bliss theme) or taskbar to access all features</li>
            </ul>

            <h2 className="text-xl font-semibold mt-6 mb-3">📚 Learn More</h2>
            <div className="space-y-2 mb-6">
              <p>
                <a
                  href="https://github.com/mojomast/devussy#readme"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline font-medium"
                >
                  → Full README with Installation & CLI Usage
                </a>
              </p>
              <p>
                <a
                  href="https://github.com/mojomast/devussy/blob/main/AGENTS.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline font-medium"
                >
                  → AGENTS.md - Critical guidance for AI agents
                </a>
              </p>
              <p className="text-sm text-muted-foreground">
                Check the <code className="bg-gray-800 px-2 py-1 rounded">handoff.md</code> file in your downloaded artifacts for detailed technical documentation.
              </p>
            </div>

            <h2 className="text-xl font-semibold mt-6 mb-3">👨‍💻 Credits</h2>
            <p className="mb-2">Created by <strong>Kyle Durepos</strong>.</p>
            <p className="text-sm text-muted-foreground italic">
              "We out here shippin' code and slammin' Cadillac doors. BRRRRRRRRRRRRRRRRRRRRRRRRRR"
            </p>

            <div className="mt-6 flex items-center justify-between">
              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={dontShowHelpAgain}
                    onChange={(e) => {
                      const v = e.target.checked;
                      try { localStorage.setItem('devussy_help_dismissed', v ? '1' : '0'); } catch (err) { }
                      setDontShowHelpAgain(v);
                    }}
                  />
                  Don't show this again
                </label>
                <label className="flex items-center gap-2 text-xs text-muted-foreground">
                  <input
                    type="checkbox"
                    checked={analyticsOptOut}
                    onChange={(e) => {
                      const v = e.target.checked;
                      try {
                        const expires = new Date();
                        expires.setFullYear(expires.getFullYear() + 1);
                        document.cookie = `devussy_analytics_optout=${v ? '1' : '0'}; path=/; expires=${expires.toUTCString()}; SameSite=Lax`;
                      } catch (err) { }
                      setAnalyticsOptOut(v);
                    }}
                  />
                  Disable anonymous usage analytics for this browser
                </label>
              </div>
              <div>
                <Button variant="secondary" onClick={() => closeWindow(window.id)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        );
      case 'irc':
        return <IrcClient />;
      case 'pipeline-guide':
        return (
          <div className="h-full overflow-auto p-6">
            <div className="mb-6">
              <h1 className="text-2xl font-bold mb-2">Adaptive Pipeline Architecture</h1>
              <p className="text-sm text-muted-foreground">
                Devussy's 7-stage pipeline adapts to project complexity, from tiny prototypes to enterprise systems.
              </p>
            </div>
            <PipelineOverview currentStage={0} compact={false} />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <main className="flex min-h-screen flex-col relative bg-transparent overflow-hidden">
      {/* Desktop Icons */}
      {theme === 'bliss' && (
        <div className="absolute top-4 left-4 z-0 flex flex-col gap-6 p-4">
          {/* My Computer */}
          <button
            className="group flex flex-col items-center w-[70px] gap-1 focus:outline-none"
            onDoubleClick={handleNewProject}
          >
            <div className="w-12 h-12 relative">
              <img src="/devussy_logo_minimal.png" className="w-full h-full object-contain drop-shadow-md" />
            </div>
            <span className="text-white text-xs font-medium px-1 rounded group-hover:bg-[#0B61DE] group-focus:bg-[#0B61DE] group-focus:border group-focus:border-dotted drop-shadow-md text-center leading-tight">
              My Computer
            </span>
          </button>

          {/* mIRC */}
          <button
            className="group flex flex-col items-center w-[70px] gap-1 focus:outline-none"
            onDoubleClick={() => handleOpenIrc()}
          >
            <div className="w-12 h-12 relative bg-white/10 rounded-lg border border-white/20 flex items-center justify-center shadow-lg backdrop-blur-sm">
              {/* Custom mIRC-like icon since we don't have the asset */}
              <div className="relative w-8 h-8">
                <div className="absolute inset-0 bg-red-500 rounded-full transform -rotate-12 opacity-80"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <MessageSquare className="text-white w-5 h-5 transform rotate-12" fill="currentColor" />
                </div>
                <div className="absolute -bottom-1 -right-1 bg-green-500 w-3 h-3 rounded-full border-2 border-white"></div>
              </div>
            </div>
            <span className="text-white text-xs font-medium px-1 rounded group-hover:bg-[#0B61DE] group-focus:bg-[#0B61DE] group-focus:border group-focus:border-dotted drop-shadow-md text-center leading-tight">
              mIRC
            </span>
          </button>
        </div>
      )}

      {/* Global Header / Toolbar (Optional) */}
      {theme !== 'bliss' && (
        <div className="absolute top-4 right-4 z-50 flex items-center gap-2">
          <ThemeToggle />
          <CheckpointManager
            currentState={{
              projectName,
              languages,
              requirements,
              design,
              plan,
              stage: getActiveStage()
            }}
            onLoad={handleLoadCheckpoint}
          />
          <ModelSettings
            configs={modelConfigs}
            onConfigsChange={setModelConfigs}
            activeStage={getActiveStage()}
          />
        </div>
      )}

      {windows.map((window) => (
        <WindowFrame
          key={window.id}
          title={window.title}
          initialPosition={window.position}
          initialSize={window.size}
          isActive={activeWindowId === window.id}
          isMinimized={window.isMinimized}
          onFocus={() => focusWindow(window.id)}
          onClose={() => closeWindow(window.id)}
          onMinimize={() => toggleMinimize(window.id)}
          className="absolute"
          style={{ zIndex: window.zIndex }}
        >
          {renderWindowContent(window)}
        </WindowFrame>
      ))}

      <Taskbar
        windows={windows.map(w => ({ id: w.id, title: w.title, type: w.type }))}
        activeWindowId={activeWindowId}
        minimizedWindowIds={windows.filter(w => w.isMinimized).map(w => w.id)}
        onWindowClick={(id) => {
          const win = windows.find(w => w.id === id);
          if (win?.isMinimized) {
            toggleMinimize(id);
          } else {
            focusWindow(id);
          }
        }}
        onNewProject={handleNewProject}
        onHelp={handleHelp}
        onOpenModelSettings={handleOpenModelSettings}
        onOpenIrc={() => handleOpenIrc()}
        currentState={{
          projectName,
          languages,
          requirements,
          design,
          plan,
          stage: getActiveStage()
        }}
        onLoadCheckpoint={handleLoadCheckpoint}
        modelConfigs={modelConfigs}
        onModelConfigsChange={setModelConfigs}
        activeStage={getActiveStage()}
        ircNick={ircNick}
      />
    </main>
  );
}
