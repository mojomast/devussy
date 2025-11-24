"use strict";
"use client";
Object.defineProperty(exports, "__esModule", { value: true });
exports.InterviewView = void 0;
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = require("react");
const button_1 = require("@/components/ui/button");
const scroll_area_1 = require("@/components/ui/scroll-area");
const input_1 = require("@/components/ui/input");
const lucide_react_1 = require("lucide-react");
const utils_1 = require("@/utils");
const InterviewView = ({ modelConfig, onInterviewComplete }) => {
    const [history, setHistory] = (0, react_1.useState)([]);
    const [input, setInput] = (0, react_1.useState)("");
    const [isLoading, setIsLoading] = (0, react_1.useState)(false);
    const scrollRef = (0, react_1.useRef)(null);
    const hasInitialized = (0, react_1.useRef)(false);
    // Initial greeting
    (0, react_1.useEffect)(() => {
        if (!hasInitialized.current && history.length === 0) {
            hasInitialized.current = true;
            handleSend("Hello! I'd like to start a new project.");
        }
    }, []);
    (0, react_1.useEffect)(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [history, isLoading]);
    const handleSend = async (text) => {
        if (!text.trim())
            return;
        const newHistory = [...history, { role: 'user', content: text }];
        setHistory(newHistory);
        setInput("");
        setIsLoading(true);
        try {
            const response = await fetch('/api/interview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    userInput: text,
                    history: history.filter(m => m.role !== 'system'), // Only send user/assistant messages
                    modelConfig
                }),
            });
            if (!response.ok)
                throw new Error('Failed to send message');
            const data = await response.json();
            setHistory(prev => [...prev, { role: 'assistant', content: data.response }]);
            if (data.isComplete && data.extractedData) {
                // Add a small delay so the user can read the final message
                setTimeout(() => {
                    onInterviewComplete(data.extractedData);
                }, 2000);
            }
        }
        catch (error) {
            console.error("Interview error:", error);
            setHistory(prev => [...prev, { role: 'assistant', content: "I'm sorry, I encountered an error. Please try again." }]);
        }
        finally {
            setIsLoading(false);
        }
    };
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend(input);
        }
    };
    return ((0, jsx_runtime_1.jsxs)("div", { className: "flex flex-col h-full max-w-3xl mx-auto", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex items-center justify-between p-4 border-b border-border bg-muted/20", children: [(0, jsx_runtime_1.jsxs)("h2", { className: "text-lg font-semibold flex items-center gap-2", children: [(0, jsx_runtime_1.jsx)(lucide_react_1.MessageSquare, { className: "h-5 w-5" }), "Project Interview"] }), (0, jsx_runtime_1.jsx)("div", { className: "text-xs text-muted-foreground", children: "Chat with AI to define your project requirements" })] }), (0, jsx_runtime_1.jsx)(scroll_area_1.ScrollArea, { className: "flex-1 p-4", children: (0, jsx_runtime_1.jsxs)("div", { className: "space-y-4 pb-4", children: [history.map((msg, idx) => (msg.role !== 'system' && ((0, jsx_runtime_1.jsx)("div", { className: (0, utils_1.cn)("flex w-full", msg.role === 'user' ? "justify-end" : "justify-start"), children: (0, jsx_runtime_1.jsx)("div", { className: (0, utils_1.cn)("max-w-[80%] rounded-lg px-4 py-2 text-sm", msg.role === 'user'
                                    ? "bg-primary text-primary-foreground"
                                    : "bg-muted text-foreground"), children: (0, jsx_runtime_1.jsx)("div", { className: "whitespace-pre-wrap", children: msg.content }) }) }, idx)))), isLoading && ((0, jsx_runtime_1.jsx)("div", { className: "flex justify-start", children: (0, jsx_runtime_1.jsx)("div", { className: "bg-muted rounded-lg px-4 py-2", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Loader2, { className: "h-4 w-4 animate-spin" }) }) })), (0, jsx_runtime_1.jsx)("div", { ref: scrollRef })] }) }), (0, jsx_runtime_1.jsxs)("div", { className: "p-4 border-t border-border bg-background", children: [(0, jsx_runtime_1.jsxs)("div", { className: "flex gap-2", children: [(0, jsx_runtime_1.jsx)(input_1.Input, { value: input, onChange: (e) => setInput(e.target.value), onKeyDown: handleKeyDown, placeholder: "Type your answer...", disabled: isLoading, className: "flex-1", autoFocus: true }), (0, jsx_runtime_1.jsx)(button_1.Button, { onClick: () => handleSend(input), disabled: isLoading || !input.trim(), size: "icon", children: (0, jsx_runtime_1.jsx)(lucide_react_1.Send, { className: "h-4 w-4" }) })] }), (0, jsx_runtime_1.jsxs)("div", { className: "mt-2 text-xs text-center text-muted-foreground", children: ["Type ", (0, jsx_runtime_1.jsx)("strong", { children: "/done" }), " when you are ready to generate the design."] })] })] }));
};
exports.InterviewView = InterviewView;
