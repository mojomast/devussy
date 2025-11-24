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
Object.defineProperty(exports, "__esModule", { value: true });
exports.DesignView = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importStar(require("react"));
const button_1 = require("@/components/ui/button");
const scroll_area_1 = require("@/components/ui/scroll-area");
const lucide_react_1 = require("lucide-react");
const shareLinks_1 = require("@/shareLinks");
const eventBus_1 = require("@/apps/eventBus");
const DesignView = ({ projectName, requirements, languages, modelConfig, onDesignComplete, autoRun = false }) => {
    const bus = (0, eventBus_1.useEventBus)();
    const [designContent, setDesignContent] = (0, react_1.useState)("");
    const [designData, setDesignData] = (0, react_1.useState)(null);
    const [isGenerating, setIsGenerating] = (0, react_1.useState)(false);
    const [viewMode, setViewMode] = (0, react_1.useState)('preview');
    const [isEditing, setIsEditing] = (0, react_1.useState)(false);
    const [error, setError] = (0, react_1.useState)(null);
    // Ref to track the current abort controller
    const abortControllerRef = react_1.default.useRef(null);
    const isGeneratingRef = react_1.default.useRef(false);
    const generateDesign = async () => {
        var _a;
        if (isGeneratingRef.current)
            return;
        setIsGenerating(true);
        setError(null);
        setDesignContent("");
        isGeneratingRef.current = true;
        // Create new abort controller
        const controller = new AbortController();
        abortControllerRef.current = controller;
        try {
            const response = await fetch('/api/design', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    projectName,
                    requirements,
                    languages,
                    modelConfig
                }),
                signal: controller.signal
            });
            if (!response.ok)
                throw new Error('Failed to generate design');
            const reader = (_a = response.body) === null || _a === void 0 ? void 0 : _a.getReader();
            if (!reader)
                throw new Error('No response body');
            const decoder = new TextDecoder();
            let buffer = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done)
                    break;
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || "";
                for (const part of parts) {
                    const line = part.trim();
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6);
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.content) {
                                setDesignContent((prev) => prev + data.content);
                            }
                            if (data.done && data.design) {
                                setDesignData(data.design);
                                return;
                            }
                            if (data.error) {
                                throw new Error(data.error);
                            }
                        }
                        catch (e) {
                            console.error("Failed to parse SSE JSON:", e);
                        }
                    }
                }
            }
        }
        catch (err) {
            if (err.name === 'AbortError') {
                console.log('Design generation aborted');
                return;
            }
            console.error("Design generation error:", err);
            setError(err.message || "An error occurred");
        }
        finally {
            if (abortControllerRef.current === controller) {
                setIsGenerating(false);
                isGeneratingRef.current = false;
                abortControllerRef.current = null;
            }
        }
    };
    // Auto-generate on mount
    (0, react_1.useEffect)(() => {
        const timeoutId = setTimeout(() => {
            generateDesign();
        }, 50);
        return () => {
            clearTimeout(timeoutId);
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [projectName, requirements, JSON.stringify(languages), modelConfig]);
    const hasAutoAdvanced = react_1.default.useRef(false);
    // Auto-advance when complete
    (0, react_1.useEffect)(() => {
        if (autoRun && !isGenerating && designContent && !hasAutoAdvanced.current) {
            const timer = setTimeout(() => {
                hasAutoAdvanced.current = true;
                // Pass the design data or construct it from content if structured data is missing
                onDesignComplete(designData || { raw_llm_response: designContent, project_name: projectName });
            }, 1500);
            return () => clearTimeout(timer);
        }
    }, [autoRun, isGenerating, designContent, designData, onDesignComplete, projectName]);
    const handleApprove = () => {
        onDesignComplete(designData || { raw_llm_response: designContent, project_name: projectName });
    };
    const handleShare = async () => {
        var _a;
        if (!designContent && !designData)
            return;
        try {
            const shareData = {
                projectName,
                requirements,
                languages: languages.join(', '),
                design: designData || { raw_llm_response: designContent, project_name: projectName },
            };
            const url = (0, shareLinks_1.generateShareLink)('design', shareData);
            try {
                bus.emit('shareLinkGenerated', {
                    stage: 'design',
                    data: shareData,
                    url,
                });
            }
            catch (err) {
                console.error('[DesignView] Failed to emit shareLinkGenerated event', err);
            }
            let copied = false;
            if (typeof navigator !== 'undefined' && ((_a = navigator.clipboard) === null || _a === void 0 ? void 0 : _a.writeText)) {
                try {
                    await navigator.clipboard.writeText(url);
                    copied = true;
                }
                catch (_b) {
                    copied = false;
                }
            }
            if (typeof window !== 'undefined') {
                window.prompt(copied
                    ? 'Share link copied to clipboard. You can also copy it from here:'
                    : 'Copy this Devussy share link:', url);
            }
        }
        catch (err) {
            console.error('[DesignView] Failed to generate share link', err);
        }
    };
    return ((0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col h-full", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between p-4 border-b border-border bg-muted/20", children: [(0, jsx_runtime_1.jsxs)("h2", { className: "text-lg font-semibold flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.LayoutGrid, { className: "h-5 w-5" }), "System Design"] }), (0, jsx_runtime_1.jsxs)("div", { className: "flex gap-2", children: [designContent && !isGenerating && ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(button_1.Button, { variant: "outline", size: "sm", onClick: () => setViewMode(viewMode === 'preview' ? 'raw' : 'preview'), children: viewMode === 'preview' ? ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(lucide_react_1.FileCode, { className: "h-4 w-4 mr-2" }), " Raw Text"] })) : ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(lucide_react_1.LayoutGrid, { className: "h-4 w-4 mr-2" }), " Preview"] })) }), viewMode === 'raw' && ((0, jsx_runtime_1.jsxs)(button_1.Button, { variant: "outline", size: "sm", onClick: () => setIsEditing(!isEditing), children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Edit2, { className: "h-4 w-4 mr-2" }), isEditing ? "Preview" : "Edit"] }))] })), (0, jsx_runtime_1.jsxs)(button_1.Button, { variant: "outline", size: "sm", onClick: handleShare, disabled: isGenerating || (!designContent && !designData), children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Share2, { className: "h-4 w-4 mr-2" }), "Share"] }), (0, jsx_runtime_1.jsx)(button_1.Button, { variant: "outline", size: "sm", onClick: generateDesign, disabled: isGenerating, children: "Regenerate" }), (0, jsx_runtime_1.jsxs)(button_1.Button, { size: "sm", onClick: handleApprove, disabled: isGenerating || !designContent, children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Check, { className: "h-4 w-4 mr-2" }), "Approve Design"] })] })] }), (0, jsx_runtime_1.jsx)(scroll_area_1.ScrollArea, { className: "flex-1 p-6", children: isGenerating && !designContent ? ((0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col items-center justify-center h-full space-y-4 text-muted-foreground", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "h-8 w-8 animate-spin text-primary" }), (0, jsx_runtime_1.jsx)("p", { children: "Architecting system solution..." })] })) : error ? ((0, jsx_runtime_1.jsxs)("div", { className: "text-destructive p-4 border border-destructive/20 rounded-lg bg-destructive/10", children: ["Error: ", error] })) : (viewMode === 'preview' ? ((0, jsx_runtime_1.jsx)("div", { className: "prose prose-invert max-w-none", children: (0, jsx_runtime_1.jsx)("div", { className: "whitespace-pre-wrap font-mono text-sm", children: designContent }) })) : ((0, jsx_runtime_1.jsx)("div", { className: "h-full", children: isEditing ? ((0, jsx_runtime_1.jsx)("textarea", { className: "w-full h-full min-h-[400px] bg-transparent border border-border rounded-lg p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary", value: designContent, onChange: (e) => setDesignContent(e.target.value) })) : ((0, jsx_runtime_1.jsx)("pre", { className: "whitespace-pre-wrap font-mono text-sm bg-transparent p-0", children: designContent })) }))) })] }));
};
exports.DesignView = DesignView;
