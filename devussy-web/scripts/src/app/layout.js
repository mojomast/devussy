"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.metadata = void 0;
exports.default = RootLayout;
const jsx_runtime_1 = require("react/jsx-runtime");
const google_1 = require("next/font/google");
require("./globals.css");
const AppLayout_1 = require("@/components/layout/AppLayout");
const ThemeProvider_1 = require("@/components/theme/ThemeProvider");
const jetbrainsMono = (0, google_1.JetBrains_Mono)({ subsets: ["latin"] });
exports.metadata = {
    title: "Devussy",
    description: "AI-Powered Development Pipeline",
};
function RootLayout({ children, }) {
    return ((0, jsx_runtime_1.jsx)("html", { lang: "en", className: "dark overflow-hidden", style: { overscrollBehavior: 'none' }, children: (0, jsx_runtime_1.jsx)("body", { className: `${jetbrainsMono.className} antialiased overflow-hidden h-full`, style: { overscrollBehavior: 'none' }, children: (0, jsx_runtime_1.jsxs)(ThemeProvider_1.ThemeProvider, { children: [(0, jsx_runtime_1.jsx)("div", { className: "scanlines" }), (0, jsx_runtime_1.jsx)(AppLayout_1.AppLayout, { children: children })] }) }) }));
}
