"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AppRegistry = void 0;
const react_1 = __importDefault(require("react"));
const irc_1 = __importDefault(require("./irc"));
const pipeline_1 = __importDefault(require("./pipeline"));
const help_1 = __importDefault(require("./help"));
const modelSettings_1 = __importDefault(require("./modelSettings"));
const lucide_react_1 = require("lucide-react");
const InitApp = {
    id: "init",
    name: "New Project",
    icon: react_1.default.createElement(lucide_react_1.Sparkles, { className: "w-4 h-4" }),
    defaultSize: { width: 800, height: 750 },
    startMenuCategory: "Most Used",
    component: () => null,
};
const InterviewApp = {
    id: "interview",
    name: "Requirements Interview",
    icon: react_1.default.createElement(lucide_react_1.MessageSquare, { className: "w-4 h-4" }),
    defaultSize: { width: 700, height: 600 },
    startMenuCategory: "Devussy",
    component: () => null,
};
const DesignApp = {
    id: "design",
    name: "System Design",
    icon: react_1.default.createElement(lucide_react_1.Layers, { className: "w-4 h-4" }),
    defaultSize: { width: 800, height: 700 },
    startMenuCategory: "Devussy",
    component: () => null,
};
const PlanApp = {
    id: "plan",
    name: "Development Plan",
    icon: react_1.default.createElement(lucide_react_1.GitBranch, { className: "w-4 h-4" }),
    defaultSize: { width: 900, height: 750 },
    startMenuCategory: "Devussy",
    component: () => null,
};
const ExecuteApp = {
    id: "execute",
    name: "Execution Phase",
    icon: react_1.default.createElement(lucide_react_1.Zap, { className: "w-4 h-4" }),
    defaultSize: { width: 1200, height: 800 },
    startMenuCategory: "Devussy",
    component: () => null,
};
const HandoffApp = {
    id: "handoff",
    name: "Project Handoff",
    icon: react_1.default.createElement(lucide_react_1.Code2, { className: "w-4 h-4" }),
    defaultSize: { width: 900, height: 800 },
    startMenuCategory: "Devussy",
    component: () => null,
};
exports.AppRegistry = {
    [InitApp.id]: InitApp,
    [InterviewApp.id]: InterviewApp,
    [DesignApp.id]: DesignApp,
    [PlanApp.id]: PlanApp,
    [ExecuteApp.id]: ExecuteApp,
    [HandoffApp.id]: HandoffApp,
    [help_1.default.id]: help_1.default,
    [modelSettings_1.default.id]: modelSettings_1.default,
    [pipeline_1.default.id]: pipeline_1.default,
    [irc_1.default.id]: irc_1.default,
};
