"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Header = Header;
const jsx_runtime_1 = require("react/jsx-runtime");
const lucide_react_1 = require("lucide-react");
function Header() {
    return ((0, jsx_runtime_1.jsx)("header", { className: "sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60", children: (0, jsx_runtime_1.jsxs)("div", { className: "container flex h-14 max-w-screen-2xl items-center", children: [(0, jsx_runtime_1.jsx)("div", { className: "mr-4 flex items-center space-x-2", children: (0, jsx_runtime_1.jsxs)("a", { href: "https://github.com/mojomast/devussy", target: "_blank", rel: "noopener noreferrer", className: "flex items-center space-x-2 hover:opacity-80 transition-opacity", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Terminal, { className: "h-6 w-6 text-primary" }), (0, jsx_runtime_1.jsx)("span", { className: "hidden font-bold sm:inline-block text-lg tracking-tight", children: "DEVUSSY STUDIO" })] }) }), (0, jsx_runtime_1.jsxs)("div", { className: "flex flex-1 items-center justify-between space-x-2 md:justify-end", children: [(0, jsx_runtime_1.jsx)("div", { className: "w-full flex-1 md:w-auto md:flex-none" }), (0, jsx_runtime_1.jsx)("nav", { className: "flex items-center" })] })] }) }));
}
