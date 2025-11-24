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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.HandoffView = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importStar(require("react"));
const button_1 = require("@/components/ui/button");
const scroll_area_1 = require("@/components/ui/scroll-area");
const card_1 = require("@/components/ui/card");
const input_1 = require("@/components/ui/input");
const lucide_react_1 = require("lucide-react");
const jszip_1 = __importDefault(require("jszip"));
const HandoffView = ({ design, plan, modelConfig }) => {
    var _a;
    const [handoffContent, setHandoffContent] = (0, react_1.useState)("");
    const [isGenerating, setIsGenerating] = (0, react_1.useState)(false);
    const [githubToken, setGithubToken] = (0, react_1.useState)("");
    const [repoName, setRepoName] = (0, react_1.useState)("");
    const [isPushing, setIsPushing] = (0, react_1.useState)(false);
    const [pushResult, setPushResult] = (0, react_1.useState)(null);
    // Tab state
    const [activeTab, setActiveTab] = (0, react_1.useState)('handoff');
    const [selectedPhase, setSelectedPhase] = (0, react_1.useState)(1);
    const generateHandoff = async () => {
        setIsGenerating(true);
        try {
            const response = await fetch('/api/handoff', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    design,
                    plan,
                    modelConfig
                })
            });
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = 'Failed to generate handoff';
                try {
                    const errorJson = JSON.parse(errorText);
                    if (errorJson.error)
                        errorMessage = errorJson.error;
                }
                catch (e) {
                    errorMessage = errorText || errorMessage;
                }
                throw new Error(errorMessage);
            }
            const data = await response.json();
            setHandoffContent(data.content);
        }
        catch (error) {
            console.error("Handoff generation failed:", error);
            setHandoffContent("Error generating handoff documentation.");
        }
        finally {
            setIsGenerating(false);
        }
    };
    // Auto-generate on mount
    react_1.default.useEffect(() => {
        generateHandoff();
    }, []);
    const formatDesignAsMarkdown = (design) => {
        // If we have raw_llm_response (new standard) or raw_response (legacy), use it
        if (design.raw_llm_response) {
            return design.raw_llm_response;
        }
        if (design.raw_response) {
            return design.raw_response;
        }
        // Otherwise, format the design object as markdown
        let md = `# ${design.project_name || 'Project Design'}\n\n`;
        if (design.objectives && Array.isArray(design.objectives)) {
            md += `## Objectives\n\n`;
            design.objectives.forEach((obj) => {
                // Skip separator markers
                if (obj === '--' || obj === '---')
                    return;
                md += `- ${obj}\n`;
            });
            md += `\n`;
        }
        if (design.architecture) {
            md += `## Architecture\n\n${design.architecture}\n\n`;
        }
        if (design.tech_stack && Array.isArray(design.tech_stack)) {
            md += `## Technology Stack\n\n`;
            design.tech_stack.forEach((tech) => {
                md += `- ${tech}\n`;
            });
            md += `\n`;
        }
        if (design.data_model) {
            md += `## Data Model\n\n${design.data_model}\n\n`;
        }
        if (design.api_design) {
            md += `## API Design\n\n${design.api_design}\n\n`;
        }
        if (design.security) {
            md += `## Security\n\n${design.security}\n\n`;
        }
        if (design.deployment) {
            md += `## Deployment\n\n${design.deployment}\n\n`;
        }
        return md;
    };
    const formatPlanAsMarkdown = (plan) => {
        let md = `# Development Plan\n\n`;
        if (plan.project_name) {
            md += `**Project:** ${plan.project_name}\n\n`;
        }
        if (plan.phases && Array.isArray(plan.phases)) {
            md += `## Phases\n\n`;
            plan.phases.forEach((phase) => {
                const phaseNum = phase.number || phase.phase_number;
                const phaseTitle = phase.title || phase.name || `Phase ${phaseNum}`;
                md += `### Phase ${phaseNum}: ${phaseTitle}\n\n`;
                if (phase.description) {
                    md += `${phase.description}\n\n`;
                }
                if (phase.steps && Array.isArray(phase.steps) && phase.steps.length > 0) {
                    md += `**Steps:**\n\n`;
                    phase.steps.forEach((step, idx) => {
                        const stepTitle = step.title || step.name || `Step ${idx + 1}`;
                        md += `${idx + 1}. ${stepTitle}\n`;
                        if (step.description) {
                            md += `   ${step.description}\n`;
                        }
                    });
                    md += `\n`;
                }
                if (phase.deliverables && Array.isArray(phase.deliverables)) {
                    md += `**Deliverables:**\n`;
                    phase.deliverables.forEach((deliverable) => {
                        md += `- ${deliverable}\n`;
                    });
                    md += `\n`;
                }
                if (phase.acceptance_criteria && Array.isArray(phase.acceptance_criteria)) {
                    md += `**Acceptance Criteria:**\n`;
                    phase.acceptance_criteria.forEach((criteria) => {
                        md += `- ${criteria}\n`;
                    });
                    md += `\n`;
                }
                md += `---\n\n`;
            });
        }
        return md;
    };
    const getPhaseMarkdown = (phaseNum) => {
        if (!plan || !plan.phases)
            return "No phases found.";
        const phase = plan.phases.find((p) => (p.number || p.phase_number) === phaseNum);
        if (!phase)
            return "Phase not found.";
        let content = `# Phase ${phaseNum}: ${phase.title || phase.name}\n\n`;
        content += `## Description\n${phase.description || 'No description'}\n\n`;
        if (phase.steps && phase.steps.length > 0) {
            content += `## Steps\n\n`;
            phase.steps.forEach((step, idx) => {
                content += `### ${idx + 1}. ${step.title || step.name || `Step ${idx + 1}`}\n\n`;
                if (step.description) {
                    content += `${step.description}\n\n`;
                }
                if (step.details) {
                    content += `**Details:**\n${step.details}\n\n`;
                }
                if (step.acceptance_criteria && step.acceptance_criteria.length > 0) {
                    content += `**Acceptance Criteria:**\n`;
                    step.acceptance_criteria.forEach((criteria) => {
                        content += `- ${criteria}\n`;
                    });
                    content += `\n`;
                }
            });
        }
        return content;
    };
    const handleDownload = async () => {
        const zip = new jszip_1.default();
        // Add core files with proper markdown formatting
        zip.file("project_design.md", formatDesignAsMarkdown(design));
        zip.file("development_plan.md", formatPlanAsMarkdown(plan));
        zip.file("handoff_instructions.md", handoffContent);
        // Add individual phase documents
        if (plan && plan.phases) {
            const phasesFolder = zip.folder("phases");
            plan.phases.forEach((phase) => {
                const phaseNumber = phase.number || phase.phase_number;
                const phaseTitle = (phase.title || phase.name || `Phase ${phaseNumber}`).replace(/[^a-z0-9]/gi, '_').toLowerCase();
                const fileName = `phase_${phaseNumber}_${phaseTitle}.md`;
                phasesFolder === null || phasesFolder === void 0 ? void 0 : phasesFolder.file(fileName, getPhaseMarkdown(phaseNumber));
            });
        }
        // Generate blob and download
        const content = await zip.generateAsync({ type: "blob" });
        const url = window.URL.createObjectURL(content);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${design.project_name || "devussy-project"}.zip`;
        a.click();
        window.URL.revokeObjectURL(url);
    };
    const handleGithubPush = async () => {
        if (!githubToken || !repoName)
            return;
        setIsPushing(true);
        setPushResult(null);
        try {
            const response = await fetch('/api/github/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    repoName,
                    token: githubToken,
                    design,
                    plan,
                    handoffContent
                })
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to create repository');
            }
            setPushResult(`Success! Repository created at: ${data.data.repoUrl}`);
            // Optionally open in new tab
            // window.open(data.data.repoUrl, '_blank');
        }
        catch (error) {
            console.error("GitHub push failed:", error);
            setPushResult(`Failed to push to GitHub: ${error.message}`);
        }
        finally {
            setIsPushing(false);
        }
    };
    return ((0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col h-full", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between p-4 border-b border-border bg-muted/20", children: [(0, jsx_runtime_1.jsxs)("h2", { className: "text-lg font-semibold flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.CheckCircle, { className: "h-5 w-5 text-green-500" }), "Project Handoff"] }), (0, jsx_runtime_1.jsx)("div", { className: "flex gap-2", children: (0, jsx_runtime_1.jsxs)(button_1.Button, { size: "sm", onClick: handleDownload, disabled: !handoffContent, children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Download, { className: "h-4 w-4 mr-2" }), "Download Artifacts"] }) })] }), (0, jsx_runtime_1.jsxs)("div", { className: "flex border-b border-border overflow-x-auto bg-muted/10", children: [(0, jsx_runtime_1.jsxs)("button", { className: `px-4 py-2 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'handoff' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`, onClick: () => setActiveTab('handoff'), children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Terminal, { className: "h-4 w-4" }), "Handoff Instructions"] }), (0, jsx_runtime_1.jsxs)("button", { className: `px-4 py-2 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'design' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`, onClick: () => setActiveTab('design'), children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Code, { className: "h-4 w-4" }), "Project Design"] }), (0, jsx_runtime_1.jsxs)("button", { className: `px-4 py-2 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'plan' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`, onClick: () => setActiveTab('plan'), children: [(0, jsx_runtime_1.jsx)(lucide_react_1.List, { className: "h-4 w-4" }), "Development Plan"] }), (0, jsx_runtime_1.jsxs)("button", { className: `px-4 py-2 text-sm font-medium flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'phases' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`, onClick: () => setActiveTab('phases'), children: [(0, jsx_runtime_1.jsx)(lucide_react_1.FileText, { className: "h-4 w-4" }), "Phase Details"] })] }), (0, jsx_runtime_1.jsxs)(scroll_area_1.ScrollArea, { className: "flex-1 p-6", children: [activeTab === 'handoff' && ((0, jsx_runtime_1.jsxs)("div", { className: "grid gap-6", children: [(0, jsx_runtime_1.jsxs)(card_1.Card, { children: [(0, jsx_runtime_1.jsxs)(card_1.CardHeader, { children: [(0, jsx_runtime_1.jsx)(card_1.CardTitle, { children: "Handoff Instructions" }), (0, jsx_runtime_1.jsx)(card_1.CardDescription, { children: "Final summary and next steps for your project." })] }), (0, jsx_runtime_1.jsx)(card_1.CardContent, { children: isGenerating ? ((0, jsx_runtime_1.jsx)("div", { className: "flex items-center justify-center p-8", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "h-6 w-6 animate-spin text-primary" }) })) : ((0, jsx_runtime_1.jsx)("div", { className: "prose prose-invert max-w-none text-sm", children: (0, jsx_runtime_1.jsx)("pre", { className: "whitespace-pre-wrap font-sans", children: handoffContent }) })) })] }), (0, jsx_runtime_1.jsxs)(card_1.Card, { children: [(0, jsx_runtime_1.jsxs)(card_1.CardHeader, { children: [(0, jsx_runtime_1.jsxs)(card_1.CardTitle, { className: "flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Github, { className: "h-5 w-5" }), "Push to GitHub"] }), (0, jsx_runtime_1.jsx)(card_1.CardDescription, { children: "Create a new repository and push your project code." })] }), (0, jsx_runtime_1.jsxs)(card_1.CardContent, { className: "space-y-4", children: [(0, jsx_runtime_1.jsxs)("div", { className: "grid gap-2", children: [(0, jsx_runtime_1.jsx)("label", { className: "text-sm font-medium", children: "Repository Name" }), (0, jsx_runtime_1.jsx)(input_1.Input, { placeholder: "my-awesome-project", value: repoName, onChange: (e) => setRepoName(e.target.value) })] }), (0, jsx_runtime_1.jsxs)("div", { className: "grid gap-2", children: [(0, jsx_runtime_1.jsx)("label", { className: "text-sm font-medium", children: "Personal Access Token" }), (0, jsx_runtime_1.jsx)(input_1.Input, { type: "password", placeholder: "ghp_...", value: githubToken, onChange: (e) => setGithubToken(e.target.value) })] }), pushResult && ((0, jsx_runtime_1.jsx)("div", { className: `text-sm ${pushResult.includes("Success") ? "text-green-500" : "text-red-500"}`, children: pushResult })), (0, jsx_runtime_1.jsxs)(button_1.Button, { className: "w-full", onClick: handleGithubPush, disabled: isPushing || !repoName || !githubToken, children: [isPushing ? ((0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "h-4 w-4 animate-spin mr-2" })) : ((0, jsx_runtime_1.jsx)(lucide_react_1.Github, { className: "h-4 w-4 mr-2" })), "Create & Push"] })] })] })] })), activeTab === 'design' && ((0, jsx_runtime_1.jsx)("div", { className: "prose prose-invert max-w-none", children: (0, jsx_runtime_1.jsx)("pre", { className: "whitespace-pre-wrap font-mono text-sm bg-transparent p-0", children: formatDesignAsMarkdown(design) }) })), activeTab === 'plan' && ((0, jsx_runtime_1.jsx)("div", { className: "prose prose-invert max-w-none", children: (0, jsx_runtime_1.jsx)("pre", { className: "whitespace-pre-wrap font-mono text-sm bg-transparent p-0", children: formatPlanAsMarkdown(plan) }) })), activeTab === 'phases' && ((0, jsx_runtime_1.jsxs)("div", { className: "space-y-4", children: [(0, jsx_runtime_1.jsx)("div", { className: "flex flex-wrap gap-2 pb-4 border-b border-border", children: (_a = plan === null || plan === void 0 ? void 0 : plan.phases) === null || _a === void 0 ? void 0 : _a.map((phase) => ((0, jsx_runtime_1.jsxs)(button_1.Button, { variant: selectedPhase === (phase.number || phase.phase_number) ? "default" : "outline", size: "sm", onClick: () => setSelectedPhase(phase.number || phase.phase_number), children: ["Phase ", phase.number || phase.phase_number] }, phase.number || phase.phase_number))) }), (0, jsx_runtime_1.jsx)("div", { className: "prose prose-invert max-w-none", children: (0, jsx_runtime_1.jsx)("pre", { className: "whitespace-pre-wrap font-mono text-sm bg-transparent p-0", children: getPhaseMarkdown(selectedPhase) }) })] }))] })] }));
};
exports.HandoffView = HandoffView;
