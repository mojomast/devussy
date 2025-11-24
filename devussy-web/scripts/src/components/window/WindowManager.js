"use strict";
"use client";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WindowManager = WindowManager;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const WindowFrame_1 = require("./WindowFrame");
const framer_motion_1 = require("framer-motion");
function WindowManager({ windows, setWindows }) {
    const [activeWindowId, setActiveWindowId] = (0, react_1.useState)(null);
    const handleFocus = (id) => {
        setActiveWindowId(id);
    };
    const handleClose = (id) => {
        setWindows((prev) => prev.filter((w) => w.id !== id));
    };
    const handleMinimize = (id) => {
        setWindows((prev) => prev.map((w) => (w.id === id ? Object.assign(Object.assign({}, w), { isMinimized: !w.isMinimized }) : w)));
    };
    return ((0, jsx_runtime_1.jsxs)("div", { className: "relative h-full w-full overflow-hidden", children: [(0, jsx_runtime_1.jsx)(framer_motion_1.AnimatePresence, { children: windows.map((window) => (!window.isMinimized && ((0, jsx_runtime_1.jsx)(WindowFrame_1.WindowFrame, { id: window.id, title: window.title, isActive: activeWindowId === window.id, isMinimized: window.isMinimized, onFocus: () => handleFocus(window.id), onClose: () => handleClose(window.id), onMinimize: () => handleMinimize(window.id), initialPosition: window.position, children: window.content }, window.id)))) }), (0, jsx_runtime_1.jsx)("div", { className: "absolute bottom-4 left-1/2 flex -translate-x-1/2 gap-2", children: windows.filter(w => w.isMinimized).map(w => ((0, jsx_runtime_1.jsx)("button", { onClick: () => handleMinimize(w.id), className: "rounded-full bg-primary px-4 py-2 text-xs font-bold text-primary-foreground shadow-lg transition-transform hover:scale-105", children: w.title }, w.id))) })] }));
}
