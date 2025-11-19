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
import { Taskbar } from "@/components/window/Taskbar";

type WindowType = 'init' | 'interview' | 'design' | 'plan' | 'execute' | 'handoff' | 'hivemind';

interface WindowState {
  id: string;
  type: WindowType;
  title: string;
  position: { x: number; y: number };
  zIndex: number;
  isMinimized?: boolean;
  props?: any;
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
      model: 'gpt-5-mini',
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

  // Window Management Functions
  const spawnWindow = (type: WindowType, title: string, props?: any) => {
    const id = `${type}-${Date.now()}`;
    const offset = windows.length * 30;
    const newWindow: WindowState = {
      id,
      type,
      title,
      position: { x: 100 + offset, y: 100 + offset },
      zIndex: nextZIndex,
      props
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
            modelConfig={getEffectiveConfig('execute')}
          />
        );
      default:
        return null;
    }
  };

  return (
    <main className="flex min-h-screen flex-col relative bg-gradient-to-b from-background to-muted overflow-hidden">
      {/* Global Header / Toolbar (Optional) */}
      <div className="absolute top-4 right-4 z-50">
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
      />
    </main>
  );
}
