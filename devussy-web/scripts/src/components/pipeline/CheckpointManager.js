"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CheckpointManager = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const button_1 = require("@/components/ui/button");
const input_1 = require("@/components/ui/input");
const dialog_1 = require("@/components/ui/dialog");
const scroll_area_1 = require("@/components/ui/scroll-area");
const lucide_react_1 = require("lucide-react");
const CheckpointManager = ({ currentState, onLoad }) => {
    const [isOpen, setIsOpen] = (0, react_1.useState)(false);
    const [checkpoints, setCheckpoints] = (0, react_1.useState)([]);
    const [newCheckpointName, setNewCheckpointName] = (0, react_1.useState)("");
    const [isLoading, setIsLoading] = (0, react_1.useState)(false);
    const [isSaving, setIsSaving] = (0, react_1.useState)(false);
    const fetchCheckpoints = async () => {
        setIsLoading(true);
        try {
            const res = await fetch(`/api/checkpoints`);
            const data = await res.json();
            if (data.checkpoints) {
                setCheckpoints(data.checkpoints);
            }
        }
        catch (e) {
            console.error("Failed to fetch checkpoints", e);
        }
        finally {
            setIsLoading(false);
        }
    };
    (0, react_1.useEffect)(() => {
        if (isOpen) {
            fetchCheckpoints();
        }
    }, [isOpen]);
    const handleSave = async () => {
        if (!newCheckpointName)
            return;
        setIsSaving(true);
        try {
            const payload = Object.assign(Object.assign({}, currentState), { name: newCheckpointName, timestamp: Date.now() / 1000 });
            await fetch(`/api/checkpoints`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            setNewCheckpointName("");
            fetchCheckpoints();
        }
        catch (e) {
            console.error("Failed to save checkpoint", e);
        }
        finally {
            setIsSaving(false);
        }
    };
    const handleLoad = async (id) => {
        setIsLoading(true);
        try {
            const res = await fetch(`/api/checkpoints?id=${id}`);
            const data = await res.json();
            onLoad(data);
            setIsOpen(false);
        }
        catch (e) {
            console.error("Failed to load checkpoint", e);
        }
        finally {
            setIsLoading(false);
        }
    };
    return ((0, jsx_runtime_1.jsxs)(dialog_1.Dialog, { open: isOpen, onOpenChange: setIsOpen, children: [(0, jsx_runtime_1.jsx)(dialog_1.DialogTrigger, { asChild: true, children: (0, jsx_runtime_1.jsxs)(button_1.Button, { variant: "outline", size: "sm", className: "gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Save, { className: "h-4 w-4" }), "Checkpoints"] }) }), (0, jsx_runtime_1.jsxs)(dialog_1.DialogContent, { className: "sm:max-w-[500px]", children: [(0, jsx_runtime_1.jsx)(dialog_1.DialogHeader, { children: (0, jsx_runtime_1.jsxs)(dialog_1.DialogTitle, { className: "flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.FileJson, { className: "h-5 w-5" }), "Project Checkpoints"] }) }), (0, jsx_runtime_1.jsxs)("div", { className: "flex gap-2 py-4", children: [(0, jsx_runtime_1.jsx)(input_1.Input, { placeholder: "Checkpoint Name...", value: newCheckpointName, onChange: (e) => setNewCheckpointName(e.target.value), onKeyDown: (e) => e.key === 'Enter' && handleSave() }), (0, jsx_runtime_1.jsx)(button_1.Button, { onClick: handleSave, disabled: !newCheckpointName || isSaving, children: isSaving ? (0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "h-4 w-4 animate-spin" }) : "Save Current" })] }), (0, jsx_runtime_1.jsx)("div", { className: "text-sm font-medium mb-2", children: "Saved Checkpoints" }), (0, jsx_runtime_1.jsx)(scroll_area_1.ScrollArea, { className: "h-[300px] border rounded-md p-2", children: isLoading && checkpoints.length === 0 ? ((0, jsx_runtime_1.jsx)("div", { className: "flex justify-center items-center h-full", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "h-6 w-6 animate-spin text-muted-foreground" }) })) : checkpoints.length === 0 ? ((0, jsx_runtime_1.jsx)("div", { className: "text-center text-muted-foreground py-8", children: "No checkpoints found" })) : ((0, jsx_runtime_1.jsx)("div", { className: "space-y-2", children: checkpoints.map((cp) => ((0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors group", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col gap-1 overflow-hidden", children: [(0, jsx_runtime_1.jsx)("div", { className: "font-medium truncate", children: cp.name }), (0, jsx_runtime_1.jsxs)("div", { className: "text-xs text-muted-foreground flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Clock, { className: "h-3 w-3" }), new Date(cp.timestamp * 1000).toLocaleString()] }), (0, jsx_runtime_1.jsxs)("div", { className: "text-xs text-muted-foreground truncate", children: [cp.projectName, " \u2022 ", cp.stage] })] }), (0, jsx_runtime_1.jsxs)(button_1.Button, { size: "sm", variant: "secondary", onClick: () => handleLoad(cp.id), disabled: isLoading, className: "opacity-0 group-hover:opacity-100 transition-opacity", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.Download, { className: "h-4 w-4 mr-2" }), " Load"] })] }, cp.id))) })) })] })] }));
};
exports.CheckpointManager = CheckpointManager;
