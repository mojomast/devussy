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
import { AppRegistry } from "@/apps/AppRegistry";
import { EventBusProvider, useEventBus } from "@/apps/eventBus";
import { decodeSharePayload, type ShareLinkPayload } from "@/shareLinks";

type WindowType = keyof typeof AppRegistry;

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

function PageInner() {
  const { theme } = useTheme();
  const bus = useEventBus();
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
        spawnAppWindow('handoff', 'Project Handoff');
      } else if (data.stage === 'execute' && data.plan) {
        spawnAppWindow('execute', 'Execution Phase');
      } else if (data.stage === 'plan' && data.design) {
        spawnAppWindow('plan', 'Development Plan');
      } else if (data.stage === 'design') {
        spawnAppWindow('design', 'System Design');
      } else if (data.stage === 'interview') {
        spawnAppWindow('interview', 'Requirements Interview');
      } else {
        // Default to init if unknown or incomplete
        spawnAppWindow('init', 'Devussy Studio');
      }
    }, 100);
  };

  useEffect(() => {
    const unsubscribe = bus.subscribe('openShareLink', (payload: any) => {
      try {
        const sharePayload = payload as ShareLinkPayload;
        if (!sharePayload) return;

        const checkpointLike = {
          ...(sharePayload.data || {}),
          stage:
            sharePayload.stage ||
            (sharePayload.data && (sharePayload.data as any).stage),
        };

        handleLoadCheckpoint(checkpointLike);
      } catch (e) {
        console.error('[page.tsx] Error handling openShareLink event', e);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [bus]);

  useEffect(() => {
    try {
      if (typeof window === 'undefined') return;
      const key = 'devussy_share_payload';
      const encoded = window.sessionStorage.getItem(key);
      if (!encoded) return;

      window.sessionStorage.removeItem(key);
      const decoded = decodeSharePayload(encoded);
      if (!decoded) return;

      const checkpointLike = {
        ...(decoded.data || {}),
        stage: decoded.stage || (decoded.data && (decoded.data as any).stage),
      };

      handleLoadCheckpoint(checkpointLike);
    } catch (e) {
      console.error(
        '[page.tsx] Failed to restore from share payload in sessionStorage',
        e,
      );
    }
  }, []);

  // Window Management Functions
  const getWindowSize = (type: WindowType): { width: number; height: number } => {
    const appDef = AppRegistry[type];
    if (appDef && appDef.defaultSize) {
      return appDef.defaultSize;
    }
    return { width: 600, height: 400 };
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

  const spawnAppWindow = (appId: WindowType, title: string, props?: Record<string, any>, options?: { isMinimized?: boolean }) => {
    spawnWindow(appId, title, props, options);
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
    spawnAppWindow('interview', 'Requirements Interview');
  };

  const handleSkipInterview = () => {
    if (projectName && requirements) {
      spawnAppWindow('design', 'System Design');
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
      spawnAppWindow('design', 'System Design');
    }, 100);
  };

  const handleInterviewComplete = (data: any) => {
    setProjectName(data.project_name || "");
    setRequirements(data.requirements || "");
    setLanguages(data.primary_language || "");

    spawnAppWindow('design', 'System Design');
  };

  const handleDesignComplete = (designData: any) => {
    setDesign(designData);
    spawnAppWindow('plan', 'Development Plan');
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
    try {
      bus.emit('planGenerated', {
        projectName,
        languages,
        requirements,
        plan: planData,
        phaseCount: planData?.phases?.length || 0,
      });
    } catch (e) {
      console.error('[page.tsx] Error emitting planGenerated event', e);
    }
    spawnAppWindow('execute', 'Execution Phase');
  };

  const handlePhaseComplete = (detailedPlan?: any) => {
    // Update plan with detailed phases if provided
    if (detailedPlan) {
      console.log('[page.tsx] Updating plan with detailed phases');
      setPlan(detailedPlan);
    }
    spawnAppWindow('handoff', 'Project Handoff');
  };



  const handleNewProject = () => {
    spawnAppWindow('init', 'New Project');
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
    spawnAppWindow('help', 'Devussy Studio Help');
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
    spawnAppWindow('model-settings', 'AI Model Settings');
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
    spawnAppWindow('irc', 'IRC Chat – #devussy-chat', undefined, options);
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
  const renderAppContent = (window: WindowState) => {
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
      case 'model-settings': {
        const appDef = AppRegistry[window.type];
        if (appDef && appDef.component) {
          const Component = appDef.component as React.FC<any>;
          return (
            <Component
              configs={modelConfigs}
              onConfigsChange={setModelConfigs}
              activeStage={getActiveStage()}
              {...(window.props || {})}
            />
          );
        }
        return null;
      }
      case 'help': {
        const appDef = AppRegistry[window.type];
        if (appDef && appDef.component) {
          const Component = appDef.component as React.FC<any>;
          return (
            <Component
              dontShowHelpAgain={dontShowHelpAgain}
              setDontShowHelpAgain={setDontShowHelpAgain}
              analyticsOptOut={analyticsOptOut}
              setAnalyticsOptOut={setAnalyticsOptOut}
              onClose={() => closeWindow(window.id)}
              {...(window.props || {})}
            />
          );
        }
        return null;
      }
      case 'irc': {
        const appDef = AppRegistry[window.type];
        if (appDef && appDef.component) {
          const Component = appDef.component as React.FC<any>;
          return <Component {...(window.props || {})} />;
        }
        return null;
      }
      default: {
        const appDef = AppRegistry[window.type];
        if (appDef && appDef.component) {
          const Component = appDef.component as React.FC<any>;
          return <Component {...(window.props || {})} />;
        }
        return null;
      }
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
          {renderAppContent(window)}
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
        onOpenApp={(appId) => {
          switch (appId) {
            case 'init':
              handleNewProject();
              break;
            case 'interview':
              handleStartInterview();
              break;
            case 'design':
              spawnAppWindow('design', 'System Design');
              break;
            case 'plan':
              spawnAppWindow('plan', 'Development Plan');
              break;
            case 'execute':
              spawnAppWindow('execute', 'Execution Phase');
              break;
            case 'handoff':
              spawnAppWindow('handoff', 'Project Handoff');
              break;
            case 'help':
              handleHelp();
              break;
            case 'model-settings':
              handleOpenModelSettings();
              break;
            case 'irc':
              handleOpenIrc();
              break;
            default: {
              const appDef = AppRegistry[appId as WindowType];
              const title = appDef?.name || 'Devussy App';
              spawnAppWindow(appId as WindowType, title);
            }
          }
        }}
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

export default function Page() {
  return (
    <EventBusProvider>
      <PageInner />
    </EventBusProvider>
  );
}
