import React from "react";
import type { AppDefinition, AppContext } from "./appTypes";
import { ClipboardList, Sparkles, Share2, Box, GitBranch } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

interface DevplanProgressViewProps {
  onClose?: () => void;
  appContext?: AppContext;
}

const DevplanProgressView: React.FC<DevplanProgressViewProps> = ({ onClose }) => {
  return (
    <div className="h-full flex flex-col p-4 gap-4">
      <Card className="flex-shrink-0">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <ClipboardList className="w-5 h-5 text-primary" />
              <div>
                <CardTitle className="text-base">App Framework Progress</CardTitle>
                <CardDescription className="text-xs">
                  Snapshot of the DevPlan implementation for the Devussy application framework.
                </CardDescription>
              </div>
            </div>
            {onClose && (
              <Button size="sm" variant="outline" onClick={onClose}>
                Close
              </Button>
            )}
          </div>
        </CardHeader>
      </Card>

      <ScrollArea className="flex-1 rounded-md border bg-background/40 p-4">
        <div className="space-y-6 text-sm leading-relaxed">
          <section className="space-y-1">
            <div className="flex items-center gap-2 font-medium">
              <Sparkles className="w-4 h-4 text-primary" />
              <span>App Registry & Window Manager</span>
            </div>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>Central <code>AppRegistry</code> now drives window types via <code>WindowType = keyof typeof AppRegistry</code>.</li>
              <li>Core pipeline apps (<code>interview</code>, <code>design</code>, <code>plan</code>, <code>execute</code>, <code>handoff</code>) and utilities (<code>help</code>, <code>model-settings</code>, <code>pipeline</code>, <code>scratchpad</code>, <code>irc</code>) are all registry-driven.</li>
              <li>Single-instance semantics are respected for apps that declare <code>singleInstance: true</code>.</li>
            </ul>
          </section>

          <section className="space-y-1">
            <div className="flex items-center gap-2 font-medium">
              <Share2 className="w-4 h-4 text-primary" />
              <span>Share Links & Cross-App Flow</span>
            </div>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li><code>generateShareLink(stage, data)</code> and <code>decodeSharePayload</code> helpers implemented in <code>shareLinks.ts</code> using JSON + base64-url.</li>
              <li><code>/share</code> route reads the payload, shows a summary, persists it to <code>sessionStorage</code>, and offers an "Open Devussy" path back to the desktop.</li>
              <li><code>IrcClient</code> detects share links in chat, renders them as in-app buttons, and emits an <code>openShareLink</code> event over the event bus.</li>
              <li>Main desktop page subscribes to <code>openShareLink</code> and restores pipeline state via <code>handleLoadCheckpoint</code>, spawning the correct stage window.</li>
            </ul>
          </section>

          <section className="space-y-1">
            <div className="flex items-center gap-2 font-medium">
              <Box className="w-4 h-4 text-primary" />
              <span>Event Bus & AppContext</span>
            </div>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>Global typed <code>EventBus</code> exposes lifecycle events like <code>interviewCompleted</code>, <code>designCompleted</code>, <code>planGenerated</code>, <code>executionStarted</code>, <code>executionPhaseUpdated</code>, and <code>executionCompleted</code>.</li>
              <li><code>createAppContext(bus)</code> wraps the event bus to provide <code>emit</code>, <code>subscribe</code>, <code>getState</code>, and <code>setState</code> for registry apps.</li>
              <li>Apps like IRC and Scratchpad use <code>AppContext</code> to coordinate shared state and messaging without touching the window manager.</li>
            </ul>
          </section>

          <section className="space-y-1">
            <div className="flex items-center gap-2 font-medium">
              <GitBranch className="w-4 h-4 text-primary" />
              <span>Compose & Nginx Generation</span>
            </div>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>Apps can declare <code>services</code>, <code>proxy</code>, and <code>env</code> blocks in their <code>AppDefinition</code>.</li>
              <li><code>scripts/generate-compose.ts</code> consumes these definitions to build Docker Compose overlays and Nginx fragments (e.g., IRC <code>/apps/irc/ws/</code> WebSocket proxy).</li>
              <li>Integration tests in <code>tests/integration/test_compose_generator.py</code> assert that generated compose/nginx files contain the expected IRC wiring.</li>
            </ul>
          </section>

          <section className="space-y-1">
            <div className="flex items-center gap-2 font-medium">
              <ClipboardList className="w-4 h-4 text-primary" />
              <span>Testing & Regression Harness</span>
            </div>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              <li>Integration tests cover share link round-trips, event bus notifications, compose generation, and window manager/AppRegistry invariants.</li>
              <li>Suite is designed as a baseline regression harness for future apps and richer <code>AppContext</code> usage.</li>
            </ul>
          </section>
        </div>
      </ScrollArea>
    </div>
  );
};

const DevplanProgressApp: AppDefinition = {
  id: "devplan-progress",
  name: "App Framework Progress",
  icon: <ClipboardList className="w-4 h-4" />,
  defaultSize: { width: 760, height: 540 },
  startMenuCategory: "Devussy",
  singleInstance: true,
  component: DevplanProgressView,
};

export default DevplanProgressApp;
