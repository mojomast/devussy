"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ArrowRight, Sparkles, Layers, Code2, GitBranch, MessageSquare } from "lucide-react";
import { WindowFrame } from "@/components/window/WindowFrame";
import { DesignView } from "@/components/pipeline/DesignView";
import { PlanView } from "@/components/pipeline/PlanView";
import { ExecutionView } from "@/components/pipeline/ExecutionView";
import { HandoffView } from "@/components/pipeline/HandoffView";
import { InterviewView } from "@/components/pipeline/InterviewView";
import { HiveMindView } from "@/components/pipeline/HiveMindView";
import { ModelSettings, ModelConfigs, PipelineStage } from "@/components/pipeline/ModelSettings";
import { CheckpointManager } from "@/components/pipeline/CheckpointManager";
import { Taskbar } from "@/components/window/Taskbar";

type WindowType = 'init' | 'interview' | 'design' | 'plan' | 'execute' | 'handoff' | 'hivemind' | 'help';

interface WindowState {
  id: string;
  type: WindowType;
  title: string;
  position: { x: number; y: number };
  zIndex: number;
  isMinimized?: boolean;
  props?: any;
  size?: { width: number; height: number };
}

export default function Page() {
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

  // Pipeline Data
  const [design, setDesign] = useState<any>(null);
  const [plan, setPlan] = useState<any>(null);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);

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
        return { width: 800, height: 700 };  // Fits form content comfortably
      case 'interview':
        return { width: 700, height: 600 };
      case 'design':
        return { width: 800, height: 700 };
      case 'plan':
        return { width: 900, height: 750 };
      case 'execute':
        return { width: 1200, height: 800 };  // Wide for multi-column
      case 'handoff':
        return { width: 800, height: 700 };
      case 'hivemind':
        return { width: 1000, height: 700 };
      case 'help':
        return { width: 700, height: 600 };
      default:
        return { width: 600, height: 400 };
    }
  };

  // Window Management Functions
  const spawnWindow = (type: WindowType, title: string, props?: any) => {
    const id = `${type}-${Date.now()}`;
    const offset = windows.length * 30;
    const size = getWindowSize(type);
    const newWindow: WindowState = {
      id,
      type,
      title,
      position: { x: 100 + offset, y: 100 + offset },
      zIndex: nextZIndex,
      props,
      size
    };

    setWindows(prev => [...prev, newWindow]);
    setNextZIndex(prev => prev + 1);
    setActiveWindowId(id);
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
    spawnWindow('interview', 'Requirements Interview');
  };

  const handleSkipInterview = () => {
    if (projectName && requirements) {
      spawnWindow('design', 'System Design');
    }
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

  const handleSpawnHiveMind = (phase: any, plan: any, projectName: string) => {
    spawnWindow('hivemind', `HiveMind: Phase ${phase.number}`, {
      phase,
      plan,
      projectName
    });
  };

  const handleSpawnDesignHiveMind = () => {
    spawnWindow('hivemind', 'HiveMind: Design', {
      type: 'design',
      projectName,
      requirements,
      languages: languages.split(',').map(l => l.trim()).filter(Boolean)
    });
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
                  Start a new project with an AI interview or skip directly to design.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  className="w-full font-bold"
                  size="lg"
                  onClick={handleStartInterview}
                >
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Start Interactive Interview
                </Button>

                <div className="relative">
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
              <CardFooter>
                <Button
                  className="w-full"
                  variant="secondary"
                  onClick={handleSkipInterview}
                  disabled={!projectName || !requirements}
                >
                  Skip Interview & Initialize <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
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
            onSpawnHiveMindWindow={handleSpawnDesignHiveMind}
          />
        );
      case 'plan':
        return (
          <PlanView
            design={design}
            modelConfig={getEffectiveConfig('plan')}
            onPlanApproved={handlePlanApproved}
          />
        );
      case 'execute':
        return (
          <ExecutionView
            plan={plan}
            projectName={projectName}
            modelConfig={getEffectiveConfig('execute')}
            onComplete={handlePhaseComplete}
            onSpawnHiveMindWindow={handleSpawnHiveMind}
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
      case 'hivemind':
        return (
          <HiveMindView
            phase={window.props?.phase}
            plan={window.props?.plan}
            projectName={window.props?.projectName}
            type={window.props?.type}
            requirements={window.props?.requirements}
            languages={window.props?.languages}
            modelConfig={getEffectiveConfig('execute')}
          />
        );
      case 'help':
        return (
          <div className="h-full overflow-auto p-6 prose prose-invert max-w-none">
            <h1 className="text-2xl font-bold mb-4">Devussy Studio Help</h1>

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
              <li>Enable <strong>Swarm Mode</strong> (experimental) for multi-agent consensus</li>
              <li>Windows can be minimized but not closed - find them in the taskbar</li>
            </ul>
            <h2 className="text-xl font-semibold mt-6 mb-3">Need More Help?</h2>
            <p>Check the <code className="bg-gray-800 px-2 py-1 rounded">handoff.md</code> file in your project for detailed technical documentation.</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <main className="flex min-h-screen flex-col relative bg-gradient-to-b from-background to-muted overflow-hidden">
      {/* Global Header / Toolbar (Optional) */}
      <div className="absolute top-4 right-4 z-50 flex items-center gap-2">
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
      />
    </main>
  );
}
