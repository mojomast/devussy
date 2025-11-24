import React from "react";
import type { AppDefinition, AppContext } from "./appTypes";
import { StickyNote } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface ScratchpadViewProps {
  onClose?: () => void;
  appContext?: AppContext;
}

const ScratchpadView: React.FC<ScratchpadViewProps> = ({ onClose, appContext }) => {
  const [text, setText] = React.useState<string>(() => {
    try {
      const state = appContext?.getState?.();
      if (state && typeof state === "object" && typeof (state as any).scratchpad === "string") {
        return (state as any).scratchpad as string;
      }
    } catch (err) {}

    try {
      const stored = localStorage.getItem("devussy_scratchpad");
      if (typeof stored === "string") {
        return stored;
      }
    } catch (err) {}

    return "";
  });

  const handleChange: React.ChangeEventHandler<HTMLTextAreaElement> = (event) => {
    const value = event.target.value;
    setText(value);

    try {
      localStorage.setItem("devussy_scratchpad", value);
    } catch (err) {}

    try {
      if (appContext?.setState) {
        appContext.setState((prev: any) => ({ ...(prev || {}), scratchpad: value }));
      }
    } catch (err) {
      console.error("[Scratchpad] Failed to persist to AppContext", err);
    }
  };

  const handleClear = () => {
    setText("");
    try {
      localStorage.removeItem("devussy_scratchpad");
    } catch (err) {}
    try {
      if (appContext?.setState) {
        appContext.setState((prev: any) => {
          const next = { ...(prev || {}) };
          if (Object.prototype.hasOwnProperty.call(next, "scratchpad")) {
            delete (next as any).scratchpad;
          }
          return next;
        });
      }
    } catch (err) {
      console.error("[Scratchpad] Failed to clear AppContext state", err);
    }
  };

  return (
    <div className="h-full flex flex-col p-4 gap-3">
      <Card className="flex-1 flex flex-col">
        <CardHeader className="pb-2 flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-base">
            <StickyNote className="w-4 h-4" />
            Scratchpad
          </CardTitle>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
          )}
        </CardHeader>
        <div className="px-4 pb-4 flex-1 flex flex-col">
          <Textarea
            className="flex-1 resize-none text-sm"
            placeholder="Jot down notes, TODOs, or prompts to share with other windows via AppContext."
            value={text}
            onChange={handleChange}
          />
          <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
            <span>Scratchpad content persists in this browser and shared AppContext.</span>
            <Button variant="outline" size="sm" onClick={handleClear} disabled={!text}>
              Clear
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

const ScratchpadApp: AppDefinition = {
  id: "scratchpad",
  name: "Scratchpad",
  icon: <StickyNote className="w-4 h-4" />,
  defaultSize: { width: 520, height: 420 },
  startMenuCategory: "Devussy",
  singleInstance: true,
  component: ScratchpadView,
};

export default ScratchpadApp;
