"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const lucide_react_1 = require("lucide-react");
const ModelSettings_1 = require("@/components/pipeline/ModelSettings");
const ModelSettingsWindow = ({ configs, onConfigsChange, activeStage, }) => {
    return ((0, jsx_runtime_1.jsx)(ModelSettings_1.ModelSettings, { configs: configs, onConfigsChange: onConfigsChange, activeStage: activeStage, isWindowMode: true }));
};
const ModelSettingsApp = {
    id: "model-settings",
    name: "AI Model Settings",
    icon: (0, jsx_runtime_1.jsx)(lucide_react_1.Settings, { className: "w-4 h-4" }),
    defaultSize: { width: 500, height: 650 },
    startMenuCategory: "Settings",
    component: ModelSettingsWindow,
};
exports.default = ModelSettingsApp;
