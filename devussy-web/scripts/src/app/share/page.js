"use strict";
'use client';
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = SharePage;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const navigation_1 = require("next/navigation");
const button_1 = require("@/components/ui/button");
const shareLinks_1 = require("@/shareLinks");
function SharePage() {
    const searchParams = (0, navigation_1.useSearchParams)();
    const router = (0, navigation_1.useRouter)();
    const [status, setStatus] = (0, react_1.useState)('idle');
    const [summary, setSummary] = (0, react_1.useState)('');
    (0, react_1.useEffect)(() => {
        var _a, _b;
        const encoded = searchParams.get('payload');
        if (!encoded) {
            setStatus('invalid');
            return;
        }
        const decoded = (0, shareLinks_1.decodeSharePayload)(encoded);
        if (!decoded) {
            setStatus('invalid');
            return;
        }
        setStatus('valid');
        const stage = decoded.stage || 'unknown';
        const projectName = ((_a = decoded.data) === null || _a === void 0 ? void 0 : _a.projectName) || ((_b = decoded.data) === null || _b === void 0 ? void 0 : _b.project_name) || '';
        const summaryText = projectName ? `${stage} – ${projectName}` : stage;
        setSummary(summaryText);
        try {
            if (typeof window !== 'undefined') {
                window.sessionStorage.setItem('devussy_share_payload', encoded);
            }
        }
        catch (err) {
            console.error('[share page] Failed to persist share payload', err);
        }
    }, [searchParams]);
    const handleOpenMainApp = () => {
        router.push('/');
    };
    return ((0, jsx_runtime_1.jsx)("main", { className: "min-h-screen flex items-center justify-center bg-background text-foreground", children: (0, jsx_runtime_1.jsxs)("div", { className: "max-w-lg w-full px-6 py-8 space-y-4 border border-border/40 rounded-xl bg-background/80 shadow-lg", children: [(0, jsx_runtime_1.jsx)("h1", { className: "text-2xl font-bold tracking-tight", children: "Devussy Share Link" }), status === 'idle' && ((0, jsx_runtime_1.jsx)("p", { className: "text-sm text-muted-foreground", children: "Validating share link..." })), status === 'invalid' && ((0, jsx_runtime_1.jsx)("p", { className: "text-sm text-destructive", children: "This share link is invalid or has an unsupported payload." })), status === 'valid' && ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsxs)("p", { className: "text-sm text-muted-foreground", children: ["This link contains shared Devussy state", summary && ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [' ', "for ", (0, jsx_runtime_1.jsx)("span", { className: "font-medium text-foreground", children: summary })] })), "."] }), (0, jsx_runtime_1.jsx)("p", { className: "text-xs text-muted-foreground", children: "Click the button below to open the main Devussy desktop. The app will restore this shared state and open the appropriate Devussy window." }), (0, jsx_runtime_1.jsx)(button_1.Button, { className: "mt-2", onClick: handleOpenMainApp, children: "Open Devussy" })] }))] }) }));
}
