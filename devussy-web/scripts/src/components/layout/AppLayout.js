"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AppLayout = AppLayout;
const jsx_runtime_1 = require("react/jsx-runtime");
const Header_1 = require("./Header");
function AppLayout({ children }) {
    return ((0, jsx_runtime_1.jsxs)("div", { className: "relative min-h-screen bg-background font-sans text-foreground antialiased selection:bg-primary/20 selection:text-primary", children: [(0, jsx_runtime_1.jsx)("div", { className: "fixed inset-0 z-0 bg-logo" }), (0, jsx_runtime_1.jsx)(Header_1.Header, {}), (0, jsx_runtime_1.jsx)("main", { className: "flex-1", children: children })] }));
}
