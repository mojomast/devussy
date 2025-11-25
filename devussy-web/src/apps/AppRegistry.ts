import React from "react";
import type { AppDefinition } from "./appTypes";
import IrcApp from "./irc";
import PipelineApp from "./pipeline";
import HelpApp from "./help";
import ModelSettingsApp from "./modelSettings";
import ScratchpadApp from "./scratchpad";
import DevplanProgressApp from "./devplanProgress";
import { MessageSquare, Sparkles, Layers, Code2, GitBranch, Zap } from "lucide-react";

const MODEL_SETTINGS_APP_ID = "model-settings";

const InitApp: AppDefinition = {
  id: "init",
  name: "New Project",
  icon: React.createElement(Sparkles, { className: "w-4 h-4" }),
  defaultSize: { width: 800, height: 750 },
  startMenuCategory: "Most Used",
  component: () => null,
};

const InterviewApp: AppDefinition = {
  id: "interview",
  name: "Requirements Interview",
  icon: React.createElement(MessageSquare, { className: "w-4 h-4" }),
  defaultSize: { width: 700, height: 600 },
  startMenuCategory: "Devussy",
  component: () => null,
};

const DesignApp: AppDefinition = {
  id: "design",
  name: "System Design",
  icon: React.createElement(Layers, { className: "w-4 h-4" }),
  defaultSize: { width: 800, height: 700 },
  startMenuCategory: "Devussy",
  component: () => null,
};

const PlanApp: AppDefinition = {
  id: "plan",
  name: "Development Plan",
  icon: React.createElement(GitBranch, { className: "w-4 h-4" }),
  defaultSize: { width: 900, height: 750 },
  startMenuCategory: "Devussy",
  component: () => null,
};

const ExecuteApp: AppDefinition = {
  id: "execute",
  name: "Execution Phase",
  icon: React.createElement(Zap, { className: "w-4 h-4" }),
  defaultSize: { width: 1200, height: 800 },
  startMenuCategory: "Devussy",
  component: () => null,
};

const HandoffApp: AppDefinition = {
  id: "handoff",
  name: "Project Handoff",
  icon: React.createElement(Code2, { className: "w-4 h-4" }),
  defaultSize: { width: 900, height: 800 },
  startMenuCategory: "Devussy",
  component: () => null,
};
export const AppRegistry: Record<string, AppDefinition> = {
  [InitApp.id]: InitApp,
  [InterviewApp.id]: InterviewApp,
  [DesignApp.id]: DesignApp,
  [PlanApp.id]: PlanApp,
  [ExecuteApp.id]: ExecuteApp,
  [HandoffApp.id]: HandoffApp,
  [HelpApp.id]: HelpApp,
  [MODEL_SETTINGS_APP_ID]: ModelSettingsApp,
  [PipelineApp.id]: PipelineApp,
  [ScratchpadApp.id]: ScratchpadApp,
  [DevplanProgressApp.id]: DevplanProgressApp,
  [IrcApp.id]: IrcApp,
};
