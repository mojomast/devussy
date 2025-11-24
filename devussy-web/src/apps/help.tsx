import React from "react";
import type { AppDefinition } from "./appTypes";
import { HelpCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HelpViewProps {
  onClose?: () => void;
}

const HelpView: React.FC<HelpViewProps> = ({ onClose }) => {
  // Help preferences
  const [dontShowHelpAgain, setDontShowHelpAgain] = React.useState<boolean>(() => {
    try { return localStorage.getItem('devussy_help_dismissed') === '1'; } catch (e) { return false; }
  });

  const [analyticsOptOut, setAnalyticsOptOut] = React.useState<boolean>(false);

  React.useEffect(() => {
    try {
      const cookies = document.cookie.split(';').map(c => c.trim());
      const cookie = cookies.find(c => c.startsWith('devussy_analytics_optout='));
      if (cookie) {
        const value = (cookie.split('=')[1] || '').toLowerCase();
        if (value === '1' || value === 'true' || value === 'yes') {
          setAnalyticsOptOut(true);
        }
      }
    } catch (e) { }
  }, []);

  return (
    <div className="h-full overflow-auto p-6 prose prose-invert max-w-none">
      <h1 className="text-2xl font-bold mb-4">Devussy Studio Help</h1>
      <div className="rounded-md p-3 bg-background/80 text-sm text-muted-foreground mb-4">
        <strong className="text-primary">Public Demo:</strong> This is a limited time public demo for Devussy. It is in constant development and things may break at times, but we're working on it! Please avoid putting any sensitive secrets here. Thank you for trying Devussy Studio.
      </div>

      <h2 className="text-xl font-semibold mt-6 mb-3">Getting Started</h2>
      <p>Devussy Studio is an AI-powered development pipeline that takes you from requirements to deployment-ready code.</p>

      <h3 className="text-lg font-semibold mt-4 mb-2">Pipeline Stages:</h3>
      <ol className="list-decimal list-inside space-y-2">
        <li><strong>Interview</strong> - Interactive chat to gather requirements</li>
        <li><strong>Design</strong> - Generate system architecture and design</li>
        <li><strong>Plan</strong> - Create detailed development plan with phases</li>
        <li><strong>Execute</strong> - Generate code for each phase</li>
        <li><strong>Handoff</strong> - Export project and push to GitHub</li>
      </ol>

      <h2 className="text-xl font-semibold mt-6 mb-3">IRC Chat Addon</h2>
      <p>Devussy now includes a built-in IRC client accessible via the taskbar or desktop icon.</p>
      <ul className="list-disc list-inside space-y-1">
        <li>Join <code className="bg-gray-800 px-2 py-1 rounded">#devussy-chat</code> to chat with other users</li>
        <li>Click on usernames to start private messages</li>
        <li>Server logs are collected in the <strong>Status</strong> tab</li>
        <li>Your IRC nickname is saved automatically</li>
      </ul>
      <h2 className="text-xl font-semibold mt-6 mb-3">Circular Stateless Development</h2>
      <p>Devussy enables <strong>agent-agnostic, stateless development</strong> where any AI agent can pick up where another left off.</p>

      <h3 className="text-lg font-semibold mt-4 mb-2">How It Works:</h3>
      <ol className="list-decimal list-inside space-y-2">
        <li><strong>Generate Plan</strong> - Use Devussy to create a comprehensive development plan</li>
        <li><strong>Export Handoff</strong> - Download the plan, design, and context as a zip file</li>
        <li><strong>Share with Any Agent</strong> - Give the handoff document to any AI coding assistant (Claude, GPT, Gemini, etc.)</li>
        <li><strong>Agent Reads Context</strong> - Tell the agent: <code className="bg-gray-800 px-2 py-1 rounded">"Read the handoff.md file and implement the next phase"</code></li>
        <li><strong>Iterate</strong> - Different agents can work on different phases, all following the same plan</li>
      </ol>
      <h3 className="text-lg font-semibold mt-4 mb-2">Key Benefits:</h3>
      <ul className="list-disc list-inside space-y-1">
        <li><strong>No vendor lock-in</strong> - Switch between AI providers freely</li>
        <li><strong>Consistent quality</strong> - All agents follow the same plan</li>
        <li><strong>Parallel development</strong> - Multiple agents can work on different phases</li>
        <li><strong>Full context</strong> - Handoff document contains everything needed</li>
      </ul>
      <h2 className="text-xl font-semibold mt-6 mb-3">Tips</h2>
      <ul className="list-disc list-inside space-y-1">
        <li>Use <strong>checkpoints</strong> to save your progress at any stage</li>
        <li>Edit phases in the Plan view before execution</li>
        <li>Adjust <strong>concurrency</strong> in settings to control parallel execution</li>
        <li>Windows can be minimized - find them in the taskbar</li>
        <li>Use the <strong>Start Menu</strong> (Bliss theme) or taskbar to access all features</li>
      </ul>
      <h2 className="text-xl font-semibold mt-6 mb-3">Need More Help?</h2>
      <p>Check the <code className="bg-gray-800 px-2 py-1 rounded">handoff.md</code> file in your project for detailed technical documentation.</p>

      <h2 className="text-xl font-semibold mt-6 mb-3">Credits</h2>
      <p>Created by <strong>Kyle Durepos</strong>.</p>

      <div className="mt-6 flex items-center justify-between">
        <div className="flex flex-col gap-2">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={dontShowHelpAgain}
              onChange={(e) => {
                const v = e.target.checked;
                try { localStorage.setItem('devussy_help_dismissed', v ? '1' : '0'); } catch (err) { }
                setDontShowHelpAgain(v);
              }}
            />
            Don't show this again
          </label>
          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={analyticsOptOut}
              onChange={(e) => {
                const v = e.target.checked;
                try {
                  const expires = new Date();
                  expires.setFullYear(expires.getFullYear() + 1);
                  document.cookie = `devussy_analytics_optout=${v ? '1' : '0'}; path=/; expires=${expires.toUTCString()}; SameSite=Lax`;
                } catch (err) { }
                setAnalyticsOptOut(v);
              }}
            />
            Disable anonymous usage analytics for this browser
          </label>
        </div>
        <div>
          <Button variant="secondary" onClick={() => onClose?.()}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};

const HelpApp: AppDefinition = {
  id: "help",
  name: "Devussy Studio Help",
  icon: <HelpCircle className="w-4 h-4" />,
  defaultSize: { width: 700, height: 600 },
  startMenuCategory: "Most Used",
  singleInstance: true,
  component: HelpView,
};

export default HelpApp;
