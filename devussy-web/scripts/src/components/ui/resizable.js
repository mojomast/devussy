"use strict";
"use client";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ResizablePanelGroup = ResizablePanelGroup;
exports.ResizablePanel = ResizablePanel;
exports.ResizableHandle = ResizableHandle;
const jsx_runtime_1 = require("react/jsx-runtime");
const lucide_react_1 = require("lucide-react");
const ResizablePrimitive = __importStar(require("react-resizable-panels"));
const utils_1 = require("@/utils");
function ResizablePanelGroup(_a) {
    var { className } = _a, props = __rest(_a, ["className"]);
    return ((0, jsx_runtime_1.jsx)(ResizablePrimitive.PanelGroup, Object.assign({ "data-slot": "resizable-panel-group", className: (0, utils_1.cn)("flex h-full w-full data-[panel-group-direction=vertical]:flex-col", className) }, props)));
}
function ResizablePanel(_a) {
    var props = __rest(_a, []);
    return (0, jsx_runtime_1.jsx)(ResizablePrimitive.Panel, Object.assign({ "data-slot": "resizable-panel" }, props));
}
function ResizableHandle(_a) {
    var { withHandle, className } = _a, props = __rest(_a, ["withHandle", "className"]);
    return ((0, jsx_runtime_1.jsx)(ResizablePrimitive.PanelResizeHandle, Object.assign({ "data-slot": "resizable-handle", className: (0, utils_1.cn)("bg-border focus-visible:ring-ring relative flex w-px items-center justify-center after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 focus-visible:ring-1 focus-visible:ring-offset-1 focus-visible:outline-hidden data-[panel-group-direction=vertical]:h-px data-[panel-group-direction=vertical]:w-full data-[panel-group-direction=vertical]:after:left-0 data-[panel-group-direction=vertical]:after:h-1 data-[panel-group-direction=vertical]:after:w-full data-[panel-group-direction=vertical]:after:translate-x-0 data-[panel-group-direction=vertical]:after:-translate-y-1/2 [&[data-panel-group-direction=vertical]>div]:rotate-90", className) }, props, { children: withHandle && ((0, jsx_runtime_1.jsx)("div", { className: "bg-border z-10 flex h-4 w-3 items-center justify-center rounded-xs border", children: (0, jsx_runtime_1.jsx)(lucide_react_1.GripVerticalIcon, { className: "size-2.5" }) })) })));
}
