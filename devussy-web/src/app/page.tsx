"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ArrowRight, Sparkles, Layers, Code2, GitBranch, MessageSquare, Zap, Play } from "lucide-react";
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

type WindowType = 'init' | 'interview' | 'design' | 'plan' | 'execute' | 'handoff' | 'help' | 'model-settings' | 'irc';

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
    { id: 'init-1', type: 'init', title: 'Devussy Studio', position: { x: 50, y: 50 }, zIndex: 10 }
  ]);
  const [activeWindowId, setActiveWindowId] = useState<string>('init-1');
  const [nextZIndex, setNextZIndex] = useState(20);

  // Project State (Shared across windows)
  const [projectName, setProjectName] = useState("");
  const [languages, setLanguages] = useState("");
  const [requirements, setRequirements] = useState("");

  // Auto-run State
  const [isAutoRun, setIsAutoRun] = useState(false);

  // Pipeline Data
  const [design, setDesign] = useState<any>(null);
  const [plan, setPlan] = useState<any>(null);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);

  // Help preferences
  const [dontShowHelpAgain, setDontShowHelpAgain] = useState<boolean>(() => {
    try { return localStorage.getItem('devussy_help_dismissed') === '1'; } catch (e) { return false; }
  });

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
    handoff: null
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
        return { width: 800, height: 750 };  // Fits form content comfortably
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

  // Auto-open Help modal on the first visit (unless dismissed)
  useEffect(() => {
    try {
      const dismissed = localStorage.getItem('devussy_help_dismissed');
      const seen = localStorage.getItem('devussy_seen_help');
      if (!dismissed && !seen) {
        // Delay slightly to allow initial window to render
        setTimeout(() => {
          handleHelp();
          try { localStorage.setItem('devussy_seen_help', '1'); } catch (e) { }
        }, 300);
      }
    } catch (e) {
      // localStorage might be unavailable; ignore silently
    }
  }, []);

  // Render Content based on Window Type
  const renderWindowContent = (window: WindowState) => {
    switch (window.type) {
      case 'init':
        return (
          <div className="h-full flex items-center justify-center p-8">
            <Card className="w-full max-w-md border-primary/10 shadow-2xl">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <Sparkles className="h-6 w-6 text-primary" />
                  New Project
                </CardTitle>
                <CardDescription>
                  Interview → Project design → DevPlan phases → Handoff Markdown artifacts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  className="w-full font-bold bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white border-0"
                  size="lg"
                  onClick={handleTryItNow}
                >
                  <Play className="mr-2 h-5 w-5 fill-current" />
                  Try it now (One-click sample)
                </Button>

                <div className="relative py-2">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-background px-2 text-muted-foreground">Or Start Fresh</span>
                  </div>
                </div>

                <Button
                  className="w-full font-bold"
                  variant="outline"
                  size="lg"
                  onClick={handleStartInterview}
                >
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Start Interactive Interview
                </Button>

                <div className="relative py-2">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-background px-2 text-muted-foreground">Or Manual Input</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="name" className="text-sm font-medium">Project Name</label>
                  <Input
                    id="name"
                    placeholder="e.g., E-commerce Platform"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="languages" className="text-sm font-medium">Languages & Stack</label>
                  <Input
                    id="languages"
                    placeholder="Python, Next.js, PostgreSQL..."
                    value={languages}
                    onChange={(e) => setLanguages(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="requirements" className="text-sm font-medium">Requirements</label>
                  <Textarea
                    id="requirements"
                    placeholder="I want a web app that..."
                    className="min-h-[100px]"
                    value={requirements}
                    onChange={(e) => setRequirements(e.target.value)}
                  />
                </div>
              </CardContent>
              <CardFooter className="flex flex-col gap-2">
                <Button
                  className="w-full"
                  variant="secondary"
                  onClick={handleSkipInterview}
                  disabled={!projectName || !requirements}
                >
                  Skip Interview & Initialize <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                <p className="text-xs text-center text-muted-foreground mt-2">
                  Works with OpenAI / generic OpenAI-compatible / Requesty / Aether / AgentRouter
                </p>
              </CardFooter>
            </Card>
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
            autoRun={isAutoRun}
          />
        );
      case 'plan':
        return (
          <PlanView
            design={design}
            onPlanApproved={handlePlanApproved}
            modelConfig={getEffectiveConfig('plan')}
            autoRun={isAutoRun}
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
          <div className="h-full overflow-auto p-6 prose prose-invert max-w-none">
            <h1 className="text-2xl font-bold mb-4">Devussy Studio Help</h1>
            <div className="rounded-md p-3 bg-background/80 text-sm text-muted-foreground mb-4">
              <strong className="text-primary">Public Demo:</strong> This is a limited time public demo for Devussy. It is in constant development and things may break at times, but we're working on it! Please avoid putting any sensitive secrets here. Thank you for trying Devussy Studio.
            </div>

            <h2 className="text-xl font-semibold mt-6 mb-3">Getting Started</h2>
            <p>Devussy Studio is an AI-powered development pipeline that takes you from requirements to deployment-ready code.</p>

            <h3 className="text-lg font-semibold mt-4 mb-2">Pipeline Stages:</h3>
            <ol className="list-decimal list-inside space-y-2">
              <li><strong>Interview</strong> - Interactive chat to gather requirements</li>
              <li><strong>Design</strong> - Generate system architecture and design</li>
              <li><strong>Plan</strong> - Create detailed development plan with phases</li>
              <li><strong>Execute</strong> - Generate code for each phase</li>
              <li><strong>Handoff</strong> - Export project and push to GitHub</li>
            </ol>
            <h2 className="text-xl font-semibold mt-6 mb-3">Circular Stateless Development</h2>
            <p>Devussy enables <strong>agent-agnostic, stateless development</strong> where any AI agent can pick up where another left off.</p>

            <h3 className="text-lg font-semibold mt-4 mb-2">How It Works:</h3>
            <ol className="list-decimal list-inside space-y-2">
              <li><strong>Generate Plan</strong> - Use Devussy to create a comprehensive development plan</li>
              <li><strong>Export Handoff</strong> - Download the plan, design, and context as a zip file</li>
              <li><strong>Share with Any Agent</strong> - Give the handoff document to any AI coding assistant (Claude, GPT, Gemini, etc.)</li>
              <li><strong>Agent Reads Context</strong> - Tell the agent: <code className="bg-gray-800 px-2 py-1 rounded">"Read the handoff.md file and implement the next phase"</code></li>
              <li><strong>Iterate</strong> - Different agents can work on different phases, all following the same plan</li>
            </ol>
            <h3 className="text-lg font-semibold mt-4 mb-2">Key Benefits:</h3>
            <ul className="list-disc list-inside space-y-1">
              <li>✅ <strong>No vendor lock-in</strong> - Switch between AI providers freely</li>
              <li>✅ <strong>Consistent quality</strong> - All agents follow the same plan</li>
              <li>✅ <strong>Parallel development</strong> - Multiple agents can work on different phases</li>
              <li>✅ <strong>Full context</strong> - Handoff document contains everything needed</li>
            </ul>
            <h2 className="text-xl font-semibold mt-6 mb-3">Tips</h2>
            <ul className="list-disc list-inside space-y-1">
              <li>Use <strong>checkpoints</strong> to save your progress at any stage</li>
              <li>Edit phases in the Plan view before execution</li>
              <li>Adjust <strong>concurrency</strong> in settings to control parallel execution</li>
              <li>Windows can be minimized but not closed - find them in the taskbar</li>
            </ul>
            <h2 className="text-xl font-semibold mt-6 mb-3">Need More Help?</h2>
            <p>Check the <code className="bg-gray-800 px-2 py-1 rounded">handoff.md</code> file in your project for detailed technical documentation.</p>

            <h2 className="text-xl font-semibold mt-6 mb-3">Credits</h2>
            <p>Created by <strong>Kyle Durepos</strong>.</p>

            <div className="mt-6 flex items-center justify-between">
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
      default:
        return null;
    }
  };

  return (
    <main className="flex min-h-screen flex-col relative bg-transparent">
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
      />
    </main>
  );
}
