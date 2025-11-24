"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const lucide_react_1 = require("lucide-react");
const PipelineRoot = () => null;
const PipelineApp = {
    id: "pipeline",
    name: "Devussy Pipeline",
    icon: (0, jsx_runtime_1.jsx)(lucide_react_1.Layers, { className: "w-4 h-4" }),
    defaultSize: { width: 900, height: 750 },
    startMenuCategory: "Devussy",
    component: PipelineRoot,
};
exports.default = PipelineApp;
