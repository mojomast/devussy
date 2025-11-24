"use strict";
"use client";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PhaseCard = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const card_1 = require("@/components/ui/card");
const button_1 = require("@/components/ui/button");
const input_1 = require("@/components/ui/input");
const textarea_1 = require("@/components/ui/textarea");
const lucide_react_1 = require("lucide-react");
const PhaseCard = ({ phase, isExpanded = true, canMoveUp = false, canMoveDown = false, onUpdate, onDelete, onMoveUp, onMoveDown, onToggle }) => {
    const [isEditing, setIsEditing] = (0, react_1.useState)(false);
    const [editedTitle, setEditedTitle] = (0, react_1.useState)(phase.title);
    const [editedDescription, setEditedDescription] = (0, react_1.useState)(phase.description || "");
    const handleSave = () => {
        if (onUpdate) {
            onUpdate(Object.assign(Object.assign({}, phase), { title: editedTitle, description: editedDescription }));
        }
        setIsEditing(false);
    };
    const handleCancel = () => {
        setEditedTitle(phase.title);
        setEditedDescription(phase.description || "");
        setIsEditing(false);
    };
    return ((0, jsx_runtime_1.jsxs)(card_1.Card, { className: "bg-card/50 border-border/50 hover:border-border transition-colors", children: [(0, jsx_runtime_1.jsx)(card_1.CardHeader, { className: "pb-3", children: (0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between gap-2", children: [(0, jsx_runtime_1.jsx)("div", { className: "flex-1 min-w-0", children: isEditing ? ((0, jsx_runtime_1.jsx)(input_1.Input, { value: editedTitle, onChange: (e) => setEditedTitle(e.target.value), className: "font-medium", placeholder: "Phase title" })) : ((0, jsx_runtime_1.jsxs)(card_1.CardTitle, { className: "text-base font-medium cursor-pointer hover:text-primary transition-colors", onClick: onToggle, children: ["Phase ", phase.number, ": ", phase.title] })) }), (0, jsx_runtime_1.jsxs)("div", { className: "flex items-center gap-1", children: [canMoveUp && ((0, jsx_runtime_1.jsx)(button_1.Button, { variant: "ghost", size: "sm", className: "h-7 w-7 p-0", onClick: onMoveUp, title: "Move up", children: (0, jsx_runtime_1.jsx)(lucide_react_1.ChevronUp, { className: "h-4 w-4" }) })), canMoveDown && ((0, jsx_runtime_1.jsx)(button_1.Button, { variant: "ghost", size: "sm", className: "h-7 w-7 p-0", onClick: onMoveDown, title: "Move down", children: (0, jsx_runtime_1.jsx)(lucide_react_1.ChevronDown, { className: "h-4 w-4" }) })), isEditing ? ((0, jsx_runtime_1.jsxs)(jsx_runtime_1.Fragment, { children: [(0, jsx_runtime_1.jsx)(button_1.Button, { variant: "ghost", size: "sm", className: "h-7 w-7 p-0 text-green-500 hover:text-green-600", onClick: handleSave, title: "Save", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Save, { className: "h-4 w-4" }) }), (0, jsx_runtime_1.jsx)(button_1.Button, { variant: "ghost", size: "sm", className: "h-7 w-7 p-0", onClick: handleCancel, title: "Cancel", children: (0, jsx_runtime_1.jsx)(lucide_react_1.X, { className: "h-4 w-4" }) })] })) : ((0, jsx_runtime_1.jsx)(button_1.Button, { variant: "ghost", size: "sm", className: "h-7 w-7 p-0", onClick: () => setIsEditing(true), title: "Edit", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Edit2, { className: "h-4 w-4" }) })), onDelete && ((0, jsx_runtime_1.jsx)(button_1.Button, { variant: "ghost", size: "sm", className: "h-7 w-7 p-0 text-destructive hover:text-destructive/80", onClick: onDelete, title: "Delete", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Trash2, { className: "h-4 w-4" }) }))] })] }) }), isExpanded && ((0, jsx_runtime_1.jsx)(card_1.CardContent, { className: "pt-0", children: isEditing ? ((0, jsx_runtime_1.jsx)(textarea_1.Textarea, { value: editedDescription, onChange: (e) => setEditedDescription(e.target.value), placeholder: "Phase description...", className: "min-h-[80px] text-sm" })) : ((0, jsx_runtime_1.jsx)(card_1.CardDescription, { className: "text-sm whitespace-pre-wrap", children: phase.description || "No description" })) }))] }));
};
exports.PhaseCard = PhaseCard;
